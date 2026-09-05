# asr — 语音转写子包（M7）

音频块 → 文本 的转写引擎模块。采用「抽象基类 + 可插拔实现」，通过 `ASR_PROVIDER` 配置切换，无 key 时自动降级到 mock，保证全链路可跑通。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：`ASREngine` 抽象 + Mock 引擎（V1）+ 真实厂商引擎（V2）。 |
| `base.py` | `ASREngine(ABC)` 抽象基类：定义 `async transcribe(audio_path) -> str` 抽象方法（音频块 → 文本，失败抛异常由 worker 记 error_message）。 |
| `mock.py` | `MockEngine(ASREngine)`：V1 默认实现，内置示例会议文本 `_DEMO_TEXT`，`transcribe` 带可观测延时（`asyncio.sleep(delay_seconds)`）模拟处理过程，用于无真实音频/key 时演示全链路与进度。 |

## 实现演进

| 版本 | 引擎 | 说明 |
|------|------|------|
| V1（当前） | `MockEngine` | 内置示例文本 + 延时，无 key 可跑 |
| V2（规划） | `BaiduEngine` / 讯飞 / 阿里 / `WhisperEngine` | 真实录音文件识别，`ASR_PROVIDER` 切换；缺 key 自动落回 mock |
