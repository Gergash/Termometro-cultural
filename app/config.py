"""
Centralized configuration for Termómetro Cultural.
Uses pydantic-settings with .env loading.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="termometro-cultural", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://localhost/termometro_cultural",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://localhost/termometro_cultural",
        alias="DATABASE_URL_SYNC",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    use_redis_queue: bool = Field(default=False, alias="USE_REDIS_QUEUE")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    grok_api_key: Optional[str] = Field(default=None, alias="GROK_API_KEY")
    grok_model: str = Field(default="grok-2", alias="GROK_MODEL")

    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    proxy_rotation: bool = Field(default=False, alias="PROXY_ROTATION")
    proxy_list: str = Field(default="", alias="PROXY_LIST")

    municipality_name: str = Field(default="Tuluá", alias="MUNICIPALITY_NAME")
    municipality_region: str = Field(default="Valle del Cauca", alias="MUNICIPALITY_REGION")
    timezone: str = Field(default="America/Bogota", alias="TIMEZONE")

    # Scheduler
    scrape_interval_hours: int = Field(default=12, alias="SCRAPE_INTERVAL_HOURS")
    process_batch_size: int = Field(default=100, alias="PROCESS_BATCH_SIZE")

    @property
    def proxy_urls(self) -> List[str]:
        if not self.proxy_list:
            return []
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
