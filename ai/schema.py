"""Pydantic models for AI request/response payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AdditionalRequest(BaseModel):
    """A single additional data request from the AI."""
    category: str = ""  # e.g. "labs", "cultures", "io", "notes", "imaging"
    description: str = ""  # e.g. "need blood culture results from past 7 days"
    parameters: dict[str, str] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """AI response after analyzing round-1 data."""
    summary_so_far: str = ""
    key_issues: list[str] = Field(default_factory=list)
    additional_requests: list[AdditionalRequest] = Field(default_factory=list)
    confidence: float = 0.0  # 0-1, how complete the AI feels the data is


class ClinicalSummary(BaseModel):
    """Final structured clinical summary."""
    header: str = ""  # [Bed] Name - Day N
    hospital_course: str = ""
    objective: str = ""  # VS, Lab trends, Imaging
    assessment_and_plan: str = ""  # Problem list with findings + treatments
    raw_markdown: str = ""  # The complete markdown output
