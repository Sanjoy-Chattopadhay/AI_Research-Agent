from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "AI Research Agent"
    app_version: str = "3.0.0"
    environment: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"
    cors_origins: str = "*"

    # --- Database ---
    database_url: str = "sqlite:///./data/app.db"

    # --- Auth ---
    secret_key: str = Field(
        default="change-me-in-production-this-is-only-a-dev-default-key-do-not-ship",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # --- LLM providers (any one is enough; first configured wins) ---
    # Groq — https://console.groq.com  (free, very fast, OpenAI-compatible)
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenRouter — https://openrouter.ai  (free models available)
    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Hugging Face Inference — https://huggingface.co/settings/tokens
    hf_api_key: str | None = None
    hf_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # Ollama (local, fully offline)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2"

    # OpenAI (optional fallback)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Default provider order — first available is used
    default_provider: Literal["groq", "openrouter", "hf", "ollama", "openai"] = "groq"

    # --- RAG / embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_dir: str = "./data/vector_store"
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 20

    # --- Rate limiting ---
    rate_limit_per_minute: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
