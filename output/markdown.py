"""Per-patient markdown file generator."""

from __future__ import annotations

from pathlib import Path

from config.settings import settings


def save_patient_markdown(chart_no: str, markdown: str) -> Path:
    """Write a single patient's summary to an .md file."""
    out = Path(settings.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{chart_no}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def combine_markdowns(summaries: list[tuple[str, str]]) -> str:
    """Combine multiple (chart_no, markdown) pairs into one document."""
    parts: list[str] = []
    for chart_no, md in summaries:
        parts.append(md)
        parts.append("\n---\n")
    return "\n".join(parts)
