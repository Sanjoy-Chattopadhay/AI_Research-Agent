from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Chat ----
class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    conversation_id: int | None = None
    provider: Literal["groq", "openrouter", "hf", "ollama", "openai", "auto"] = "auto"
    use_rag: bool = False
    document_ids: list[int] = Field(default_factory=list)
    stream: bool = True


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    provider: str
    model: str
    tokens: int
    latency_ms: int
    tools_used: list[str] = Field(default_factory=list)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tokens: int
    latency_ms: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    id: int
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


# ---- Documents ----
class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    num_chunks: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Feedback ----
class FeedbackCreate(BaseModel):
    message_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comment: str = ""


# ---- Metrics ----
class MetricsOut(BaseModel):
    total_conversations: int
    total_messages: int
    total_tokens: int
    total_latency_ms: int
    by_provider: dict[str, Any]
