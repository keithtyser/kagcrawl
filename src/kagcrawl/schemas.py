from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AuthorRole = Literal["host", "competitor", "unknown"]
EvidenceLevel = Literal["confirmed", "plausible", "disputed"]


class Link(BaseModel):
    url: str
    target_type: Literal["discussion", "notebook", "competition", "external", "unknown"] = "unknown"


class Comment(BaseModel):
    author: str | None = None
    author_role: AuthorRole = "unknown"
    created_at_text: str | None = None
    body_text: str


class ThreadRecord(BaseModel):
    competition_slug: str | None = None
    kaggle_thread_id: str | None = None
    url: str
    title: str
    author: str | None = None
    author_role: AuthorRole = "unknown"
    created_at_text: str | None = None
    upvotes: int | None = None
    comment_count: int | None = None
    body_text: str
    comments: list[Comment] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)


class NotebookRecord(BaseModel):
    owner: str
    slug: str
    url: str
    title: str
    markdown_text: str
    selected_code_cells: list[str] = Field(default_factory=list)
    raw_path: str | None = None


class AlphaFinding(BaseModel):
    title: str
    url: str
    author: str | None = None
    author_role: AuthorRole = "unknown"
    alpha_score: float
    why_it_matters: str
    claims: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = "plausible"
    linked_notebooks: list[str] = Field(default_factory=list)
    takeaway: str


class AlphaReport(BaseModel):
    competition: str
    generated_at: datetime
    threads_scanned: int
    findings: list[AlphaFinding] = Field(default_factory=list)
    host_updates: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    next_assets: list[str] = Field(default_factory=list)
    resolved_notebooks: list[NotebookRecord] = Field(default_factory=list)
    notebook_resolution_errors: list[str] = Field(default_factory=list)
