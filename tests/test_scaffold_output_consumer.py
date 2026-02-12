import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/scaffold_output_consumer.py"


def test_scaffold_creates_repo_with_contract_assets(tmp_path: Path):
    target = tmp_path / "lcs-output-consumer"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--target", str(target)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Scaffold created at" in result.stdout
    assert (target / "pyproject.toml").is_file()
    assert (target / "lcs_output_consumer/main.py").is_file()
    assert (target / "contracts/index.json").is_file()
    assert (target / "schemas/manifest.schema.json").is_file()
    assert (target / "docs/contract/CONSUMER-API-V1.md").is_file()
    assert (target / "fixtures/contracts/golden_path_snapshot.json").is_file()


def test_scaffold_requires_force_for_existing_non_empty_target(tmp_path: Path):
    target = tmp_path / "lcs-output-consumer"
    target.mkdir(parents=True)
    (target / "keep.txt").write_text("existing", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--target", str(target)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Use --force to overwrite" in result.stderr
