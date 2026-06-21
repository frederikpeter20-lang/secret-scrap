from __future__ import annotations

import logging
from typing import Sequence

import aiohttp

from ..config import PushoverConfig

_logger = logging.getLogger(__name__)


async def send_notifications(results: Sequence, config: PushoverConfig) -> None:
    """Send notifications via Pushover."""
    if not results:
        return

    async with aiohttp.ClientSession() as session:
        for result in results:
            payload = {
                "token": config.token,
                "user": config.user,
                "title": result.get_title(),
                "message": result.get_message(),
                "url": result.get_url(),
                "url_title": "Zur Suche öffnen",
            }
            if config.device:
                payload["device"] = ",".join(config.device)

            try:
                async with session.post(
                    "https://api.pushover.net/1/messages.json",
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        _logger.info("Pushover notification sent for '%s'", result.get_title())
                    else:
                        data = await resp.json()
                        _logger.error("Pushover error: %s", data)
            except Exception as e:
                _logger.error("Failed to send Pushover notification: %s", e)
