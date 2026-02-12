#!/usr/bin/env python3
"""Validate machine-readable learning-content artifacts against JSON schemas."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ContractPair:
    artifact: str
    schema: str


REQUIRED_CONTRACTS = (
    ContractPair("brief.json", "brief.schema.json"),
    ContractPair("design.json", "design.schema.json"),
    ContractPair("sequence.json", "sequence.schema.json"),
    ContractPair("audit-report.json", "audit-report.schema.json"),
    ContractPair("outputs/manifest.json", "manifest.schema.json"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--unit-dir", required=True, help="Unit directory under specs/")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def _validate_json(artifact_path: Path, schema_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"{artifact_path}: invalid JSON ({exc})"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"{schema_path}: invalid schema JSON ({exc})"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(artifact), key=str):
        location = "/".join(str(p) for p in error.path) or "<root>"
        errors.append(f"{artifact_path}: {location}: {error.message}")

    return errors


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    unit_dir = Path(args.unit_dir).resolve()
    schemas_dir = repo_root / "schemas"

    missing_files: list[str] = []
    missing_schemas: list[str] = []
    validated: list[str] = []
    errors: list[str] = []

    for pair in REQUIRED_CONTRACTS:
        artifact_path = unit_dir / pair.artifact
        schema_path = schemas_dir / pair.schema

        if not schema_path.is_file():
            missing_schemas.append(str(schema_path))
            continue

        if not artifact_path.is_file():
            missing_files.append(str(artifact_path))
            continue

        validated.append(str(artifact_path))
        errors.extend(_validate_json(artifact_path, schema_path))

    status = "PASS" if not missing_files and not missing_schemas and not errors else "BLOCK"
    payload = {
        "STATUS": status,
        "UNIT_DIR": str(unit_dir),
        "VALIDATED": validated,
        "MISSING_FILES": missing_files,
        "MISSING_SCHEMAS": missing_schemas,
        "ERRORS": errors,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: {status}")
        print(f"UNIT_DIR: {unit_dir}")
        print(f"VALIDATED: {len(validated)}")
        if missing_schemas:
            print("MISSING_SCHEMAS:")
            for item in missing_schemas:
                print(f"  - {item}")
        if missing_files:
            print("MISSING_FILES:")
            for item in missing_files:
                print(f"  - {item}")
        if errors:
            print("ERRORS:")
            for item in errors:
                print(f"  - {item}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
