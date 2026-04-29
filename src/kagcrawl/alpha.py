from __future__ import annotations

from datetime import datetime, timezone

from .schemas import AlphaFinding, AlphaReport, ThreadRecord


def score_thread(thread: ThreadRecord) -> tuple[float, list[str]]:
    score = 0.1
    reasons: list[str] = []
    text = thread.body_text.lower()
    if "competition host" in text or "metric update" in text:
        score += 0.4
        reasons.append("host_or_metric_update")
    if any(k in text for k in ["score", "validation", "runtime", "memory", "grpo", "lora", "reverse engineered", "bug", "fix"]):
        score += 0.3
        reasons.append("technical_signal")
    notebook_links = [l.url for l in thread.links if l.target_type == "notebook"]
    if notebook_links:
        score += 0.2
        reasons.append("linked_notebook")
    if thread.upvotes:
        score += min(thread.upvotes / 100.0, 0.2)
        reasons.append("upvotes")
    return min(score, 0.99), reasons


def build_finding(thread: ThreadRecord) -> AlphaFinding:
    score, reasons = score_thread(thread)
    notebook_links = [l.url for l in thread.links if l.target_type == "notebook"]
    claims = []
    lowered = thread.body_text.splitlines()
    for line in lowered:
        line = line.strip()
        if len(line) > 40 and len(claims) < 5:
            claims.append(line[:300])
    return AlphaFinding(
        title=thread.title,
        url=thread.url,
        author=thread.author,
        author_role=thread.author_role,
        alpha_score=score,
        why_it_matters=", ".join(reasons) if reasons else "general discussion signal",
        claims=claims[:3],
        evidence_level="plausible",
        linked_notebooks=notebook_links,
        takeaway=claims[0] if claims else thread.title,
    )


def crawl_alpha_report(competition: str, threads: list[ThreadRecord]) -> AlphaReport:
    findings = sorted((build_finding(t) for t in threads), key=lambda x: x.alpha_score, reverse=True)
    host_updates = [f.url for f in findings if "host_or_metric_update" in f.why_it_matters]
    next_assets = []
    for f in findings:
        next_assets.extend(f.linked_notebooks)
    deduped_assets = list(dict.fromkeys(next_assets))
    return AlphaReport(
        competition=competition,
        generated_at=datetime.now(timezone.utc),
        threads_scanned=len(threads),
        findings=findings,
        host_updates=host_updates,
        contradictions=[],
        next_assets=deduped_assets,
    )
