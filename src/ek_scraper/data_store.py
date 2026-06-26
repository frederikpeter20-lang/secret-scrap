"""JSON-backed data store for tracking seen advertisements."""

from __future__ import annotations

import logging
import pathlib
from typing import Any

import pydantic

__all__ = ["DataStore", "AdItem"]

_logger = logging.getLogger(__name__)


class AdItem(pydantic.BaseModel):
    """Definition of an advertisement item."""

    id: str = pydantic.Field(description="Unique advertisement ID")
    url: str = pydantic.Field(description="Direct URL to advertisement")
    title: str = pydantic.Field(description="Advertisement title")
    description: str = pydantic.Field(description="Advertisement description")
    location: str = pydantic.Field(description="Item location")
    price: str = pydantic.Field(description="Price string (e.g. '450 €')")
    is_top_ad: bool = pydantic.Field(description="Whether this is a promoted top ad")
    image_url: str | None = pydantic.Field(
        default=None, description="URL to item image"
    )
    pruneable: bool = pydantic.Field(
        default=True, description="Internal: can be removed on prune", exclude=True
    )


class _DataStoreData(pydantic.BaseModel):
    """Internal data store format."""

    ad_items: dict[str, AdItem] = pydantic.Field(default_factory=dict)

    def __contains__(self, key: object) -> bool:
        """Check if ad_item ID exists."""
        return key in self.ad_items

    def add(self, ad_item: AdItem) -> bool:
        """Add an ad item. Returns True if new, False if already seen."""
        if ad_item.id in self.ad_items:
            _logger.debug("Ad item '%s' already in data store", ad_item.id)
            self.ad_items[ad_item.id].pruneable = False
            return False

        ad_item.pruneable = False
        self.ad_items[ad_item.id] = ad_item
        return True

    def prune(self) -> None:
        """Remove old ad items marked as pruneable."""
        pruneable_ids = [
            aid for aid, item in self.ad_items.items() if item.pruneable
        ]
        _logger.info("Pruning %d old items from data store", len(pruneable_ids))
        for aid in pruneable_ids:
            del self.ad_items[aid]

    def mark_as_non_pruneable(self, ad_item: AdItem) -> None:
        """Mark an item as non-pruneable."""
        if item := self.ad_items.get(ad_item.id):
            item.pruneable = False


class DataStore:
    """JSON-backed data store for tracking seen advertisements.

    Prevents duplicate notifications for the same items across multiple runs.
    """

    def __init__(self, path: pathlib.Path, prune_on_close: bool = True):
        """Initialize data store.

        Args:
            path: Path to JSON file for persistence
            prune_on_close: Whether to remove old items on close
        """
        self._path = path
        self._data = _DataStoreData()
        self._prune_on_close = prune_on_close

    def __enter__(self) -> DataStore:
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def open(self) -> None:
        """Load data from disk."""
        try:
            if self._path.exists() and self._path.stat().st_size > 0:
                self._data = _DataStoreData.model_validate_json(
                    self._path.read_text()
                )
        except pydantic.ValidationError:
            _logger.error(
                "Invalid data store schema. Please delete the file and start fresh."
            )
            raise
        except FileNotFoundError:
            _logger.info("Data store will be created at %s", self._path)

    def close(self) -> None:
        """Save data to disk."""
        if self._prune_on_close:
            self.prune()
        self._path.write_text(
            self._data.model_dump_json(by_alias=True, exclude_none=True)
        )

    def prune(self) -> None:
        """Remove old items."""
        self._data.prune()

    def add(self, ad_item: AdItem) -> bool:
        """Add an item to the store.

        Args:
            ad_item: Advertisement item to add

        Returns:
            True if item is new, False if already seen
        """
        return self._data.add(ad_item)

    def mark_as_non_pruneable(self, ad_item: AdItem) -> None:
        """Mark an item as non-pruneable (important items)."""
        self._data.mark_as_non_pruneable(ad_item)
