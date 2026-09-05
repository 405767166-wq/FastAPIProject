# tests — 单元测试目录

pytest 测试代码。通过 `pyproject.toml` 配置 `pythonpath = ["backend"]` 与 `testpaths = ["backend/tests"]`、`asyncio_mode = "auto"`，运行命令：`python -m pytest -q`。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：backend 单元测试，运行方式 `python -m pytest -q`。 |
| `test_smoke.py` | 骨架冒烟测试，用 `fastapi.testclient.TestClient` 验证应用可启动及基础路由：`test_health`（健康检查返回 `code=0`、`status=up`、`storage=memory`、`asr=mock`）、`test_empty_meeting_list`（空列表）、`test_not_found_meeting`（不存在返回 404 + `40401`）、`test_upload_still_pending_in_skeleton`（骨架阶段上传返回 501）。核心逻辑实现后此文件将扩展/替换为队列、词频、全流程等测试。 |

## 规划中的测试（对应 版本规划.md §5 V1 验收）

- 队列入队/消费（M4 考核点）
- Counter 词频 Top-N（M5 考核点）
- 上传 → 处理 → 完成 的整链路（mock）
