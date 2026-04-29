from __future__ import annotations

import json
from pathlib import Path

from .schemas import AlphaReport


def report_to_json(report: AlphaReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2)


def report_to_txt(report: AlphaReport) -> str:
    lines = [
        f"Competition: {report.competition}",
        f"Generated at: {report.generated_at.isoformat()}",
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
            lines.extend([
                f"- {notebook.owner}/{notebook.slug}",
                f"  URL: {notebook.url}",
                f"  Title: {notebook.title}",
            ])
            markdown = notebook.markdown_text.strip()
            if markdown:
                preview = markdown[:500].replace("\n", " ")
                lines.append(f"  Markdown preview: {preview}")
            if notebook.selected_code_cells:
                lines.append(f"  Code cells captured: {len(notebook.selected_code_cells)}")
            lines.append("")
    if report.notebook_resolution_errors:
        lines.append("Notebook resolution errors:")
        for err in report.notebook_resolution_errors:
            lines.append(f"- {err}")
        lines.append("")
    if report.next_assets:
        lines.append("Linked notebooks / next assets:")
        for asset in report.next_assets:
            lines.append(f"- {asset}")
    return "\n".join(lines).strip() + "\n"


def write_output(content: str, out_path: str | Path) -> None:
    Path(out_path).write_text(content)
