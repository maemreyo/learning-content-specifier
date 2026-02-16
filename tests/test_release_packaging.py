import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / ".genreleases"
VERSION = "v9.9.9-rc.1"


def _cleanup_release_dir() -> None:
    shutil.rmtree(RELEASE_DIR, ignore_errors=True)


def _assert_template_pack_in_zip(zip_path: Path) -> None:
    assert zip_path.is_file(), f"missing package: {zip_path}"
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())
    assert ".lcs/template-pack/v1/catalog.json" in names
    assert ".lcs/config/stage-context-map.v1.json" in names


def _assert_command_frontmatter_in_zip(zip_path: Path, command_path: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        payload = archive.read(command_path).decode("utf-8")
    assert "\nargument-hint:" in payload
    assert "\nscripts:\n" in payload
    assert "\ngate_scripts:\n" in payload


def _assert_command_uses_explicit_stage(zip_path: Path, command_path: str, stage: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        payload = archive.read(command_path).decode("utf-8")
    assert f"--stage {stage}" in payload or f"-Stage {stage}" in payload


@pytest.mark.skipif(os.name == "nt", reason="bash packaging test runs on non-Windows")
def test_create_release_packages_sh_includes_template_pack_catalog() -> None:
    _cleanup_release_dir()
    env = os.environ.copy()
    env["AGENTS"] = "codex"
    env["SCRIPTS"] = "sh"
    env["SKIP_CONTRACT_PACKAGE"] = "1"

    try:
        subprocess.run(
            ["bash", str(ROOT / "tooling/ci/create-release-packages.sh"), VERSION],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        zip_path = RELEASE_DIR / f"learning-content-specifier-template-codex-sh-{VERSION}.zip"
        _assert_template_pack_in_zip(zip_path)
        _assert_command_frontmatter_in_zip(zip_path, ".codex/commands/lcs.design.md")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.rubric.md", "rubric")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.audit.md", "audit")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.author.md", "author")
    finally:
        _cleanup_release_dir()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")
def test_create_release_packages_ps1_includes_template_pack_catalog() -> None:
    _cleanup_release_dir()
    env = os.environ.copy()
    env["SKIP_CONTRACT_PACKAGE"] = "1"

    try:
        subprocess.run(
            [
                "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(ROOT / "tooling/ci/create-release-packages.ps1"),
                "-Version",
                VERSION,
                "-Agents",
                "codex",
                "-Scripts",
                "ps",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        zip_path = RELEASE_DIR / f"learning-content-specifier-template-codex-ps-{VERSION}.zip"
        _assert_template_pack_in_zip(zip_path)
        _assert_command_frontmatter_in_zip(zip_path, ".codex/commands/lcs.design.md")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.rubric.md", "rubric")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.audit.md", "audit")
        _assert_command_uses_explicit_stage(zip_path, ".codex/commands/lcs.author.md", "author")
    finally:
        _cleanup_release_dir()
