#!/usr/bin/env python3
"""Deterministically parse rubric gate lines for authoring hard gates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


GATE_LINE_RE = re.compile(
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
    parser.add_argument("--rubrics-dir", required=True, help="Path to rubrics directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    rubrics_dir = Path(args.rubrics_dir).resolve()
    blockers: list[str] = []
    parse_errors: list[str] = []
    gate_count = 0
    unchecked_count = 0
    non_pass_count = 0
    seen_gate_ids: set[str] = set()

    if not rubrics_dir.is_dir():
        blockers.append(f"Missing rubrics directory: {rubrics_dir}")
    else:
        rubric_files = sorted(rubrics_dir.glob("*.md"))
        if not rubric_files:
            blockers.append(f"No rubric files found in {rubrics_dir}")
        else:
            for rubric_file in rubric_files:
                file_gate_count = 0
                for line_no, raw_line in enumerate(rubric_file.read_text(encoding="utf-8").splitlines(), start=1):
                    line = raw_line.strip()
                    if not line:
                        continue

                    if "Gate ID:" not in line:
                        continue

                    match = GATE_LINE_RE.match(raw_line)
                    if not match:
                        parse_errors.append(f"{rubric_file}:{line_no}: non-parseable gate line")
                        continue

                    file_gate_count += 1
                    gate_count += 1
                    gate_id = match.group("gate_id").upper()
                    checked = match.group("checked").lower() == "x"
                    status = match.group("status").upper()
                    evidence = match.group("evidence").strip()

                    if gate_id in seen_gate_ids:
                        blockers.append(f"{rubric_file}:{line_no}: duplicate gate ID {gate_id}")
                    seen_gate_ids.add(gate_id)

                    if not checked:
                        unchecked_count += 1
                    if status != "PASS":
                        non_pass_count += 1

                    if checked and status != "PASS":
                        blockers.append(
                            f"{rubric_file}:{line_no}: checked gate {gate_id} must use Status PASS"
                        )
                    if status == "PASS" and not checked:
                        blockers.append(
                            f"{rubric_file}:{line_no}: PASS gate {gate_id} must be checked [x]"
                        )
                    if status == "PASS" and evidence.lower() in {"[pending]", "pending", "n/a", "none"}:
                        blockers.append(
                            f"{rubric_file}:{line_no}: PASS gate {gate_id} requires concrete evidence reference"
                        )

                if file_gate_count == 0:
                    blockers.append(f"{rubric_file}: no parseable gate lines found")

    status = "PASS" if not blockers and not parse_errors else "BLOCK"
    payload = {
        "STATUS": status,
        "RUBRICS_DIR": str(rubrics_dir),
        "GATE_COUNT": gate_count,
        "UNCHECKED_COUNT": unchecked_count,
        "NON_PASS_COUNT": non_pass_count,
        "PARSE_ERROR_COUNT": len(parse_errors),
        "PARSE_ERRORS": parse_errors,
        "BLOCKERS": blockers,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: {status}")
        print(f"RUBRICS_DIR: {rubrics_dir}")
        print(f"GATE_COUNT: {gate_count}")
        print(f"UNCHECKED_COUNT: {unchecked_count}")
        print(f"NON_PASS_COUNT: {non_pass_count}")
        print(f"PARSE_ERROR_COUNT: {len(parse_errors)}")
        if parse_errors:
            print("PARSE_ERRORS:")
            for item in parse_errors:
                print(f"  - {item}")
        if blockers:
            print("BLOCKERS:")
            for item in blockers:
                print(f"  - {item}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
