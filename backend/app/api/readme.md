# api — REST API 路由子包（M3）

FastAPI 路由层，承载全部 HTTP 接口。统一挂载在 `/api` 前缀下，响应体遵循 `接口文档.md` §5.1 的统一结构。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合路由：创建 `api_router = APIRouter(prefix="/api")`，并 `include_router` 挂载 `health` 与 `meetings` 两个子路由。 |
| `health.py` | 健康检查 `GET /api/health`：返回服务状态、版本、`queue`（native/redis）、`queue_size`、`storage`（memory/mysql）、`asr` 提供方、`mysql`/`redis` 布尔标记及会议总数，用于观测各扩展是否生效。 |
| `meetings.py` | 会议相关 REST 路由（prefix `/meetings`）：`GET ""` 列表（P2.2）、`POST ""` 上传（P2.1，骨架阶段返回 501）、`GET /{meeting_id}` 详情（P2.3）、`GET /{meeting_id}/words` 词频（P2.5）、`GET /{meeting_id}/summary` 总结（P2.6）、`DELETE /{meeting_id}` 删除（P2.7）。内部通过 `_store(request)` 从 `app.state.store` 取存储实现。 |

## 接口对应关系（对照 版本规划.md §3）

| 接口 | 路径 | V1 | 现状 |
|------|------|----|------|
| P2.1 上传 | `POST /api/meetings` | ✅ | 骨架占位（501） |
| P2.2 列表 | `GET /api/meetings` | ✅ | 已接 MemoryStore |
| P2.3 详情 | `GET /api/meetings/{id}` | ✅ | 已接 MemoryStore |
| P2.5 词频 | `GET /api/meetings/{id}/words` | ✅ | 已接 MemoryStore |
| P2.6 总结 | `GET /api/meetings/{id}/summary` | ✅ | 已接 MemoryStore |
| P2.7 删除 | `DELETE /api/meetings/{id}` | ✅ | 已接 MemoryStore |
| 健康检查 | `GET /api/health` | ✅ | 已实现 |
