from kagcrawl.schemas import Link, ThreadRecord
from kagcrawl.resolve import resolve_linked_notebooks


def test_resolve_linked_notebooks_dedupes_and_collects_errors(monkeypatch) -> None:
    calls = []

    class DummyNotebook:
        def __init__(self, owner: str, slug: str) -> None:
            self.owner = owner
            self.slug = slug
            self.url = f"https://www.kaggle.com/code/{owner}/{slug}"
            self.title = slug
            self.markdown_text = "summary"
            self.selected_code_cells = []
            self.raw_path = None

    def fake_fetch(owner: str, slug: str):
        calls.append((owner, slug))
        if slug == "broken":
            raise RuntimeError("pull failed")
        return DummyNotebook(owner, slug)

    monkeypatch.setattr("kagcrawl.resolve.fetch_notebook", fake_fetch)

    threads = [
        ThreadRecord(
            url="https://www.kaggle.com/competitions/x/discussion/1",
            title="t1",
            body_text="x",
            links=[
                Link(url="https://www.kaggle.com/code/a/good", target_type="notebook"),
                Link(url="https://www.kaggle.com/code/a/good", target_type="notebook"),
                Link(url="https://www.kaggle.com/code/b/broken", target_type="notebook"),
            ],
        )
    ]

    resolved, errors = resolve_linked_notebooks(threads)
    assert [(n.owner, n.slug) for n in resolved] == [("a", "good")]
    assert errors == ["b/broken: pull failed"]
    assert calls == [("a", "good"), ("b", "broken")]
