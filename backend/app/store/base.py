"""M10 存储抽象：会议记录 + 词频。

V1：`MemoryStore`（内存 dict，重启即失，兜底模式，不依赖 MySQL）。
V2：`MySQLStore`（服务器 MySQL + SQLAlchemy，配好 MYSQL_HOST 自动启用）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class MeetingStore(ABC):
    """会议与词频的存储协议（API 层与 worker 层都只依赖本接口）。"""

    @abstractmethod
    def create_meeting(self, *, meeting_id: str, title: str, file_name: str,
                       file_path: str, file_size: int, **extra) -> dict:
        """新建记录（status=queued），返回完整记录。"""

    @abstractmethod
    def get_meeting(self, meeting_id: str) -> dict | None:
        """按 meeting_id 取记录，不存在返回 None。"""

    @abstractmethod
    def list_meetings(self, page: int = 1, page_size: int = 10,
                      status: str | None = None, keyword: str | None = None
                      ) -> tuple[int, list[dict]]:
        """分页/筛选列表，返回 (total, items)。items 内为可序列化的 dict。"""

    @abstractmethod
    def update_meeting(self, meeting_id: str, **fields) -> dict | None:
        """按字段更新（status/progress/stage/transcript/summary/error_message...）。"""

    @abstractmethod
    def delete_meeting(self, meeting_id: str) -> bool:
        """删除会议记录及其词频。返回是否存在。"""

    @abstractmethod
    def save_words(self, meeting_id: str, items: list[dict]) -> None:
        """保存词频明细 [{"word":..., "freq":...}]（幂等覆盖）。"""

    @abstractmethod
    def get_words(self, meeting_id: str) -> list[dict]:
        """读取词频明细（按 freq 降序）。"""
