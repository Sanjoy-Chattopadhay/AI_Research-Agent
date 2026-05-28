from datetime import datetime, timezone

from fastapi import APIRouter

from app.agents.providers import available_providers
from app.config import get_settings

settings = get_settings()
router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    providers = [p.name for p in available_providers()]
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "providers_configured": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/providers")
def providers():
    return [
        {"name": p.name, "model": p.model, "base_url": p.base_url}
        for p in available_providers()
    ]
