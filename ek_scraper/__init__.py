"""ek-scraper: An improved Kleinanzeigen scraper with notifications."""

__version__ = "2.0.0"
__author__ = "Frederik Peter"

from .cli import main
from .data_store import AdItem, DataStore

__all__ = ["main", "AdItem", "DataStore", "__version__"]
