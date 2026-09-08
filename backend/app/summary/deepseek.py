"""DeepSeek 会议总结（M8，真实 AI 总结）。

按用户自建抽象 `app/summary/dsbase.py` 的 `deepseeksummary` 实现：
    text = await DeepSeekSummarizer().summary(context)      # 纯 DeepSeek 调用 → 纪要文本

同时实现 `Summarizer.summarize(transcript, top_words) -> dict` 以对齐 worker/既有约定：
    - 成功 → {"summary": 纪要, "is_mock": False, "model": settings.deepseek_model}
    - 无 key / 调用失败 → 自动降级 TemplateSummarizer（is_mock=True），任务不失败
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.summary.dsbase import deepseeksummary
from app.summary.template import TemplateSummarizer

logger = logging.getLogger(__name__)

#: 系统提示词：约束模型输出「主题/要点/结论/待办」四段结构化纪要。
SYSTEM_PROMPT = (
    "你是一名专业的会议纪要整理助手。请根据用户提供的会议转写文本"
    "（可能包含口语、重复和语气词），提炼生成结构化中文会议纪要，"
    "必须包含【主题】【要点】【结论】【待办】四个段落，语言精炼、要点明确。"
)


def _build_context(transcript: str, top_words: list[dict] | None) -> str:
    """把转写全文 + M5 高频词拼成给模型的用户上下文。"""
    words = "、".join(str(w.get("word", "")) for w in (top_words or []) if w.get("word"))
    lines = [f"会议转写全文：\n{transcript or '（无转写文本）'}"]
    if words:
        lines.append(f"\n会议高频词参考：{words}")
    lines.append("\n请基于以上内容生成会议纪要。")
    return "\n".join(lines)


class DeepSeekSummarizer(deepseeksummary):
    """调用 DeepSeek（deepseek-chat，OpenAI 兼容接口）生成会议总结。"""

    def __init__(self, fallback=None) -> None:
        self._fallback = fallback or TemplateSummarizer()
        self._base_url = settings.deepseek_base_url.rstrip("/")
        self._model = settings.deepseek_model
        self._api_key = settings.deepseek_api_key


    async def summary(self, context: str) -> str:
        """调用 deepseek-chat 生成总结文本；失败抛异常（由 summarize 负责降级）。"""
        if not self._api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY（backend/.env）")
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            "temperature": 0.3,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
        data = resp.json()
        if resp.status_code != 200 or "choices" not in data:
            raise RuntimeError(
                f"DeepSeek 调用失败 HTTP {resp.status_code}: "
                f"{data.get('error', data) if isinstance(data, dict) else data}"
            )
        return data["choices"][0]["message"]["content"].strip()


    async def summarize(
        self, transcript: str, top_words: list[dict] | None = None
    ) -> dict:
        """真实总结优先；无 key/异常自动降级模板（is_mock=True）。"""
        try:
            context = _build_context(transcript, top_words)
            text = await self.summary(context)
            return {"summary": text, "is_mock": False, "model": self._model}
        except Exception as exc:  # noqa: BLE001 - 降级，不让整条任务失败
            logger.warning("DeepSeek 总结失败，降级模板: %s", exc)
            return await self._fallback.summarize(transcript, top_words)
