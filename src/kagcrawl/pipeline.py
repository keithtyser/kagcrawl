from __future__ import annotations

from .artifacts import load_notebooks_from_artifact_dir, load_threads_from_artifact_dir
from .capabilities import get_capability_report
from .discussions import list_discussion_threads
from .resolve import resolve_linked_notebooks
from .thread import fetch_thread


def gather_threads(competition: str, max_threads: int, thread_artifact_dir: str | None = None):
    if thread_artifact_dir:
        return load_threads_from_artifact_dir(thread_artifact_dir)
    capabilities = get_capability_report()
    if not capabilities.live_discussion_crawl:
        raise RuntimeError(
            "live discussion crawling unavailable. Run 'kagcrawl doctor' or provide --thread-artifact-dir with uploaded snapshots/json."
        )
    urls = list_discussion_threads(competition, limit=max_threads)
    return [fetch_thread(url) for url in urls]


def gather_notebooks(threads, resolve_notebooks: bool, notebook_artifact_dir: str | None = None):
    if notebook_artifact_dir:
        return load_notebooks_from_artifact_dir(notebook_artifact_dir), []
    if not resolve_notebooks:
        return [], []
    capabilities = get_capability_report()
    if not capabilities.live_notebook_pull:
        return [], [
            "live notebook pull unavailable. Run 'kagcrawl doctor' or provide --notebook-artifact-dir with uploaded .ipynb files."
        ]
    return resolve_linked_notebooks(threads)
