from __future__ import annotations

from .notebook import fetch_notebook
from .schemas import NotebookRecord, ThreadRecord
from .utils.links import parse_notebook_slug


def resolve_linked_notebooks(threads: list[ThreadRecord]) -> tuple[list[NotebookRecord], list[str]]:
    resolved: list[NotebookRecord] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for thread in threads:
        for link in thread.links:
            parsed = parse_notebook_slug(link.url)
            if not parsed:
                continue
            key = (parsed[0], parsed[1])
            if key in seen:
                continue
            seen.add(key)
            try:
                resolved.append(fetch_notebook(*key))
            except Exception as exc:
                errors.append(f"{key[0]}/{key[1]}: {exc}")
    return resolved, errors
