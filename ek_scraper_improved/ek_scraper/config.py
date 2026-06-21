from __future__ import annotations

import re
from typing import Any

from pydantic import Field, field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import __version__


class SearchConfig(BaseSettings):
    name: str
    url: str
    recursive: bool = True


class FilterConfig(BaseSettings):
    exclude_topads: bool = True
    exclude_patterns: list[re.Pattern[str]] = Field(default_factory=list)
    price_min: int | None = None
    price_max: int | None = None

    @field_serializer("exclude_patterns")
    def serialize_exclude_patterns(self, patterns: list[re.Pattern[str]], _info: Any) -> list[str]:
        return [p.pattern for p in patterns]


class NtfyShConfig(BaseSettings):
    topic: str
    priority: int = 3


class PushoverConfig(BaseSettings):
    token: str
    user: str
    device: list[str] = Field(default_factory=list)

    def model_dump_api(self) -> dict[str, Any]:
        data = self.model_dump()
        if self.device:
            data["device"] = ",".join(self.device)
        return data


class TelegramConfig(BaseSettings):
    bot_token: str
    chat_id: str | int


class NotificationsConfig(BaseSettings):
    pushover: PushoverConfig | None = None
    ntfy_sh: NtfyShConfig | None = Field(default=None, alias="ntfy.sh")
    telegram: TelegramConfig | None = None


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    filter: FilterConfig = Field(default_factory=FilterConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    searches: list[SearchConfig] = Field(default_factory=list)

    # Global settings
    request_delay_min: float = 1.5
    request_delay_max: float = 4.0
    request_timeout: int = 30

    # Proxy support (http://user:pass@host:port or list for rotation)
    proxy: str | list[str] | None = None
    use_proxy: bool = False
