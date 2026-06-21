from __future__ import annotations

import logging
import pathlib
from typing import Any

import pydantic

__all__ = ["DataStore", "AdItem"]

_logger = logging.getLogger(__name__)


class AdItem(pydantic.BaseModel):
    """Definition of an Ad item"""

    id: str
    url: str
    title: str
    description: str
    location: str
    price: str
    is_top_ad: bool
    image_url: str | None = None
    pruneable: bool = pydantic.Field(default=True, exclude=True)


class _DataStoreData(pydantic.BaseModel):
    ad_items: dict[str, AdItem] = pydantic.Field(default_factory=dict)

    def __contains__(self, key: object) -> bool:
        return key in self.ad_items

    def add(self, ad_item: AdItem) -> bool:
        if ad_item.id in self.ad_items:
            _logger.debug("Ad item '%s' already in data store", ad_item.id)
            self.ad_items[ad_item.id].pruneable = False
            return False

        ad_item.pruneable = False
        self.ad_items[ad_item.id] = ad_item
        return True

    def prune(self) -> None:
        pruneable_ids = [aid for aid, item in self.ad_items.items() if item.pruneable]
        _logger.info("Pruning %d old items from data store", len(pruneable_ids))
        for aid in pruneable_ids:
            del self.ad_items[aid]

    def mark_as_non_pruneable(self, ad_item: AdItem) -> None:
        if item := self.ad_items.get(ad_item.id):
            item.pruneable = False


class DataStore:
    """JSON-backed data store for seen advertisements"""

    def __init__(self, path: pathlib.Path, prune_on_close: bool = True):
        self._path = path
        self._data = _DataStoreData()
        self._prune_on_close = prune_on_close

    def __enter__(self) -> DataStore:
        self.open()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def open(self) -> None:
        try:
            if self._path.exists() and self._path.stat().st_size > 0:
                self._data = _DataStoreData.model_validate_json(self._path.read_text())
        except pydantic.ValidationError:
            _logger.error("Invalid data store schema. Please delete the file and start fresh.")
            raise
        except FileNotFoundError:
            _logger.info("Data store will be created at %s", self._path)

    def close(self) -> None:
        if self._prune_on_close:
            self.prune()
        self._path.write_text(self._data.model_dump_json(by_alias=True, exclude_none=True))

    def prune(self) -> None:
        self._data.prune()

    def add(self, ad_item: AdItem) -> bool:
        return self._data.add(ad_item)

    def mark_as_non_pruneable(self, ad_item: AdItem) -> None:
        self._data.mark_as_non_pruneable(ad_item)