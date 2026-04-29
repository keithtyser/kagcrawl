from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from .browser import BrowserUnavailableError, extract_urls, fetch_page, snapshot_to_text
from .schemas import Comment, Link, ThreadRecord
from .utils.links import classify_link, parse_competition_slug, parse_discussion_id


USER_AGENT = "Mozilla/5.0 (compatible; kagcrawl/0.1)"


def _extract_upvotes(text: str) -> int | None:
    m = re.search(r"\b(\d+) votes?\b", text)
    return int(m.group(1)) if m else None


def _thread_title_match(snapshot: str) -> re.Match[str] | None:
    candidates = list(re.finditer(r'heading "([^"]+)" \[ref=e\d+\] \[level=(\d+)\]', snapshot))
    for match in candidates:
        text, level = match.group(1), match.group(2)
        if level == "1":
            continue
        if re.match(r"^\d+ Comments?$", text):
            continue
        return match
    return candidates[-1] if candidates else None


def _thread_header_window(snapshot: str) -> str:
    title_match = _thread_title_match(snapshot)
    if not title_match:
        return snapshot[:1200]
    start = max(0, title_match.start() - 1200)
    return snapshot[start:title_match.start()]


def _extract_author_role(snapshot: str) -> str:
    if "Competition Host" in _thread_header_window(snapshot):
        return "host"
    return "unknown"


def _extract_created_at(snapshot: str) -> str | None:
    m = re.search(r"· (Posted .*?|Last comment .*?)(?:\n|$)", _thread_header_window(snapshot))
    return m.group(1).strip() if m else None


def _extract_thread_title(snapshot: str, fallback_title: str) -> str:
    match = _thread_title_match(snapshot)
    if match:
        return match.group(1)
    cleaned = fallback_title.replace(" | Kaggle", "").strip()
    return cleaned or fallback_title


def _extract_author(snapshot: str) -> str | None:
    window = _thread_header_window(snapshot)
    candidates = re.findall(r'link "([^"]+)" \[ref=e\d+\]:', window)
    for candidate in reversed(candidates):
        if "profile" in candidate.lower():
            continue
        if candidate in {"Learn more", "Sign In", "Register"}:
            continue
        return candidate
    return None


def _fetch_thread_http(url: str) -> ThreadRecord:
    headers = {"User-Agent": USER_AGENT}
    resp = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    body_text = soup.body.get_text("\n", strip=True) if soup.body else resp.text
    links: list[Link] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = f"https://www.kaggle.com{href}"
        links.append(Link(url=href, target_type=classify_link(href)))
    return ThreadRecord(
        competition_slug=parse_competition_slug(url),
        kaggle_thread_id=parse_discussion_id(url),
        url=url,
        title=title,
        upvotes=_extract_upvotes(body_text),
        body_text=body_text,
        comments=[],
        links=links,
    )


def _extract_body_text(snapshot: str) -> str:
    match = _thread_title_match(snapshot)
    if match:
        return snapshot_to_text(snapshot[match.start():])
    return snapshot_to_text(snapshot)


def fetch_thread(url: str) -> ThreadRecord:
    try:
        page = fetch_page(url, waits_ms=(2500, 1200), scrolls=1)
        links = [Link(url=link, target_type=classify_link(link)) for link in extract_urls(page.snapshot)]
        body_text = _extract_body_text(page.snapshot)
        return ThreadRecord(
            competition_slug=parse_competition_slug(url),
            kaggle_thread_id=parse_discussion_id(url),
            url=url,
            title=_extract_thread_title(page.snapshot, page.title or url),
            author=_extract_author(page.snapshot),
            author_role=_extract_author_role(page.snapshot),
            created_at_text=_extract_created_at(page.snapshot),
            upvotes=_extract_upvotes(body_text),
            body_text=body_text,
            comments=[],
            links=links,
        )
    except BrowserUnavailableError:
        return _fetch_thread_http(url)
    except Exception:
        return _fetch_thread_http(url)
