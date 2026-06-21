from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import AsyncGenerator
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from .config import Config, FilterConfig, SearchConfig
from .data_store import AdItem, DataStore
from .error import ScraperError

_logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
]

REFERERS = [
    "https://www.google.de/",
    "https://www.google.com/",
    "https://www.kleinanzeigen.de/",
    "https://duckduckgo.com/",
    "",
]


def get_random_headers() -> dict[str, str]:
    """Return randomized headers with rotating User-Agent and Referer."""
    ua = random.choice(USER_AGENTS)
    referer = random.choice(REFERERS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def get_proxy(config: Config) -> str | None:
    """Get a proxy from config (supports single or list for basic rotation)."""
    if not config.use_proxy or not config.proxy:
        return None
    if isinstance(config.proxy, list):
        return random.choice(config.proxy)
    return config.proxy


async def get_filtered_search_result(
    search: SearchConfig,
    filter_config: FilterConfig,
    store: DataStore,
    config: Config,
) -> list[AdItem]:
    """Fetch and filter search results."""
    # Placeholder implementation
    _logger.info("Fetching results for search: %s", search.name)
    return []
