from __future__ import annotations

import json
import subprocess
from pathlib import Path


def pull_notebook(owner: str, slug: str, workdir: str | Path) -> Path:
    outdir = Path(workdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ref = f"{owner}/{slug}"
    cmd = ["kaggle", "kernels", "pull", ref, "-p", str(outdir), "--metadata"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return outdir / f"{slug}.ipynb"


def parse_ipynb(ipynb_path: str | Path) -> dict:
    path = Path(ipynb_path)
    notebook = json.loads(path.read_text())
    markdown_blocks: list[str] = []
    code_blocks: list[str] = []
    for cell in notebook.get("cells", []):
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        if cell.get("cell_type") == "markdown":
            markdown_blocks.append(source)
        elif cell.get("cell_type") == "code":
            code_blocks.append(source)
    return {
        "markdown_text": "\n\n".join(markdown_blocks).strip(),
        "selected_code_cells": code_blocks,
    }
