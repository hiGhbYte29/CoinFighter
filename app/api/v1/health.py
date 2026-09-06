import os

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(request: Request) -> dict:
    settings = request.app.state.settings
    writable = os.access(settings.local_data_dir, os.W_OK)
    return {
        "status": "ready" if writable else "degraded",
        "storage": "writable" if writable else "read-only",
        "provider": settings.default_provider,
    }
