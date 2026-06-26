"""Configuration models using pydantic and pydantic-settings."""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field, field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchConfig(BaseSettings):
    """Configuration for a single search on kleinanzeigen.de."""

    name: str = Field(..., description="Human-readable name for this search")
    url: str = Field(..., description="Full search URL from kleinanzeigen.de")
    recursive: bool = Field(
        default=True, description="Follow pagination to scrape all results"
    )


class FilterConfig(BaseSettings):
    """Filtering configuration for advertisement items."""

    exclude_topads: bool = Field(
        default=True, description="Exclude promoted top ads"
    )
    exclude_patterns: list[re.Pattern[str]] = Field(
        default_factory=list,
        description="Regex patterns to exclude (title/description)",
    )
    price_min: int | None = Field(
        default=None, description="Minimum price in EUR (inclusive)"
    )
    price_max: int | None = Field(
        default=None, description="Maximum price in EUR (inclusive)"
    )

    @field_serializer("exclude_patterns")
    def serialize_exclude_patterns(
        self, patterns: list[re.Pattern[str]], _info: Any
    ) -> list[str]:
        """Serialize regex patterns to strings."""
        return [p.pattern for p in patterns]


class NtfyShConfig(BaseSettings):
    """Configuration for ntfy.sh notifications."""

    topic: str = Field(..., description="ntfy.sh topic name")
    priority: int = Field(default=3, description="Priority level (1-5)")


class PushoverConfig(BaseSettings):
    """Configuration for Pushover notifications."""

    token: str = Field(..., description="Pushover application token")
    user: str = Field(..., description="Pushover user key")
    device: list[str] = Field(
        default_factory=list, description="Target devices (optional)"
    )

    def model_dump_api(self) -> dict[str, Any]:
        """Format config for Pushover API."""
        data = self.model_dump()
        if self.device:
            data["device"] = ",".join(self.device)
        return data


class TelegramConfig(BaseSettings):
    """Configuration for Telegram notifications."""

    bot_token: str = Field(..., description="Telegram bot token")
    chat_id: str | int = Field(..., description="Telegram chat ID")


class NotificationsConfig(BaseSettings):
    """Configuration for all notification channels."""

    pushover: PushoverConfig | None = Field(default=None)
    ntfy_sh: NtfyShConfig | None = Field(default=None, alias="ntfy.sh")
    telegram: TelegramConfig | None = Field(default=None)


class Config(BaseSettings):
    """Main configuration model."""

    model_config = SettingsConfigDict(
        env_prefix="EK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    filter: FilterConfig = Field(default_factory=FilterConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    searches: list[SearchConfig] = Field(default_factory=list)

    request_delay_min: float = Field(
        default=1.5, description="Minimum delay between requests (seconds)"
    )
    request_delay_max: float = Field(
        default=4.0, description="Maximum delay between requests (seconds)"
    )
    request_timeout: int = Field(
        default=30, description="Request timeout (seconds)"
    )

    proxy: str | list[str] | None = Field(
        default=None, description="Proxy URL or list for rotation"
    )
    use_proxy: bool = Field(default=False, description="Enable proxy usage")
