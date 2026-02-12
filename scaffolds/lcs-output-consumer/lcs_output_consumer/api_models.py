from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    category: Literal["IO", "SCHEMA", "CONSISTENCY", "GATE"]
    message: str
    artifact: str | None = None


class ArtifactStatus(BaseModel):
    id: str
    type: str
    path: str
    media_type: str
    checksum: str
    exists: bool
    checksum_ok: bool | None = None


class GateSnapshot(BaseModel):
    decision: Literal["PASS", "BLOCK"]
    open_critical: int = 0
    open_high: int = 0
    authoring_eligible: bool = False
    audit_decision: Literal["PASS", "BLOCK", "UNKNOWN"] = "UNKNOWN"


class UnitMetadata(BaseModel):
    entry_level: str | None = None
    modality: str | None = None
    duration_minutes: int | None = None


class UnitValidationResult(BaseModel):
    unit_id: str
    unit_path: str
    status: Literal["PASS", "BLOCK"]
    issues: list[ValidationIssue] = Field(default_factory=list)
    gates: GateSnapshot
    artifacts: list[ArtifactStatus] = Field(default_factory=list)
    metadata: UnitMetadata = Field(default_factory=UnitMetadata)
    manifest: dict[str, Any] | None = None


class IngestionFsRequest(BaseModel):
    repo_path: str
    unit_glob: str = "specs/*"
    contract_version: str


class ValidationUnitRequest(BaseModel):
    unit_path: str


class UnitRecord(BaseModel):
    unit_id: str
    unit_path: str
    gate_status: Literal["PASS", "BLOCK"]
    metadata: UnitMetadata
    manifest: dict[str, Any] | None = None
    gates: GateSnapshot
    artifacts: list[ArtifactStatus] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
    updated_at: datetime


class IngestionRunSummary(BaseModel):
    run_id: str
    started_at: datetime
    ended_at: datetime
    repo_path: str
    unit_glob: str
    contract_version: str
    total_units: int
    pass_units: int
    block_units: int
