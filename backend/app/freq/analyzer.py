"""M5 词频分析器（V1 考核点）：jieba 分词 → 过滤停用词/单字/标点 → Counter 计数 → Top-N。

考核点（对照 接口文档.md §4.5）：
    - 中文必须 jieba 分词后再计数（按词统计，而非按字）；
    - 原生 `collections.Counter` 累加；
    - 停用词表过滤「的/了/我们/嗯/啊」等口语与虚词；
    - 归一化：统一小写、去标点，过滤单字/无意义词；
    - `Counter.most_common(n)` 取 Top-N，并按 `min_freq` 过滤。

对 `analyze(text, top_n=20, min_freq=1)` 的调用方约定：
    - 返回 `[{"word": w, "freq": c}, ...]`，按 `freq` 降序；
    - 每个 `word` 为归一化后（小写、去标点、去空白）的合法词，长度 >= 2，且不在停用词表内。
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path

import jieba

# jieba 首次导入会打印「Building prefix dict ...」的 INFO 日志，这里降到 WARNING 保持测试输出干净。
jieba.setLogLevel(logging.WARNING)

# 停用词表：与 analyze 同目录的 stopwords.txt，每行一个词，`#` 开头为注释。
_STOPWORDS_FILE = Path(__file__).with_name("stopwords.txt")

# 只保留「文字」类的 token（中文/英文字母/数字/下划线）；纯标点、空白、表情等会被此正则排除。
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _load_stopwords() -> frozenset[str]:
    """从 stopwords.txt 读取停用词，文件缺失时返回空集（不抛错）。"""
    if not _STOPWORDS_FILE.exists():
        return frozenset()
    words = []
    for line in _STOPWORDS_FILE.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if not word or word.startswith("#"):
            continue
        words.append(word)
    return frozenset(words)


#: 模块级停用词集合（导入时加载一次，供 analyze 与测试复用）。
STOPWORDS: frozenset[str] = _load_stopwords()


def _is_meaningful(word: str) -> bool:
    """判断一个已归一化（小写、去空白）的 token 是否应计入词频。

    过滤规则：空串、单字、停用词、纯标点/空白等非文字 token。
    """
    if not word:
        return False
    if len(word) < 2:
        return False
    if word in STOPWORDS:
        return False
    return bool(_WORD_RE.fullmatch(word))


def analyze(text: str, top_n: int = 20, min_freq: int = 1) -> list[dict]:
    """统计文本词频，返回按频次降序的 Top-N 词表。

    参数
    ----
    text:
        转写全文（中文按 jieba 分词，英文统一小写后合并计数）。
    top_n:
        最多返回的高频词数量；<= 0 时返回空列表。
    min_freq:
        只保留频次 >= min_freq 的词。

    返回
    ----
    `[{"word": str, "freq": int}, ...]`，按 `freq` 降序排列。
    """
    if not text:
        return []
    if top_n <= 0:
        return []

    counter: Counter[str] = Counter()
    for token in jieba.lcut(text):
        word = token.strip().lower()
        if _is_meaningful(word):
            counter[word] += 1

    return [
        {"word": word, "freq": freq}
        for word, freq in counter.most_common(top_n)
        if freq >= min_freq
    ]
