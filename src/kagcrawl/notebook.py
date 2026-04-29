from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .schemas import NotebookRecord
from .utils.kaggle_cli import parse_ipynb, pull_notebook


def load_notebook_from_ipynb(ipynb_path: str | Path, owner: str | None = None, slug: str | None = None) -> NotebookRecord:
    path = Path(ipynb_path)
    parsed = parse_ipynb(path)
    notebook_slug = slug or path.stem
    notebook_owner = owner or "local"
    return NotebookRecord(
        owner=notebook_owner,
        slug=notebook_slug,
        url=f"file://{path}",
        title=notebook_slug,
        markdown_text=parsed["markdown_text"],
        selected_code_cells=parsed["selected_code_cells"],
        raw_path=str(path),
    )



def fetch_notebook(owner: str, slug: str, workdir: str | None = None) -> NotebookRecord:
    if workdir:
        ipynb_path = pull_notebook(owner, slug, workdir)
        return load_notebook_from_ipynb(ipynb_path, owner=owner, slug=slug)
    with TemporaryDirectory(prefix="kagcrawl_") as tmp:
        ipynb_path = pull_notebook(owner, slug, tmp)
        return load_notebook_from_ipynb(ipynb_path, owner=owner, slug=slug)
