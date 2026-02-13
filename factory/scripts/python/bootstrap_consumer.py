#!/usr/bin/env python3
"""Bootstrap lcs-output-consumer from release assets (consumer template + contracts package)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx


CHECKSUM_SIDECAR_SUFFIXES = (".sha256", ".sha256sum", ".sha256.txt")
SEMVER_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
SEMVER_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_CONSUMER_CONTRACT_VERSION_FILE = (
    Path(__file__).resolve().parents[3] / "contracts" / "consumer-contract-version.txt"
)


class BootstrapError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumer-version", required=True, help="Consumer release tag (vX.Y.Z)")
    parser.add_argument("--target", required=True, help="Target directory for bootstrap")
    parser.add_argument("--contracts-version", help="Contracts release tag (default: consumer-version)")
    parser.add_argument("--consumer-owner", default=os.getenv("LCS_CONSUMER_REPO_OWNER", "maemreyo"))
    parser.add_argument("--consumer-repo", default=os.getenv("LCS_CONSUMER_REPO_NAME", "lcs-output-consumer"))
    parser.add_argument("--core-owner", default=os.getenv("LCS_CORE_REPO_OWNER", "maemreyo"))
    parser.add_argument("--core-repo", default=os.getenv("LCS_CORE_REPO_NAME", "learning-content-specifier"))
    parser.add_argument("--consumer-asset", help="Consumer template asset name")
    parser.add_argument("--contracts-asset", help="Contracts package asset name")
    parser.add_argument("--consumer-sha256", help="Expected SHA256 for consumer asset")
    parser.add_argument("--contracts-sha256", help="Expected SHA256 for contracts asset")
    parser.add_argument("--allow-missing-checksum", action="store_true", help="Allow download when no checksum sidecar is found")
    parser.add_argument(
        "--required-contract-version",
        default=os.getenv("LCS_REQUIRED_CONTRACT_VERSION"),
        help="Required consumer contract semver (X.Y.Z); major must match downloaded contract index",
    )
    parser.add_argument(
        "--required-contract-version-file",
        default=str(DEFAULT_CONSUMER_CONTRACT_VERSION_FILE),
        help="Fallback file for required consumer contract version when --required-contract-version is not provided",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite non-empty target directory")
    parser.add_argument("--github-token", default=os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    _assert_tag(args.consumer_version)
    contracts_version = args.contracts_version or args.consumer_version
    _assert_tag(contracts_version)
    required_contract_version = _resolve_required_contract_version(
        args.required_contract_version,
        args.required_contract_version_file,
    )

    target = Path(args.target).expanduser().resolve()
    _prepare_target(target, force=args.force)

    consumer_asset = args.consumer_asset or f"lcs-output-consumer-template-{args.consumer_version}.zip"
    contracts_asset = args.contracts_asset or f"lcs-contracts-{contracts_version}.zip"

    headers = _auth_headers(args.github_token)

    with tempfile.TemporaryDirectory(prefix="lcs-bootstrap-") as temp_dir:
        temp_root = Path(temp_dir)
        consumer_zip = temp_root / consumer_asset
        contracts_zip = temp_root / contracts_asset

        consumer_release = _fetch_release(args.consumer_owner, args.consumer_repo, args.consumer_version, headers)
        contracts_release = _fetch_release(args.core_owner, args.core_repo, contracts_version, headers)

        consumer_asset_payload = _find_asset(consumer_release, consumer_asset)
        contracts_asset_payload = _find_asset(contracts_release, contracts_asset)

        _download_asset(consumer_asset_payload, consumer_zip, headers)
        _download_asset(contracts_asset_payload, contracts_zip, headers)

        consumer_expected_sha = args.consumer_sha256 or _resolve_release_checksum(
            consumer_release,
            consumer_asset,
            headers,
        )
        contracts_expected_sha = args.contracts_sha256 or _resolve_release_checksum(
            contracts_release,
            contracts_asset,
            headers,
        )

        _verify_or_raise(
            label="consumer asset",
            file_path=consumer_zip,
            expected_sha=consumer_expected_sha,
            allow_missing=args.allow_missing_checksum,
        )
        _verify_or_raise(
            label="contracts asset",
            file_path=contracts_zip,
            expected_sha=contracts_expected_sha,
            allow_missing=args.allow_missing_checksum,
        )

        _extract_zip(consumer_zip, target)
        _extract_zip(contracts_zip, target)

    verify_contract_index(target)
    verify_contract_major_compatibility(target, required_contract_version)

    print(f"Bootstrap complete: {target}")
    print("Next steps:")
    print(f"  cd {target}")
    print("  uv sync")
    print("  uv run uvicorn lcs_output_consumer.main:app --reload")
    return 0


def _assert_tag(tag: str) -> None:
    if not SEMVER_TAG_PATTERN.match(tag):
        raise BootstrapError(f"Invalid tag format '{tag}', expected vX.Y.Z")


def _resolve_required_contract_version(explicit_value: str | None, fallback_file: str | None) -> str:
    candidate = (explicit_value or "").strip()
    if not candidate and fallback_file:
        fallback_path = Path(fallback_file).expanduser().resolve()
        if fallback_path.is_file():
            candidate = fallback_path.read_text(encoding="utf-8").strip()

    if not candidate:
        raise BootstrapError(
            "Missing required contract version. Provide --required-contract-version "
            "or maintain contracts/consumer-contract-version.txt."
        )

    if not SEMVER_VERSION_PATTERN.match(candidate):
        raise BootstrapError(f"Invalid required contract version '{candidate}', expected X.Y.Z")

    return candidate


def _prepare_target(target: Path, force: bool) -> None:
    if target.exists() and any(target.iterdir()):
        if not force:
            raise BootstrapError(f"Target directory is not empty: {target} (use --force)")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def _auth_headers(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _fetch_release(owner: str, repo: str, tag: str, headers: dict[str, str]) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
    if response.status_code != 200:
        raise BootstrapError(f"Failed to fetch release {owner}/{repo}@{tag}: HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        raise BootstrapError(f"Invalid release JSON payload for {owner}/{repo}@{tag}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BootstrapError(f"Unexpected release payload type for {owner}/{repo}@{tag}")
    return payload


def _find_asset(release_payload: dict, asset_name: str) -> dict:
    assets = release_payload.get("assets", [])
    if not isinstance(assets, list):
        raise BootstrapError("Release payload missing valid assets list")
    for asset in assets:
        if isinstance(asset, dict) and asset.get("name") == asset_name:
            return asset
    raise BootstrapError(f"Release asset not found: {asset_name}")


def _download_asset(asset_payload: dict, out_file: Path, headers: dict[str, str]) -> None:
    url = asset_payload.get("browser_download_url")
    if not isinstance(url, str) or not url:
        raise BootstrapError(f"Asset missing browser_download_url: {asset_payload.get('name')}")

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
    if response.status_code != 200:
        raise BootstrapError(f"Failed to download asset {asset_payload.get('name')}: HTTP {response.status_code}")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(response.content)


def _resolve_release_checksum(release_payload: dict, asset_name: str, headers: dict[str, str]) -> str | None:
    assets = release_payload.get("assets", [])
    if not isinstance(assets, list):
        return None

    lookup = {asset.get("name"): asset for asset in assets if isinstance(asset, dict)}
    for suffix in CHECKSUM_SIDECAR_SUFFIXES:
        sidecar_name = f"{asset_name}{suffix}"
        sidecar = lookup.get(sidecar_name)
        if not isinstance(sidecar, dict):
            continue
        url = sidecar.get("browser_download_url")
        if not isinstance(url, str) or not url:
            continue
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
        if response.status_code != 200:
            continue
        checksum = extract_first_sha256(response.text)
        if checksum:
            return checksum

    return None


def extract_first_sha256(raw_text: str) -> str | None:
    match = re.search(r"\b([a-fA-F0-9]{64})\b", raw_text)
    if not match:
        return None
    return match.group(1).lower()


def _verify_or_raise(label: str, file_path: Path, expected_sha: str | None, allow_missing: bool) -> None:
    actual = sha256_file(file_path)
    if expected_sha is None:
        if allow_missing:
            print(f"Warning: no checksum provided for {label}; computed sha256={actual}")
            return
        raise BootstrapError(f"Missing checksum for {label}. Provide --*sha256 or release sidecar asset.")

    normalized = expected_sha.lower()
    if not re.fullmatch(r"[a-f0-9]{64}", normalized):
        raise BootstrapError(f"Invalid expected checksum format for {label}: {expected_sha}")
    if actual != normalized:
        raise BootstrapError(f"Checksum mismatch for {label}: expected {normalized}, got {actual}")


def _extract_zip(zip_path: Path, target: Path) -> None:
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(target)
    except zipfile.BadZipFile as exc:
        raise BootstrapError(f"Invalid zip archive: {zip_path}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_contract_index(target_root: Path) -> None:
    index_path = target_root / "contracts/index.json"
    if not index_path.is_file():
        raise BootstrapError(f"Missing contracts index after bootstrap: {index_path}")

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    entries = payload.get("entries", {})

    for group in ("schemas", "docs_digest", "fixtures"):
        values = entries.get(group, [])
        if not isinstance(values, list):
            raise BootstrapError(f"contracts/index.json invalid entries.{group}")

        for item in values:
            if not isinstance(item, dict):
                raise BootstrapError(f"contracts/index.json invalid entry in {group}")
            rel = item.get("path")
            sha = item.get("sha256")
            if not isinstance(rel, str) or not rel:
                raise BootstrapError(f"contracts/index.json missing path in {group}")
            if not isinstance(sha, str) or not sha:
                raise BootstrapError(f"contracts/index.json missing sha256 for {rel}")

            file_path = target_root / rel
            if not file_path.is_file():
                raise BootstrapError(f"contract entry file missing: {rel}")
            actual = sha256_file(file_path)
            if actual != sha:
                raise BootstrapError(f"contract entry checksum mismatch: {rel}")


def _semver_major(version: str) -> int:
    if not SEMVER_VERSION_PATTERN.match(version):
        raise BootstrapError(f"Invalid semver value '{version}', expected X.Y.Z")
    return int(version.split(".", 1)[0])


def verify_contract_major_compatibility(target_root: Path, required_contract_version: str) -> None:
    index_path = target_root / "contracts/index.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    package_contract_version = payload.get("contract_version")
    if not isinstance(package_contract_version, str):
        raise BootstrapError("contracts/index.json missing contract_version")

    required_major = _semver_major(required_contract_version)
    package_major = _semver_major(package_contract_version)

    if required_major != package_major:
        raise BootstrapError(
            f"Contract major mismatch: required={required_contract_version} package={package_contract_version}"
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
