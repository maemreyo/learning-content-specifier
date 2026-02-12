#!/usr/bin/env python3
"""Scaffold a standalone lcs-output-consumer repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from pathlib import Path


SEMVER_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_CONTRACT_VERSION_FILE = (
    Path(__file__).resolve().parents[3] / "contracts" / "consumer-contract-version.txt"
)


class ScaffoldError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Target directory for standalone consumer repo")
    parser.add_argument(
        "--contracts-version",
        help="Pinned required contract version (X.Y.Z). Fallback reads contracts/consumer-contract-version.txt",
    )
    parser.add_argument(
        "--contracts-version-file",
        default=str(DEFAULT_CONTRACT_VERSION_FILE),
        help="Fallback file for required contract version when --contracts-version is omitted",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite non-empty target directory")
    return parser.parse_args()


def resolve_contract_version(explicit_value: str | None, fallback_file: str | None) -> str:
    candidate = (explicit_value or "").strip()
    if not candidate and fallback_file:
        path = Path(fallback_file).expanduser().resolve()
        if path.is_file():
            candidate = path.read_text(encoding="utf-8").strip()

    if not candidate:
        raise ScaffoldError(
            "Missing contracts version. Provide --contracts-version or maintain contracts/consumer-contract-version.txt."
        )

    if not SEMVER_VERSION_PATTERN.match(candidate):
        raise ScaffoldError(f"Invalid contracts version '{candidate}', expected X.Y.Z")

    return candidate


def prepare_target(target: Path, force: bool) -> None:
    if target.exists() and any(target.iterdir()):
        if not force:
            raise ScaffoldError(f"Target directory is not empty: {target} (use --force)")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def write_file(base_dir: Path, relative_path: str, content: str) -> None:
    path = base_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_files(contracts_version: str) -> dict[str, str]:
    pyproject = textwrap.dedent(
        """\
        [project]
        name = "lcs-output-consumer"
        version = "0.1.0"
        description = "Standalone integration backbone for LCS outputs"
        requires-python = ">=3.11"
        dependencies = [
          "fastapi>=0.115.0",
          "uvicorn>=0.30.0",
          "httpx>=0.27.0",
        ]

        [project.optional-dependencies]
        test = [
          "pytest>=8.0.0",
        ]

        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"
        """
    )

    readme = textwrap.dedent(
        """\
        # lcs-output-consumer

        Standalone Library Backbone for LCS outputs.

        ## Responsibilities
        - Ingest unit folders from local filesystem.
        - Validate contracts and gate parity.
        - Expose catalog/query APIs for downstream applications.

        ## Quick Start
        1. `cp .env.example .env`
        2. `uv sync --extra test`
        3. `uv run uvicorn src.lcs_output_consumer.main:app --reload`

        ## Required APIs
        - `GET /healthz`
        - `POST /v1/ingestions/fs`
        - `POST /v1/validations/unit`
        - `GET /v1/units`
        - `GET /v1/units/{unit_id}`
        - `GET /v1/units/{unit_id}/manifest`
        - `GET /v1/units/{unit_id}/gates`
        - `GET /v1/units/{unit_id}/artifacts`
        """
    )

    files: dict[str, str] = {
        ".gitignore": textwrap.dedent(
            """\
            .venv
            __pycache__
            .pytest_cache
            .env
            .DS_Store
            """
        ),
        ".env.example": textwrap.dedent(
            f"""\
            REQUIRED_CONTRACT_VERSION={contracts_version}
            CORE_CONTRACTS_ZIP=
            """
        ),
        "pyproject.toml": pyproject,
        "README.md": readme,
        "contracts/consumer-contract-version.txt": f"{contracts_version}\n",
        "contracts/README.md": textwrap.dedent(
            """\
            # Contract Sync

            This folder stores the synced contract package from `learning-content-specifier`.

            Required files:
            - `contracts/index.json`
            - `contracts/schemas/*.schema.json`
            - `contracts/docs/*.md`
            - `contracts/fixtures/*.json`
            """
        ),
        "integration-manifest.md": textwrap.dedent(
            f"""\
            # Consumer Integration Manifest (v1)

            ## Role
            `lcs-output-consumer` is the library backbone between Factory and Apps.

            ## Upstream dependency
            - Source repo: `learning-content-specifier`
            - Required contract version pin: `{contracts_version}`

            ## Required checks
            1. Contract checksum verification.
            2. Contract major compatibility check.
            3. Manifest-first ingestion policy.

            ## Downstream
            Apps (teacher/learner) MUST consume via BFF and MUST NOT path-guess artifacts.
            """
        ),
        "src/lcs_output_consumer/__init__.py": "__all__ = [\"main\"]\n",
        "src/lcs_output_consumer/main.py": textwrap.dedent(
            """\
            from fastapi import FastAPI

            app = FastAPI(title="lcs-output-consumer", version="0.1.0")


            @app.get("/healthz")
            async def healthz() -> dict[str, str]:
                return {"status": "ok"}


            @app.post("/v1/ingestions/fs")
            async def ingest_fs(payload: dict) -> dict:
                return {"status": "accepted", "payload": payload}


            @app.post("/v1/validations/unit")
            async def validate_unit(payload: dict) -> dict:
                return {"status": "accepted", "payload": payload}


            @app.get("/v1/units")
            async def list_units() -> dict:
                return {"items": []}


            @app.get("/v1/units/{unit_id}")
            async def get_unit(unit_id: str) -> dict:
                return {"unit_id": unit_id}


            @app.get("/v1/units/{unit_id}/manifest")
            async def get_manifest(unit_id: str) -> dict:
                return {"unit_id": unit_id, "manifest": {}}


            @app.get("/v1/units/{unit_id}/gates")
            async def get_gates(unit_id: str) -> dict:
                return {"unit_id": unit_id, "decision": "BLOCK"}


            @app.get("/v1/units/{unit_id}/artifacts")
            async def get_artifacts(unit_id: str) -> dict:
                return {"unit_id": unit_id, "items": []}
            """
        ),
        "tests/test_smoke.py": textwrap.dedent(
            """\
            from fastapi.testclient import TestClient
            from src.lcs_output_consumer.main import app

            client = TestClient(app)


            def test_healthz():
                response = client.get("/healthz")
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
            """
        ),
        ".github/workflows/ci.yml": textwrap.dedent(
            """\
            name: CI

            on:
              push:
                branches: ["main"]
              pull_request:

            jobs:
              tests:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - uses: astral-sh/setup-uv@v4
                  - run: uv sync --extra test
                  - run: uv run pytest -q
            """
        ),
        ".github/workflows/release.yml": textwrap.dedent(
            """\
            name: Release

            on:
              push:
                tags:
                  - "v*.*.*"

            jobs:
              package:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - name: Build release zip
                    run: |
                      mkdir -p .genreleases
                      zip -r ".genreleases/lcs-output-consumer-template-${GITHUB_REF_NAME}.zip" . \
                        -x ".git/*" ".venv/*" ".pytest_cache/*" ".genreleases/*"
                  - uses: actions/upload-artifact@v4
                    with:
                      name: consumer-template-${{ github.ref_name }}
                      path: .genreleases/*
            """
        ),
    }
    return files


def scaffold_output_consumer_repo(target: Path, contracts_version: str) -> None:
    files = build_files(contracts_version=contracts_version)
    for relative_path, content in files.items():
        write_file(target, relative_path, content)


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    contracts_version = resolve_contract_version(args.contracts_version, args.contracts_version_file)
    prepare_target(target, force=args.force)
    scaffold_output_consumer_repo(target=target, contracts_version=contracts_version)
    print(f"Scaffold complete: {target}")
    print("Next steps:")
    print(f"  cd {target}")
    print("  cp .env.example .env")
    print("  uv sync --extra test")
    print("  uv run pytest -q")
    print("  uv run uvicorn src.lcs_output_consumer.main:app --reload")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScaffoldError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
