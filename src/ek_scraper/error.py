"""Exception classes for the scraper."""

from __future__ import annotations


class ScraperError(Exception):
    """Base exception for all scraper-related errors."""

    pass


class UnexpectedHTMLResponse(ScraperError):
    """Raised when the server returns non-HTML content."""

    pass


class NotificationError(ScraperError):
    """Raised when notification sending fails."""

    pass
