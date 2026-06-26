"""ek-scraper: Production-ready Kleinanzeigen scraper with notifications."""

__version__ = "2.0.0"
__author__ = "Frederik Peter"
__license__ = "MIT"

from .cli import main
from .data_store import AdItem, DataStore
from .error import ScraperError

__all__ = [
    "main",
    "AdItem",
    "DataStore",
    "ScraperError",
    "__version__",
]
