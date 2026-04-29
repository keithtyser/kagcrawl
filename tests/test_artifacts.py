import json
from pathlib import Path

from kagcrawl.artifacts import load_notebooks_from_artifact_dir, load_threads_from_artifact_dir


SNAPSHOT = '''
- main:
  - link "Michael D. Moffitt" [ref=e39]:
    - /url: /mmoffitt
  - text: · Posted 4 hours ago · Competition Host
  - heading "NeuroGolf Update for April 28th" [ref=e43] [level=3]
  - paragraph:
    - text: Thanks again to all teams for their helpful and detailed feedback.
  - link "Notebook" [ref=e50]:
    - /url: https://www.kaggle.com/code/mmoffitt/the-2026-neurogolf-metric-migration-manual
'''


def test_load_threads_from_artifact_dir(tmp_path: Path) -> None:
    (tmp_path / "thread1.snapshot").write_text(SNAPSHOT)
    records = load_threads_from_artifact_dir(tmp_path)
    assert len(records) == 1
    assert records[0].title == "NeuroGolf Update for April 28th"
    assert records[0].author == "Michael D. Moffitt"
    assert records[0].author_role == "host"
    assert any(link.target_type == "notebook" for link in records[0].links)


def test_load_notebooks_from_artifact_dir(tmp_path: Path) -> None:
    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Hello\n", "world"]},
            {"cell_type": "code", "source": ["print(123)\n"]},
        ]
    }
    (tmp_path / "sample.ipynb").write_text(json.dumps(nb))
    records = load_notebooks_from_artifact_dir(tmp_path)
    assert len(records) == 1
    assert records[0].owner == "local"
    assert records[0].slug == "sample"
    assert "Hello" in records[0].markdown_text
    assert records[0].selected_code_cells == ["print(123)\n"]
