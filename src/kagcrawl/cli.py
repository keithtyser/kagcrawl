from __future__ import annotations

import json
from typing import Optional

import typer

from .alpha import crawl_alpha_report
from .artifacts import load_notebooks_from_artifact_dir, load_threads_from_artifact_dir
from .capabilities import get_capability_report
from .exporters import report_to_json, report_to_txt, write_output
from .notebook import fetch_notebook, load_notebook_from_ipynb
from .pipeline import gather_notebooks, gather_threads
from .thread import fetch_thread, thread_from_snapshot

app = typer.Typer(help="Agent-first Kaggle discussion crawler")


@app.command()
def doctor(format: str = typer.Option("txt", "--format")) -> None:
    report = get_capability_report()
    payload = {
        "agent_browser": report.agent_browser,
        "kaggle_cli": report.kaggle_cli,
        "kaggle_dns": report.kaggle_dns,
        "github_dns": report.github_dns,
        "live_discussion_crawl": report.live_discussion_crawl,
        "live_notebook_pull": report.live_notebook_pull,
        "recommended_modes": report.recommended_modes(),
    }
    if format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return
    lines = [
        "Kagcrawl doctor",
        f"- agent-browser: {'yes' if report.agent_browser else 'no'}",
        f"- kaggle CLI: {'yes' if report.kaggle_cli else 'no'}",
        f"- Kaggle DNS/network: {'yes' if report.kaggle_dns else 'no'}",
        f"- GitHub DNS/network: {'yes' if report.github_dns else 'no'}",
        f"- live discussion crawl: {'yes' if report.live_discussion_crawl else 'no'}",
        f"- live notebook pull: {'yes' if report.live_notebook_pull else 'no'}",
        f"- recommended modes: {', '.join(report.recommended_modes())}",
    ]
    if report.offline_artifacts_only:
        lines.append("- next step: upload discussion snapshots/json and .ipynb files, then use --thread-artifact-dir and --notebook-artifact-dir")
    elif not report.live_discussion_crawl:
        lines.append("- next step: discussion crawling is blocked. Use uploaded thread snapshots/json via --thread-artifact-dir")
    elif not report.live_notebook_pull:
        lines.append("- next step: notebook pulling is blocked. Use uploaded .ipynb files via --notebook-artifact-dir")
    typer.echo("\n".join(lines))


@app.command()
def thread(
    url: Optional[str] = None,
    snapshot_file: Optional[str] = typer.Option(None, "--snapshot-file"),
    format: str = typer.Option("json", "--format"),
) -> None:
    if snapshot_file:
        from pathlib import Path
        record = thread_from_snapshot(Path(snapshot_file).read_text(), source_name=snapshot_file)
    elif url:
        record = fetch_thread(url)
    else:
        raise typer.BadParameter("Provide a URL or --snapshot-file")
    if format == "txt":
        typer.echo(record.body_text)
    else:
        typer.echo(json.dumps(record.model_dump(mode="json"), indent=2))


@app.command()
def notebook(
    ref: Optional[str] = None,
    ipynb_path: Optional[str] = typer.Option(None, "--ipynb-path"),
    format: str = typer.Option("json", "--format"),
) -> None:
    if ipynb_path:
        record = load_notebook_from_ipynb(ipynb_path)
    else:
        if not ref or "/" not in ref:
            raise typer.BadParameter("Notebook ref must be OWNER/SLUG unless using --ipynb-path")
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
    thread_artifact_dir: Optional[str] = typer.Option(None, "--thread-artifact-dir"),
    notebook_artifact_dir: Optional[str] = typer.Option(None, "--notebook-artifact-dir"),
    format: str = typer.Option("txt", "--format"),
    out: Optional[str] = typer.Option(None, "--out"),
) -> None:
    threads = gather_threads(competition, max_threads, thread_artifact_dir=thread_artifact_dir)
    resolved, resolution_errors = gather_notebooks(
        threads,
        resolve_notebooks=resolve_notebooks,
        notebook_artifact_dir=notebook_artifact_dir,
    )
    report = crawl_alpha_report(
        competition,
        threads,
        resolved_notebooks=resolved,
        notebook_resolution_errors=resolution_errors,
    )
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
    resolve_notebooks: bool = typer.Option(False, "--resolve-notebooks"),
    thread_artifact_dir: Optional[str] = typer.Option(None, "--thread-artifact-dir"),
    notebook_artifact_dir: Optional[str] = typer.Option(None, "--notebook-artifact-dir"),
    out: str = typer.Option(..., "--out"),
) -> None:
    threads = gather_threads(competition, max_threads, thread_artifact_dir=thread_artifact_dir)
    resolved, resolution_errors = gather_notebooks(
        threads,
        resolve_notebooks=resolve_notebooks,
        notebook_artifact_dir=notebook_artifact_dir,
    )
    report = crawl_alpha_report(
        competition,
        threads,
        resolved_notebooks=resolved,
        notebook_resolution_errors=resolution_errors,
    )
    content = report_to_txt(report)
    write_output(content, out)
    typer.echo(out)


if __name__ == "__main__":
    app()
