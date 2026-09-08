"""M11 worker 管线单元测试：入队→消费→completed；失败→failed+error_message。

对照 版本规划.md M11 与任务表第 4 行：
    - 生产者 push → worker 消费（pop）→ 处理管线（M6 分块→M7 ASR→M5 词频→M8 总结→M10 落库）→ completed；
    - 处理失败时置 failed 并写入 error_message（不静默丢失）。
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from app.asr.mock import MockEngine
from app.queue.native_queue import NativeTaskQueue
from app.store.memory import MemoryStore
from app.summary.template import TemplateSummarizer
from app.worker import Worker

# backend/tests/test_worker.py -> parent[2] 为仓库根目录。
_TMP = Path(__file__).resolve().parents[2] / ".tmp"


@pytest.fixture
def temp_ws() -> Path:
    """每个用例独立临时目录（仓库 .tmp 下），用毕即删。"""
    base = _TMP / f"test_worker_{uuid.uuid4().hex[:8]}"
    base.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


async def test_enqueue_consume_to_completed(temp_ws: Path) -> None:
    store = MemoryStore()
    queue = NativeTaskQueue()

    audio = temp_ws / "audio.mp3"
    audio.write_bytes(b"fake-audio-bytes")
    meeting_id = "m1"
    store.create_meeting(
        meeting_id=meeting_id,
        title="周会",
        file_name="audio.mp3",
        file_path=str(audio),
        file_size=len(b"fake-audio-bytes"),
    )

    # 入队 → 消费
    queue.push({"meeting_id": meeting_id, "file_path": str(audio), "title": "周会"})
    task = await queue.pop()

    worker = Worker(queue=queue, store=store, asr=MockEngine(delay_seconds=0), summarizer=TemplateSummarizer())
    await worker._handle(task)

    record = store.get_meeting(meeting_id)
    assert record is not None
    assert record["status"] == "completed"
    assert record["progress"] == 100
    assert record["stage"] == "done"
    assert record["transcript"]
    assert record["summary"]
    assert record["summary_is_mock"] is True
    # M5 词频已落库
    words = store.get_words(meeting_id)
    assert words
    assert all(set(w) == {"word", "freq"} for w in words)


async def test_enqueue_consume_records_file_and_progress(temp_ws: Path) -> None:
    """验证处理过程中 chunk_count 与逐块进度被写入。"""
    store = MemoryStore()
    queue = NativeTaskQueue()
    audio = temp_ws / "audio.mp3"
    audio.write_bytes(b"fake-audio-bytes")
    meeting_id = "m2"
    store.create_meeting(
        meeting_id=meeting_id, title="周会", file_name="audio.mp3",
        file_path=str(audio), file_size=len(b"fake-audio-bytes"),
    )
    queue.push({"meeting_id": meeting_id, "file_path": str(audio), "title": "周会"})
    task = await queue.pop()

    worker = Worker(queue=queue, store=store, asr=MockEngine(delay_seconds=0), summarizer=TemplateSummarizer())
    await worker._handle(task)

    record = store.get_meeting(meeting_id)
    assert record["chunk_count"] == 1  # V1 单块
    assert record["progress"] == 100


async def test_failure_marks_failed_with_error(temp_ws: Path) -> None:
    """源文件不存在 → 分块/转写抛异常 → 置 failed + error_message。"""
    store = MemoryStore()
    queue = NativeTaskQueue()
    meeting_id = "m3"
    bad_path = str(temp_ws / "not_exist" / "audio.mp3")  # 不存在的文件
    store.create_meeting(
        meeting_id=meeting_id, title="周会", file_name="audio.mp3",
        file_path=bad_path, file_size=1,
    )
    task = {"meeting_id": meeting_id, "file_path": bad_path, "title": "周会"}

    worker = Worker(queue=queue, store=store, asr=MockEngine(delay_seconds=0), summarizer=TemplateSummarizer())
    await worker._handle(task)

    record = store.get_meeting(meeting_id)
    assert record is not None
    assert record["status"] == "failed"
    assert record["error_message"]
