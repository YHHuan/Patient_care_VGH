"""Core crawl → AI analysis → re-crawl → summary loop."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import pandas as pd

from ai.client import AIClient
from ai.schema import AdditionalRequest
from cache.manager import load_all_rounds, load_cache, save_cache, save_summary
from config.settings import settings
from scraper.fetchers import (
    fetch_admin_id,
    fetch_bw_bl,
    fetch_drainage,
    fetch_drugs,
    fetch_lab_report,
    fetch_lab_value,
    fetch_last_admission,
    fetch_op,
    fetch_progress_notes,
    fetch_recent_reports,
    fetch_tpr,
)
from scraper.session import VGHSession

logger = logging.getLogger(__name__)


def _df_to_text(df: pd.DataFrame | None, label: str = "") -> str:
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return ""
    prefix = f"### {label}\n" if label else ""
    return prefix + df.to_string(index=False) + "\n"


def _dict_to_text(d: dict, label: str = "") -> str:
    if not d:
        return ""
    prefix = f"### {label}\n" if label else ""
    lines = [f"- {k}: {v}" for k, v in d.items()]
    return prefix + "\n".join(lines) + "\n"


class Orchestrator:
    """Runs the full pipeline for one or many patients."""

    def __init__(self, session: VGHSession) -> None:
        self.session = session
        self.ai = AIClient()

    async def process_patient(
        self,
        hist_no: str,
        *,
        from_cache: bool = False,
        on_progress: Any = None,  # callback(str)
    ) -> str:
        """Full pipeline for a single patient. Returns markdown summary."""

        def _log(msg: str) -> None:
            logger.info("[%s] %s", hist_no, msg)
            if on_progress:
                on_progress(f"[{hist_no}] {msg}")

        # ── Round 1: baseline crawl ─────────────────────────────
        if from_cache:
            round1 = load_cache(hist_no, 1)
            if round1 is None:
                raise ValueError(f"No cached data for {hist_no}")
            _log("Loaded round 1 from cache")
        else:
            _log("Round 1: baseline crawl")
            round1 = await self._crawl_baseline(hist_no)
            save_cache(hist_no, 1, round1)
            _log("Round 1 complete, cached")

        # ── AI analysis pass ────────────────────────────────────
        all_data = dict(round1)
        data_text = self._format_patient_data(all_data)
        _log("AI analysis pass...")
        analysis = await self.ai.analyze(data_text)
        _log(
            f"AI confidence: {analysis.confidence:.0%}, "
            f"additional requests: {len(analysis.additional_requests)}"
        )

        # ── Rounds 2+: targeted re-crawl ────────────────────────
        round_num = 2
        while (
            analysis.additional_requests
            and analysis.confidence < 0.85
            and round_num <= settings.max_rounds
        ):
            _log(f"Round {round_num}: targeted crawl ({len(analysis.additional_requests)} items)")
            admin_id = round1.get("_admin_id", "")
            extra = await self._crawl_additional(
                hist_no, admin_id, analysis.additional_requests
            )
            save_cache(hist_no, round_num, extra)
            all_data.update(extra)

            # Re-analyze with more data
            data_text = self._format_patient_data(all_data)
            _log(f"AI re-analysis pass (round {round_num})...")
            analysis = await self.ai.analyze(data_text)
            _log(f"AI confidence now: {analysis.confidence:.0%}")
            round_num += 1

        # ── Final summary pass ──────────────────────────────────
        data_text = self._format_patient_data(all_data)
        _log("Generating final summary...")
        summary = await self.ai.summarize(data_text)
        save_summary(hist_no, summary.raw_markdown)
        _log("Done!")

        return summary.raw_markdown

    async def process_patient_list(
        self,
        patients: list[dict[str, str]],
        *,
        on_progress: Any = None,
    ) -> list[tuple[str, str | None, str | None]]:
        """Process multiple patients sequentially with inter-patient delay.

        Returns list of (hist_no, markdown_or_None, error_or_None).
        """
        results: list[tuple[str, str | None, str | None]] = []

        for i, pat in enumerate(patients):
            hist_no = pat.get("hist_no", "")
            if not hist_no:
                continue

            try:
                md = await self.process_patient(hist_no, on_progress=on_progress)
                results.append((hist_no, md, None))
            except Exception as exc:
                logger.error("Failed to process %s: %s", hist_no, exc)
                results.append((hist_no, None, str(exc)))

            # Inter-patient delay (skip after last patient)
            if i < len(patients) - 1:
                delay = random.uniform(
                    settings.patient_delay_min, settings.patient_delay_max
                )
                if on_progress:
                    on_progress(f"Waiting {delay:.0f}s before next patient...")
                await asyncio.sleep(delay)

        return results

    # ── internal crawlers ──────────────────────────────────────

    async def _crawl_baseline(self, hist_no: str) -> dict[str, Any]:
        """Round 1: fetch the 6 core categories."""
        data: dict[str, Any] = {}

        # Resolve admin_id first (needed by several endpoints)
        admin_id = await fetch_admin_id(self.session, hist_no)
        data["_admin_id"] = admin_id

        # Fetch in sequence (anti-blocking: each has built-in delay)
        # Demographics
        try:
            demo = await fetch_last_admission(self.session, hist_no)
            data["admission_note"] = demo
        except Exception as e:
            logger.warning("admission_note failed: %s", e)

        # Vitals
        try:
            tpr = await fetch_tpr(self.session, hist_no, admin_id)
            data["vitals"] = tpr.to_dict() if not tpr.empty else {}
        except Exception as e:
            logger.warning("vitals failed: %s", e)

        # Labs (SMAC + CBC)
        for rt in ("SMAC", "CBC"):
            try:
                lab = await fetch_lab_report(self.session, hist_no, rt)
                data[f"lab_{rt.lower()}"] = lab.to_dict() if not lab.empty else {}
            except Exception as e:
                logger.warning("lab_%s failed: %s", rt.lower(), e)

        # Meds
        try:
            drugs = await fetch_drugs(self.session, hist_no, admin_id)
            data["medications"] = drugs.to_dict() if not drugs.empty else {}
        except Exception as e:
            logger.warning("medications failed: %s", e)

        # Imaging
        try:
            reports = await fetch_recent_reports(self.session, hist_no, 5)
            data["recent_reports"] = reports
        except Exception as e:
            logger.warning("recent_reports failed: %s", e)

        return data

    async def _crawl_additional(
        self,
        hist_no: str,
        admin_id: str,
        requests: list[AdditionalRequest],
    ) -> dict[str, Any]:
        """Targeted crawl based on AI requests."""
        data: dict[str, Any] = {}

        for req in requests[:5]:  # Cap at 5
            cat = req.category.lower()
            try:
                if cat == "cultures" or cat == "labs":
                    # Fetch specific lab type or longer history
                    rt = req.parameters.get("type", "SMAC")
                    months = req.parameters.get("months", "24")
                    lab = await fetch_lab_report(self.session, hist_no, rt, months)
                    key = f"lab_{rt.lower()}_{months}m"
                    data[key] = lab.to_dict() if not lab.empty else {}

                elif cat == "io":
                    io = await fetch_drainage(self.session, hist_no, admin_id)
                    data["io_drainage"] = io.to_dict() if io is not None and not io.empty else {}

                elif cat == "notes":
                    notes = await fetch_progress_notes(
                        self.session, hist_no, admin_id,
                        num=int(req.parameters.get("num", "3")),
                    )
                    data["progress_notes"] = notes

                elif cat == "operations":
                    op = await fetch_op(self.session, hist_no)
                    data["operation"] = op

                elif cat == "imaging":
                    reports = await fetch_recent_reports(
                        self.session, hist_no,
                        int(req.parameters.get("num", "5")),
                    )
                    data["recent_reports_extended"] = reports

            except Exception as e:
                logger.warning("Additional fetch %s failed: %s", cat, e)

        return data

    def _format_patient_data(self, data: dict[str, Any]) -> str:
        """Convert crawled data dict into readable text for AI."""
        parts: list[str] = []

        if "admission_note" in data and data["admission_note"]:
            parts.append(f"### Admission Note\n{data['admission_note']}\n")

        if "vitals" in data and data["vitals"]:
            parts.append(_df_to_text(pd.DataFrame(data["vitals"]), "Vitals (TPR)"))

        for key in sorted(data.keys()):
            if key.startswith("lab_") and data[key]:
                label = key.replace("_", " ").upper()
                parts.append(_df_to_text(pd.DataFrame(data[key]), label))

        if "medications" in data and data["medications"]:
            parts.append(_df_to_text(pd.DataFrame(data["medications"]), "Medications"))

        if "recent_reports" in data and data["recent_reports"]:
            parts.append("### Recent Reports\n" + "\n".join(f"- {r}" for r in data["recent_reports"]) + "\n")

        if "io_drainage" in data and data["io_drainage"]:
            parts.append(_df_to_text(pd.DataFrame(data["io_drainage"]), "I/O Drainage"))

        if "progress_notes" in data and data["progress_notes"]:
            parts.append("### Progress Notes\n")
            for note in data["progress_notes"]:
                parts.append(f"**{note.get('date', '')}**")
                for key in ("Subjective", "Objective", "Assessment", "Plan"):
                    if key in note:
                        parts.append(f"_{key}_: {note[key]}")
                parts.append("")

        if "operation" in data and data["operation"]:
            parts.append(_dict_to_text(data["operation"], "Operation"))

        return "\n".join(parts) if parts else "(No data available)"
