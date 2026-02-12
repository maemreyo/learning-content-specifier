#!/usr/bin/env python3
"""Scaffold a standalone lcs-output-consumer repository from this LCS core repo."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Target directory for new standalone repo")
    parser.add_argument("--force", action="store_true", help="Overwrite target if it already exists")
    parser.add_argument(
        "--without-contracts",
        action="store_true",
        help="Skip copying contract sync assets (contracts/index, schemas, docs digest, fixtures)",
    )
    return parser.parse_args()


def copy_tree_contents(src: Path, dest: Path) -> None:
    for child in src.iterdir():
        target_child = dest / child.name
        if child.is_dir():
            shutil.copytree(child, target_child)
        else:
            shutil.copy2(child, target_child)


def copy_contract_assets(repo_root: Path, target_root: Path) -> None:
    copy_file(repo_root / "contracts/index.json", target_root / "contracts/index.json")
    copy_file(repo_root / "contracts/README.md", target_root / "contracts/README.md")

    for schema in sorted((repo_root / "schemas").glob("*.schema.json")):
        copy_file(schema, target_root / "schemas" / schema.name)

    for doc in sorted((repo_root / "docs/contract").glob("*.md")):
        copy_file(doc, target_root / "docs/contract" / doc.name)

    for fixture in sorted((repo_root / "fixtures/contracts").glob("*.json")):
        copy_file(fixture, target_root / "fixtures/contracts" / fixture.name)


def copy_file(src: Path, dest: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"Missing source file: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    scaffold_root = repo_root / "scaffolds/lcs-output-consumer"
    target_root = Path(args.target).expanduser().resolve()

    if not scaffold_root.is_dir():
        print(f"Missing scaffold source: {scaffold_root}", file=sys.stderr)
        return 1

    if target_root.exists() and any(target_root.iterdir()) and not args.force:
        print(f"Target directory is not empty: {target_root}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    if target_root.exists() and args.force:
        shutil.rmtree(target_root)

    target_root.mkdir(parents=True, exist_ok=True)
    copy_tree_contents(scaffold_root, target_root)

    if not args.without_contracts:
        copy_contract_assets(repo_root, target_root)

    print(f"Scaffold created at: {target_root}")
    if not args.without_contracts:
        print("Contract assets synced from current LCS repo.")
    else:
        print("Contract asset copy skipped (--without-contracts).")

    print("Next steps:")
    print(f"  cd {target_root}")
    print("  uv sync")
    print("  uv run uvicorn lcs_output_consumer.main:app --reload")
    return 0


if __name__ == "__main__":
    sys.exit(main())
