"""语音转写引擎抽象（M7）。

V1：`MockEngine`（内置示例文本 + 可观测延时，无 key 全链路可跑）。
V2：`BaiduEngine`（录音文件识别）/ 讯飞 / 阿里 / `WhisperEngine`，由 ASR_PROVIDER 切换。
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class ASREngine(ABC):
    @abstractmethod
    def transcribe_short(self,path: str, token: str, fmt: str = "wav") -> str:
        """音频块 → 文本。失败抛异常（由 worker 记 error_message）。"""