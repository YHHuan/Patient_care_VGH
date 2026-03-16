"""JSON checkpoint cache — one file per patient per round."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config.settings import settings


def _cache_dir() -> Path:
    p = Path(settings.cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_key(chart_no: str, round_num: int) -> str:
    return f"{chart_no}_round{round_num}"


def save_cache(chart_no: str, round_num: int, data: dict[str, Any]) -> Path:
    """Save a round's crawled data to JSON."""
    path = _cache_dir() / f"{cache_key(chart_no, round_num)}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return path


def load_cache(chart_no: str, round_num: int) -> dict[str, Any] | None:
    """Load cached data for a round, or None if not found."""
    path = _cache_dir() / f"{cache_key(chart_no, round_num)}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_rounds(chart_no: str) -> dict[str, Any]:
    """Merge all cached rounds for a patient into one dict."""
    merged: dict[str, Any] = {}
    for i in range(1, 10):
        data = load_cache(chart_no, i)
        if data is None:
            break
        merged.update(data)
    return merged


def list_cached_patients() -> list[str]:
    """List chart numbers that have any cached data."""
    seen: set[str] = set()
    cache = _cache_dir()
    if not cache.exists():
        return []
    for f in cache.iterdir():
        if f.suffix == ".json":
            # filename: 12345678_round1.json
            parts = f.stem.split("_round")
            if parts:
                seen.add(parts[0])
    return sorted(seen)


def save_summary(chart_no: str, markdown: str) -> Path:
    """Save final AI summary."""
    path = _cache_dir() / f"{chart_no}_summary.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path
