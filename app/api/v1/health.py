import os

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    """检查应用进程是否正常存活。"""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(request: Request) -> dict:
    """检查应用依赖是否已就绪。"""
    settings = request.app.state.settings
    writable = os.access(settings.local_data_dir, os.W_OK)
    return {
        "status": "ready" if writable else "degraded",
        "storage": "writable" if writable else "read-only",
        "provider": settings.default_provider,
    }
