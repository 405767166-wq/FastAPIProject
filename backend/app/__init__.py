"""会议纪要智能转写系统 — backend 包。

V1（基本功能）：原生 asyncio.Queue + dict/Counter + MemoryStore + Mock ASR + 模板总结 + 全 REST。
V2（所有功能）：在 V1 基础上增加 MySQL / Redis / ffmpeg / 真实 ASR / DeepSeek / 实时进度 / 前端 / Nginx。
详见 接口文档.md 与 版本规划.md。
"""

__version__ = "0.2.0"
