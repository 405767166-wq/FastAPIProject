# backend — 后端应用根目录

会议纪要智能转写系统的 FastAPI 后端，基于 **Python 3.12**。本目录是被 pytest 识别为源码根（`pyproject.toml` 中 `pythonpath = ["backend"]`）的应用包所在位置。

## 本级每个文件说明

| 文件 / 目录 | 说明 |
|-------------|------|
| `app/` | FastAPI 应用主包：装配入口、配置、统一响应、worker 与各业务子包（api/asr/chunk/freq/queue/store/summary）。详见其 `readme.md`。 |
| `tests/` | pytest 单元测试目录（当前为骨架冒烟测试）。详见其 `readme.md`。 |
| `.env.example` | 环境配置模板：复制为 `backend/.env` 后按需填写。V1 默认值即可运行（原生队列 + 内存存储 + mock ASR + 模板总结）；填 `MYSQL_HOST`/`REDIS_URL`/`DEEPSEEK_API_KEY` 即切换到对应 V2 扩展。字段与 `app/config.py` 的 `Settings` 一一对应。 |

## 目录结构

```
backend/
├─ app/               应用包（核心代码）
│  ├─ api/            REST 路由
│  ├─ asr/            语音转写（M7）
│  ├─ chunk/          音频分块（M6）
│  ├─ freq/           词频统计（M5，考核点）
│  ├─ queue/          任务队列（M4，考核点）
│  ├─ store/          存储（M10）
│  ├─ summary/        智能总结（M8）
│  ├─ __init__.py     包说明与 __version__
│  ├─ config.py       配置读取（pydantic-settings）
│  ├─ errors.py       业务异常与错误码
│  ├─ main.py         FastAPI 装配入口
│  ├─ responses.py    统一响应体
│  └─ worker.py       后台消费循环（M11）
├─ tests/             pytest 测试
└─ .env.example       配置模板
```

## 启动与测试

```bash
# 启动（本目录下）
uvicorn app.main:app --reload --port 8000

# 测试（仓库根目录下）
python -m pytest -q
```
