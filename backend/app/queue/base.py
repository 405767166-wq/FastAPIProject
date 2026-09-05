"""任务队列抽象（M4）。

V1：`NativeTaskQueue`（asyncio.Queue，考核点，默认）。
V2：`RedisQueue`（Redis List：LPUSH / BRPOP，配好 REDIS_URL 自动启用）。
业务层只依赖本接口，不感知实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TaskQueue(ABC):
    @abstractmethod
    def push(self, task: dict) -> None:
        """生产者入队（不阻塞）。task 形如 {meeting_id, file_path, title, ...}。"""

    @abstractmethod
    async def pop(self) -> dict:
        """消费者出队（阻塞直到有任务）。"""
