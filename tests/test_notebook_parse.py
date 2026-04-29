import json
from pathlib import Path

from kagcrawl.utils.kaggle_cli import parse_ipynb


def test_parse_ipynb(tmp_path: Path):
    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title\n", "Some text"]},
            {"cell_type": "code", "source": ["print('hello')\n"]},
        ]
    }
    path = tmp_path / "demo.ipynb"
    path.write_text(json.dumps(nb))
    parsed = parse_ipynb(path)
    assert "Title" in parsed["markdown_text"]
    assert parsed["selected_code_cells"] == ["print('hello')\n"]
