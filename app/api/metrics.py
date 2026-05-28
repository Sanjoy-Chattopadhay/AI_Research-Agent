from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Conversation, Feedback, Message, UsageRecord, User
from app.schemas import FeedbackCreate, MetricsOut

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsOut)
def my_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_conversations = (
        db.query(func.count(Conversation.id)).filter(Conversation.user_id == user.id).scalar() or 0
    )
    total_messages = (
        db.query(func.count(Message.id))
        .join(Conversation)
        .filter(Conversation.user_id == user.id)
        .scalar()
        or 0
    )
    rows = db.query(UsageRecord).filter(UsageRecord.user_id == user.id).all()

    total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in rows)
    total_latency = sum(r.latency_ms for r in rows)

    by_provider: dict[str, dict] = defaultdict(
        lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0, "avg_latency_ms": 0}
    )
    for r in rows:
        bp = by_provider[r.provider]
        bp["calls"] += 1
        bp["tokens"] += r.prompt_tokens + r.completion_tokens
        bp["cost_usd"] += r.cost_usd
        bp["avg_latency_ms"] += r.latency_ms
    for stats in by_provider.values():
        if stats["calls"]:
            stats["avg_latency_ms"] = stats["avg_latency_ms"] // stats["calls"]
            stats["cost_usd"] = round(stats["cost_usd"], 6)

    return MetricsOut(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tokens=total_tokens,
        total_latency_ms=total_latency,
        by_provider=dict(by_provider),
    )


feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


@feedback_router.post("", status_code=201)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fb = Feedback(
        user_id=user.id,
        message_id=payload.message_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}
