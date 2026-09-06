"""统一响应体封装。对应 接口文档.md §5.1：

    { "code": 0, "message": "ok", "data": ... }
"""

from __future__ import annotations

from typing import Any


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def error(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
