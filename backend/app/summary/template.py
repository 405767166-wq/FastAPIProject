"""模板降级总结（M8 V1 默认）：摘取全文前 N 字 + 高频词占位，生成可读纪要。"""

from __future__ import annotations

from app.summary.base import Summarizer


class TemplateSummarizer(Summarizer):
    """无 DeepSeek key 时的保底实现，恒置 is_mock=True。"""

    async def summarize(self, transcript: str, top_words: list[dict] | None = None) -> dict:
        # TODO(V1 步骤 3): 结构化输出「主题/要点/结论/待办」，高频词占位 + is_mock=true
        raise NotImplementedError("模板总结将在 V1 核心逻辑实现后启用")
