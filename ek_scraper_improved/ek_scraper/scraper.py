from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import AsyncGenerator
from urllib.parse import urljoin

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .config import Config, FilterConfig, SearchConfig
from .data_store import AdItem, DataStore
from .error import ScraperError


async def download_image(session: aiohttp.ClientSession, url: str, timeout: int = 15) -> bytes | None:
    """Download image (thumbnail) and return bytes. Returns None on failure."""
    if not url:
        return None
    try:
        headers = get_random_headers()
        async with asyncio.timeout(timeout):
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200 and resp.content_type.startswith("image/"):
                    return await resp.read()
    except Exception as e:
        _logger.warning("Failed to download image %s: %s", url, e)
    return None

_logger = logging.getLogger(__name__)

# Multiple realistic User-Agents for rotation (updated 2026)
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
    "",  # direct
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


class ScraperError(Exception):
    """Base exception for scraper errors"""
    pass


async def get_soup(
    session: aiohttp.ClientSession, url: str, timeout: int = 30, proxy: str | None = None
) -> BeautifulSoup:
    """Fetch page and return BeautifulSoup object with proper error handling.
    Supports proxy and rotating headers.
    """
    headers = get_random_headers()

    try:
        async with asyncio.timeout(timeout):
            kwargs = {"headers": headers}
            if proxy:
                kwargs["proxy"] = proxy
            async with session.get(url, **kwargs) as resp:
                if resp.status != 200:
                    raise ScraperError(f"HTTP {resp.status} for {url}")
                if not resp.content_type.startswith("text/html"):
                    raise ScraperError(f"Unexpected content type: {resp.content_type}")
                html = await resp.text()
                return BeautifulSoup(html, "lxml")
    except asyncio.TimeoutError:
        raise ScraperError(f"Timeout fetching {url}")
    except aiohttp.ClientError as e:
        raise ScraperError(f"Network error for {url}: {e}") from e


def parse_price(price_str: str) -> int | None:
    """Extract numeric price from string like '450 €' or 'VB'."""
    if not price_str or "VB" in price_str.upper():
        return None
    match = re.search(r"([\d.]+)", price_str.replace(".", ""))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def get_pagination_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Find all pagination links."""
    urls = []
    for a in soup.select("a.pagination-page, a[href*='page=']"):
        href = a.get("href")
        if isinstance(href, str):
            full_url = urljoin(base_url, href)
            if full_url not in urls:
                urls.append(full_url)
    return urls


async def get_ad_items_from_page(
    soup: BeautifulSoup, base_url: str
) -> AsyncGenerator[AdItem, None]:
    """Extract AdItems from a single search result page."""
    articles = soup.find_all("article", class_="aditem") or soup.find_all(
        "article", attrs={"data-adid": True}
    )

    for article in articles:
        try:
            ad_id = article.get("data-adid") or article.get("data-id")
            if not ad_id:
                continue

            title_el = article.select_one(".text-module-begin a, h2 a, .aditem-main--middle--title a")
            title = title_el.get_text(strip=True) if title_el else "Kein Titel"

            desc_el = article.select_one(
                ".aditem-main--middle--description, .aditem-main--middle--description-text"
            )
            description = desc_el.get_text(strip=True) if desc_el else ""

            loc_el = article.select_one('i[class*="icon-pin"], .aditem-main--top--left')
            location = loc_el.parent.get_text(strip=True) if loc_el and loc_el.parent else "Unbekannt"

            price_el = article.select_one('p[class*="price"], .aditem-main--middle--price')
            price = price_el.get_text(strip=True) if price_el else "Preis auf Anfrage"

            img_el = article.select_one(".imagebox, .galleryimage")
            image_url = img_el.get("data-imgsrc") or img_el.get("src") if img_el else None

            is_top = bool(article.select_one(".icon-feature-topad, .topad"))

            yield AdItem(
                id=str(ad_id),
                url=urljoin(base_url, article.get("data-href") or ""),
                title=title,
                description=description,
                location=location,
                price=price,
                is_top_ad=is_top,
                image_url=image_url,
            )
        except Exception as e:
            _logger.warning("Failed to parse one ad item: %s", e)
            continue


async def scrape_search(
    search: SearchConfig, config: Config
) -> list[AdItem]:
    """Scrape all ads for one search (with rate limiting and pagination)."""
    all_ads: list[AdItem] = []
    seen_urls: set[str] = set()

    proxy = get_proxy(config)
    if proxy:
        _logger.info("Using proxy: %s", proxy.split("@")[-1] if "@" in proxy else proxy)

    async with aiohttp.ClientSession() as session:
        # First page
        soup = await get_soup(session, search.url, timeout=config.request_timeout, proxy=proxy)
        async for ad in get_ad_items_from_page(soup, search.url):
            all_ads.append(ad)

        if search.recursive:
            pagination_urls = get_pagination_urls(soup, search.url)

            for page_url in pagination_urls:
                if page_url in seen_urls:
                    continue
                seen_urls.add(page_url)

                # Rate limiting - very important!
                delay = random.uniform(config.request_delay_min, config.request_delay_max)
                await asyncio.sleep(delay)

                try:
                    page_soup = await get_soup(session, page_url, timeout=config.request_timeout, proxy=proxy)
                    async for ad in get_ad_items_from_page(page_soup, page_url):
                        all_ads.append(ad)
                except ScraperError as e:
                    _logger.warning("Skipping page %s due to error: %s", page_url, e)
                    continue

    _logger.info("Scraped %d ads for '%s'", len(all_ads), search.name)
    return all_ads


async def get_filtered_search_result(
    search: SearchConfig, filter_cfg: FilterConfig, data_store: DataStore, config: Config
) -> list[AdItem]:
    """Return only new, non-excluded ads."""
    all_ads = await scrape_search(search, config)
    new_ads: list[AdItem] = []

    for ad in all_ads:
        if not data_store.add(ad):
            continue  # already seen

        if ad_item_is_excluded(ad, filter_cfg):
            continue

        new_ads.append(ad)

    return new_ads


def ad_item_is_excluded(ad: AdItem, f: FilterConfig) -> bool:
    if f.exclude_topads and ad.is_top_ad:
        return True

    price = parse_price(ad.price)
    if f.price_min is not None and price is not None and price < f.price_min:
        return True
    if f.price_max is not None and price is not None and price > f.price_max:
        return True

    for pattern in f.exclude_patterns:
        if pattern.search(ad.title) or pattern.search(ad.description):
            return True

    return False