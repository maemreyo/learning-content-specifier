from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .api_models import IngestionRunSummary, UnitRecord


class CatalogStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS units (
                unit_id TEXT PRIMARY KEY,
                unit_path TEXT NOT NULL,
                gate_status TEXT NOT NULL,
                entry_level TEXT,
                modality TEXT,
                duration_minutes INTEGER,
                manifest_json TEXT,
                gates_json TEXT NOT NULL,
                artifacts_json TEXT NOT NULL,
                issues_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ingestion_run_id TEXT
            );

            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                repo_path TEXT NOT NULL,
                unit_glob TEXT NOT NULL,
                contract_version TEXT NOT NULL,
                total_units INTEGER NOT NULL,
                pass_units INTEGER NOT NULL,
                block_units INTEGER NOT NULL
            );
            """
        )
        self._conn.commit()

    def upsert_unit(self, record: UnitRecord, ingestion_run_id: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        metadata = record.metadata.model_dump()
        self._conn.execute(
            """
            INSERT INTO units (
                unit_id, unit_path, gate_status,
                entry_level, modality, duration_minutes,
                manifest_json, gates_json, artifacts_json, issues_json, metadata_json,
                updated_at, ingestion_run_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unit_id) DO UPDATE SET
                unit_path=excluded.unit_path,
                gate_status=excluded.gate_status,
                entry_level=excluded.entry_level,
                modality=excluded.modality,
                duration_minutes=excluded.duration_minutes,
                manifest_json=excluded.manifest_json,
                gates_json=excluded.gates_json,
                artifacts_json=excluded.artifacts_json,
                issues_json=excluded.issues_json,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at,
                ingestion_run_id=excluded.ingestion_run_id
            """,
            (
                record.unit_id,
                record.unit_path,
                record.gate_status,
                metadata.get("entry_level"),
                metadata.get("modality"),
                metadata.get("duration_minutes"),
                json.dumps(record.manifest) if record.manifest is not None else None,
                json.dumps(record.gates.model_dump()),
                json.dumps([item.model_dump() for item in record.artifacts]),
                json.dumps([item.model_dump() for item in record.issues]),
                json.dumps(metadata),
                now,
                ingestion_run_id,
            ),
        )
        self._conn.commit()

    def list_units(
        self,
        gate_status: str | None = None,
        entry_level: str | None = None,
        modality: str | None = None,
        duration_min: int | None = None,
        duration_max: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []

        if gate_status:
            conditions.append("gate_status = ?")
            params.append(gate_status)
        if entry_level:
            conditions.append("entry_level = ?")
            params.append(entry_level)
        if modality:
            conditions.append("modality = ?")
            params.append(modality)
        if duration_min is not None:
            conditions.append("duration_minutes >= ?")
            params.append(duration_min)
        if duration_max is not None:
            conditions.append("duration_minutes <= ?")
            params.append(duration_max)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = (
            "SELECT * FROM units "
            f"{where_clause} "
            "ORDER BY updated_at DESC "
            "LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_payload(row) for row in rows]

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM units WHERE unit_id = ?", (unit_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_payload(row)

    def record_ingestion_run(self, summary: IngestionRunSummary) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO ingestion_runs (
                run_id, started_at, ended_at,
                repo_path, unit_glob, contract_version,
                total_units, pass_units, block_units
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary.run_id,
                summary.started_at.isoformat(),
                summary.ended_at.isoformat(),
                summary.repo_path,
                summary.unit_glob,
                summary.contract_version,
                summary.total_units,
                summary.pass_units,
                summary.block_units,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "unit_id": row["unit_id"],
            "unit_path": row["unit_path"],
            "gate_status": row["gate_status"],
            "metadata": json.loads(row["metadata_json"]),
            "manifest": json.loads(row["manifest_json"]) if row["manifest_json"] else None,
            "gates": json.loads(row["gates_json"]),
            "artifacts": json.loads(row["artifacts_json"]),
            "issues": json.loads(row["issues_json"]),
            "updated_at": row["updated_at"],
            "ingestion_run_id": row["ingestion_run_id"],
        }
