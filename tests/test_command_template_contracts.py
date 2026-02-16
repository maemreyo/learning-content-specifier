from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMMAND_TEMPLATE_DIR = ROOT / "factory" / "templates" / "commands"
ARGUMENT_HINT_PATTERN = re.compile(r"^\[[^\[\]]+\]$")


def _parse_frontmatter(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise AssertionError(f"{path} is missing YAML frontmatter start marker")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise AssertionError(f"{path} is missing YAML frontmatter end marker")
    payload = yaml.safe_load(parts[1]) or {}
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} frontmatter must parse into an object")
    return payload


def test_command_templates_require_argument_hint_and_description() -> None:
    templates = sorted(COMMAND_TEMPLATE_DIR.glob("*.md"))
    assert templates, "No command templates found"

    for template in templates:
        frontmatter = _parse_frontmatter(template)
        description = frontmatter.get("description")
        hint = frontmatter.get("argument-hint")

        assert isinstance(description, str) and description.strip(), (
            f"{template.name} missing non-empty frontmatter.description"
        )
        assert isinstance(hint, str) and hint.strip(), (
            f"{template.name} missing non-empty frontmatter.argument-hint"
        )
        assert ARGUMENT_HINT_PATTERN.match(hint.strip()), (
            f"{template.name} argument-hint must use bracketed concise format, got: {hint!r}"
        )
