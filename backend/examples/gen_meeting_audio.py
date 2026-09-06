"""生成一段"周会"风格的中文语音测试音频（16kHz / 单声道 / wav）。

原理：
  1. edge-tts（微软在线语音合成，免费）把会议文本合成为 mp3
  2. imageio-ffmpeg 内置的 ffmpeg 转成 百度短语音要求的 16k 单声道 wav

用法：
  python gen_meeting_audio.py                        # 默认输出 backend/uploads/samples/meeting_demo_16k.wav
  python gen_meeting_audio.py 输出路径.wav
  python gen_meeting_audio.py --voice zh-CN-YunxiNeural  # 换男声

依赖：edge-tts、imageio-ffmpeg（已在项目 .venv 安装）
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MEETING_TEXT = (
    "大家好，欢迎参加本周的项目例会。先汇报整体进度，前端页面已经基本完成，正在联调接口。"
    "后端的录音转写模块还在开发中，预计本周五交付。数据库方面，会议记录表已经建好，词频表也已经完成。"
    "接下来分配本周任务，张工负责接口联调，李工负责写测试用例，王工负责部署服务器。"
    "请注意，下周一项目正式上线，所有功能必须在周日前完成回归测试，遇到问题及时在群里沟通。"
    "好，今天的会议就到这里，散会。"
)

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "uploads" / "samples" / "meeting_demo_16k.wav"


async def synth_mp3(text: str, mp3_path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(mp3_path)


def mp3_to_wav_16k(mp3_path: str, wav_path: str) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1",
         "-f", "wav", wav_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 转换失败 code={proc.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成会议测试音频")
    parser.add_argument("out", nargs="?", default=str(DEFAULT_OUT), help="输出 wav 路径")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural",
                        help="edge-tts 中文音色，如 zh-CN-YunxiNeural(男声)")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        print(f"① 语音合成（{args.voice}）...")
        asyncio.run(synth_mp3(MEETING_TEXT, tmp_mp3, args.voice))
        print(f"   生成 mp3: {os.path.getsize(tmp_mp3)} 字节")

        print("② ffmpeg 转 16kHz 单声道 wav ...")
        mp3_to_wav_16k(tmp_mp3, str(out_path))

        with wave.open(str(out_path), "rb") as w:
            dur = w.getnframes() / w.getframerate()
            print(f"✓ 完成: {out_path}")
            print(f"  格式: {w.getnchannels()}声道 {w.getframerate()}Hz "
                  f"时长 {dur:.1f}s（{os.path.getsize(out_path)} 字节）")
            if dur > 58:
                print("⚠️ 时长接近 60s，百度短语音可能超限，建议精简文本重生成")
        return 0
    finally:
        try:
            os.remove(tmp_mp3)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
