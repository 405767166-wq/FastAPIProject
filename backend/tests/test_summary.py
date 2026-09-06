"""M8 模板总结单元测试：断言 is_mock=True 与「主题/要点/结论/待办」结构。

对照任务表第 2 行验证方式：
    - summarize 返回 is_mock=True、model="template"；
    - summary 文本含「主题 / 要点 / 结论 / 待办」四段；
    - 「主题」用到 M5 的 top_words（高频词占位），「要点」摘取转写全文前 N 字。
"""

from __future__ import annotations

from app.summary.template import TemplateSummarizer

TRANSCRIPT = "会议讨论了项目上线计划，以及后续的风险控制与里程碑安排。"


async def test_summary_is_mock_and_model() -> None:
    result = await TemplateSummarizer().summarize(TRANSCRIPT, [{"word": "项目", "freq": 5}])
    assert result["is_mock"] is True
    assert result["model"] == "template"
    assert isinstance(result["summary"], str) and result["summary"]


async def test_summary_contains_four_sections() -> None:
    result = await TemplateSummarizer().summarize(TRANSCRIPT, [{"word": "项目", "freq": 5}])
    for section in ("【主题】", "【要点】", "【结论】", "【待办】"):
        assert section in result["summary"]


async def test_summary_uses_top_words_for_topic() -> None:
    top_words = [{"word": "项目", "freq": 5}, {"word": "上线", "freq": 3}]
    result = await TemplateSummarizer().summarize(TRANSCRIPT, top_words)
    assert "项目" in result["summary"]
    assert "上线" in result["summary"]


async def test_summary_excerpts_transcript() -> None:
    result = await TemplateSummarizer().summarize(TRANSCRIPT, None)
    # 要点段落应摘取转写全文的前 N 字
    assert "会议讨论了项目上线计划" in result["summary"]


async def test_summary_handles_empty_input() -> None:
    result = await TemplateSummarizer().summarize("", None)
    assert result["is_mock"] is True
    assert result["model"] == "template"
    for section in ("【主题】", "【要点】", "【结论】", "【待办】"):
        assert section in result["summary"]


async def test_summary_truncates_long_transcript() -> None:
    long_text = "会议" * 500  # 1000 字，超出默认 200 字摘取上限
    result = await TemplateSummarizer().summarize(long_text, None)
    assert "……" in result["summary"]
