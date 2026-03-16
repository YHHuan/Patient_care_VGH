"""OpenRouter API wrapper for Claude Sonnet 4.6."""

from __future__ import annotations

import json
import logging
import re

import httpx

from ai.schema import AnalysisResponse, ClinicalSummary
from ai.prompts import ANALYSIS_PROMPT, SUMMARY_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)


class AIClient:
    """Calls Claude via OpenRouter."""

    def __init__(self) -> None:
        self._api_key = settings.openrouter_api_key
        self._model = settings.ai_model
        self._base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def _chat(self, prompt: str, *, retries: int = 2) -> str:
        """Send a single chat completion request."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(1, retries + 1):
                try:
                    resp = await client.post(
                        self._base_url, json=payload, headers=headers
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                except Exception:
                    if attempt == retries:
                        raise
                    logger.warning("AI request failed (attempt %d), retrying", attempt)

        raise RuntimeError("AI request failed")

    async def analyze(self, patient_data_text: str) -> AnalysisResponse:
        """Round-1 analysis: review data, request additional info."""
        prompt = ANALYSIS_PROMPT.format(patient_data=patient_data_text)
        raw = await self._chat(prompt)

        # Extract JSON from response (may be wrapped in ```json ... ```)
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match is None:
            logger.error("AI returned non-JSON response: %s", raw[:200])
            return AnalysisResponse(
                summary_so_far=raw[:500],
                confidence=0.3,
            )

        try:
            parsed = json.loads(json_match.group())
            return AnalysisResponse(**parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse AI JSON: %s", exc)
            return AnalysisResponse(summary_so_far=raw[:500], confidence=0.3)

    async def summarize(self, patient_data_text: str) -> ClinicalSummary:
        """Final pass: generate structured markdown summary."""
        prompt = SUMMARY_PROMPT.format(patient_data=patient_data_text)
        raw = await self._chat(prompt)

        # Parse sections from markdown
        lines = raw.strip().split("\n")
        header = ""
        for line in lines:
            if line.startswith("# ") and "Day" in line:
                header = line.lstrip("# ").strip()
                break

        return ClinicalSummary(
            header=header,
            raw_markdown=raw,
        )
