from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Analyzer"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"

    cors_origins: str = "http://localhost:5173"
    max_pdf_size_mb: int = 10
    max_resume_chars: int = 30_000

    resume_cache_ttl_seconds: int = 86_400
    match_cache_ttl_seconds: int = 86_400
    redis_url: str | None = None

    dashscope_api_key: SecretStr | None = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    ai_timeout_seconds: float = 35.0
    ai_max_retries: int = 2
    prompt_version: str = "2026-07-v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.dashscope_api_key and self.dashscope_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
