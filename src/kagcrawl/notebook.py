from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .schemas import NotebookRecord
from .utils.kaggle_cli import parse_ipynb, pull_notebook


def fetch_notebook(owner: str, slug: str, workdir: str | None = None) -> NotebookRecord:
    if workdir:
        ipynb_path = pull_notebook(owner, slug, workdir)
        parsed = parse_ipynb(ipynb_path)
        raw_path = str(ipynb_path)
    else:
        with TemporaryDirectory(prefix="kagcrawl_") as tmp:
            ipynb_path = pull_notebook(owner, slug, tmp)
            parsed = parse_ipynb(ipynb_path)
            raw_path = str(ipynb_path)
    return NotebookRecord(
        owner=owner,
        slug=slug,
        url=f"https://www.kaggle.com/code/{owner}/{slug}",
        title=slug,
        markdown_text=parsed["markdown_text"],
        selected_code_cells=parsed["selected_code_cells"],
        raw_path=raw_path,
    )
