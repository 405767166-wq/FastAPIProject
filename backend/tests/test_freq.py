"""M5 词频分析器单元测试（考核点：jieba 分词 + Counter + 停用词过滤 + Top-N）。

覆盖 版本规划.md §5 与 接口文档.md §4.5 的 V1 验收点：
    - 中文按「词」统计而非按「字」；
    - 停用词 / 单字 / 标点过滤；
    - 英文归一化（统一小写后合并计数）；
    - Top-N 截断与 min_freq 过滤；
    - 返回结构为 [{"word", "freq"}] 且按 freq 降序。
"""

from __future__ import annotations

from app.freq.analyzer import STOPWORDS, analyze


def test_empty_or_punctuation_only_text() -> None:
    assert analyze("") == []
    assert analyze("   ") == []
    assert analyze("，。！？、；：") == []


def test_count_by_word_not_by_char() -> None:
    # 「会议」出现 3 次、「总结」出现 1 次：应按词统计，而不是把每个汉字都当成一个词。
    items = analyze("会议 会议 会议 总结")
    assert items[0] == {"word": "会议", "freq": 3}
    assert items[1] == {"word": "总结", "freq": 1}
    # 不能出现按字统计的结果（每个词长度都应 >= 2）
    assert all(len(it["word"]) >= 2 for it in items)


def test_stopwords_loaded() -> None:
    # 文档明确要求过滤「的/了/我们/嗯/啊」等口语与虚词。
    assert {"的", "了", "我们", "嗯", "啊"} <= STOPWORDS


def test_stopwords_filtered() -> None:
    items = analyze("我们 的 会议 嗯 啊 会议")
    words = {it["word"] for it in items}
    assert "会议" in words
    for sw in ("的", "了", "我们", "嗯", "啊"):
        assert sw not in words


def test_single_char_filtered() -> None:
    items = analyze("好 会议 会议")
    words = {it["word"] for it in items}
    assert "好" not in words  # 单字被过滤
    assert "会议" in words


def test_punctuation_filtered() -> None:
    items = analyze("会议，会议！会议。")
    assert items == [{"word": "会议", "freq": 3}]
    assert all(not any(ch in "，。！？、；：,.!?;:" for ch in it["word"]) for it in items)


def test_top_n_limit() -> None:
    text = " ".join(["会议"] * 3 + ["总结"] * 2 + ["上线"] * 1)
    items = analyze(text, top_n=2)
    assert len(items) == 2
    assert [it["word"] for it in items] == ["会议", "总结"]


def test_top_n_zero_or_negative_returns_empty() -> None:
    assert analyze("会议 会议", top_n=0) == []
    assert analyze("会议 会议", top_n=-1) == []


def test_min_freq_filter() -> None:
    text = " ".join(["会议"] * 3 + ["总结"] * 1)
    items = analyze(text, min_freq=2)
    assert [it["word"] for it in items] == ["会议"]


def test_lowercase_normalization() -> None:
    # 英文统一小写后合并计数：hello/Hello/HELLO 都归并为 "hello"。
    items = analyze("hello Hello HELLO")
    by_word = {it["word"]: it["freq"] for it in items}
    assert by_word == {"hello": 3}


def test_output_shape_and_desc_order() -> None:
    text = " ".join(["会议"] * 5 + ["总结"] * 3 + ["上线"] * 1)
    items = analyze(text, top_n=10)
    assert items
    assert all(set(it) == {"word", "freq"} for it in items)
    freqs = [it["freq"] for it in items]
    assert freqs == sorted(freqs, reverse=True)
    assert [it["word"] for it in items] == ["会议", "总结", "上线"]
