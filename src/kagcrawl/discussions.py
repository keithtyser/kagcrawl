from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from .browser import BrowserUnavailableError, extract_urls, fetch_page
from .utils.links import classify_link, parse_discussion_id


USER_AGENT = "Mozilla/5.0 (compatible; kagcrawl/0.1)"


def _list_discussion_threads_http(competition: str, limit: int = 30, sort_by: str = "hotness") -> list[str]:
    url = f"https://www.kaggle.com/competitions/{competition}/discussion?sortBy={sort_by}"
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


def _extract_discussion_urls_from_snapshot(snapshot: str, competition: str) -> list[str]:
    pattern = re.compile(rf"^https://www\.kaggle\.com/competitions/{re.escape(competition)}/discussion/\d+$")
    urls: list[str] = []
    for url in extract_urls(snapshot):
        if not pattern.match(url):
            continue
        if parse_discussion_id(url) and url not in urls:
            urls.append(url)
    return urls


def list_discussion_threads(competition: str, limit: int = 30, sort_by: str = "hotness") -> list[str]:
    try:
        page = fetch_page(
            f"https://www.kaggle.com/competitions/{competition}/discussion?sortBy={sort_by}",
            waits_ms=(2500, 1500),
            scrolls=max(1, min(8, (limit // 8) + 1)),
        )
        urls = _extract_discussion_urls_from_snapshot(page.snapshot, competition)
        if urls:
            return urls[:limit]
    except BrowserUnavailableError:
        pass
    except Exception:
        # fall back to simple HTTP parsing when browser extraction fails
        pass
    return _list_discussion_threads_http(competition, limit=limit, sort_by=sort_by)
