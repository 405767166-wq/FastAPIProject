"""应用配置：从 backend/.env 读取（pydantic-settings）。

V1 阶段所有扩展项保持空值 → 自动走 原生队列 + 内存存储 + Mock ASR + 模板总结。
V2 阶段填入服务器信息即可切换（见 版本规划.md §4），代码无需改动。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（config.py 的上两级：app/config.py -> backend/）
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 服务 ----
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # ---- 存储目录 ----
    upload_dir: str = str(BACKEND_DIR / "uploads")

    # ---- V2 扩展：MySQL（留空 => memory 存储）----
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_db: str = "meeting_minutes"

    # ---- V2 扩展：Redis（留空 => 原生 asyncio.Queue）----
    redis_url: str = ""

    # ---- 语音转写：V1 恒为 mock；V2 可切换 baidu/whisper/... ----
    asr_provider: str = "mock"
    asr_chunk_seconds: int = 60

    # ---- DeepSeek 总结：V1 留空 => 模板降级 ----
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    @property
    def storage_backend(self) -> str:
        """V1: memory；V2: 配置了 MYSQL_HOST 即 mysql。"""
        return "mysql" if self.mysql_host else "memory"

    @property
    def queue_backend(self) -> str:
        """V1: native；V2: 配置了 REDIS_URL 即 redis。"""
        return "redis" if self.redis_url else "native"

    def ensure_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


settings = get_settings()
