"""M6 分块单元测试：无 ffmpeg 时整文件单块（chunk_count=1），接口与进度模型一致。

对照 版本规划.md M6 与 接口文档.md §4.6 的 V1 降级要求：
    - SingleChunker 把整文件作为唯一块，返回值列表长度为 1（进度分母 chunk_count=1）；
    - 块文件被复制到 work_dir（chunk_0001.*），内容与源文件一致；
    - 实现 Chunker 抽象接口，供 worker 以 len(chunks) 作为 chunk_count。

注：临时目录放在仓库根 `.tmp/` 下（而非 pytest 默认系统临时目录），以适配本环境的文件沙箱。
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from app.chunk.base import Chunker
from app.chunk.single import SingleChunker

# backend/tests/test_chunk.py -> parent[2] 为仓库根目录。
_TMP = Path(__file__).resolve().parents[2] / ".tmp"


@pytest.fixture
def temp_ws() -> Path:
    """每个用例独立临时目录（仓库 .tmp 下），用毕即删。"""
    base = _TMP / f"test_chunk_{uuid.uuid4().hex[:8]}"
    base.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


def test_returns_one_chunk(temp_ws: Path) -> None:
    src = temp_ws / "audio.mp3"
    src.write_bytes(b"fake-audio-bytes")
    chunks = SingleChunker().chunk(str(src), str(temp_ws / "work"))
    assert isinstance(chunks, list)
    assert len(chunks) == 1  # chunk_count = 1（进度分母）


def test_chunk_file_exists(temp_ws: Path) -> None:
    src = temp_ws / "audio.mp3"
    src.write_bytes(b"x")
    chunk_path = SingleChunker().chunk(str(src), str(temp_ws / "work"))[0]
    assert Path(chunk_path).is_file()


def test_chunk_copies_content(temp_ws: Path) -> None:
    content = b"fake-audio-content-123"
    src = temp_ws / "audio.mp3"
    src.write_bytes(content)
    chunk_path = SingleChunker().chunk(str(src), str(temp_ws / "work"))[0]
    assert Path(chunk_path).read_bytes() == content


def test_chunk_naming_convention(temp_ws: Path) -> None:
    src = temp_ws / "audio.mp3"
    src.write_bytes(b"x")
    chunk_path = SingleChunker().chunk(str(src), str(temp_ws / "work"))[0]
    assert Path(chunk_path).name == "chunk_0001.mp3"


def test_chunk_work_dir_created(temp_ws: Path) -> None:
    src = temp_ws / "audio.mp3"
    src.write_bytes(b"x")
    work_dir = temp_ws / "nested" / "chunks"
    chunk_path = SingleChunker().chunk(str(src), str(work_dir))[0]
    assert work_dir.is_dir()
    assert str(Path(chunk_path).parent) == str(work_dir)


def test_works_with_non_mp3_source(temp_ws: Path) -> None:
    # 不同源扩展名也按单块处理（命名仍为 chunk_0001.mp3，符合 readme 说明）
    src = temp_ws / "audio.wav"
    src.write_bytes(b"x")
    chunks = SingleChunker().chunk(str(src), str(temp_ws / "work"))
    assert len(chunks) == 1
    assert Path(chunks[0]).is_file()


def test_implements_chunker_interface(temp_ws: Path) -> None:
    chunker = SingleChunker()
    assert isinstance(chunker, Chunker)
    src = temp_ws / "audio.mp3"
    src.write_bytes(b"x")
    assert len(chunker.chunk(str(src), str(temp_ws / "work"))) == 1
