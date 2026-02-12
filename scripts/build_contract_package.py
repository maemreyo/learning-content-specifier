#!/usr/bin/env python3
"""Build and verify the LCS contract sync package for standalone consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover - fallback for older Python in local shells
    tomllib = None


INDEX_PATH = Path("contracts/index.json")
CONTRACT_PACKAGE_SCHEMA_VERSION = "1.0"
CONTRACT_VERSION = "1.0.0"

SCHEMA_GLOBS = ("schemas/*.schema.json",)
DOC_GLOBS = ("docs/contract/*.md", "contracts/README.md")
FIXTURE_GLOBS = ("fixtures/contracts/*.json",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--sync", action="store_true", help="Write contracts/index.json from current sources")
    parser.add_argument("--verify", action="store_true", help="Verify contracts/index.json is up to date")
    parser.add_argument("--package-version", help="Create contract zip (format: vX.Y.Z)")
    parser.add_argument("--output-dir", default=".genreleases", help="Output directory for contract zip")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_lcs_version(pyproject_path: Path) -> str:
    if tomllib is not None:
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            project = payload.get("project", {})
            version = project.get("version")
            if isinstance(version, str) and version:
                return version
        except Exception:  # noqa: BLE001
            pass

    # Regex fallback when tomllib is unavailable or pyproject is malformed.
    text = pyproject_path.read_text(encoding="utf-8")
    section_match = re.search(r"(?ms)^\[project\]\s*(.+?)(?:^\[|\Z)", text)
    if not section_match:
        return "0.0.0"
    project_block = section_match.group(1)
    version_match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', project_block)
    if not version_match:
        return "0.0.0"
    return version_match.group(1)


def collect_entries(repo_root: Path, globs: tuple[str, ...], include_schema_id: bool = False) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for pattern in globs:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root).as_posix()
            entry: dict[str, Any] = {
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            if include_schema_id:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError(f"Schema file must be a JSON object: {path}")
                schema_id = payload.get("$id")
                if not isinstance(schema_id, str) or not schema_id.strip():
                    raise ValueError(f"Schema file missing non-empty $id: {path}")
                entry["id"] = schema_id
            entries.append(entry)
    return entries


def build_index(repo_root: Path) -> dict[str, Any]:
    lcs_version = read_lcs_version(repo_root / "pyproject.toml")
    schemas = collect_entries(repo_root, SCHEMA_GLOBS, include_schema_id=True)
    docs = collect_entries(repo_root, DOC_GLOBS)
    fixtures = collect_entries(repo_root, FIXTURE_GLOBS)

    return {
        "contract_package_schema_version": CONTRACT_PACKAGE_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "lcs_cli_version": lcs_version,
        "compatibility": {
            "semver": {
                "major": "breaking",
                "minor": "additive",
                "patch": "non-structural-fix",
            },
            "manifest_first_required": True,
            "interop_required": ["xapi"],
            "interop_optional": ["case", "qti", "lti", "cmi5"],
        },
        "entries": {
            "schemas": schemas,
            "docs_digest": docs,
            "fixtures": fixtures,
        },
    }


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def load_index(index_file: Path) -> dict[str, Any]:
    return json.loads(index_file.read_text(encoding="utf-8"))


def write_index(index_file: Path, payload: dict[str, Any]) -> None:
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(canonical_json(payload), encoding="utf-8")


def verify_index(index_file: Path, expected: dict[str, Any]) -> bool:
    if not index_file.exists():
        print(f"Missing index file: {index_file}", file=sys.stderr)
        return False

    current = load_index(index_file)
    if current != expected:
        print("contracts/index.json is out of sync with sources.", file=sys.stderr)
        return False

    print("Contract index verification passed")
    return True


def build_zip(repo_root: Path, package_version: str, output_dir: Path) -> Path:
    if not re.match(r"^v\d+\.\d+\.\d+$", package_version):
        raise ValueError("package version must match vX.Y.Z")

    zip_path = output_dir / f"lcs-contracts-{package_version}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)

    index = load_index(repo_root / INDEX_PATH)
    entries = (
        index.get("entries", {}).get("schemas", [])
        + index.get("entries", {}).get("docs_digest", [])
        + index.get("entries", {}).get("fixtures", [])
    )

    included = {"contracts/index.json"}
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(repo_root / INDEX_PATH, arcname="contracts/index.json")
        for item in entries:
            path = str(item.get("path", ""))
            if not path or path in included:
                continue
            file_path = repo_root / path
            if not file_path.is_file():
                raise FileNotFoundError(f"Contract package entry missing: {path}")
            archive.write(file_path, arcname=path)
            included.add(path)

    print(f"Created contract package: {zip_path}")
    return zip_path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    index_file = repo_root / INDEX_PATH
    expected = build_index(repo_root)

    did_action = False
    ok = True

    if args.sync:
        write_index(index_file, expected)
        print(f"Updated {index_file}")
        did_action = True

    if args.verify or (not args.sync and not args.package_version):
        ok = verify_index(index_file, expected)
        did_action = True

    if args.package_version:
        if not index_file.exists():
            write_index(index_file, expected)
        if not verify_index(index_file, expected):
            return 1
        build_zip(repo_root, args.package_version, (repo_root / args.output_dir).resolve())
        did_action = True

    if not did_action:
        print("No action requested", file=sys.stderr)
        return 1

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
