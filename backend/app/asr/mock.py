"""Mock 转写引擎（M7 V1 默认）：内置示例会议文本 + 模拟处理延时。"""

from __future__ import annotations

import asyncio

from app.asr.base import ASREngine

# 内置示例文本：无真实音频/key 时用于演示全链路
_DEMO_TEXT = (
    "我们今天开会讨论项目的上线计划。首先回顾上周进度，"
    "前端页面已经完成，后端接口还在联调。接下来分配本周任务，"
    "张工负责数据库设计，李工负责接口开发，王工负责测试用例。"
    "会议结论是周五前完成联调，下周一正式上线。大家有没有其他问题？好，散会。"
)


class MockEngine(ASREngine):
    """按音频块序号返回示例文本，附带可观测延时（演示进度用）。"""

    def __init__(self, delay_seconds: float = 0.3) -> None:
        self._delay = delay_seconds

    async def transcribe(self, audio_path: str) -> str:
        await asyncio.sleep(self._delay)  # 模拟"处理中"，让进度可见
        return _DEMO_TEXT
