from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Query

from .api_models import (
    IngestionFsRequest,
    IngestionRunSummary,
    UnitRecord,
    ValidationUnitRequest,
)
from .contract_sync import ContractBundle, ContractSyncError
from .store import CatalogStore
from .validator import validate_unit


def _resolve_repo_root() -> Path:
    configured = os.getenv("LCS_CONSUMER_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def _resolve_db_path(repo_root: Path) -> Path:
    configured = os.getenv("LCS_CONSUMER_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return repo_root / "data" / "catalog.sqlite3"


app = FastAPI(title="LCS Output Consumer API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    repo_root = _resolve_repo_root()
    db_path = _resolve_db_path(repo_root)

    app.state.repo_root = repo_root
    app.state.store = CatalogStore(db_path)

    try:
        app.state.contract_bundle = ContractBundle.load(repo_root)
        app.state.contract_error = None
    except ContractSyncError as exc:
        app.state.contract_bundle = None
        app.state.contract_error = str(exc)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    if app.state.contract_bundle is None:
        return {"status": "degraded", "reason": app.state.contract_error}
    return {"status": "ok"}


@app.post("/v1/validations/unit")
def validate_single_unit(payload: ValidationUnitRequest) -> dict:
    bundle = _require_bundle()
    unit_path = Path(payload.unit_path).expanduser().resolve()
    if not unit_path.is_dir():
        raise HTTPException(status_code=400, detail=f"unit path is not a directory: {unit_path}")

    result = validate_unit(unit_path, bundle)
    record = UnitRecord(
        unit_id=result.unit_id,
        unit_path=result.unit_path,
        gate_status=result.gates.decision,
        metadata=result.metadata,
        manifest=result.manifest,
        gates=result.gates,
        artifacts=result.artifacts,
        issues=result.issues,
        updated_at=datetime.now(timezone.utc),
    )
    app.state.store.upsert_unit(record)
    return result.model_dump()


@app.post("/v1/ingestions/fs")
def ingest_filesystem(payload: IngestionFsRequest) -> dict:
    bundle = _require_bundle()
    try:
        bundle.assert_compatible_version(payload.contract_version)
    except ContractSyncError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    repo_path = Path(payload.repo_path).expanduser().resolve()
    if not repo_path.is_dir():
        raise HTTPException(status_code=400, detail=f"repo_path is not a directory: {repo_path}")

    started_at = datetime.now(timezone.utc)
    run_id = str(uuid4())

    candidates = sorted(path for path in repo_path.glob(payload.unit_glob) if path.is_dir())
    results = [validate_unit(path, bundle) for path in candidates]

    pass_units = 0
    block_units = 0
    for result in results:
        if result.status == "PASS":
            pass_units += 1
        else:
            block_units += 1

        record = UnitRecord(
            unit_id=result.unit_id,
            unit_path=result.unit_path,
            gate_status=result.gates.decision,
            metadata=result.metadata,
            manifest=result.manifest,
            gates=result.gates,
            artifacts=result.artifacts,
            issues=result.issues,
            updated_at=datetime.now(timezone.utc),
        )
        app.state.store.upsert_unit(record, ingestion_run_id=run_id)

    ended_at = datetime.now(timezone.utc)
    summary = IngestionRunSummary(
        run_id=run_id,
        started_at=started_at,
        ended_at=ended_at,
        repo_path=str(repo_path),
        unit_glob=payload.unit_glob,
        contract_version=payload.contract_version,
        total_units=len(results),
        pass_units=pass_units,
        block_units=block_units,
    )
    app.state.store.record_ingestion_run(summary)

    return {
        "run": summary.model_dump(),
        "units": [result.model_dump() for result in results],
    }


@app.get("/v1/units")
def list_units(
    gate_status: str | None = Query(default=None),
    entry_level: str | None = Query(default=None),
    modality: str | None = Query(default=None),
    duration_min: int | None = Query(default=None),
    duration_max: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items = app.state.store.list_units(
        gate_status=gate_status,
        entry_level=entry_level,
        modality=modality,
        duration_min=duration_min,
        duration_max=duration_max,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "count": len(items)}


@app.get("/v1/units/{unit_id}")
def get_unit(unit_id: str) -> dict:
    unit = app.state.store.get_unit(unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"unit not found: {unit_id}")
    return unit


@app.get("/v1/units/{unit_id}/manifest")
def get_unit_manifest(unit_id: str) -> dict:
    unit = _get_unit_or_404(unit_id)
    return {"unit_id": unit_id, "manifest": unit["manifest"]}


@app.get("/v1/units/{unit_id}/gates")
def get_unit_gates(unit_id: str) -> dict:
    unit = _get_unit_or_404(unit_id)
    return {"unit_id": unit_id, "gates": unit["gates"]}


@app.get("/v1/units/{unit_id}/artifacts")
def get_unit_artifacts(unit_id: str) -> dict:
    unit = _get_unit_or_404(unit_id)
    return {"unit_id": unit_id, "artifacts": unit["artifacts"]}


def _require_bundle() -> ContractBundle:
    bundle = app.state.contract_bundle
    if bundle is None:
        raise HTTPException(status_code=500, detail=f"contract bundle unavailable: {app.state.contract_error}")
    return bundle


def _get_unit_or_404(unit_id: str) -> dict:
    unit = app.state.store.get_unit(unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"unit not found: {unit_id}")
    return unit


def run() -> None:
    uvicorn.run("lcs_output_consumer.main:app", host="0.0.0.0", port=8088, reload=False)


if __name__ == "__main__":
    run()
