#!/usr/bin/env python3
"""Validate canonical rubric-gates.json with optional markdown parity checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MD_GATE_LINE_RE = re.compile(
    r"^\s*-\s*\[(?P<checked>[ xX])\]\s*"
    r"Gate ID:\s*(?P<gate_id>RB[0-9]{3})\s*\|\s*"
    r"Group:\s*(?P<group>[a-z][a-z0-9-]*)\s*\|\s*"
    r"Status:\s*(?P<status>PASS|FAIL|BLOCK|UNSET|TODO)\s*\|\s*"
    r"Severity:\s*(?P<severity>CRITICAL|HIGH|MEDIUM|LOW)\s*\|\s*"
    r"Evidence:\s*(?P<evidence>.+?)\s*$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rubric-gates-file", required=True, help="Path to rubric-gates.json")
    parser.add_argument("--rubrics-dir", help="Optional rubrics directory for markdown parity checks")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _parse_md_gate_ids(rubrics_dir: Path) -> tuple[list[str], list[str]]:
    parse_errors: list[str] = []
    gate_ids: list[str] = []

    if not rubrics_dir.is_dir():
        return gate_ids, parse_errors

    for rubric_file in sorted(rubrics_dir.glob("*.md")):
        for line_no, raw_line in enumerate(rubric_file.read_text(encoding="utf-8").splitlines(), start=1):
            if "Gate ID:" not in raw_line:
                continue
            match = MD_GATE_LINE_RE.match(raw_line)
            if not match:
                parse_errors.append(f"{rubric_file}:{line_no}: non-parseable gate line")
                continue
            gate_ids.append(match.group("gate_id").upper())

    return gate_ids, parse_errors


def main() -> int:
    args = parse_args()
    rubric_gates_file = Path(args.rubric_gates_file).resolve()
    rubrics_dir = Path(args.rubrics_dir).resolve() if args.rubrics_dir else None

    blockers: list[str] = []
    parse_errors: list[str] = []
    parity_warnings: list[str] = []
    gate_count = 0
    unchecked_count = 0
    non_pass_count = 0
    seen_gate_ids: set[str] = set()

    if not rubric_gates_file.is_file():
        blockers.append(f"Missing rubric gates artifact: {rubric_gates_file}")
    else:
        payload = _load_json(rubric_gates_file)
        if payload is None:
            parse_errors.append(f"{rubric_gates_file}: invalid JSON object")
        else:
            gates = payload.get("gates")
            if not isinstance(gates, list):
                parse_errors.append(f"{rubric_gates_file}: gates must be an array")
                gates = []

            for index, gate in enumerate(gates):
                if not isinstance(gate, dict):
                    parse_errors.append(f"{rubric_gates_file}: gates[{index}] must be an object")
                    continue

                gate_id = str(gate.get("gate_id", "")).upper()
                checked = bool(gate.get("checked", False))
                status = str(gate.get("status", "")).upper()
                evidence = str(gate.get("evidence", "")).strip()

                if not gate_id:
                    parse_errors.append(f"{rubric_gates_file}: gates[{index}].gate_id is required")
                    continue

                gate_count += 1
                if gate_id in seen_gate_ids:
                    blockers.append(f"{rubric_gates_file}: duplicate gate ID {gate_id}")
                seen_gate_ids.add(gate_id)

                if not checked:
                    unchecked_count += 1
                if status != "PASS":
                    non_pass_count += 1

                if checked and status != "PASS":
                    blockers.append(
                        f"{rubric_gates_file}: gate {gate_id} is checked=true but status is {status}"
                    )
                if status == "PASS" and not checked:
                    blockers.append(
                        f"{rubric_gates_file}: gate {gate_id} is PASS but checked=false"
                    )
                if status == "PASS" and evidence.lower() in {"", "[pending]", "pending", "n/a", "none"}:
                    blockers.append(
                        f"{rubric_gates_file}: gate {gate_id} is PASS but evidence is not concrete"
                    )

            if gate_count == 0:
                blockers.append(f"{rubric_gates_file}: gates must contain at least one gate entry")

    if rubrics_dir is not None:
        md_gate_ids, md_parse_errors = _parse_md_gate_ids(rubrics_dir)
        if md_parse_errors:
            parity_warnings.extend(md_parse_errors)
        if md_gate_ids:
            json_ids = sorted(seen_gate_ids)
            md_ids = sorted(set(md_gate_ids))
            if md_ids != json_ids:
                parity_warnings.append(
                    "rubric markdown gate ids do not match rubric-gates.json gate ids"
                )

    status = "PASS" if not blockers and not parse_errors else "BLOCK"
    payload = {
        "STATUS": status,
        "RUBRIC_GATES_FILE": str(rubric_gates_file),
        "RUBRICS_DIR": str(rubrics_dir) if rubrics_dir else "",
        "GATE_COUNT": gate_count,
        "UNCHECKED_COUNT": unchecked_count,
        "NON_PASS_COUNT": non_pass_count,
        "PARSE_ERROR_COUNT": len(parse_errors),
        "PARSE_ERRORS": parse_errors,
        "PARITY_WARNING_COUNT": len(parity_warnings),
        "PARITY_WARNINGS": parity_warnings,
        "BLOCKERS": blockers,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: {status}")
        print(f"RUBRIC_GATES_FILE: {rubric_gates_file}")
        print(f"GATE_COUNT: {gate_count}")
        print(f"UNCHECKED_COUNT: {unchecked_count}")
        print(f"NON_PASS_COUNT: {non_pass_count}")
        print(f"PARSE_ERROR_COUNT: {len(parse_errors)}")
        if parse_errors:
            print("PARSE_ERRORS:")
            for item in parse_errors:
                print(f"  - {item}")
        if parity_warnings:
            print("PARITY_WARNINGS:")
            for item in parity_warnings:
                print(f"  - {item}")
        if blockers:
            print("BLOCKERS:")
            for item in blockers:
                print(f"  - {item}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

