from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from urllib.parse import urljoin

KAGGLE_ROOT = "https://www.kaggle.com"


class BrowserUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class BrowserPage:
    url: str
    snapshot: str
    title: str | None = None


def _browser_cmd() -> str:
    override = os.environ.get("KAGCRAWL_AGENT_BROWSER", "").strip()
    if override:
        return override
    cmd = shutil.which("agent-browser")
    if cmd:
        return cmd
    bundled = os.path.expanduser("~/.hermes/hermes-agent/node_modules/.bin/agent-browser")
    if os.path.exists(bundled):
        return bundled
    raise BrowserUnavailableError(
        "agent-browser not found. Install it or set KAGCRAWL_AGENT_BROWSER to its path."
    )


def _run_browser(*args: str, timeout: int = 90) -> dict:
    cmd = [_browser_cmd(), *args, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"agent-browser failed: {' '.join(cmd)}")
    data = json.loads(proc.stdout)
    if not data.get("success", False):
        raise RuntimeError(data.get("error") or f"agent-browser unsuccessful: {' '.join(cmd)}")
    return data["data"]


def fetch_page(url: str, *, waits_ms: tuple[int, ...] = (2500,), scrolls: int = 0) -> BrowserPage:
    session = f"kagcrawl-{uuid.uuid4().hex[:12]}"
    try:
        _run_browser("--session", session, "open", url, timeout=120)
        for wait_ms in waits_ms:
            _run_browser("--session", session, "wait", str(wait_ms), timeout=max(30, wait_ms // 1000 + 15))
        snapshots: list[str] = []
        first = _run_browser("--session", session, "snapshot", timeout=120)
        snapshots.append(first["snapshot"])
        for _ in range(scrolls):
            _run_browser("--session", session, "scroll", "down", "1200", timeout=60)
            _run_browser("--session", session, "wait", "1200", timeout=60)
            snap = _run_browser("--session", session, "snapshot", timeout=120)
            snapshots.append(snap["snapshot"])
        title_data = _run_browser("--session", session, "get", "title", timeout=60)
        title = title_data.get("title")
        deduped = []
        seen = set()
        for snap in snapshots:
            if snap not in seen:
                deduped.append(snap)
                seen.add(snap)
        return BrowserPage(url=url, snapshot="\n\n".join(deduped), title=title)
    finally:
        try:
            _run_browser("--session", session, "close", timeout=30)
        except Exception:
            pass


_URL_RE = re.compile(r'/url:\s+"?([^"\n]+)"?')


def extract_urls(snapshot: str, *, base_url: str = KAGGLE_ROOT) -> list[str]:
    urls: list[str] = []
    for raw in _URL_RE.findall(snapshot):
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
    lines: list[str] = []
    for raw in snapshot.splitlines():
        line = raw.strip()
        if not line or line.startswith("- /url:"):
            continue
        line = re.sub(r'^[\-\s]+', '', line)
        line = re.sub(r'\s*\[ref=e\d+\](?:\s*\[nth=\d+\])?', '', line)
        line = re.sub(r'\s*\[level=\d+\]', '', line)
        line = re.sub(r'^(link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation|main|separator|list|tablist|alert|document):\s*', '', line)
        quoted_match = re.match(r'^(?:link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation)\s+"([^"]+)"$', line)
        if quoted_match:
            line = quoted_match.group(1)
        else:
            line = re.sub(r'^(?:link|button|heading|paragraph|text|strong|listitem|tab|textbox|navigation)\s+"([^"]+)"\s*:?', r'\1', line)
        line = re.sub(r'\s+', ' ', line).strip()
        if line and line not in {':', 'img', 'more_horiz', 'expand_more', 'menu'}:
            lines.append(line)
    out: list[str] = []
    previous = None
    for line in lines:
        if line != previous:
            out.append(line)
        previous = line
    return "\n".join(out)
