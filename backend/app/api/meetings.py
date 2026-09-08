"""会议 REST 路由（M3）：对应 接口文档.md §5.2 ~ §5.8。

V1：列表/详情/词频/总结/删除已接 MemoryStore（真实语义）；
上传（P2.1）已实现：校验 → 落盘 → 建记录(queued) → 入队；
处理管线（worker）在后续任务启用。
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Request, UploadFile

from app.config import settings
from app.errors import ApiError, ErrCode
from app.queue.base import TaskQueue
from app.responses import ok
from app.store.base import MeetingStore

router = APIRouter(prefix="/meetings")

# P2.1 上传校验（接口文档.md §5.2）：允许的音频扩展名与大小上限。
ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200MB


def _store(request: Request) -> MeetingStore:
    return request.app.state.store


def _queue(request: Request) -> TaskQueue:
    return request.app.state.queue


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
async def create_meeting(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(None),
) -> dict:
    """P2.1 上传会议录音：校验（扩展名/大小）→ 落盘 → 建记录(queued) → 入队。"""
    file_name = file.filename or ""
    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTS:
        raise ApiError(
            ErrCode.PARAM,
            f"仅支持音频文件（mp3/wav/m4a/aac），收到扩展名：{ext or '无'}",
            http_status=400,
        )

    meeting_id = uuid.uuid4().hex
    meeting_dir = Path(settings.upload_dir) / meeting_id
    dest = meeting_dir / f"raw{ext}"

    size = 0
    too_large = False
    try:
        meeting_dir.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    too_large = True
                    break
                out.write(chunk)
    except Exception as exc:
        raise ApiError(ErrCode.INTERNAL, f"文件落盘失败：{exc}", http_status=500) from exc
    finally:
        await file.close()

    if too_large:
        dest.unlink(missing_ok=True)
        raise ApiError(ErrCode.PARAM, "文件大小超过 200MB 上限", http_status=400)

    title_final = (title or "").strip() or file_name
    record = _store(request).create_meeting(
        meeting_id=meeting_id,
        title=title_final,
        file_name=file_name,
        file_path=str(dest),
        file_size=size,
    )

    _queue(request).push({
        "meeting_id": meeting_id,
        "file_path": str(dest),
        "title": title_final,
    })

    return ok({
        "meeting_id": meeting_id,
        "title": title_final,
        "status": record.get("status", "queued"),
        "progress": record.get("progress", 0),
        "message": "已进入处理队列",
    })


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str, request: Request) -> dict:
    """P2.3 会议详情。"""
    record = _store(request).get_meeting(meeting_id)
    if record is None:
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    return ok(record)


@router.get("/{meeting_id}/words")
async def get_words(meeting_id: str, request: Request,
                    top: Annotated[int, Query(ge=1)] = 20,
                    min_freq: Annotated[int, Query(ge=1)] = 1) -> dict:
    """P2.5 词频查询：min_freq 过滤低频词，top 截取前 N 个（按 freq 降序）。"""
    store = _store(request)
    if store.get_meeting(meeting_id) is None:
        raise ApiError(ErrCode.NOT_FOUND, "会议不存在", http_status=404)
    items = store.get_words(meeting_id)
    if not items:
        raise ApiError(ErrCode.STAGE, "任务尚未到词频阶段", http_status=409)
    filtered = [w for w in items if w.get("freq", 0) >= min_freq]
    return ok({
        "meeting_id": meeting_id,
        "total_words": len(items),  # 去重词数（过滤前，接口文档 P2.5 语义）
        "items": filtered[:top],    # 按 min_freq 过滤 + top 截断
    })


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
