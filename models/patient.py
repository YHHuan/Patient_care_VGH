"""Data models for all patient data categories."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Demographics(BaseModel):
    """Category A: basic patient info."""
    chart_no: str = ""
    name: str = ""
    gender: str = ""
    age: int | None = None
    birth_date: date | None = None
    bed: str = ""
    admission_date: date | None = None
    attending_physician: str = ""
    diagnosis: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class VitalSign(BaseModel):
    """Single vital sign measurement."""
    timestamp: datetime | None = None
    temperature: float | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    spo2: float | None = None
    pain_score: int | None = None


class LabResult(BaseModel):
    """Single lab test result."""
    test_name: str = ""
    value: str = ""
    unit: str = ""
    reference_range: str = ""
    is_abnormal: bool = False
    collected_at: datetime | None = None
    report_group: str = ""


class Medication(BaseModel):
    """Single medication order."""
    drug_name: str = ""
    dose: str = ""
    route: str = ""
    frequency: str = ""
    start_date: date | None = None
    end_date: date | None = None
    status: str = ""  # active / discontinued / prn


class ImagingReport(BaseModel):
    """Single imaging report."""
    modality: str = ""  # CXR, CT, MRI, Echo, etc.
    exam_date: date | None = None
    body_part: str = ""
    findings: str = ""
    impression: str = ""


class IORecord(BaseModel):
    """Intake/output record for a single shift or day."""
    record_date: date | None = None
    shift: str = ""  # D / E / N or 24h
    intake_ml: float | None = None
    output_ml: float | None = None
    urine_ml: float | None = None
    drain_ml: float | None = None
    balance_ml: float | None = None


class Operation(BaseModel):
    """Surgical/procedure record."""
    op_date: date | None = None
    procedure_name: str = ""
    surgeon: str = ""
    anesthesia: str = ""
    findings: str = ""
    complications: str = ""


class ClinicalNote(BaseModel):
    """Admission note, progress note, or duty note."""
    note_type: str = ""  # admission / progress / duty
    author: str = ""
    written_at: datetime | None = None
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    raw_text: str = ""


class PatientData(BaseModel):
    """Aggregated data for a single patient across all rounds."""
    demographics: Demographics = Field(default_factory=Demographics)
    vitals: list[VitalSign] = Field(default_factory=list)
    labs: list[LabResult] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    imaging: list[ImagingReport] = Field(default_factory=list)
    io_records: list[IORecord] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
    notes: list[ClinicalNote] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)

    @property
    def chart_no(self) -> str:
        return self.demographics.chart_no

    @property
    def display_name(self) -> str:
        d = self.demographics
        return f"[{d.bed}] {d.name}" if d.bed else d.name
