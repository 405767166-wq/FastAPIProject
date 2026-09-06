"""FastAPI 装配入口（V1 骨架）。

启动方式（backend 目录下）：
    uvicorn app.main:app --reload --port 8000

生命周期：启动时拉起后台 worker 消费任务队列；关闭时优雅取消。
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api import api_router
from app.config import settings
from app.errors import ApiError
from app.queue.native_queue import NativeTaskQueue
from app.responses import error
from app.store.base import MeetingStore
from app.store.memory import MemoryStore
from app.worker import Worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_store() -> MeetingStore:
    """V1：内存存储。V2：settings.storage_backend == "mysql" 时换 MySQLStore。"""
    return MemoryStore()


def build_queue():
    """V1：原生 asyncio.Queue。V2：settings.queue_backend == "redis" 时换 RedisQueue。"""
    return NativeTaskQueue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = build_store()
    queue = build_queue()
    worker = Worker(queue=queue, store=store)

    app.state.store = store
    app.state.queue = queue
    app.state.worker = worker

    worker_task = asyncio.create_task(worker.run())
    logger.info("应用启动：storage=%s queue=%s asr=%s upload_dir=%s",
                settings.storage_backend, settings.queue_backend,
                settings.asr_provider, settings.upload_dir)
    try:
        yield
    finally:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task
        logger.info("应用关闭：worker 已停止")


app = FastAPI(
    title="会议纪要智能转写系统",
    description="V1：基本功能（原生队列/内存存储/Mock ASR/模板总结/全 REST）；V2 见 版本规划.md",
    version=__version__,
    lifespan=lifespan,
)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """业务异常 → 统一响应体 {code, message, data} + 对应 HTTP 状态码。"""
    return JSONResponse(
        status_code=exc.http_status,
        content=error(exc.code, exc.message, exc.data),
    )


app.include_router(api_router)
