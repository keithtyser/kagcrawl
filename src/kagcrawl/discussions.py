from __future__ import annotations

from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from .utils.links import classify_link


USER_AGENT = "Mozilla/5.0 (compatible; kagcrawl/0.1)"


def list_discussion_threads(competition: str, limit: int = 30, sort_by: str = "hotness") -> list[str]:
    params = urlencode({"sortBy": sort_by})
    url = f"https://www.kaggle.com/competitions/{competition}/discussion?{params}"
    resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    seen: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = f"https://www.kaggle.com{href}"
        if classify_link(href) == "discussion" and href not in seen:
            seen.append(href)
        if len(seen) >= limit:
            break
    return seen
