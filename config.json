"""Search URL Generator for kleinanzeigen.de"""
from __future__ import annotations

import urllib.parse
from typing import Optional


def generate_search_url(
    keyword: str,
    location: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    category: Optional[str] = None,
    sort: str = "date",  # date, price_asc, price_desc, distance
) -> str:
    """
    Generate a kleinanzeigen.de search URL.

    Examples:
        generate_search_url("fahrrad", location="berlin", price_min=50, price_max=300)
        -> https://www.kleinanzeigen.de/s-berlin/fahrrad/k0l3331?price=50:300&sort=DATE

    Note: Location needs the correct slug or ID. For best results, use the URL from the website.
    """
    base = "https://www.kleinanzeigen.de/s-"

    # Build path
    if location:
        path = f"{location}/{keyword}/k0"
    else:
        path = f"{keyword}/k0"

    if category:
        path = f"{category}/{path}"

    url = base + path

    # Query params
    params = {}
    if price_min is not None or price_max is not None:
        min_p = price_min or ""
        max_p = price_max or ""
        params["price"] = f"{min_p}:{max_p}"

    sort_map = {
        "date": "DATE",
        "price_asc": "PRICE_ASC",
        "price_desc": "PRICE_DESC",
        "distance": "DISTANCE",
    }
    if sort in sort_map:
        params["sort"] = sort_map[sort]

    if params:
        url += "?" + urllib.parse.urlencode(params)

    return url


if __name__ == "__main__":
    print(generate_search_url("wohnung mieten", location="hamburg", price_min=800, price_max=1500))
    print(generate_search_url("fahrrad", price_min=100))
