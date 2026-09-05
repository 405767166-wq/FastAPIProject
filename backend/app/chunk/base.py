"""分块器抽象（M6）。

V1：`SingleChunker`（无 ffmpeg：整文件视为 1 块，chunk_count=1）。
V2：`FFmpegChunker`（按时长/大小切块，逐块进度分母 = chunk_count）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Chunker(ABC):
    @abstractmethod
    def chunk(self, audio_path: str, work_dir: str) -> list[str]:
        """返回切块文件路径列表（V1 单块即原文件自身）。"""
