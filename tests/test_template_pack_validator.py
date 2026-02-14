import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT.parent / "subjects" / "english" / ".lcs" / "template-pack" / "v1"
VALIDATOR = PACK_DIR / "validators" / "validate_template_pack.py"


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
def test_template_pack_validator_blocks_tfng_not_given_direct_evidence(tmp_path: Path) -> None:
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
                    "claim_profile": {
                        "statement_type": "author_claim",
                        "evidence_basis": "not_addressed",
                        "scope_anchor": "Paragraph 3",
                        "reasoning_path": "The passage discusses outcomes by group but does not confirm this universal claim.",
                        "trap_type": "modifier_shift",
                    },
                    "evidence_hint": "According to the text in paragraph 3, this is stated.",
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
    assert any(item["code"] == "TMP_TFNG_NOT_GIVEN_EVIDENCE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_matching_headings_invalid_mapping(tmp_path: Path) -> None:
    item_file = tmp_path / "matching-headings-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "matching-headings.v1",
                "exercise_type": "MATCHING_HEADINGS",
                "item": {
                    "item_id": "MH-1",
                    "instructions": "Match paragraphs with headings.",
                    "passage_ref": "P-1",
                    "sections": [
                        {
                            "section_id": "A",
                            "text": "Paragraph A explains one main idea about reading strategy transfer.",
                        },
                        {
                            "section_id": "B",
                            "text": "Paragraph B focuses on repeated exposure and vocabulary retention benefits.",
                        },
                        {
                            "section_id": "C",
                            "text": "Paragraph C discusses routines and the impact of consistent daily habits.",
                        },
                    ],
                    "headings": [
                        {"heading_id": "i", "text": "Strategy transfer"},
                        {"heading_id": "ii", "text": "Vocabulary retention"},
                        {"heading_id": "iii", "text": "Habit formation"},
                        {"heading_id": "iv", "text": "Distractor heading"},
                    ],
                    "answer_map": [
                        {"section_id": "A", "heading_id": "i"},
                        {"section_id": "A", "heading_id": "ii"},
                        {"section_id": "B", "heading_id": "v"},
                    ],
                    "explanation": "Invalid mapping for regression.",
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
    assert any(item["code"] == "TMP_MH_SECTION_DUP_MAP" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_matching_information_invalid_mapping(tmp_path: Path) -> None:
    item_file = tmp_path / "matching-information-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "matching-information.v1",
                "exercise_type": "MATCHING_INFORMATION",
                "item": {
                    "item_id": "MI-1",
                    "instructions": "Match each statement with the paragraph that contains the information.",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "sections": [
                        {
                            "section_id": "A",
                            "text": (
                                "Paragraph A explains that speed alone does not indicate deep learning, "
                                "and teachers should evaluate transfer and revision quality in parallel."
                            ),
                        },
                        {
                            "section_id": "B",
                            "text": (
                                "Paragraph B compares structured and unstructured AI classroom use and "
                                "shows stronger gains when evidence-check routines are required."
                            ),
                        },
                        {
                            "section_id": "C",
                            "text": (
                                "Paragraph C links weekly teacher coaching with more stable implementation "
                                "across classes and fewer quality gaps between groups."
                            ),
                        },
                        {
                            "section_id": "D",
                            "text": (
                                "Paragraph D recommends combining process evidence and product grading to "
                                "balance innovation with assessment reliability in practice."
                            ),
                        },
                    ],
                    "statements": [
                        {
                            "statement_id": "1",
                            "text": "A comparison was made between two implementation models.",
                            "information_type": "comparison",
                        },
                        {
                            "statement_id": "2",
                            "text": "Teacher coaching influenced classroom consistency.",
                            "information_type": "reason_cause",
                        },
                        {
                            "statement_id": "3",
                            "text": "A policy recommendation combined process and product evidence.",
                            "information_type": "recommendation",
                        },
                        {
                            "statement_id": "4",
                            "text": "Completion speed was presented as an incomplete measure.",
                            "information_type": "factual_detail",
                        },
                    ],
                    "mapping_policy": {"allow_section_reuse": False},
                    "answer_map": [
                        {"statement_id": "1", "section_id": "B"},
                        {"statement_id": "1", "section_id": "C"},
                        {"statement_id": "2", "section_id": "Z"},
                        {"statement_id": "3", "section_id": "D"},
                    ],
                    "explanation": "Invalid mapping for regression coverage.",
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
    assert any(item["code"] == "TMP_MI_STATEMENT_DUP_MAP" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_sentence_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "sentence-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "sentence-completion.v1",
                "exercise_type": "SENTENCE_COMPLETION",
                "item": {
                    "item_id": "SC-1",
                    "instructions": "Complete each sentence with NO MORE THAN TWO WORDS AND/OR A NUMBER.",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "completion_policy": {
                        "max_words": 2,
                        "allow_number": True,
                        "source_constraint": "from_passage",
                        "blank_token": "____",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "stems": [
                        {
                            "stem_id": "1",
                            "sentence": "Pilot schools scheduled ____ coaching sessions for teachers during the first term.",
                            "answer_key": ["weekly"],
                            "rationale": "The source identifies weekly coaching as the policy used during the pilot term.",
                        },
                        {
                            "stem_id": "2",
                            "sentence": "Learners improved more when they followed an ____ routine before submission.",
                            "answer_key": ["very large weekly routine"],
                            "rationale": "This key is intentionally too long to trigger answer-limit regression behavior.",
                        },
                        {
                            "stem_id": "3",
                            "sentence": "Unstructured AI use produced ____ gains across classes in the comparison study.",
                            "answer_key": ["smaller"],
                            "rationale": "The comparison paragraph describes smaller gains in unstructured adoption groups.",
                        },
                        {
                            "stem_id": "4",
                            "sentence": "Policy guidance recommended keeping revision ____ as process evidence in assessment.",
                            "answer_key": ["logs"],
                            "rationale": "Revision logs are listed as process evidence in the policy recommendation.",
                        },
                    ],
                    "explanation": "The fixture intentionally includes one overlong answer variant for validator coverage.",
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
    assert any(item["code"] == "TMP_SC_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_multiple_response_with_single_correct_choice(tmp_path: Path) -> None:
    item_file = tmp_path / "multiple-response-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "multiple-response.v1",
                "exercise_type": "MULTIPLE_RESPONSE",
                "item": {
                    "item_id": "MR-1",
                    "prompt": "Choose TWO correct ideas.",
                    "choices": [
                        {"choice_id": "A", "text": "Idea A"},
                        {"choice_id": "B", "text": "Idea B"},
                        {"choice_id": "C", "text": "Idea C"},
                        {"choice_id": "D", "text": "Idea D"},
                    ],
                    "correct_choice_ids": ["A"],
                    "explanation": "Only one choice set intentionally.",
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
    assert any(item["code"] == "TMP_MR_CORRECT_MIN" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_multiple_response_without_distractor(tmp_path: Path) -> None:
    item_file = tmp_path / "multiple-response-no-distractor.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "multiple-response.v1",
                "exercise_type": "MULTIPLE_RESPONSE",
                "item": {
                    "item_id": "MR-2",
                    "prompt": "Choose TWO correct ideas.",
                    "choices": [
                        {"choice_id": "A", "text": "Idea A"},
                        {"choice_id": "B", "text": "Idea B"},
                        {"choice_id": "C", "text": "Idea C"},
                        {"choice_id": "D", "text": "Idea D"},
                    ],
                    "correct_choice_ids": ["A", "B", "C", "D"],
                    "explanation": "All choices marked correct intentionally.",
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
    assert any(item["code"] == "TMP_MR_NO_DISTRACTOR" for item in payload["FINDINGS"])


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
                    "constraint_profile": {
                        "required_keyword": "believed",
                        "keyword_must_be_unchanged": True,
                        "output_word_min": 4,
                        "output_word_max": 10,
                        "transformation_focus": "passive_voice",
                        "meaning_anchor": "The rewrite keeps the same claim with a passive structure.",
                    },
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
