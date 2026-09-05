# chunk — 音频分块子包（M6）

将长录音切分为多个音频块，用于支撑逐块转写、细粒度进度与并发。采用「抽象基类 + 可插拔实现」。

## 本级每个文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包说明：`Chunker` 抽象 + 单块降级（V1）+ ffmpeg 真实切块（V2）。 |
| `base.py` | `Chunker(ABC)` 抽象基类：定义 `chunk(audio_path, work_dir) -> list[str]` 抽象方法，返回切块文件路径列表（V1 单块即原文件自身）。 |
| `single.py` | `SingleChunker(Chunker)`：V1 默认实现，无 ffmpeg 时把原始音频原样复制为唯一块 `chunk_0001.mp3`，进度分母为 1。 |

## 实现演进

| 版本 | 分块器 | 说明 |
|------|--------|------|
| V1（当前） | `SingleChunker` | 整文件单块（`chunk_count=1`），保持 stage/进度模型完整 |
| V2（规划） | `FFmpegChunker` | `ffmpeg -ss/-t` 按时长（默认 60s/块）或大小切块，逐块进度 |
