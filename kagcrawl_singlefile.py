from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

KAGGLE_ROOT = "https://www.kaggle.com"
USER_AGENT = "Mozilla/5.0 (compatible; kagcrawl-singlefile/0.1)"


def classify_link(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    if "kaggle.com" not in host:
        return "external"
    if "/competitions/" in path and "/discussion/" in path:
        return "discussion"
    if path.startswith("/code/"):
        return "notebook"
    if path.startswith("/competitions/"):
        return "competition"
    return "unknown"


def parse_notebook_slug(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 3 and parts[0] == "code":
        return parts[1], parts[2]
    return None


def parse_discussion_id(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if "discussion" in parts:
        idx = parts.index("discussion")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def parse_competition_slug(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "competitions":
        return parts[1]
    return None


@dataclass
class Link:
    url: str
    target_type: str = "unknown"


@dataclass
class ThreadRecord:
    competition_slug: str | None
    kaggle_thread_id: str | None
    url: str
    title: str
    author: str | None = None
    author_role: str = "unknown"
    created_at_text: str | None = None
    upvotes: int | None = None
    body_text: str = ""
    links: list[Link] = field(default_factory=list)


@dataclass
class NotebookRecord:
    owner: str
    slug: str
    url: str
    title: str
    markdown_text: str
    selected_code_cells: list[str]
    raw_path: str | None = None


@dataclass
class AlphaFinding:
    title: str
    url: str
    author: str | None
    author_role: str
    alpha_score: float
    why_it_matters: str
    claims: list[str]
    evidence_level: str
    linked_notebooks: list[str]
    takeaway: str


@dataclass
class AlphaReport:
    competition: str
    generated_at: str
    threads_scanned: int
    findings: list[AlphaFinding]
    host_updates: list[str]
    contradictions: list[str]
    next_assets: list[str]
    resolved_notebooks: list[NotebookRecord] = field(default_factory=list)
    notebook_resolution_errors: list[str] = field(default_factory=list)


def _browser_cmd() -> str:
    override = os.environ.get("KAGCRAWL_AGENT_BROWSER", "").strip()
    if override:
        return override
    cmd = shutil.which("agent-browser")
    if cmd:
        return cmd
    raise RuntimeError("agent-browser not found. Set KAGCRAWL_AGENT_BROWSER or install agent-browser.")


def _run_browser(*args: str, timeout: int = 120) -> dict:
    proc = subprocess.run([_browser_cmd(), *args, "--json"], capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "agent-browser failed")
    data = json.loads(proc.stdout)
    if not data.get("success"):
        raise RuntimeError(data.get("error") or "agent-browser unsuccessful")
    return data["data"]


def fetch_page(url: str, waits_ms: tuple[int, ...] = (2500,), scrolls: int = 0) -> tuple[str, str | None]:
    session = f"kagcrawl-{uuid.uuid4().hex[:12]}"
    try:
        _run_browser("--session", session, "open", url)
        for wait_ms in waits_ms:
            _run_browser("--session", session, "wait", str(wait_ms), timeout=max(30, wait_ms // 1000 + 15))
        snapshots = [_run_browser("--session", session, "snapshot")["snapshot"]]
        for _ in range(scrolls):
            _run_browser("--session", session, "scroll", "down", "1200")
            _run_browser("--session", session, "wait", "1200")
            snapshots.append(_run_browser("--session", session, "snapshot")["snapshot"])
        title = _run_browser("--session", session, "get", "title").get("title")
        deduped = []
        seen = set()
        for snap in snapshots:
            if snap not in seen:
                deduped.append(snap)
                seen.add(snap)
        return "\n\n".join(deduped), title
    finally:
        try:
            _run_browser("--session", session, "close", timeout=30)
        except Exception:
            pass


def extract_urls(snapshot: str, base_url: str = KAGGLE_ROOT) -> list[str]:
    urls = []
    for raw in re.findall(r'/url:\s+"?([^"\n]+)"?', snapshot):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("www."):
            normalized = f"https://{raw}"
        else:
            normalized = urljoin(base_url, raw)
        if normalized not in urls:
            urls.append(normalized)
    return urls


def snapshot_to_text(snapshot: str) -> str:
    lines = []
    for raw in snapshot.splitlines():
        line = raw.strip()
        if not line or line.startswith("- /url:"):
            continue
        line = re.sub(r'^[\-\s]+', '', line)
        line = re.sub(r'\s*\[ref=e\d+\](?:\s*\[nth=\d+\])?', '', line)
        line = re.sub(r'\s*\[level=\d+\]', '', line)
        line = re.sub(r'^(link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation|main|separator|list|tablist|alert|document):\s*', '', line)
        quoted = re.match(r'^(?:link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation)\s+"([^"]+)"$', line)
        if quoted:
            line = quoted.group(1)
        else:
            line = re.sub(r'^(?:link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation)\s+"([^"]+)"\s*:?', r'\1', line)
        line = re.sub(r'\s+', ' ', line).strip()
        if line and line not in {':', 'img', 'more_horiz', 'expand_more', 'menu'}:
            lines.append(line)
    out = []
    prev = None
    for line in lines:
        if line != prev:
            out.append(line)
        prev = line
    return "\n".join(out)


def list_discussion_threads(competition: str, limit: int = 20) -> list[str]:
    snapshot, _ = fetch_page(
        f"https://www.kaggle.com/competitions/{competition}/discussion?sortBy=hotness",
        waits_ms=(2500, 1500),
        scrolls=max(1, min(8, (limit // 8) + 1)),
    )
    pattern = re.compile(rf"^https://www\.kaggle\.com/competitions/{re.escape(competition)}/discussion/\d+$")
    urls = []
    for url in extract_urls(snapshot):
        if pattern.match(url) and url not in urls:
            urls.append(url)
    return urls[:limit]


def _thread_title_match(snapshot: str):
    candidates = list(re.finditer(r'heading "([^"]+)" \[ref=e\d+\] \[level=(\d+)\]', snapshot))
    for match in candidates:
        text, level = match.group(1), match.group(2)
        if level == "1":
            continue
        if re.match(r"^\d+ Comments?$", text):
            continue
        return match
    return candidates[-1] if candidates else None


def _thread_header_window(snapshot: str) -> str:
    match = _thread_title_match(snapshot)
    if not match:
        return snapshot[:1200]
    return snapshot[max(0, match.start() - 1200):match.start()]


def fetch_thread(url: str) -> ThreadRecord:
    snapshot, page_title = fetch_page(url, waits_ms=(2500, 1200), scrolls=1)
    title_match = _thread_title_match(snapshot)
    title = title_match.group(1) if title_match else (page_title or url)
    header = _thread_header_window(snapshot)
    author = None
    candidates = re.findall(r'link "([^"]+)" \[ref=e\d+\]:', header)
    for candidate in reversed(candidates):
        if "profile" in candidate.lower() or candidate in {"Learn more", "Sign In", "Register"}:
            continue
        author = candidate
        break
    created = None
    m = re.search(r"· (Posted .*?|Last comment .*?)(?:\n|$)", header)
    if m:
        created = m.group(1).strip()
    role = "host" if "Competition Host" in header else "unknown"
    body_region = snapshot[title_match.start():] if title_match else snapshot
    body_text = snapshot_to_text(body_region)
    links = [Link(url=u, target_type=classify_link(u)) for u in extract_urls(snapshot)]
    votes = None
    vm = re.search(r"\b(\d+) votes?\b", body_text)
    if vm:
        votes = int(vm.group(1))
    return ThreadRecord(
        competition_slug=parse_competition_slug(url),
        kaggle_thread_id=parse_discussion_id(url),
        url=url,
        title=title,
        author=author,
        author_role=role,
        created_at_text=created,
        upvotes=votes,
        body_text=body_text,
        links=links,
    )


def pull_notebook(owner: str, slug: str, workdir: str | Path) -> Path:
    outdir = Path(workdir)
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "pull", f"{owner}/{slug}", "-p", str(outdir), "--metadata"], check=True, capture_output=True, text=True)
    return outdir / f"{slug}.ipynb"


def fetch_notebook(owner: str, slug: str) -> NotebookRecord:
    with tempfile.TemporaryDirectory(prefix="kagcrawl_") as tmp:
        ipynb = pull_notebook(owner, slug, tmp)
        notebook = json.loads(Path(ipynb).read_text())
        markdown = []
        code = []
        for cell in notebook.get("cells", []):
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue
            if cell.get("cell_type") == "markdown":
                markdown.append(source)
            elif cell.get("cell_type") == "code":
                code.append(source)
        return NotebookRecord(
            owner=owner,
            slug=slug,
            url=f"https://www.kaggle.com/code/{owner}/{slug}",
            title=slug,
            markdown_text="\n\n".join(markdown).strip(),
            selected_code_cells=code,
            raw_path=str(ipynb),
        )


def resolve_linked_notebooks(threads: list[ThreadRecord]) -> tuple[list[NotebookRecord], list[str]]:
    resolved = []
    errors = []
    seen = set()
    for thread in threads:
        for link in thread.links:
            parsed = parse_notebook_slug(link.url)
            if not parsed or parsed in seen:
                continue
            seen.add(parsed)
            try:
                resolved.append(fetch_notebook(*parsed))
            except Exception as exc:
                errors.append(f"{parsed[0]}/{parsed[1]}: {exc}")
    return resolved, errors


def build_finding(thread: ThreadRecord) -> AlphaFinding:
    score = 0.1
    reasons = []
    text = thread.body_text.lower()
    if thread.author_role == "host" or "metric update" in text:
        score += 0.4
        reasons.append("host_or_metric_update")
    if any(k in text for k in ["score", "validation", "runtime", "memory", "grpo", "lora", "bug", "fix"]):
        score += 0.3
        reasons.append("technical_signal")
    notebook_links = [l.url for l in thread.links if l.target_type == "notebook"]
    if notebook_links:
        score += 0.2
        reasons.append("linked_notebook")
    if thread.upvotes:
        score += min(thread.upvotes / 100.0, 0.2)
        reasons.append("upvotes")
    claims = [line[:300] for line in thread.body_text.splitlines() if len(line.strip()) > 40][:3]
    return AlphaFinding(
        title=thread.title,
        url=thread.url,
        author=thread.author,
        author_role=thread.author_role,
        alpha_score=min(score, 0.99),
        why_it_matters=", ".join(reasons) if reasons else "general discussion signal",
        claims=claims,
        evidence_level="plausible",
        linked_notebooks=notebook_links,
        takeaway=claims[0] if claims else thread.title,
    )


def crawl_alpha(competition: str, max_threads: int = 10, resolve_notebooks_flag: bool = False) -> AlphaReport:
    urls = list_discussion_threads(competition, limit=max_threads)
    threads = [fetch_thread(url) for url in urls]
    notebooks, errors = (resolve_linked_notebooks(threads) if resolve_notebooks_flag else ([], []))
    findings = sorted([build_finding(t) for t in threads], key=lambda x: x.alpha_score, reverse=True)
    next_assets = []
    for f in findings:
        next_assets.extend(f.linked_notebooks)
    next_assets = list(dict.fromkeys(next_assets))
    return AlphaReport(
        competition=competition,
        generated_at=datetime.now(timezone.utc).isoformat(),
        threads_scanned=len(threads),
        findings=findings,
        host_updates=[f.url for f in findings if "host_or_metric_update" in f.why_it_matters],
        contradictions=[],
        next_assets=next_assets,
        resolved_notebooks=notebooks,
        notebook_resolution_errors=errors,
    )


def report_to_txt(report: AlphaReport) -> str:
    lines = [
        f"Competition: {report.competition}",
        f"Generated at: {report.generated_at}",
        f"Threads scanned: {report.threads_scanned}",
        "",
        "Top findings:",
    ]
    for idx, finding in enumerate(report.findings[:10], start=1):
        lines.extend([
            f"{idx}. {finding.title}",
            f"   URL: {finding.url}",
            f"   Score: {finding.alpha_score:.2f}",
            f"   Why: {finding.why_it_matters}",
            f"   Takeaway: {finding.takeaway}",
            "",
        ])
    if report.resolved_notebooks:
        lines.append("Resolved notebooks:")
        for notebook in report.resolved_notebooks:
            lines.append(f"- {notebook.owner}/{notebook.slug}")
            lines.append(f"  URL: {notebook.url}")
            if notebook.markdown_text:
                lines.append(f"  Markdown preview: {notebook.markdown_text[:500].replace(chr(10), ' ')}")
            lines.append("")
    if report.notebook_resolution_errors:
        lines.append("Notebook resolution errors:")
        lines.extend(f"- {e}" for e in report.notebook_resolution_errors)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-file kagcrawl for sandbox uploads")
    sub = parser.add_subparsers(dest="cmd", required=True)
    alpha = sub.add_parser("alpha")
    alpha.add_argument("competition")
    alpha.add_argument("--max-threads", type=int, default=10)
    alpha.add_argument("--resolve-notebooks", action="store_true")
    alpha.add_argument("--format", choices=["json", "txt"], default="txt")

    args = parser.parse_args()
    if args.cmd == "alpha":
        report = crawl_alpha(args.competition, max_threads=args.max_threads, resolve_notebooks_flag=args.resolve_notebooks)
        if args.format == "json":
            print(json.dumps(asdict(report), indent=2))
        else:
            print(report_to_txt(report), end="")


if __name__ == "__main__":
    main()
