import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.research_agent import estimate_cost_usd, run_agent, stream_agent
from app.database import get_db
from app.deps import get_current_user
from app.models import Conversation, Document, Message, UsageRecord, User
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def _conversation_history(conv: Conversation) -> list[dict[str, str]]:
    return [
        {"role": m.role, "content": m.content}
        for m in conv.messages
        if m.role in ("user", "assistant") and m.content
    ]


def _resolve_namespaces(db: Session, user_id: int, document_ids: list[int]) -> list[str]:
    if not document_ids:
        return []
    rows = (
        db.query(Document.vector_namespace)
        .filter(Document.user_id == user_id, Document.id.in_(document_ids))
        .all()
    )
    return [r[0] for r in rows]


def _ensure_conversation(
    db: Session, user: User, conversation_id: int | None, provider: str, first_query: str
) -> Conversation:
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv
    title = first_query[:60] + ("…" if len(first_query) > 60 else "")
    conv = Conversation(user_id=user.id, title=title, provider=provider)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Non-streaming chat endpoint — returns full response in one JSON object."""
    conv = _ensure_conversation(db, user, request.conversation_id, request.provider, request.query)
    history = _conversation_history(conv)
    namespaces = _resolve_namespaces(db, user.id, request.document_ids) if request.use_rag else []

    run = await run_agent(
        user_query=request.query,
        history=history,
        provider_pref=request.provider,
        rag_namespaces=namespaces,
    )

    user_msg = Message(conversation_id=conv.id, role="user", content=request.query)
    bot_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=run.answer,
        tokens=run.tokens,
        latency_ms=run.latency_ms,
        tool_calls={"tools_used": run.tools_used} if run.tools_used else None,
    )
    db.add_all([user_msg, bot_msg])

    db.add(
        UsageRecord(
            user_id=user.id,
            provider=run.provider,
            model=run.model,
            prompt_tokens=0,
            completion_tokens=run.tokens,
            latency_ms=run.latency_ms,
            cost_usd=estimate_cost_usd(run.provider, 0, run.tokens),
        )
    )
    db.commit()
    db.refresh(bot_msg)

    return ChatResponse(
        conversation_id=conv.id,
        message_id=bot_msg.id,
        answer=run.answer,
        provider=run.provider,
        model=run.model,
        tokens=run.tokens,
        latency_ms=run.latency_ms,
        tools_used=run.tools_used,
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Server-Sent Events streaming endpoint."""
    conv = _ensure_conversation(db, user, request.conversation_id, request.provider, request.query)
    history = _conversation_history(conv)
    namespaces = _resolve_namespaces(db, user.id, request.document_ids) if request.use_rag else []

    # Persist the user message immediately so it shows up even if streaming aborts
    user_msg = Message(conversation_id=conv.id, role="user", content=request.query)
    db.add(user_msg)
    db.commit()

    conv_id = conv.id
    user_id = user.id

    async def event_source():
        # Emit conversation_id up front so the client can attach
        yield f"event: meta\ndata: {json.dumps({'conversation_id': conv_id})}\n\n"
        final_payload: dict | None = None
        try:
            async for event in stream_agent(
                user_query=request.query,
                history=history,
                provider_pref=request.provider,
                rag_namespaces=namespaces,
            ):
                if event["event"] == "done":
                    final_payload = event["data"]
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming failed")
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
            return

        # Persist assistant message after stream completes
        if final_payload:
            from app.database import SessionLocal

            db2 = SessionLocal()
            try:
                bot_msg = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=final_payload.get("answer", ""),
                    tokens=final_payload.get("tokens", 0),
                    latency_ms=final_payload.get("latency_ms", 0),
                    tool_calls=(
                        {"tools_used": final_payload.get("tools_used", [])}
                        if final_payload.get("tools_used")
                        else None
                    ),
                )
                db2.add(bot_msg)
                db2.add(
                    UsageRecord(
                        user_id=user_id,
                        provider=final_payload.get("provider", "unknown"),
                        model=final_payload.get("model", "unknown"),
                        completion_tokens=final_payload.get("tokens", 0),
                        latency_ms=final_payload.get("latency_ms", 0),
                        cost_usd=estimate_cost_usd(
                            final_payload.get("provider", ""),
                            0,
                            final_payload.get("tokens", 0),
                        ),
                    )
                )
                db2.commit()
                yield f"event: saved\ndata: {json.dumps({'message_id': bot_msg.id})}\n\n"
            finally:
                db2.close()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
