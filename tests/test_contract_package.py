import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "contracts" / "index.json"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_contract_index_checksums_are_in_sync():
    payload = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    entries = payload["entries"]

    for group_name in ("schemas", "docs_digest", "fixtures"):
        assert entries[group_name], f"{group_name} must not be empty"
        for item in entries[group_name]:
            rel = item["path"]
            path = ROOT / rel
            assert path.is_file(), f"missing indexed file: {rel}"
            assert item["sha256"] == _sha256_file(path), f"checksum mismatch for {rel}"


def test_contract_index_manifest_first_policy_is_enabled():
    payload = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    compatibility = payload["compatibility"]
    assert compatibility["manifest_first_required"] is True
    assert "xapi" in compatibility["interop_required"]


def test_contract_package_verify_script_passes():
    cmd = ["uv", "run", "python", str(ROOT / "factory/scripts/python/build_contract_package.py"), "--verify"]
    result = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    assert "Contract index verification passed" in result.stdout


def test_contract_package_build_zip_contains_required_entries(tmp_path: Path):
    version = "v9.9.9"
    cmd = [
        "uv",
        "run",
        "python",
        str(ROOT / "factory/scripts/python/build_contract_package.py"),
        "--verify",
        "--package-version",
        version,
        "--output-dir",
        str(tmp_path),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)

    zip_path = tmp_path / f"lcs-contracts-{version}.zip"
    assert zip_path.is_file(), f"missing package: {zip_path}"

    with zipfile.ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

    assert "contracts/index.json" in names
    assert "contracts/schemas/manifest.schema.json" in names
    assert "contracts/docs/CONSUMER-API-V1.md" in names
    assert "contracts/fixtures/golden_path_snapshot.json" in names
