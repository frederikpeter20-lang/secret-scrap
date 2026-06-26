"""Command-line interface for ek-scraper."""

from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import sys
from typing import Any

from . import __version__
from .config import Config
from .data_store import DataStore
from .scraper import get_filtered_search_result
from .url_generator import generate_search_url

_logger = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    """Configure logging to console."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def run(
    config_file: pathlib.Path,
    data_store: pathlib.Path,
    send_notifications: bool = True,
    **kwargs: Any,
) -> None:
    """Run the scraper."""
    _logger.info("Loading configuration from %s", config_file)
    config = Config.model_validate_json(config_file.read_text())

    with DataStore(data_store, prune_on_close=True) as store:
        results = []
        for search in config.searches:
            _logger.info("Processing search: %s", search.name)
            new_ads = await get_filtered_search_result(
                search, config.filter, store, config
            )
            if new_ads:
                results.append(
                    type(
                        "Result",
                        (),
                        {
                            "search_config": search,
                            "ad_items": new_ads,
                            "get_title": lambda s=search: s.name,
                            "get_message": lambda self: f"Found {len(new_ads)} new ads",
                            "get_url": lambda s=search: s.url,
                        },
                    )()
                )

    for r in results:
        _logger.info("%s: %d new ads", r.get_title(), len(r.ad_items))

    if not send_notifications or not results:
        return

    _logger.info("Sending notifications for %d searches", len(results))
    # TODO: Implement notification sending


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ek-scraper - Scraper for kleinanzeigen.de",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run scraper with config
  ek-scraper run config.json

  # Run with custom data store location
  ek-scraper run config.json --data-store /tmp/ek-data.json

  # Generate search URL
  ek-scraper generate-url --keyword "fahrrad" --location "berlin" --price-max 500
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ek-scraper {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the scraper")
    run_parser.add_argument(
        "config_file",
        type=pathlib.Path,
        nargs="?",
        default=pathlib.Path("config.json"),
        help="Path to config JSON file (default: config.json)",
    )
    run_parser.add_argument(
        "--data-store",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".ek-scraper/data.json",
        help="Path to data store file (default: ~/.ek-scraper/data.json)",
    )
    run_parser.add_argument(
        "--no-notifications",
        action="store_false",
        dest="send_notifications",
        default=True,
        help="Disable sending notifications",
    )
    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Generate URL command
    gen_parser = subparsers.add_parser(
        "generate-url", help="Generate kleinanzeigen search URL"
    )
    gen_parser.add_argument(
        "--keyword",
        required=True,
        help="Search keyword (e.g. 'fahrrad', 'wohnung')",
    )
    gen_parser.add_argument(
        "--location", help="Location filter (e.g. 'berlin', 'hamburg')"
    )
    gen_parser.add_argument(
        "--price-min", type=int, help="Minimum price in EUR"
    )
    gen_parser.add_argument(
        "--price-max", type=int, help="Maximum price in EUR"
    )
    gen_parser.add_argument("--category", help="Category code")
    gen_parser.add_argument(
        "--sort",
        default="date",
        choices=["date", "price_asc", "price_desc"],
        help="Sort order",
    )

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


if __name__ == "__main__":
    main()
