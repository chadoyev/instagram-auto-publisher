from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Telegram ──────────────────────────────────────────────
    bot_token: SecretStr = Field(alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    webhook_host: str = Field(default="", alias="WEBHOOK_HOST")
    webhook_path: str = Field(default="/ig", alias="WEBHOOK_PATH")
    webhook_port: int = Field(default=8081, alias="WEBHOOK_PORT")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    bot_mode: Literal["webhook", "polling"] = Field(
        default="polling", alias="BOT_MODE"
    )

    # ── Instagram ─────────────────────────────────────────────
    ig_username: str = Field(default="", alias="IG_USERNAME")
    ig_password: SecretStr = Field(default=SecretStr(""), alias="IG_PASSWORD")
    ig_session_path: Path = Field(
        default=BASE_DIR / "session_data" / "session.json", alias="IG_SESSION_PATH"
    )

    # ── External APIs ─────────────────────────────────────────
    hiker_api_key: str = Field(default="", alias="HIKER_API_KEY")
    tiktok_api_url: str = Field(
        default="http://tiktok-api:80", alias="TIKTOK_API_URL"
    )

    # ── Database ──────────────────────────────────────────────
    db_url: str = Field(
        default="postgresql+asyncpg://bot:bot@postgres:5432/bot",
        alias="DATABASE_URL",
    )

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # ── Content ───────────────────────────────────────────────
    default_caption: str = Field(
        default="Подписывайся!", alias="DEFAULT_CAPTION"
    )
    media_root: Path = Field(
        default=BASE_DIR / "media", alias="MEDIA_ROOT"
    )
    watermark_path: Path | None = Field(default=None, alias="WATERMARK_PATH")
    max_video_duration: int = Field(default=240, alias="MAX_VIDEO_DURATION")

    # ── Schedule defaults ─────────────────────────────────────
    daily_reset_time: str = Field(default="00:00", alias="DAILY_RESET_TIME")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | int | list[int]) -> list[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_host}{self.webhook_path}"

    def get_media_dir(self, *parts: str) -> Path:
        p = self.media_root.joinpath(*parts)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()  # type: ignore[call-arg]
