import argparse
import asyncio
import logging
import pathlib
import sys
from typing import Any

from . import __version__
from .config import Config
from .data_store import DataStore
from .notifications import pushover, ntfy_sh, telegram
from .scraper import get_filtered_search_result
from .url_generator import generate_search_url

_logger = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def run(config_file: pathlib.Path, data_store_file: pathlib.Path, send_notifications: bool, **kwargs: Any):
    config = Config.model_validate_json(config_file.read_text())

    with DataStore(data_store_file, prune_on_close=True) as store:
        results = []
        for search in config.searches:
            new_ads = await get_filtered_search_result(search, config.filter, store, config)
            if new_ads:
                results.append(type("Result", (), {
                    "search_config": search,
                    "ad_items": new_ads,
                    "get_title": lambda s=search: s.name,
                    "get_message": lambda self: f"Found {len(new_ads)} new ads",
                    "get_url": lambda s=search: s.url,
                })())

    for r in results:
        _logger.info("%s: %d new ads", r.get_title(), len(r.ad_items))

    if not send_notifications or not results:
        return

    notif_config = config.notifications
    if notif_config.pushover:
        await pushover.send_notifications(results, notif_config.pushover)
    if notif_config.ntfy_sh:
        await ntfy_sh.send_notifications(results, notif_config.ntfy_sh)
    if notif_config.telegram:
        await telegram.send_notifications(results, notif_config.telegram)


def main():
    parser = argparse.ArgumentParser(description="ek-scraper improved v2 - Scraper for kleinanzeigen.de")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run scraper
    run_parser = subparsers.add_parser("run", help="Run the scraper with a config file")
    run_parser.add_argument("config_file", type=pathlib.Path, help="Path to config JSON")
    run_parser.add_argument("--data-store", type=pathlib.Path, default=pathlib.Path.home() / "ek-scraper-v2.json")
    run_parser.add_argument("--no-notifications", action="store_false", dest="send_notifications", default=True)
    run_parser.add_argument("-v", "--verbose", action="store_true")

    # Generate search URL
    gen_parser = subparsers.add_parser("generate-url", help="Generate a kleinanzeigen.de search URL")
    gen_parser.add_argument("--keyword", required=True, help="Search keyword (e.g. 'fahrrad')")
    gen_parser.add_argument("--location", help="Location slug (e.g. 'berlin' or 'hamburg-altona')")
    gen_parser.add_argument("--price-min", type=int, help="Minimum price")
    gen_parser.add_argument("--price-max", type=int, help="Maximum price")
    gen_parser.add_argument("--category", help="Category path (e.g. 'c203' for wohnung)")
    gen_parser.add_argument("--sort", default="date", choices=["date", "price_asc", "price_desc", "distance"])

    args = parser.parse_args()
    configure_logging(getattr(args, "verbose", False))

    if args.command == "run":
        asyncio.run(run(**vars(args)))
    elif args.command == "generate-url":
        url = generate_search_url(
            keyword=args.keyword,
            location=args.location,
            price_min=args.price_min,
            price_max=args.price_max,
            category=args.category,
            sort=args.sort,
        )
        print(url)
        print("\nTipp: Öffne die URL im Browser und kopiere sie in deine config.json für beste Ergebnisse.")


if __name__ == "__main__":
    main()
