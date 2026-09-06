"""M7 Mock 转写引擎单元测试：内置示例文本 + 可观测延时，无 key 全链路可跑。

对照 版本规划.md M7 与 接口文档.md §4.7 的 V1 要求：
    - `ASREngine` 抽象：`async transcribe(audio_path) -> str`；
    - `MockEngine`：内置示例会议文本，transcribe 带可观测延时（asyncio.sleep）。
"""

from __future__ import annotations

import asyncio
import time

from app.asr.base import ASREngine
from app.asr.mock import MockEngine, _DEMO_TEXT


def test_implements_asr_engine() -> None:
    assert isinstance(MockEngine(), ASREngine)


def test_transcribe_is_awaitable_coroutine() -> None:
    coro = MockEngine(delay_seconds=0).transcribeAPI("x.mp3")
    assert asyncio.iscoroutine(coro)
    coro.close()  # 关闭未消费的协程，避免告警


async def test_transcribe_returns_demo_text() -> None:
    engine = MockEngine(delay_seconds=0)
    text = await engine.transcribeAPI("uploads/x/chunks/chunk_0001.mp3")
    assert isinstance(text, str)
    assert text == _DEMO_TEXT
    assert len(text) > 10


async def test_transcribe_returns_text_for_any_path() -> None:
    engine = MockEngine(delay_seconds=0)
    for path in ("a.mp3", "b.wav", "chunk_0002.mp3"):
        assert len(await engine.transcribeAPI(path)) > 10


async def test_transcribe_observable_delay() -> None:
    # 可观测延时：至少等待约 delay_seconds（留余量避免计时抖动）
    engine = MockEngine(delay_seconds=0.1)
    start = time.monotonic()
    await engine.transcribeAPI("x.mp3")
    elapsed = time.monotonic() - start
    assert elapsed >= 0.05


def test_default_delay_is_positive() -> None:
    # 默认 delay 应 > 0（演示进度用）；0 延迟用于测试时最快
    assert MockEngine()._delay > 0
    assert MockEngine(delay_seconds=0)._delay == 0
