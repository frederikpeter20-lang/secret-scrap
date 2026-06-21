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


def main():
    parser = argparse.ArgumentParser(description="ek-scraper improved v2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the scraper with a config file")
    run_parser.add_argument("config_file", type=pathlib.Path, help="Path to config JSON")
    run_parser.add_argument("--data-store", type=pathlib.Path, default=pathlib.Path.home() / "ek-scraper-v2.json")
    run_parser.add_argument("--no-notifications", action="store_false", dest="send_notifications", default=True)
    run_parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    configure_logging(getattr(args, "verbose", False))

    if args.command == "run":
        asyncio.run(run(**vars(args)))


if __name__ == "__main__":
    main()
