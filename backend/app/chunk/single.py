"""单块降级分块（M6 V1 默认）：无 ffmpeg 时整文件作为 1 块，进度分母为 1。"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.chunk.base import Chunker


class SingleChunker(Chunker):
    """把原始音频原样作为唯一块（复制到 work_dir 保持目录语义一致）。"""

    def chunk(self, audio_path: str, work_dir: str) -> list[str]:
        src = Path(audio_path)
        out_dir = Path(work_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "chunk_0001.mp3"
        shutil.copy2(src, target)
        return [str(target)]
