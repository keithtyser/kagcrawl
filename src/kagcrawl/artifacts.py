from __future__ import annotations

import json
from pathlib import Path

from .browser import snapshot_to_text
from .notebook import load_notebook_from_ipynb
from .schemas import NotebookRecord, ThreadRecord
from .thread import thread_from_snapshot


def load_threads_from_artifact_dir(path: str | Path) -> list[ThreadRecord]:
    base = Path(path)
    if not base.exists():
        raise FileNotFoundError(f"thread artifact dir not found: {base}")
    records: list[ThreadRecord] = []
    for artifact in sorted(base.iterdir()):
        if artifact.suffix == ".json":
            payload = json.loads(artifact.read_text())
            records.append(ThreadRecord.model_validate(payload))
        elif artifact.suffix in {".txt", ".snapshot"}:
            records.append(thread_from_snapshot(artifact.read_text(), source_name=artifact.stem))
    return records


def load_notebooks_from_artifact_dir(path: str | Path) -> list[NotebookRecord]:
    base = Path(path)
    if not base.exists():
        raise FileNotFoundError(f"notebook artifact dir not found: {base}")
    records: list[NotebookRecord] = []
    for artifact in sorted(base.iterdir()):
        if artifact.suffix == ".ipynb":
            records.append(load_notebook_from_ipynb(artifact))
        elif artifact.suffix == ".json":
            payload = json.loads(artifact.read_text())
            if {"owner", "slug", "markdown_text"}.issubset(payload.keys()):
                records.append(NotebookRecord.model_validate(payload))
    return records


def snapshot_preview(path: str | Path) -> str:
    return snapshot_to_text(Path(path).read_text())
