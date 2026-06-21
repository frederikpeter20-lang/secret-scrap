from __future__ import annotations

from typing import Any, Protocol, Sequence

if TYPE_CHECKING:
    from ..scraper import Result

class SendNotifications(Protocol):
    async def __call__(self, results: Sequence["Result"], config: Any) -> None: ...

class NotificationError(RuntimeError):
    pass

# Re-export
from . import pushover, ntfy_sh, telegram  # noqa: F401