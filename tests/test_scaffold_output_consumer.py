import json
import importlib.util
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "factory/scripts/python/bootstrap_consumer.py"
spec = importlib.util.spec_from_file_location("bootstrap_consumer", SCRIPT_PATH)
bootstrap_consumer = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(bootstrap_consumer)


def test_extract_first_sha256_parses_hash():
    raw = "sha256  0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  file.zip"
    actual = bootstrap_consumer.extract_first_sha256(raw)
    assert actual == "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def test_extract_first_sha256_returns_none_when_missing():
    assert bootstrap_consumer.extract_first_sha256("no checksum here") is None


def test_verify_contract_index_passes_for_valid_fixture_tree(tmp_path: Path):
    root = tmp_path / "consumer"
    root.mkdir(parents=True)

    (root / "contracts").mkdir()
    (root / "contracts/schemas").mkdir(parents=True)
    (root / "contracts/docs").mkdir(parents=True)
    (root / "contracts/fixtures").mkdir(parents=True)

    schema_file = root / "contracts/schemas/manifest.schema.json"
    schema_file.write_text("{}", encoding="utf-8")
    doc_file = root / "contracts/docs/README.md"
    doc_file.write_text("# doc", encoding="utf-8")
    fixture_file = root / "contracts/fixtures/golden.json"
    fixture_file.write_text("{}", encoding="utf-8")

    index_payload = {
        "entries": {
            "schemas": [
                {"path": "contracts/schemas/manifest.schema.json", "sha256": bootstrap_consumer.sha256_file(schema_file)}
            ],
            "docs_digest": [
                {"path": "contracts/docs/README.md", "sha256": bootstrap_consumer.sha256_file(doc_file)}
            ],
            "fixtures": [
                {"path": "contracts/fixtures/golden.json", "sha256": bootstrap_consumer.sha256_file(fixture_file)}
            ],
        }
    }
    (root / "contracts/index.json").write_text(json.dumps(index_payload), encoding="utf-8")

    bootstrap_consumer.verify_contract_index(root)


def test_verify_contract_index_raises_when_checksum_mismatch(tmp_path: Path):
    root = tmp_path / "consumer"
    (root / "contracts/schemas").mkdir(parents=True)
    (root / "contracts/docs").mkdir(parents=True)
    (root / "contracts/fixtures").mkdir(parents=True)

    schema_file = root / "contracts/schemas/manifest.schema.json"
    schema_file.write_text("{}", encoding="utf-8")
    (root / "contracts/index.json").write_text(
        json.dumps(
            {
                "entries": {
                    "schemas": [{"path": "contracts/schemas/manifest.schema.json", "sha256": "0" * 64}],
                    "docs_digest": [],
                    "fixtures": [],
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(bootstrap_consumer.BootstrapError):
        bootstrap_consumer.verify_contract_index(root)


def test_extract_zip_unpacks_archive(tmp_path: Path):
    zip_path = tmp_path / "sample.zip"
    target = tmp_path / "out"
    target.mkdir()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("contracts/index.json", "{}")

    bootstrap_consumer._extract_zip(zip_path, target)
    assert (target / "contracts/index.json").is_file()
