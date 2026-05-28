"""Free, no-API-key tools for the research agent.

All tools here use libraries that do NOT require paid API keys:
- DuckDuckGo web search via `ddgs`
- arXiv via `arxiv`
- Wikipedia via `wikipedia`
- A safe Python math evaluator for arithmetic
"""
from __future__ import annotations

import ast
import logging
import operator
from typing import Any, Callable

import wikipedia
from ddgs import DDGS

logger = logging.getLogger(__name__)


# ---------------- safe arithmetic ----------------
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}
_UN_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN_OPS:
        return _UN_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    try:
        result = _eval_node(ast.parse(expression, mode="eval").body)
        return f"{expression} = {result}"
    except Exception as exc:
        return f"Calculator error: {exc}"


# ---------------- web search ----------------
def web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No web results found."
        out = []
        for r in results:
            title = r.get("title", "")
            href = r.get("href") or r.get("url", "")
            body = r.get("body", "")
            out.append(f"- {title}\n  {href}\n  {body}")
        return "\n".join(out)
    except Exception as exc:
        logger.exception("DuckDuckGo search failed")
        return f"Web search error: {exc}"


# ---------------- Wikipedia ----------------
def wikipedia_search(query: str, sentences: int = 5) -> str:
    try:
        candidates = wikipedia.search(query, results=3)
        if not candidates:
            return "No Wikipedia results."
        try:
            summary = wikipedia.summary(candidates[0], sentences=sentences, auto_suggest=False)
        except wikipedia.DisambiguationError as exc:
            summary = wikipedia.summary(exc.options[0], sentences=sentences, auto_suggest=False)
        return f"Wikipedia — {candidates[0]}:\n{summary}"
    except Exception as exc:
        return f"Wikipedia error: {exc}"


# ---------------- arXiv ----------------
def arxiv_search(query: str, max_results: int = 5) -> str:
    try:
        import arxiv  # imported lazily — heavy dependency

        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        out = []
        for paper in search.results():
            authors = ", ".join(a.name for a in paper.authors[:3])
            out.append(
                f"- {paper.title}\n  Authors: {authors}\n  Published: {paper.published.date()}\n"
                f"  URL: {paper.entry_id}\n  Summary: {paper.summary[:400].strip()}..."
            )
        return "\n".join(out) if out else "No arXiv results."
    except Exception as exc:
        return f"arXiv error: {exc}"


# ---------------- Tool registry ----------------
TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    "web_search": web_search,
    "wikipedia_search": wikipedia_search,
    "arxiv_search": arxiv_search,
    "calculator": calculator,
}


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the live web with DuckDuckGo. Use for recent news, current events, "
                "or general factual lookups. Returns titles, URLs, and snippets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Fetch a short Wikipedia summary for a topic. Best for definitions and background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "sentences": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "arxiv_search",
            "description": "Search arXiv for academic papers. Returns titles, authors, dates, URLs, and abstracts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Safely evaluate an arithmetic expression (e.g. '2 * (3 + 4) ** 2').",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]


def call_tool(name: str, **kwargs) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(**kwargs)
    except TypeError as exc:
        return f"Bad arguments to {name}: {exc}"
