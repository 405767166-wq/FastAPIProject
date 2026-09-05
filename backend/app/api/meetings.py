"""会议 REST 路由（M3）：对应 接口文档.md §5.2 ~ §5.8。

V1 骨架阶段：列表/详情/词频/总结/删除已接 MemoryStore（真实语义）；
上传（P2.1）与处理管线在 V1 核心逻辑实现后启用。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.errors import ApiError, ErrCode, not_implemented
from app.responses import ok
from app.store.base import MeetingStore

router = APIRouter(prefix="/meetings")


def _store(request: Request) -> MeetingStore:
    return request.app.state.store


@router.get("")
async def list_meetings(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    status: str | None = None,
    keyword: str | None = None,
) -> dict:
    """P2.2 历史会议列表。"""
    total, items = _store(request).list_meetings(
        page=page, page_size=page_size, status=status, keyword=keyword
    )
    return ok({"total": total, "page": page, "page_size": page_size, "items": items})


@router.post("")
async def create_meeting(request: Request) -> dict:
    """P2.1 上传会议录音（multipart）。V1 核心逻辑实现后启用。"""
    raise not_implemented("POST /api/meetings")


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str, request: Request) -> dict:
    """P2.3 会议详情。"""
    record = _store(request).get_meeting(meeting_id)
    if record is None:
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    return ok(record)


@router.get("/{meeting_id}/words")
async def get_words(meeting_id: str, request: Request,
                    top: int = 20, min_freq: int = 1) -> dict:
    """P2.5 词频查询。"""
    store = _store(request)
    if store.get_meeting(meeting_id) is None:
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    items = store.get_words(meeting_id)
    if not items:
        raise ApiError(ErrCode.STAGE, "任务尚未到词频阶段", http_status=409)
    return ok({"meeting_id": meeting_id, "total_words": len(items), "items": items})


@router.get("/{meeting_id}/summary")
async def get_summary(meeting_id: str, request: Request) -> dict:
    """P2.6 总结查询。"""
    store = _store(request)
    record = store.get_meeting(meeting_id)
    if record is None:
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    if not record.get("summary"):
        raise ApiError(ErrCode.STAGE, "任务尚未完成总结", http_status=409)
    return ok({
        "meeting_id": meeting_id,
        "summary": record["summary"],
        "is_mock": bool(record.get("summary_is_mock")),
        "model": "template" if record.get("summary_is_mock") else "deepseek-chat",
    })


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, request: Request) -> dict:
    """P2.7 删除会议（记录 + 词频 + 磁盘文件由核心逻辑负责清理）。"""
    store = _store(request)
    if not store.delete_meeting(meeting_id):
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    return ok({"deleted": True})
