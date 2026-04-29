from __future__ import annotations

import json
from typing import Optional

import typer

from .alpha import crawl_alpha_report
from .discussions import list_discussion_threads
from .exporters import report_to_json, report_to_txt, write_output
from .notebook import fetch_notebook
from .thread import fetch_thread
from .utils.links import parse_notebook_slug

app = typer.Typer(help="Agent-first Kaggle discussion crawler")


@app.command()
def thread(url: str, format: str = typer.Option("json", "--format")) -> None:
    record = fetch_thread(url)
    if format == "txt":
        typer.echo(record.body_text)
    else:
        typer.echo(json.dumps(record.model_dump(mode="json"), indent=2))


@app.command()
def notebook(ref: str, format: str = typer.Option("json", "--format")) -> None:
    if "/" not in ref:
        raise typer.BadParameter("Notebook ref must be OWNER/SLUG")
    owner, slug = ref.split("/", 1)
    record = fetch_notebook(owner, slug)
    if format == "txt":
        typer.echo(record.markdown_text)
    else:
        typer.echo(json.dumps(record.model_dump(mode="json"), indent=2))


@app.command()
def alpha(
    competition: str,
    max_threads: int = typer.Option(20, "--max-threads"),
    resolve_notebooks: bool = typer.Option(False, "--resolve-notebooks"),
    format: str = typer.Option("txt", "--format"),
    out: Optional[str] = typer.Option(None, "--out"),
) -> None:
    urls = list_discussion_threads(competition, limit=max_threads)
    threads = [fetch_thread(url) for url in urls]
    report = crawl_alpha_report(competition, threads)
    if resolve_notebooks:
        # v0: just preserve linked notebook urls in next_assets; resolution can be manual or follow-up
        pass
    content = report_to_txt(report) if format == "txt" else report_to_json(report)
    if out:
        write_output(content, out)
        typer.echo(out)
    else:
        typer.echo(content)


@app.command()
def context(
    competition: str,
    max_threads: int = typer.Option(20, "--max-threads"),
    out: str = typer.Option(..., "--out"),
) -> None:
    urls = list_discussion_threads(competition, limit=max_threads)
    threads = [fetch_thread(url) for url in urls]
    report = crawl_alpha_report(competition, threads)
    content = report_to_txt(report)
    write_output(content, out)
    typer.echo(out)


if __name__ == "__main__":
    app()
