# app — FastAPI 应用主包

会议纪要智能转写系统的后端核心代码包。采用「抽象基类 + V1 原生实现（当前）+ V2 扩展实现（规划中）」的分层结构，业务层只依赖抽象接口，不感知具体实现，差异由 `.env` 配置开关决定。

## 本级每个文件说明

| 文件 / 目录 | 说明 |
|-------------|------|
| `__init__.py` | 包级文档字符串（概述 V1/V2 范围）并定义 `__version__ = "0.2.0"`。 |
| `config.py` | 应用配置：`Settings(BaseSettings)` 从 `backend/.env` 读取（pydantic-settings）；定义 `storage_backend`（memory/mysql）、`queue_backend`（native/redis）等派生属性；`get_settings()` 用 `lru_cache` 缓存并自动 `ensure_dirs()` 创建上传目录。 |
| `errors.py` | 业务错误体系：`ErrCode` 枚举（0/40001/40401/40901/50001/50002）、`ApiError` 异常类、`not_implemented()` 骨架阶段占位错误（返回 501）。 |
| `main.py` | FastAPI 装配入口：`lifespan` 中构建 store/queue/worker 并作为后台任务拉起 worker、关闭时优雅取消；注册 `ApiError` 全局异常处理器为统一响应体；`include_router(api_router)`。 |
| `responses.py` | 统一响应体封装：`ok(data, message)` 与 `err(code, message, data)`，对应 `接口文档.md` §5.1 的 `{code, message, data}` 结构。 |
| `worker.py` | M11 后台 worker：`Worker.run()` 死循环 `await queue.pop()` 后 `_handle(task)`；`_handle` 目前为骨架占位（抛 `NotImplementedError` 并落 `status=failed` + `error_message`），规划中的完整链路为 分块→ASR→词频→总结→落库。 |
| `api/` | REST 路由子包（M3）。详见其 `readme.md`。 |
| `asr/` | 语音转写子包（M7）。详见其 `readme.md`。 |
| `chunk/` | 音频分块子包（M6）。详见其 `readme.md`。 |
| `freq/` | 词频统计子包（M5，考核点）。详见其 `readme.md`。 |
| `queue/` | 任务队列子包（M4，考核点）。详见其 `readme.md`。 |
| `store/` | 存储子包（M10）。详见其 `readme.md`。 |
| `summary/` | 智能总结子包（M8）。详见其 `readme.md`。 |

## 模块归属（对照 版本规划.md）

| 子包 | 模块编号 | 职责 | V1 实现（当前） | V2 规划 |
|------|---------|------|----------------|---------|
| `api/` | M3 | REST 服务层 | health + meetings | + progress 轮询 + WS |
| `queue/` | M4 | 任务队列（考核点） | `asyncio.Queue` | Redis List |
| `freq/` | M5 | 词频哈希（考核点） | `dict`/`Counter`+jieba | Redis Hash |
| `chunk/` | M6 | 分块 | 单块降级 | ffmpeg 真实切块 |
| `asr/` | M7 | 语音转写 | MockEngine | 百度/讯飞/阿里/whisper |
| `summary/` | M8 | 智能总结 | 模板降级 | DeepSeek |
| `store/` | M10 | 持久化 | MemoryStore | MySQL |
| `worker.py` | M11 | 消息串联 | 消费循环（骨架） | 完整管线 |
