"""总结器抽象（M8）。

V1：`TemplateSummarizer`（模板降级，无 key 可用）。
V2：`DeepSeekSummarizer`（deepseek-chat，无 key/失败自动落回模板并置 summary_is_mock=true）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Summarizer(ABC):
    @abstractmethod
    async def summarize(self, transcript: str, top_words: list[dict] | None = None) -> dict:
        """返回 {"summary": str, "is_mock": bool, "model": str}。"""
