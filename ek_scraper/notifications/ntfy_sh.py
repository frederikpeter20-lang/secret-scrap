from __future__ import annotations

import logging
from typing import Sequence

import aiohttp

from ..config import NtfyShConfig

_logger = logging.getLogger(__name__)


async def send_notifications(results: Sequence, config: NtfyShConfig) -> None:
    """Send notifications via ntfy.sh."""
    if not results:
        return

    async with aiohttp.ClientSession() as session:
        for result in results:
            headers = {
                "Title": result.get_title(),
                "Priority": str(config.priority),
                "Click": result.get_url(),
            }

            try:
                async with session.post(
                    f"https://ntfy.sh/{config.topic}",
                    data=result.get_message(),
                    headers=headers,
                ) as resp:
                    if resp.status == 200:
                        _logger.info("ntfy.sh notification sent for '%s'", result.get_title())
                    else:
                        _logger.error("ntfy.sh error: %s", resp.status)
            except Exception as e:
                _logger.error("Failed to send ntfy.sh notification: %s", e)
