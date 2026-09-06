"""模板降级总结（M8 V1 默认）：摘取全文前 N 字 + 高频词占位，生成可读纪要。

考核点（对照 版本规划.md M8 与任务表第 2 行）：
    - 恒置 is_mock=True、model="template"；
    - 输出结构化纪要，含「主题 / 要点 / 结论 / 待办」四段；
    - 「主题」用 M5 的高频词（top_words）占位，「要点」摘取全文前 N 字。
"""

from __future__ import annotations

from app.summary.base import Summarizer

# 「要点」段落默认摘取转写全文的前 N 个字符。
DEFAULT_EXCERPT_CHARS = 200


def _topic_text(top_words: list[dict] | None) -> str:
    """把 M5 的高频词拼成主题占位文案；无词时给兜底说明。"""
    words = [str(w.get("word", "")).strip() for w in (top_words or [])]
    words = [w for w in words if w]
    if not words:
        return "（模板生成）暂未提炼出主题关键词"
    return "、".join(words)


def _excerpt_text(transcript: str, limit: int) -> str:
    """摘取转写全文前 limit 个字符作为「要点」占位。"""
    text = (transcript or "").strip()
    if not text:
        return "（无转写文本）"
    return text if len(text) <= limit else text[:limit] + "……"


class TemplateSummarizer(Summarizer):
    """无 DeepSeek key 时的保底实现，恒置 is_mock=True。"""

    def __init__(self, excerpt_chars: int = DEFAULT_EXCERPT_CHARS) -> None:
        self.excerpt_chars = excerpt_chars

    async def summarize(self, transcript: str, top_words: list[dict] | None = None) -> dict:
        """生成结构化纪要，返回 {"summary": str, "is_mock": bool, "model": str}。"""
        topic = _topic_text(top_words)
        excerpt = _excerpt_text(transcript, self.excerpt_chars)
        summary = (
            "【主题】\n"
            f"会议主要围绕「{topic}」展开。\n"
            "\n"
            "【要点】\n"
            f"{excerpt}\n"
            "\n"
            "【结论】\n"
            "（模板生成）以上为自动生成的会议纪要摘录，具体结论待人工复核确认。\n"
            "\n"
            "【待办】\n"
            "（模板生成）请结合会议要点梳理后续待办事项。"
        )
        return {"summary": summary, "is_mock": True, "model": "template"}
