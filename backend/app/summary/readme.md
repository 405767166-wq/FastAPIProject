# summary — 智能总结子包（M8）

对转写全文生成结构化会议纪要（主题/要点/结论/待办）。采用「抽象基类 + 可插拔实现」，无 key 时模板降级。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：`Summarizer` 抽象 + 模板降级（V1）+ DeepSeek（V2）。 |
| `base.py` | `Summarizer(ABC)` 抽象基类：定义 `async summarize(transcript, top_words) -> dict` 抽象方法，返回 `{"summary": str, "is_mock": bool, "model": str}`。 |
| `template.py` | `TemplateSummarizer(Summarizer)`：V1 默认实现（骨架占位，抛 `NotImplementedError`）。规划为：摘取全文前 N 字 + 高频词占位，生成可读纪要并恒置 `is_mock=True`。 |

## 实现演进

| 版本 | 总结器 | 说明 |
|------|--------|------|
| V1（当前） | `TemplateSummarizer` | 模板降级，`is_mock=True`，无 key 可用 |
| V2（规划） | `DeepSeekSummarizer` | `deepseek-chat` 结构化纪要 + 前置 `clean_text` 纠错去口语；无 key/失败自动落回模板 |
