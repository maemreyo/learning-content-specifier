import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT.parent / "subjects" / "english" / ".lcs" / "template-pack" / "v1"
VALIDATOR = PACK_DIR / "validators" / "validate_template_pack.py"
VALID_EXAMPLES_DIR = PACK_DIR / "examples" / "valid"
REGRESSION_EXAMPLES_DIR = PACK_DIR / "examples" / "regression"


def _run_validator(item_file: Path) -> tuple[int, dict]:
    cmd = [
        "python3",
        str(VALIDATOR),
        "--template-pack-dir",
        str(PACK_DIR),
        "--item-file",
        str(item_file),
        "--json",
    ]
    result = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout.strip())


def _load_schema_for_item(item_file: Path) -> dict:
    payload = json.loads(item_file.read_text(encoding="utf-8"))
    template_id = payload["template_id"]
    schema_file = PACK_DIR / "schemas" / f"{template_id}.schema.json"
    return json.loads(schema_file.read_text(encoding="utf-8"))


@pytest.mark.skipif(not PACK_DIR.is_dir(), reason="english template pack missing")
def test_all_valid_examples_pass_schema_and_semantic_validator() -> None:
    valid_files = sorted(VALID_EXAMPLES_DIR.glob("*.json"))
    assert valid_files, "No valid template examples found"

    for item_file in valid_files:
        payload = json.loads(item_file.read_text(encoding="utf-8"))
        schema = _load_schema_for_item(item_file)
        errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=str)
        assert not errors, f"Schema failed for {item_file.name}: {errors[0]}"

        code, validator_payload = _run_validator(item_file)
        assert code == 0, f"Validator failed for valid example: {item_file.name}"
        assert validator_payload["STATUS"] == "PASS"
        assert not any(
            finding["severity"] in {"CRITICAL", "HIGH"} for finding in validator_payload.get("FINDINGS", [])
        ), f"Unexpected blocking finding for valid example: {item_file.name}"


@pytest.mark.skipif(not PACK_DIR.is_dir(), reason="english template pack missing")
@pytest.mark.parametrize(
    ("filename", "expected_status", "expected_code", "expected_return_code"),
    [
        ("mcq.duplicate-distractor.json", "BLOCK", "TMP_MCQ_DUP_DISTRACTOR", 1),
        ("tfng.not-given-direct-evidence.json", "PASS", "TMP_TFNG_NOT_GIVEN_EVIDENCE", 0),
        ("sentence-rewrite.single-reference.json", "BLOCK", "TMP_REWRITE_REFERENCE_MIN", 1),
    ],
)
def test_regression_examples_hold_expected_validator_behavior(
    filename: str,
    expected_status: str,
    expected_code: str,
    expected_return_code: int,
) -> None:
    item_file = REGRESSION_EXAMPLES_DIR / filename
    assert item_file.is_file(), f"Missing regression fixture: {filename}"

    code, payload = _run_validator(item_file)
    assert code == expected_return_code
    assert payload["STATUS"] == expected_status
    assert any(item["code"] == expected_code for item in payload["FINDINGS"])
