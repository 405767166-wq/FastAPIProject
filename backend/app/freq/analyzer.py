"""M5 词频分析器（V1 考核点）：jieba 分词 → 过滤停用词/单字/标点 → Counter 计数 → Top-N。

实现计划（V1 步骤 3）：
    def analyze(text: str, top_n: int = 20, min_freq: int = 1) -> list[dict]:
        # words = jieba.lcut(text)
        # counter = Counter(filter(_keep, words))
        # return [{"word": w, "freq": c} for w, c in counter.most_common(top_n) if c >= min_freq]
"""

from __future__ import annotations


def analyze(text: str, top_n: int = 20, min_freq: int = 1) -> list[dict]:
    """占位：TODO(V1 步骤 3) 接入 jieba + Counter。"""
    raise NotImplementedError("词频分析将在 V1 核心逻辑实现后启用")
