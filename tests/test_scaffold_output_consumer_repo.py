import argparse
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "factory/scripts/python/scaffold_output_consumer_repo.py"
spec = importlib.util.spec_from_file_location("scaffold_output_consumer_repo", SCRIPT_PATH)
scaffold_output_consumer_repo = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(scaffold_output_consumer_repo)


def test_resolve_contract_version_from_fallback_file(tmp_path: Path):
    version_file = tmp_path / "version.txt"
    version_file.write_text("1.2.0\n", encoding="utf-8")
    assert scaffold_output_consumer_repo.resolve_contract_version("", str(version_file)) == "1.2.0"


def test_scaffold_output_consumer_repo_creates_expected_files(tmp_path: Path):
    target = tmp_path / "lcs-output-consumer"
    scaffold_output_consumer_repo.prepare_target(target, force=False)
    scaffold_output_consumer_repo.scaffold_output_consumer_repo(target=target, contracts_version="1.0.0")

    assert (target / "src/lcs_output_consumer/main.py").is_file()
    assert (target / "tests/test_smoke.py").is_file()
    assert (target / "contracts/consumer-contract-version.txt").read_text(encoding="utf-8").strip() == "1.0.0"
    assert (target / ".github/workflows/ci.yml").is_file()
    assert (target / "integration-manifest.md").is_file()


def test_main_fails_for_non_empty_target_without_force(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "consumer"
    target.mkdir(parents=True)
    (target / "existing.txt").write_text("x", encoding="utf-8")

    args = argparse.Namespace(
        target=str(target),
        contracts_version="1.0.0",
        contracts_version_file="",
        force=False,
    )
    monkeypatch.setattr(scaffold_output_consumer_repo, "parse_args", lambda: args)

    with pytest.raises(scaffold_output_consumer_repo.ScaffoldError, match="not empty"):
        scaffold_output_consumer_repo.main()
