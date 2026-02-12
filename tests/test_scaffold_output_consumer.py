import json
import io
import importlib.util
import argparse
import hashlib
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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buf.getvalue()


def _contract_zip(contract_version: str = "1.0.0") -> bytes:
    schema_content = "{}"
    doc_content = "# docs\n"
    fixture_content = "{}"
    index_payload = {
        "contract_version": contract_version,
        "entries": {
            "schemas": [
                {
                    "path": "contracts/schemas/manifest.schema.json",
                    "sha256": hashlib.sha256(schema_content.encode("utf-8")).hexdigest(),
                }
            ],
            "docs_digest": [
                {
                    "path": "contracts/docs/README.md",
                    "sha256": hashlib.sha256(doc_content.encode("utf-8")).hexdigest(),
                }
            ],
            "fixtures": [
                {
                    "path": "contracts/fixtures/golden.json",
                    "sha256": hashlib.sha256(fixture_content.encode("utf-8")).hexdigest(),
                }
            ],
        },
    }
    return _zip_bytes(
        {
            "contracts/index.json": json.dumps(index_payload),
            "contracts/schemas/manifest.schema.json": schema_content,
            "contracts/docs/README.md": doc_content,
            "contracts/fixtures/golden.json": fixture_content,
        }
    )


def test_bootstrap_main_success_with_mocked_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "consumer"
    consumer_asset = "lcs-output-consumer-template-v0.1.0.zip"
    contracts_asset = "lcs-contracts-v0.1.0.zip"

    consumer_zip = _zip_bytes({"src/lcs_output_consumer/__init__.py": "__all__ = []\n"})
    contracts_zip = _contract_zip("1.0.0")
    checksums = {
        consumer_asset: _sha256_bytes(consumer_zip),
        contracts_asset: _sha256_bytes(contracts_zip),
    }

    args = argparse.Namespace(
        consumer_version="v0.1.0",
        target=str(target),
        contracts_version=None,
        consumer_owner="example",
        consumer_repo="consumer",
        core_owner="example",
        core_repo="core",
        consumer_asset=consumer_asset,
        contracts_asset=contracts_asset,
        consumer_sha256=None,
        contracts_sha256=None,
        allow_missing_checksum=False,
        required_contract_version="1.2.0",
        required_contract_version_file="",
        force=False,
        github_token=None,
    )

    monkeypatch.setattr(bootstrap_consumer, "parse_args", lambda: args)
    monkeypatch.setattr(
        bootstrap_consumer,
        "_fetch_release",
        lambda *_args, **_kwargs: {
            "assets": [
                {"name": consumer_asset, "browser_download_url": "https://example.invalid/consumer.zip"},
                {"name": contracts_asset, "browser_download_url": "https://example.invalid/contracts.zip"},
            ]
        },
    )

    def fake_download(asset_payload: dict, out_file: Path, _headers: dict[str, str]) -> None:
        if asset_payload["name"] == consumer_asset:
            out_file.write_bytes(consumer_zip)
        elif asset_payload["name"] == contracts_asset:
            out_file.write_bytes(contracts_zip)
        else:
            raise AssertionError(f"unexpected asset: {asset_payload['name']}")

    monkeypatch.setattr(bootstrap_consumer, "_download_asset", fake_download)
    monkeypatch.setattr(
        bootstrap_consumer,
        "_resolve_release_checksum",
        lambda _release, asset_name, _headers: checksums.get(asset_name),
    )

    assert bootstrap_consumer.main() == 0
    assert (target / "contracts/index.json").is_file()
    assert (target / "src/lcs_output_consumer/__init__.py").is_file()


def test_bootstrap_main_fails_on_checksum_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "consumer"
    consumer_asset = "lcs-output-consumer-template-v0.1.0.zip"
    contracts_asset = "lcs-contracts-v0.1.0.zip"

    consumer_zip = _zip_bytes({"src/lcs_output_consumer/__init__.py": "__all__ = []\n"})
    contracts_zip = _contract_zip("1.0.0")

    args = argparse.Namespace(
        consumer_version="v0.1.0",
        target=str(target),
        contracts_version=None,
        consumer_owner="example",
        consumer_repo="consumer",
        core_owner="example",
        core_repo="core",
        consumer_asset=consumer_asset,
        contracts_asset=contracts_asset,
        consumer_sha256=None,
        contracts_sha256=None,
        allow_missing_checksum=False,
        required_contract_version="1.0.0",
        required_contract_version_file="",
        force=False,
        github_token=None,
    )

    monkeypatch.setattr(bootstrap_consumer, "parse_args", lambda: args)
    monkeypatch.setattr(
        bootstrap_consumer,
        "_fetch_release",
        lambda *_args, **_kwargs: {
            "assets": [
                {"name": consumer_asset, "browser_download_url": "https://example.invalid/consumer.zip"},
                {"name": contracts_asset, "browser_download_url": "https://example.invalid/contracts.zip"},
            ]
        },
    )
    monkeypatch.setattr(
        bootstrap_consumer,
        "_download_asset",
        lambda asset_payload, out_file, _headers: out_file.write_bytes(
            consumer_zip if asset_payload["name"] == consumer_asset else contracts_zip
        ),
    )
    monkeypatch.setattr(
        bootstrap_consumer,
        "_resolve_release_checksum",
        lambda _release, asset_name, _headers: "0" * 64 if asset_name == contracts_asset else _sha256_bytes(consumer_zip),
    )

    with pytest.raises(bootstrap_consumer.BootstrapError, match="Checksum mismatch"):
        bootstrap_consumer.main()


def test_bootstrap_main_fails_on_contract_major_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "consumer"
    consumer_asset = "lcs-output-consumer-template-v0.1.0.zip"
    contracts_asset = "lcs-contracts-v0.1.0.zip"

    consumer_zip = _zip_bytes({"src/lcs_output_consumer/__init__.py": "__all__ = []\n"})
    contracts_zip = _contract_zip("1.0.0")
    checksums = {
        consumer_asset: _sha256_bytes(consumer_zip),
        contracts_asset: _sha256_bytes(contracts_zip),
    }

    args = argparse.Namespace(
        consumer_version="v0.1.0",
        target=str(target),
        contracts_version=None,
        consumer_owner="example",
        consumer_repo="consumer",
        core_owner="example",
        core_repo="core",
        consumer_asset=consumer_asset,
        contracts_asset=contracts_asset,
        consumer_sha256=None,
        contracts_sha256=None,
        allow_missing_checksum=False,
        required_contract_version="2.0.0",
        required_contract_version_file="",
        force=False,
        github_token=None,
    )

    monkeypatch.setattr(bootstrap_consumer, "parse_args", lambda: args)
    monkeypatch.setattr(
        bootstrap_consumer,
        "_fetch_release",
        lambda *_args, **_kwargs: {
            "assets": [
                {"name": consumer_asset, "browser_download_url": "https://example.invalid/consumer.zip"},
                {"name": contracts_asset, "browser_download_url": "https://example.invalid/contracts.zip"},
            ]
        },
    )
    monkeypatch.setattr(
        bootstrap_consumer,
        "_download_asset",
        lambda asset_payload, out_file, _headers: out_file.write_bytes(
            consumer_zip if asset_payload["name"] == consumer_asset else contracts_zip
        ),
    )
    monkeypatch.setattr(
        bootstrap_consumer,
        "_resolve_release_checksum",
        lambda _release, asset_name, _headers: checksums.get(asset_name),
    )

    with pytest.raises(bootstrap_consumer.BootstrapError, match="Contract major mismatch"):
        bootstrap_consumer.main()
