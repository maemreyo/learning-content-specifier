import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_framework_registry_fixture_validates_against_schema() -> None:
    fixture = _load(ROOT / "contracts" / "fixtures" / "proficiency.framework-registry.v1.json")
    schema = _load(ROOT / "contracts" / "schemas" / "proficiency.framework-registry.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(fixture), key=str)
    assert not errors, f"Registry fixture schema error: {errors[0]}"


def test_crosswalks_fixture_validates_against_schema() -> None:
    fixture = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")
    schema = _load(ROOT / "contracts" / "schemas" / "proficiency.crosswalks.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(fixture), key=str)
    assert not errors, f"Crosswalk fixture schema error: {errors[0]}"


def test_subject_pivots_fixture_has_english_cefr_pivot() -> None:
    fixture = _load(ROOT / "contracts" / "fixtures" / "proficiency.subject-pivots.v1.json")
    assert fixture.get("pivot_version") == "1.0.0"
    pivots = fixture.get("subject_pivots", {})
    assert isinstance(pivots, dict)
    assert pivots.get("english") == "cefr.v1"

