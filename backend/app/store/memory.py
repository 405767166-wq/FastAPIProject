"""内存存储（M10 V1 默认实现）：dict 存储，重启即失，单进程可用。

- _meetings: meeting_id -> 会议记录 dict
- _words:     meeting_id -> 词频明细 list
- 列表排序依赖自增 seq（模拟自增主键语义）
"""

from __future__ import annotations

import itertools
import threading
from datetime import datetime, timezone
from typing import Any

from app.store.base import MeetingStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MemoryStore(MeetingStore):
    def __init__(self) -> None:
        self._meetings: dict[str, dict[str, Any]] = {}
        self._words: dict[str, list[dict]] = {}
        self._seq = itertools.count(1)
        self._lock = threading.Lock()  # 单进程内防并发写

    # ---------- 会议 ----------

    def create_meeting(self, *, meeting_id: str, title: str, file_name: str,
                       file_path: str, file_size: int, **extra) -> dict:
        now = _now_iso()
        record = {
            "id": next(self._seq),
            "meeting_id": meeting_id,
            "title": title or file_name,
            "file_name": file_name,
            "file_path": file_path,
            "file_size": file_size,
            "status": "queued",
            "progress": 0,
            "stage": "queued",
            "duration_sec": None,
            "chunk_count": 0,
            "transcript": None,
            "summary": None,
            "summary_is_mock": False,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        record.update(extra)
        with self._lock:
            self._meetings[meeting_id] = record
        return dict(record)

    def get_meeting(self, meeting_id: str) -> dict | None:
        rec = self._meetings.get(meeting_id)
        return dict(rec) if rec else None

    def list_meetings(self, page: int = 1, page_size: int = 10,
                      status: str | None = None,
                      keyword: str | None = None) -> tuple[int, list[dict]]:
        with self._lock:
            records = list(self._meetings.values())
        if status:
            records = [r for r in records if r["status"] == status]
        if keyword:
            kw = keyword.lower()
            records = [r for r in records
                       if kw in (r["title"] or "").lower()
                       or kw in (r["meeting_id"] or "").lower()]
        records.sort(key=lambda r: r["id"], reverse=True)
        total = len(records)
        start = (page - 1) * page_size
        items = [dict(r) for r in records[start:start + page_size]]
        return total, items

    def update_meeting(self, meeting_id: str, **fields) -> dict | None:
        with self._lock:
            rec = self._meetings.get(meeting_id)
            if rec is None:
                return None
            rec.update(fields)
            rec["updated_at"] = _now_iso()
            return dict(rec)

    def delete_meeting(self, meeting_id: str) -> bool:
        with self._lock:
            existed = self._meetings.pop(meeting_id, None) is not None
            self._words.pop(meeting_id, None)
        return existed

    # ---------- 词频 ----------

    def save_words(self, meeting_id: str, items: list[dict]) -> None:
        with self._lock:
            self._words[meeting_id] = [dict(w) for w in items]

    def get_words(self, meeting_id: str) -> list[dict]:
        words = self._words.get(meeting_id, [])
        return [dict(w) for w in words]
