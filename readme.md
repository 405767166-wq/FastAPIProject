# FastAPIProject — 项目根目录

> 会议纪要智能转写系统（Meeting Minutes Intelligent Transcription System）后端仓库根目录。

## 项目一句话定义

用户上传会议录音，系统经「分块 → 语音转文字 → 中文分词词频统计 → DeepSeek 总结」生成结构化会议纪要，全程可查看进度，并支持历史记录回查。

系统按 **V1（基本功能）/ V2（全功能）** 双版本在同一仓库内分阶段演进，当前代码处于 **V1 骨架阶段**（核心数据链路尚未实现，见 `版本规划.md`）。

## 目录骨架总览

```
FastAPIProject/
├─ backend/            后端应用（FastAPI + Python 3.12）
├─ .idea/              PyCharm IDE 工程配置（本仓库保留）
├─ .tmp/               临时文件
├─ .gitignore          Git 忽略规则
├─ pyproject.toml      Python 项目与依赖定义
├─ uv.lock             uv 依赖锁定文件
├─ 接口文档.md          系统总规格（最终长什么样）
├─ 版本规划.md          V1/V2 分两步交付的执行蓝本
└─ test_main.http      REST 冒烟测试脚本（HTTP Client）
```

## 本级每个文件说明

| 文件 / 目录 | 说明 |
|-------------|------|
| `backend/` | 后端应用根目录，含 `app/` 应用包、`tests/` 测试与 `.env.example` 配置模板。详见其 `readme.md`。 |
| `.idea/` | JetBrains PyCharm 的工程级配置文件（模块、SDK、VCS、代码检查等）。详见其 `readme.md`。 |
| `.tmp/` | 临时/探测文件目录。详见其 `readme.md`。 |
| `.gitignore` | Git 忽略规则：排除 `.venv/`、`__pycache__/`、`.pytest_cache/`、`.idea/`（注：当前仓库实际保留了 `.idea/`）、`backend/uploads/`、`.env`、`frontend/node_modules|dist`、`tools/` 等。 |
| `pyproject.toml` | 项目元数据与依赖声明：`name=fastapiproject`、`requires-python>=3.12`；运行依赖 `fastapi/uvicorn/python-multipart/pydantic-settings/jieba`；`dev` 可选依赖 `pytest/pytest-asyncio/httpx`；并配置了 pytest 的 `pythonpath=backend`、`testpaths=backend/tests`、`asyncio_mode=auto`。 |
| `uv.lock` | `uv` 包管理器生成的依赖锁定文件（锁定全部传递依赖的精确版本，保证可复现安装）。 |
| `接口文档.md` | **系统总规格文档**：项目概述、技术选型定稿、总体架构与数据流、模块划分（M1~M11）、REST API 规范（§5）、MySQL 数据库设计（§6）、配置项（§7）、部署方案（§8）、开发顺序与验收点（§9）、前期讨论结论（§10）。 |
| `版本规划.md` | **执行蓝本**：V1（基本功能，纯后端 + 原生队列 + 内存存储 + Mock ASR + 模板总结）与 V2（全功能，+ MySQL/Redis/ffmpeg/真实 ASR/DeepSeek/实时进度/前端/Nginx）的切分、模块/接口归属表、验收标准、目录结构与执行顺序。 |
| `test_main.http` | JetBrains HTTP Client 格式的 REST 冒烟脚本：健康检查、空列表、不存在详情、上传（骨架阶段返回 501）等请求示例。 |

## 常用命令

```bash
# 安装依赖（uv）
uv sync

# 运行测试
python -m pytest -q

# 启动后端（backend 目录下）
cd backend && uvicorn app.main:app --reload --port 8000
```
