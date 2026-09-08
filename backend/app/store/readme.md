# store — 存储子包（M10）

会议记录与词频的持久化。采用「抽象基类 + 可插拔实现」，V1 用内存态存储（重启即失），V2 规划接入 MySQL。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：M10 存储模块，V1 默认 `MemoryStore`，V2 `MySQLStore`。 |
| `base.py` | `MeetingStore(ABC)` 抽象基类：定义存储协议 6 个抽象方法 —— `create_meeting`（新建 queued 记录）、`get_meeting`、`list_meetings`（分页/筛选，返回 `(total, items)`）、`update_meeting`（按字段更新）、`delete_meeting`（删除记录及词频）、`save_words`/`get_words`（词频明细）。API 层与 worker 层都只依赖此接口。 |
| `memory.py` | `MemoryStore(MeetingStore)`：V1 默认实现。内部用两个 dict（`_meetings`、`_words`）+ `itertools.count` 自增 seq（模拟自增主键）+ `threading.Lock`（防并发写）；时间戳用本地时间 ISO 格式（`_now_iso`）；列表按 id 倒序分页，支持 status/keyword 筛选。 |

## 实现演进

| 版本 | 存储 | 说明 |
|------|------|------|
| V1（当前） | `MemoryStore` | 内存 dict，重启即失，兜底模式，不依赖 MySQL |
| V2（规划） | `MySQLStore` | 服务器 MySQL + SQLAlchemy，`meeting_id`/`(meeting_id, word)` 唯一索引保证幂等 |
