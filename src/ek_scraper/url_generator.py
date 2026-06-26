"""URL generator for kleinanzeigen.de searches."""

from __future__ import annotations

import urllib.parse
from typing import Optional


def generate_search_url(
    keyword: str,
    location: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    category: Optional[str] = None,
    sort: str = "date",
) -> str:
    """Generate a search URL for kleinanzeigen.de.

    Args:
        keyword: Search keyword (e.g. "fahrrad", "wohnung")
        location: Optional location filter (e.g. "berlin", "hamburg")
        price_min: Optional minimum price in EUR
        price_max: Optional maximum price in EUR
        category: Optional category code
        sort: Sort order ("date", "price_asc", "price_desc")

    Returns:
        Complete search URL string

    Example:
        >>> generate_search_url("fahrrad", location="berlin", price_max=500)
        'https://www.kleinanzeigen.de/s-fahrrad/berlin/k0?price=:500&sort=DATE'
    """
    base = "https://www.kleinanzeigen.de/s-"

    if location:
        path = f"{location}/{keyword}/k0"
    else:
        path = f"{keyword}/k0"

    if category:
        path = f"{category}/{path}"

    url = base + path
    params = {}

    if price_min is not None or price_max is not None:
        price_part = f"{price_min or ''}:{price_max or ''}"
        params["price"] = price_part

    if sort == "date":
        params["sort"] = "DATE"
    elif sort == "price_asc":
        params["sort"] = "PRICE_ASC"
    elif sort == "price_desc":
        params["sort"] = "PRICE_DESC"

    if params:
        url += "?" + urllib.parse.urlencode(params)

    return url


if __name__ == "__main__":
    # Example usage
    print(generate_search_url("fahrrad", location="berlin", price_max=500))
    print(generate_search_url("wohnung", location="hamburg", price_min=800, price_max=1200))
