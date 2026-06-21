from __future__ import annotations

import asyncio
import logging
from typing import Sequence

import aiohttp

from ..config import TelegramConfig
from ..scraper import Result, download_image

_logger = logging.getLogger(__name__)


async def send_notifications(results: Sequence[Result], config: TelegramConfig) -> None:
    """Send notifications via Telegram Bot. Sends photo + caption if first ad has image (thumbnail)."""
    if not results:
        return

    async with aiohttp.ClientSession() as session:
        for result in results:
            if not result.ad_items:
                continue

            first_ad = result.ad_items[0] if result.ad_items else None
            image_bytes = None
            if first_ad and getattr(first_ad, 'image_url', None):
                image_bytes = await download_image(session, first_ad.image_url)

            base_caption = (
                f"🤖 *{result.get_title()}*\n\n"
                f"{result.get_message()}\n\n"
                f"[Zur Suche öffnen]({result.get_url()})"
            )

            try:
                if image_bytes:
                    # Send as photo with caption (thumbnail download)
                    url = f"https://api.telegram.org/bot{config.bot_token}/sendPhoto"
                    data = aiohttp.FormData()
                    data.add_field("chat_id", str(config.chat_id))
                    data.add_field("photo", image_bytes, filename="thumbnail.jpg", content_type="image/jpeg")
                    data.add_field("caption", base_caption)
                    data.add_field("parse_mode", "Markdown")

                    async with session.post(url, data=data) as resp:
                        if resp.status != 200:
                            resp_data = await resp.json()
                            _logger.error("Telegram photo error: %s", resp_data)
                        else:
                            _logger.info("Telegram photo notification sent for '%s'", result.get_title())
                else:
                    # Fallback to text message
                    url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
                    payload = {
                        "chat_id": config.chat_id,
                        "text": base_caption,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    }
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            data = await resp.json()
                            _logger.error("Telegram error: %s", data)
                        else:
                            _logger.info("Telegram notification sent for '%s'", result.get_title())
            except Exception as e:
                _logger.error("Failed to send Telegram notification: %s", e)
