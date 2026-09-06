"""百度短语音识别引擎（M7，真实识别实现）。

统一异步接口（与 MockEngine 一致，供 worker 逐块调用）：
    text = await engine.transcribeAPI(audio_path)   # -> str

内部流程：
    读 backend/.env 的 BAIDU_API_KEY / BAIDU_SECRET_KEY
    → 换 access_token（进程内缓存，默认 30 天有效）
    → 调短语音识别标准版接口

限制：音频需 ≤60s、16k/8k 单声道；格式 wav|pcm|amr|m4a（不支持 mp3，mp3 需先转码）。
"""

from __future__ import annotations

import asyncio
import base64
import os
import time
from pathlib import Path

import requests

from app.asr.apiBase import ASREngine

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
OAUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"
ASR_URL = "https://vop.baidu.com/server_api"
_SUPPORTED_FORMATS = {"wav", "pcm", "amr", "m4a"}


class BaiduEngine(ASREngine):
    def __init__(self, delay_seconds: float = 0.2) -> None:
        self._delay = delay_seconds  # 块间小停顿，规避百度 QPS 限流
        self._token: str | None = None
        self._token_expires: float = 0.0
        try:
            from dotenv import load_dotenv
            load_dotenv(BACKEND_DIR / ".env")
        except Exception:
            pass

    # ---------- token：懒获取 + 进程内缓存 ----------

    def _get_token(self) -> str | None:
        if self._token and time.time() < self._token_expires - 300:
            return self._token
        api_key = os.environ.get("BAIDU_API_KEY", "")
        secret_key = os.environ.get("BAIDU_SECRET_KEY", "")
        if not api_key or not secret_key:
            raise RuntimeError("缺少 BAIDU_API_KEY / BAIDU_SECRET_KEY（请配置 backend/.env）")
        resp = requests.post(
            OAUTH_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key,
            },
            timeout=15,
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"获取 token 失败: HTTP {resp.status_code} {data}")
        self._token = data["access_token"]
        self._token_expires = time.time() + int(data.get("expires_in", 2592000))
        return self._token

    # ---------- 统一异步接口（worker 调用）：同步请求放线程池，不阻塞事件循环 ----------

    async def transcribeAPI(self, audio_path: str) -> str:
        await asyncio.sleep(self._delay)  # 限流缓冲
        token = await asyncio.to_thread(self._get_token)
        fmt = self._fmt_from_ext(audio_path)
        return await asyncio.to_thread(self.transcribe_short, audio_path, token, fmt)

    # ---------- 工具 ----------

    def _fmt_from_ext(self, audio_path: str) -> str:
        fmt = Path(audio_path).suffix.lower().lstrip(".")
        if fmt not in _SUPPORTED_FORMATS:
            raise RuntimeError(
                f"百度短语音不支持 .{fmt}（支持 wav/pcm/amr/m4a，16k 单声道 ≤60s）"
            )
        return fmt

    # ---------- 同步底层识别（保留：demo/外部可直接调用） ----------

    def transcribe_short(self, path: str, token: str, fmt: str = "wav") -> str:
        with open(path, "rb") as f:
            raw = f.read()  # 整段读入（60s 内文件不大）
        body = {
            "format": fmt,  # pcm/wav/amr/m4a，与文件后缀一致
            "rate": 16000,  # 采样率，固定 16000 或 8000
            "channel": 1,  # 只支持单声道
            "cuid": "meeting-demo",  # 你的机器标识，<60 字符
            "token": token,
            "dev_pid": 1537,  # 1537=普通话带标点
            "len": len(raw),  # ⚠️ 原始字节数，不是 base64 后的长度
            "speech": base64.b64encode(raw).decode(),  # base64 字符串
        }
        r = requests.post(ASR_URL, json=body, timeout=60).json()
        if r.get("err_no") != 0:
            raise RuntimeError(
                f"识别失败 err_no={r.get('err_no')} err_msg={r.get('err_msg')} sn={r.get('sn')}"
            )
        return r["result"][0]
