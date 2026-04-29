from __future__ import annotations

from urllib.parse import urlparse


def classify_link(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    if "kaggle.com" not in host:
        return "external"
    if "/competitions/" in path and "/discussion/" in path:
        return "discussion"
    if path.startswith("/code/"):
        return "notebook"
    if path.startswith("/competitions/"):
        return "competition"
    return "unknown"


def parse_notebook_slug(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 3 and parts[0] == "code":
        return parts[1], parts[2]
    return None


def parse_discussion_id(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if "discussion" in parts:
        idx = parts.index("discussion")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def parse_competition_slug(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "competitions":
        return parts[1]
    return None
