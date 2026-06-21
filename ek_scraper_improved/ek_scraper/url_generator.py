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
    sort: str = "date",
) -> str:
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
        params["price"] = f"{price_min or ''}:{price_max or ''}"
    if sort == "date":
        params["sort"] = "DATE"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return url

if __name__ == "__main__":
    print(generate_search_url("fahrrad", location="berlin", price_min=50))
