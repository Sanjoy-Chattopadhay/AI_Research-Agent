"""Core research agent loop.

We implement a small tool-calling ReAct loop ourselves rather than depending on
the moving target that is LangChain agent APIs. The agent:

1. Plans with the LLM, which may emit one or more tool calls.
2. Executes tools (web/wiki/arxiv/calculator + optional RAG).
3. Feeds tool results back into the conversation.
4. Once the model stops asking for tools, streams the final answer to the user.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from app.agents import rag
from app.agents.providers import LLMClient, ProviderConfig, parse_tool_arguments, pick_provider
from app.agents.tools import TOOL_SCHEMAS, call_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Research Assistant.

You can answer using:
- Your own knowledge.
- The tools provided (web_search, wikipedia_search, arxiv_search, calculator).
- Context from the user's uploaded documents (RAG) when supplied below.

Guidelines:
1. Use tools when the question needs fresh, specific, or authoritative information.
2. Prefer arxiv_search for academic / research / paper questions.
3. Prefer web_search for recent news, products, or non-academic facts.
4. Cite URLs inline as [source](url) when you use them.
5. Be concise, structured (use short headers / bullets when useful), and analytical.
6. If you don't know, say so — never fabricate citations or numbers.
"""

MAX_TOOL_ITERATIONS = 4


@dataclass
class AgentRun:
    answer: str = ""
    tools_used: list[str] = field(default_factory=list)
    tokens: int = 0
    latency_ms: int = 0
    provider: str = ""
    model: str = ""


def _build_messages(
    history: list[dict[str, str]],
    user_query: str,
    rag_context: str | None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-12:]:  # cap recent history
        messages.append({"role": h["role"], "content": h["content"]})
    if rag_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Relevant excerpts from the user's uploaded documents are below. "
                    "Use them when answering and cite them as [doc] when you do.\n\n"
                    f"{rag_context}"
                ),
            }
        )
    messages.append({"role": "user", "content": user_query})
    return messages


async def _tool_loop(
    client: LLMClient, messages: list[dict[str, Any]], run: AgentRun
) -> str:
    """Run tool-calls until the model produces a final answer (no more tool_calls).
    Returns the final assistant content."""
    for _ in range(MAX_TOOL_ITERATIONS):
        completion = await client.chat(messages=messages, tools=TOOL_SCHEMAS, temperature=0.3)
        msg = completion.choices[0].message
        usage = getattr(completion, "usage", None)
        if usage:
            run.tokens += getattr(usage, "total_tokens", 0) or 0

        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            return msg.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            name = tc.function.name
            args = parse_tool_arguments(tc.function.arguments)
            logger.info("tool=%s args=%s", name, args)
            run.tools_used.append(name)
            result = call_tool(name, **args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": result[:6000],
                }
            )

    # Hit the iteration cap — force one final answer with no tools.
    final = await client.chat(messages=messages, tools=None, temperature=0.3)
    if getattr(final, "usage", None):
        run.tokens += getattr(final.usage, "total_tokens", 0) or 0
    return final.choices[0].message.content or ""


async def run_agent(
    user_query: str,
    history: list[dict[str, str]] | None = None,
    provider_pref: str = "auto",
    rag_namespaces: list[str] | None = None,
) -> AgentRun:
    """Non-streaming agent run — returns final answer."""
    start = time.perf_counter()
    cfg: ProviderConfig = pick_provider(provider_pref)
    client = LLMClient(cfg)

    rag_context = _gather_rag_context(user_query, rag_namespaces or [])
    messages = _build_messages(history or [], user_query, rag_context)

    run = AgentRun(provider=cfg.name, model=cfg.model)
    run.answer = await _tool_loop(client, messages, run)
    run.latency_ms = int((time.perf_counter() - start) * 1000)
    return run


async def stream_agent(
    user_query: str,
    history: list[dict[str, str]] | None = None,
    provider_pref: str = "auto",
    rag_namespaces: list[str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yields SSE-style events: {'event': 'tool'|'token'|'done', ...}."""
    start = time.perf_counter()
    cfg = pick_provider(provider_pref)
    client = LLMClient(cfg)
    run = AgentRun(provider=cfg.name, model=cfg.model)

    yield {"event": "status", "data": {"message": f"Using {cfg.name}:{cfg.model}"}}

    rag_context = _gather_rag_context(user_query, rag_namespaces or [])
    if rag_context:
        yield {"event": "status", "data": {"message": "Retrieved document context"}}

    messages = _build_messages(history or [], user_query, rag_context)

    # Tool-calling phase (non-streaming) — keep going until model stops asking for tools.
    final_content_from_loop = ""
    used_tools = False
    for _ in range(MAX_TOOL_ITERATIONS):
        completion = await client.chat(messages=messages, tools=TOOL_SCHEMAS, temperature=0.3)
        msg = completion.choices[0].message
        usage = getattr(completion, "usage", None)
        if usage:
            run.tokens += getattr(usage, "total_tokens", 0) or 0

        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            final_content_from_loop = msg.content or ""
            break

        used_tools = True
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            name = tc.function.name
            args = parse_tool_arguments(tc.function.arguments)
            run.tools_used.append(name)
            yield {"event": "tool", "data": {"name": name, "args": args}}
            result = call_tool(name, **args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": result[:6000],
                }
            )

    # Stream the final answer.
    # If the model already produced the final content WITHOUT tools, just stream that
    # text in chunks (no second LLM call). Otherwise, ask for a fresh streamed answer.
    answer_parts: list[str] = []
    if final_content_from_loop and not used_tools:
        # No tools were needed — emit the content we already have in small chunks.
        text = final_content_from_loop
        chunk = 64
        for i in range(0, len(text), chunk):
            piece = text[i : i + chunk]
            answer_parts.append(piece)
            yield {"event": "token", "data": {"text": piece}}
    else:
        # Tools were used — stream a fresh synthesis call.
        async for token in client.stream(messages=messages, temperature=0.3):
            answer_parts.append(token)
            yield {"event": "token", "data": {"text": token}}

    run.answer = "".join(answer_parts)
    run.latency_ms = int((time.perf_counter() - start) * 1000)
    yield {
        "event": "done",
        "data": {
            "answer": run.answer,
            "tools_used": run.tools_used,
            "tokens": run.tokens,
            "latency_ms": run.latency_ms,
            "provider": run.provider,
            "model": run.model,
        },
    }


def _gather_rag_context(query: str, namespaces: list[str]) -> str:
    if not namespaces:
        return ""
    chunks: list[str] = []
    for ns in namespaces:
        ctx = rag.build_context(ns, query, k=4)
        if ctx:
            chunks.append(ctx)
    return "\n\n---\n\n".join(chunks)


def estimate_cost_usd(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Very rough cost estimate — free providers return 0."""
    rates = {
        "openai": (0.150 / 1_000_000, 0.600 / 1_000_000),  # gpt-4o-mini
        "openrouter": (0.0, 0.0),  # free-tier model assumed
        "groq": (0.0, 0.0),
        "hf": (0.0, 0.0),
        "ollama": (0.0, 0.0),
    }
    pr, cr = rates.get(provider, (0.0, 0.0))
    return prompt_tokens * pr + completion_tokens * cr
