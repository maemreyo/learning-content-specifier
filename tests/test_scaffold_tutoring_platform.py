import argparse
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "factory/scripts/python/scaffold_tutoring_platform.py"
spec = importlib.util.spec_from_file_location("scaffold_tutoring_platform", SCRIPT_PATH)
scaffold_tutoring_platform = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(scaffold_tutoring_platform)


def test_resolve_contract_version_prefers_explicit(tmp_path: Path):
    version_file = tmp_path / "version.txt"
    version_file.write_text("1.0.0\n", encoding="utf-8")
    actual = scaffold_tutoring_platform.resolve_contract_version("2.1.0", str(version_file))
    assert actual == "2.1.0"


def test_resolve_contract_version_reads_fallback_file(tmp_path: Path):
    version_file = tmp_path / "version.txt"
    version_file.write_text("1.3.0\n", encoding="utf-8")
    actual = scaffold_tutoring_platform.resolve_contract_version("", str(version_file))
    assert actual == "1.3.0"


def test_scaffold_creates_expected_structure(tmp_path: Path):
    target = tmp_path / "tutoring-platform"
    scaffold_tutoring_platform.prepare_target(target, force=False)
    scaffold_tutoring_platform.scaffold_tutoring_platform(
        target=target,
        consumer_base_url="https://consumer.example.com",
        contracts_version="1.0.0",
    )

    assert (target / "apps/teacher/app/page.tsx").is_file()
    assert (target / "apps/learner/app/page.tsx").is_file()
    assert (target / "services/bff/src/index.ts").is_file()
    assert (target / "services/workers/src/index.ts").is_file()
    assert (target / "packages/api-client/src/index.ts").is_file()
    assert (target / "infra/supabase/migrations/0001_init.sql").is_file()
    assert (target / "contracts/consumer-contract-version.txt").read_text(encoding="utf-8").strip() == "1.0.0"

    integration_manifest = (target / "integration-manifest.md").read_text(encoding="utf-8")
    assert "https://consumer.example.com" in integration_manifest
    assert "Frontends (`apps/teacher`, `apps/learner`) MUST call BFF only." in integration_manifest


def test_main_fails_for_non_empty_target_without_force(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "tutoring-platform"
    target.mkdir(parents=True)
    (target / "existing.txt").write_text("x", encoding="utf-8")

    args = argparse.Namespace(
        target=str(target),
        consumer_base_url="http://localhost:8000",
        contracts_version="1.0.0",
        contracts_version_file="",
        force=False,
    )
    monkeypatch.setattr(scaffold_tutoring_platform, "parse_args", lambda: args)

    with pytest.raises(scaffold_tutoring_platform.ScaffoldError, match="not empty"):
        scaffold_tutoring_platform.main()
