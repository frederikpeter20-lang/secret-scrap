class ScraperError(Exception):
    """Base class for all scraper-related errors."""
    pass


class UnexpectedHTMLResponse(ScraperError):
    """Raised when the server returns non-HTML content."""
    pass