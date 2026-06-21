from __future__ import annotations

from typing import Any, Protocol, Sequence

class SendNotifications(Protocol):
    async def __call__(self, results: Sequence["Result"], config: Any) -> None: ...

class NotificationError(RuntimeError):
    pass
