"""本地一键启动入口（开发用）。

PyCharm：右键本文件 → Run 'run' 即可，无需配置 FastAPI/Python 运行项。
命令行：python backend/run.py
说明：把 backend 目录放入 sys.path 并切为工作目录，再以模块方式启动 uvicorn，
      保证 `import app.main`、.env 读取、上传目录解析都正确。
"""

from __future__ import annotations

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import uvicorn  # noqa: E402

from app.config import settings  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,   # 需要热重载时改为 True（PyCharm 下重载会多开进程，演示建议 False）
        log_level="info",
    )
