"""业务异常与错误码。对应 接口文档.md §5.10。

HTTP 状态码仍按 §5.1：400/404/409/500；code 为业务错误码。
"""

from __future__ import annotations

from typing import Any


class ErrCode:
    OK = 0
    PARAM = 40001          # 参数/文件校验失败
    NOT_FOUND = 40401      # 会议不存在
    STAGE = 40901          # 任务尚未进入该阶段
    INTERNAL = 50001       # 内部错误（含 worker 落库失败）
    THIRD_PARTY = 50002    # 第三方 API（语音/总结）失败


class ApiError(Exception):
    """业务错误：由全局异常处理器转成统一响应体。"""

    def __init__(
        self,
        code: int,
        message: str,
        http_status: int = 400,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.data = data


def not_implemented(where: str) -> ApiError:
    """骨架阶段的占位错误：路由已定义但核心链路尚未实现。"""
    return ApiError(
        ErrCode.INTERNAL,
        f"接口尚未实现（骨架阶段）：{where}。按 版本规划.md §8-1 完成 V1 核心逻辑后启用。",
        http_status=501,
    )
