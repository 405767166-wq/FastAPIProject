"""测试 BaiduEngine：读取 backend/.env 的 key → 换 token → 识别本地音频。

用法（在项目根目录执行）：
    .\\.venv\\Scripts\\python.exe backend\\examples\\baiduapitest.py
    .\\.venv\\Scripts\\python.exe backend\\examples\\baiduapitest.py 你的音频.wav

默认音频：backend/uploads/samples/meeting_demo_16k.wav（41.6s 会议录音）
依赖：requests（BaiduEngine 内部使用）、httpx 或 requests（本文件换 token 用）
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 让 `app` 包可被 import（无论从哪执行本文件）
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Windows 控制台打印中文/emoji 不崩溃
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
except Exception:
    pass

from app.asr.BaiduEngine import BaiduEngine  # noqa: E402

DEFAULT_AUDIO = BACKEND_DIR / "uploads" / "samples" / "meeting_demo_16k.wav"
OAUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"


def get_token(api_key: str, secret_key: str) -> str:
    """用 API Key / Secret Key 换取 access_token。"""
    import requests

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
    return data["access_token"]


def main(audio_path: Path | None = None) -> int:
    api_key = os.environ.get("BAIDU_API_KEY", "")
    secret_key = os.environ.get("BAIDU_SECRET_KEY", "")

    if not api_key or not secret_key:
        print("❌ backend/.env 缺少 BAIDU_API_KEY / BAIDU_SECRET_KEY，请先配置。")
        return 1

    audio = audio_path or DEFAULT_AUDIO
    if not Path(audio).exists():
        print(f"❌ 音频文件不存在: {audio}")
        return 1

    print(f"① 换取 access_token（{api_key[:4]}...）")
    token = get_token(api_key, secret_key)
    print(f"   ✓ access_token = {token[:20]}...（{len(token)} 字符）")

    print(f"② 调用 BaiduEngine.transcribe_short ...")
    print(f"   音频: {audio}（{Path(audio).stat().st_size} 字节）")
    engine = BaiduEngine()
    try:
        text = engine.transcribe_short(str(audio), token, fmt="wav")
    except Exception as exc:
        print(f"✗ 识别失败: {exc}")
        return 2

    print(f"   ✓ 识别成功，文本长度 {len(text)} 字")
    print("=" * 60)
    print(text)
    print("=" * 60)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试 BaiduEngine 识别本地音频")
    parser.add_argument("audio", nargs="?", default=str(DEFAULT_AUDIO), help="wav 音频路径")
    args = parser.parse_args()
    sys.exit(main(Path(args.audio)))
