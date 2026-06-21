from __future__ import annotations

import logging
from typing import Sequence

import httpx

from ..config import PushoverConfig
from ..scraper import Result

_logger = logging.getLogger(__name__)

async def send_notifications(results: Sequence[Result], config: PushoverConfig) -> None:
    """Send notifications via Pushover."""
    # ... (full implementation)
    pass
