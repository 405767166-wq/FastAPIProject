# freq — 词频统计子包（M5，考核点）

对转写全文做中文分词并按词频累加，输出 Top-N 高频词。核心考核点之一：使用 Python 原生 `dict` / `collections.Counter` + jieba 分词（中文按词统计，而非按字）。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：jieba 分词 + Counter + 停用词过滤 + Top-N。 |
| `analyzer.py` | `analyze(text, top_n=20, min_freq=1) -> list[dict]`：当前为占位实现（抛 `NotImplementedError`）。文件 docstring 给出计划实现：`jieba.lcut(text)` → `Counter` 过滤停用词/单字/标点 → `most_common(top_n)` 且 `freq >= min_freq`，返回 `[{"word", "freq"}]`。 |

## 设计要点（对照 接口文档.md §4.5）

- **分词前置**：中文必须 jieba 分词后再计数，否则按字统计无意义。
- **停用词过滤**：过滤「的/了/我们/嗯/啊」等口语与虚词。
- **归一化**：统一小写、去标点，数字/专名可后续加自定义词典。
- **Top-N**：原生 `Counter.most_common(n)` 完成。

## 实现演进

| 版本 | 数据结构 | 说明 |
|------|----------|------|
| V1（当前） | `dict`/`Counter` + jieba（待实现） | 考核点 |
| V2（规划） | Redis Hash（`HINCRBY`） | 多 worker 并发原子累加 |
