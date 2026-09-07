from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    chat_1_id: int | None = None
    chat_2_id: int | None = None
    chat_3_id: int | None = None
    chat_3_mode: str = "auto"

    admin_chat_id: int | None = None
    admin_user_ids: list[int] = Field(default_factory=list)

    timezone: str = "Europe/Moscow"
    report_hour: int = 21
    report_minute: int = 0

    webhook_url: str | None = None
    webhook_path: str = "telegram"
    port: int = 8443

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def split_admin_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        return [int(part.strip()) for part in str(value).split(",") if part.strip()]

    @field_validator("webhook_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, value):
        if value is None or str(value).strip() == "":
            return None
        return str(value).rstrip("/")

    @field_validator("chat_3_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value):
        mode = str(value or "auto").strip().lower()
        if mode not in {"auto", "chat1", "chat2"}:
            return "auto"
        return mode

    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url

    def chat_ids(self) -> dict[str, int]:
        mapping: dict[str, int] = {}
        if self.chat_1_id is not None:
            mapping["chat1"] = self.chat_1_id
        if self.chat_2_id is not None:
            mapping["chat2"] = self.chat_2_id
        if self.chat_3_id is not None:
            mapping["chat3"] = self.chat_3_id
        return mapping


def load_settings() -> Settings:
    return Settings()
