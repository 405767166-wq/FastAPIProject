# queue — 任务队列子包（M4，考核点）

承接 API 层提交的任务并缓存，实现生产者（API）与消费者（worker）解耦。核心考核点之一：使用 Python 原生 `asyncio.Queue` 单进程内串联。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：M4 任务队列模块（考核点）。 |
| `base.py` | `TaskQueue(ABC)` 抽象基类：定义 `push(task)`（生产者入队，不阻塞）与 `async pop()`（消费者出队，阻塞直到有任务）两个抽象方法。业务层只依赖此接口，不感知具体实现。 |
| `native_queue.py` | `NativeTaskQueue(TaskQueue)`：V1 默认实现，内部持有 `asyncio.Queue[dict]`；`push()` 用 `put_nowait`，`pop()` 用 `await get()`，并提供 `size` 属性（`qsize()`）供健康检查观测在途任务数。 |

## 设计要点

- 与 FastAPI 同一事件循环：API 层 `push()` 不阻塞，worker 协程 `await pop()` 阻塞消费。
- 单元测试只测原生实现（考核点），不依赖 Redis。

## 实现演进

| 版本 | 数据结构 | 操作 | 启用条件 |
|------|----------|------|----------|
| V1（当前） | `asyncio.Queue` | `put_nowait` / `await get` | 默认 |
| V2（规划） | Redis List | `LPUSH` / `BRPOP` | 配置 `REDIS_URL` 后自动启用 |
