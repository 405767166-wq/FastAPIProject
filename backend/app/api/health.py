"""健康检查：GET /api/health（对应 接口文档.md §5.10）。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app import __version__
from app.config import settings
from app.responses import ok

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    queue = request.app.state.queue
    store = request.app.state.store
    return ok({
        "status": "up",
        "version": __version__,
        "mode": "native",                     # V1：原生队列；V2 redis 时置 redis
        "queue": settings.queue_backend,      # native | redis
        "queue_size": queue.size,             # 在途任务数
        "storage": settings.storage_backend,  # memory | mysql
        "asr": settings.asr_provider,         # mock | baidu | ...
        "mysql": False,
        "redis": False,
        # 供观测使用（不暴露内部结构）
        "meetings": store.list_meetings(page=1, page_size=1)[0],
    })
