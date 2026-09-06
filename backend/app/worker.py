"""M11 worker：后台消费循环（与 FastAPI 同进程，随应用生命周期启停）。

链路（V1）：
    pop 任务 → status=processing → M6 分块 → M7 ASR(mock) 逐块 →
    M5 词频(Counter+jieba) → M8 模板总结 → M10 落存储 → status=completed
失败：try/except + error_message 落库，不静默丢失。
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.asr.BaiduEngine import BaiduEngine
from app.asr.base import ASREngine
from app.asr.mock import MockEngine
from app.chunk.base import Chunker
from app.chunk.single import SingleChunker
from app.config import settings
from app.freq.analyzer import analyze
from app.queue.base import TaskQueue
from app.store.base import MeetingStore
from app.summary.base import Summarizer
from app.summary.template import TemplateSummarizer

logger = logging.getLogger(__name__)


class Worker:
    def __init__(
        self,
        queue: TaskQueue,
        store: MeetingStore,
        chunker: Chunker | None = None,
        asr: ASREngine | None = None,
        summarizer: Summarizer | None = None,
    ) -> None:
        """依赖注入：chunker/summarizer 默认 V1 实现；asr 默认 BaiduEngine（真实识别，
        需 backend/.env 配 BAIDU key；无 key 场景可注入 MockEngine()）。"""
        self._queue = queue
        self._store = store
        self._chunker = chunker or SingleChunker()
        self._asr = asr or BaiduEngine()
        self._summarizer = summarizer or TemplateSummarizer()

    async def run(self) -> None:
        """消费循环：被 FastAPI lifespan 作为后台任务拉起，关闭时取消。"""
        logger.info("worker 已启动，开始消费任务队列")
        while True:
            task = await self._queue.pop()
            await self._handle(task)

    async def _handle(self, task: dict) -> None:
        """处理单条任务：分块 → 转写 → 词频 → 总结 → 落存储(completed)。失败置 failed。"""
        meeting_id = task.get("meeting_id", "")
        try:
            self._store.update_meeting(
                meeting_id, status="processing", stage="chunking", progress=0,
            )
            file_path = task.get("file_path", "")

            # M6 分块（V1：整文件单块，chunk_count=1）
            work_dir = str(Path(settings.upload_dir) / meeting_id / "chunks")
            chunks = self._chunker.chunk(file_path, work_dir)
            chunk_count = len(chunks)
            self._store.update_meeting(meeting_id, chunk_count=chunk_count, stage="asr")

            # M7 语音转写：逐块交给 ASR 引擎（统一异步接口：await engine.transcribeAPI(audio_path) -> str）
            #     MockEngine   —— 无 key 演示（示例文本 + 延时）
            #     BaiduEngine  —— 真实识别（内部自管 token，支持 wav/pcm/amr/m4a）
            transcript_parts = []
            for idx, chunk in enumerate(chunks, start=1):
                text = await self._asr.transcribeAPI(chunk)
                transcript_parts.append(text)
                progress = int(idx / chunk_count * 100)
                self._store.update_meeting(meeting_id, progress=progress, stage="asr")
            transcript = "\n".join(transcript_parts)

            # M5 词频统计（jieba + Counter + 停用词 + Top-N）
            self._store.update_meeting(meeting_id, stage="freq")
            top_words = analyze(transcript, top_n=20)
            self._store.save_words(meeting_id, top_words)

            # M8 模板总结（is_mock=True）
            self._store.update_meeting(meeting_id, stage="summary")
            summary_result = await self._summarizer.summarize(transcript, top_words)
            summary = summary_result["summary"]
            summary_is_mock = bool(summary_result.get("is_mock", True))

            # M10 落存储 + completed
            self._store.update_meeting(
                meeting_id,
                status="completed",
                progress=100,
                stage="done",
                transcript=transcript,
                summary=summary,
                summary_is_mock=summary_is_mock,
            )
        except Exception as exc:  # noqa: BLE001 - worker 不允许静默丢失任务
            logger.exception("任务处理失败 meeting_id=%s", meeting_id)
            self._store.update_meeting(
                meeting_id,
                status="failed",
                error_message=str(exc)[:512],
            )
