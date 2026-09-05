"""M11 worker：后台消费循环（与 FastAPI 同进程，随应用生命周期启停）。

链路（V1 步骤 3 实现）：
    pop 任务 → status=processing → M6 分块 → M7 ASR(mock) 逐块 →
    M5 词频(Counter) → M8 模板总结 → M10 落存储 → status=completed
失败：try/except + error_message 落库，不静默丢失。
"""

from __future__ import annotations

import logging

from app.queue.base import TaskQueue
from app.store.base import MeetingStore

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, queue: TaskQueue, store: MeetingStore) -> None:
        self._queue = queue
        self._store = store

    async def run(self) -> None:
        """消费循环：被 FastAPI lifespan 作为后台任务拉起，关闭时取消。"""
        logger.info("worker 已启动，开始消费任务队列")
        while True:
            task = await self._queue.pop()
            await self._handle(task)

    async def _handle(self, task: dict) -> None:
        meeting_id = task.get("meeting_id", "")
        try:
            logger.info("处理任务 meeting_id=%s（骨架占位）", meeting_id)
            # TODO(V1 步骤 3): 更新 processing → 分块 → mock ASR → 词频 → 模板总结 → 落库 completed
            raise NotImplementedError("处理管线尚未实现（V1 骨架阶段）")
        except Exception as exc:  # noqa: BLE001 - worker 不允许静默丢失任务
            logger.exception("任务处理失败 meeting_id=%s", meeting_id)
            self._store.update_meeting(
                meeting_id,
                status="failed",
                error_message=str(exc)[:512],
            )
