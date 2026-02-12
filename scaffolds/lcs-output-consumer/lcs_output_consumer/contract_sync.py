from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContractSyncError(RuntimeError):
    pass


@dataclass
class ContractBundle:
    repo_root: Path
    contract_version: str
    schemas: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, repo_root: Path) -> "ContractBundle":
        index_path = repo_root / "contracts/index.json"
        if not index_path.is_file():
            raise ContractSyncError(f"Missing contract index: {index_path}")

        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        contract_version = str(index_payload.get("contract_version", ""))
        if not contract_version:
            raise ContractSyncError("contracts/index.json missing contract_version")

        entries = index_payload.get("entries", {})
        for group in ("schemas", "docs_digest", "fixtures"):
            group_entries = entries.get(group, [])
            if not isinstance(group_entries, list):
                raise ContractSyncError(f"contracts/index.json invalid entries.{group}")
            for item in group_entries:
                cls._verify_entry(repo_root, item)

        schema_entries = entries.get("schemas", [])
        schemas: dict[str, dict[str, Any]] = {}
        for item in schema_entries:
            path = repo_root / str(item.get("path", ""))
            if not path.is_file():
                raise ContractSyncError(f"Missing schema file: {path}")
            schemas[path.name] = json.loads(path.read_text(encoding="utf-8"))

        if not schemas:
            raise ContractSyncError("No schemas found in contracts/index.json")

        return cls(repo_root=repo_root, contract_version=contract_version, schemas=schemas)

    @staticmethod
    def _verify_entry(repo_root: Path, item: dict[str, Any]) -> None:
        rel_path = str(item.get("path", ""))
        sha = str(item.get("sha256", ""))
        if not rel_path or not sha:
            raise ContractSyncError("contracts/index.json has entry missing path or sha256")

        path = repo_root / rel_path
        if not path.is_file():
            raise ContractSyncError(f"Indexed file missing: {path}")

        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha != sha:
            raise ContractSyncError(f"Checksum mismatch for indexed file: {rel_path}")

    def assert_compatible_version(self, requested_version: str) -> None:
        current_major = _parse_major(self.contract_version)
        requested_major = _parse_major(requested_version)
        if current_major != requested_major:
            raise ContractSyncError(
                "Incompatible contract major version: "
                f"requested={requested_version}, available={self.contract_version}"
            )


def _parse_major(version: str) -> int:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ContractSyncError(f"Invalid semver value: {version}")
    return int(match.group(1))
