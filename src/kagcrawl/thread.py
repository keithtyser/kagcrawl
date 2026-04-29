from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from .schemas import Comment, Link, ThreadRecord
from .utils.links import classify_link, parse_competition_slug, parse_discussion_id


USER_AGENT = "Mozilla/5.0 (compatible; kagcrawl/0.1)"


def _extract_upvotes(text: str) -> int | None:
    m = re.search(r"\b(\d+) votes?\b", text)
    return int(m.group(1)) if m else None


def fetch_thread(url: str) -> ThreadRecord:
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
    comments: list[Comment] = []
    # lightweight v0: preserve only obvious comment blocks from plain text later if needed
    return ThreadRecord(
        competition_slug=parse_competition_slug(url),
        kaggle_thread_id=parse_discussion_id(url),
        url=url,
        title=title,
        upvotes=_extract_upvotes(body_text),
        body_text=body_text,
        comments=comments,
        links=links,
    )
