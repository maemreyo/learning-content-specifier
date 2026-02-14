import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT.parent / "subjects" / "english" / ".lcs" / "template-pack" / "v1"
VALIDATOR = PACK_DIR / "validators" / "validate_template_pack.py"


def _run_validator(item_file: Path) -> dict:
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


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_mcq_duplicate_distractor(tmp_path: Path) -> None:
    item_file = tmp_path / "mcq-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "mcq.v1",
                "exercise_type": "MCQ",
                "item": {
                    "item_id": "MCQ-1",
                    "prompt": "Choose the correct word.",
                    "choices": [
                        {"choice_id": "A", "text": "alpha"},
                        {"choice_id": "B", "text": "alpha"},
                        {"choice_id": "C", "text": "gamma"},
                        {"choice_id": "D", "text": "delta"},
                    ],
                    "correct_choice_id": "A",
                    "explanation": "A is correct.",
                    "lo_refs": ["LO1"],
                    "difficulty": "medium",
                },
            }
        ),
        encoding="utf-8",
    )

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_MCQ_DUP_DISTRACTOR" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_warns_tfng_not_given_direct_evidence(tmp_path: Path) -> None:
    item_file = tmp_path / "tfng-warning.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "tfng.v1",
                "exercise_type": "TFNG",
                "item": {
                    "item_id": "TFNG-1",
                    "passage_ref": "P-1",
                    "statement": "The article says all students pass.",
                    "label": "NOT_GIVEN",
                    "evidence_hint": "According to the text in paragraph 3, this is stated.",
                    "lo_refs": ["LO1"],
                    "difficulty": "medium",
                },
            }
        ),
        encoding="utf-8",
    )

    code, payload = _run_validator(item_file)
    assert code == 0
    assert payload["STATUS"] == "PASS"
    assert any(item["code"] == "TMP_TFNG_NOT_GIVEN_EVIDENCE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_sentence_rewrite_with_one_reference(tmp_path: Path) -> None:
    item_file = tmp_path / "rewrite-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "sentence-rewrite.v1",
                "exercise_type": "SENTENCE_REWRITE",
                "item": {
                    "item_id": "SR-1",
                    "source_sentence": "People believed it was true.",
                    "constraint": "Use believed.",
                    "reference_answers": ["It was believed true."],
                    "scoring_rubric": {
                        "grammar": "Correct grammar.",
                        "meaning_preservation": "Keep meaning.",
                        "constraint_following": "Use keyword.",
                    },
                    "lo_refs": ["LO1"],
                    "difficulty": "medium",
                },
            }
        ),
        encoding="utf-8",
    )

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_REWRITE_REFERENCE_MIN" for item in payload["FINDINGS"])
