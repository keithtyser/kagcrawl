from __future__ import annotations

import shutil
import socket
import os
from dataclasses import dataclass


@dataclass(slots=True)
class CapabilityReport:
    agent_browser: bool
    kaggle_cli: bool
    kaggle_dns: bool
    github_dns: bool

    @property
    def live_discussion_crawl(self) -> bool:
        return self.agent_browser and self.kaggle_dns

    @property
    def live_notebook_pull(self) -> bool:
        return self.kaggle_cli and self.kaggle_dns

    @property
    def offline_artifacts_only(self) -> bool:
        return not self.live_discussion_crawl and not self.live_notebook_pull

    def recommended_modes(self) -> list[str]:
        modes: list[str] = []
        if self.live_discussion_crawl:
            modes.append("live_discussions")
        if self.live_notebook_pull:
            modes.append("live_notebooks")
        if self.offline_artifacts_only:
            modes.append("offline_artifacts")
        elif not self.live_discussion_crawl or not self.live_notebook_pull:
            modes.append("hybrid_artifacts")
        return modes


def _has_command(name: str) -> bool:
    if name == "agent-browser":
        override = os.environ.get("KAGCRAWL_AGENT_BROWSER", "").strip()
        if override and os.path.exists(override):
            return True
    return shutil.which(name) is not None


def _dns_ok(hostname: str) -> bool:
    try:
        socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        return True
    except OSError:
        return False


def get_capability_report() -> CapabilityReport:
    return CapabilityReport(
        agent_browser=_has_command("agent-browser"),
        kaggle_cli=_has_command("kaggle"),
        kaggle_dns=_dns_ok("www.kaggle.com"),
        github_dns=_dns_ok("github.com"),
    )
