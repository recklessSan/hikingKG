from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AURUM_", extra="ignore")

    # Empty until the user pastes a token from @BotFather — the process
    # then idles instead of crashing compose.
    telegram_bot_token: str = ""
    # Comma-separated Telegram user ids allowed to talk to the bot.
    # Empty = deny everyone (safer default than open access).
    telegram_allowed_user_ids: str = ""

    # In-compose the backend is reachable as http://backend:8000.
    telegram_api_base: str = "http://backend:8000/api"
    # Prefer AURUM_TELEGRAM_BASIC_AUTH_*; fall back to the app's
    # AURUM_BASIC_AUTH_* so one pair covers UI + bot.
    telegram_basic_auth_user: str = ""
    telegram_basic_auth_password: str = ""
    basic_auth_user: str = ""
    basic_auth_password: str = ""

    def allowed_user_ids(self) -> set[int]:
        if not self.telegram_allowed_user_ids.strip():
            return set()
        ids: set[int] = set()
        for part in self.telegram_allowed_user_ids.split(","):
            part = part.strip()
            if part:
                ids.add(int(part))
        return ids

    def api_basic_auth(self) -> tuple[str, str] | None:
        user = self.telegram_basic_auth_user or self.basic_auth_user
        password = self.telegram_basic_auth_password or self.basic_auth_password
        if user and password:
            return user, password
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
