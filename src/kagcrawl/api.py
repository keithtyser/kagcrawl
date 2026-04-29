from __future__ import annotations

import os
import secrets
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from .alpha import crawl_alpha_report
from .capabilities import get_capability_report
from .notebook import fetch_notebook, load_notebook_from_ipynb
from .pipeline import gather_notebooks, gather_threads
from .thread import fetch_thread, thread_from_snapshot


class AlphaRequest(BaseModel):
    competition: str
    max_threads: int = Field(default=20, ge=1, le=100)
    resolve_notebooks: bool = False
    thread_artifact_dir: Optional[str] = None
    notebook_artifact_dir: Optional[str] = None


class ThreadRequest(BaseModel):
    url: Optional[str] = None
    snapshot_file: Optional[str] = None


class NotebookRequest(BaseModel):
    ref: Optional[str] = None
    ipynb_path: Optional[str] = None


app = FastAPI(title="kagcrawl API", version="0.1.0")


def _expected_api_key() -> str:
    api_key = os.environ.get("KAGCRAWL_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server missing KAGCRAWL_API_KEY",
        )
    return api_key


def require_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> None:
    expected = _expected_api_key()
    provided = (x_api_key or "").strip()
    if not provided and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided = token.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/doctor", dependencies=[Depends(require_api_key)])
def doctor() -> dict:
    report = get_capability_report()
    return {
        "agent_browser": report.agent_browser,
        "kaggle_cli": report.kaggle_cli,
        "kaggle_dns": report.kaggle_dns,
        "github_dns": report.github_dns,
        "live_discussion_crawl": report.live_discussion_crawl,
        "live_notebook_pull": report.live_notebook_pull,
        "recommended_modes": report.recommended_modes(),
    }


@app.post("/alpha", dependencies=[Depends(require_api_key)])
def alpha(req: AlphaRequest) -> dict:
    try:
        threads = gather_threads(req.competition, req.max_threads, thread_artifact_dir=req.thread_artifact_dir)
        resolved, resolution_errors = gather_notebooks(
            threads,
            resolve_notebooks=req.resolve_notebooks,
            notebook_artifact_dir=req.notebook_artifact_dir,
        )
        report = crawl_alpha_report(
            req.competition,
            threads,
            resolved_notebooks=resolved,
            notebook_resolution_errors=resolution_errors,
        )
        return report.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/thread", dependencies=[Depends(require_api_key)])
def thread(req: ThreadRequest) -> dict:
    try:
        if req.snapshot_file:
            from pathlib import Path
            record = thread_from_snapshot(Path(req.snapshot_file).read_text(), source_name=req.snapshot_file)
        elif req.url:
            record = fetch_thread(req.url)
        else:
            raise ValueError("Provide url or snapshot_file")
        return record.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/notebook", dependencies=[Depends(require_api_key)])
def notebook(req: NotebookRequest) -> dict:
    try:
        if req.ipynb_path:
            record = load_notebook_from_ipynb(req.ipynb_path)
        elif req.ref and "/" in req.ref:
            owner, slug = req.ref.split("/", 1)
            record = fetch_notebook(owner, slug)
        else:
            raise ValueError("Provide ref OWNER/SLUG or ipynb_path")
        return record.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
