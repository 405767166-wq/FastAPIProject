"""原生任务队列：asyncio.Queue（M4 考核点，V1 默认实现）。"""

from __future__ import annotations

import asyncio

from app.queue.base import TaskQueue


class NativeTaskQueue(TaskQueue):
    """单进程内 生产者(API) → 消费者(worker) 解耦。

    与 FastAPI 同一事件循环：API 层 `push()` 不阻塞，worker 协程 `await pop()` 阻塞消费。
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict] = asyncio.Queue()

    def push(self, task: dict) -> None:
        self._queue.put_nowait(task)

    async def pop(self) -> dict:
        return await self._queue.get()

    @property
    def size(self) -> int:
        """当前在途任务数（健康检查/观测用）。"""
        return self._queue.qsize()
