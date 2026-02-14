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
def test_template_pack_validator_blocks_matching_features_reuse_forbidden(tmp_path: Path) -> None:
    item_file = tmp_path / "matching-features-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "matching-features.v1",
                "exercise_type": "MATCHING_FEATURES",
                "item": {
                    "item_id": "MF-1",
                    "instructions": "Match each statement (1-6) with the correct expert profile (A-E).",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "features": [
                        {
                            "feature_id": "A",
                            "label": "Ms Rivera",
                            "descriptor": (
                                "Leads teacher coaching cycles and tracks how prompt design affects student "
                                "revision quality over time."
                            ),
                            "feature_type": "person",
                        },
                        {
                            "feature_id": "B",
                            "label": "Mr Khan",
                            "descriptor": (
                                "Prioritizes assessment reliability and requires evidence logs before accepting "
                                "AI-assisted final submissions in class."
                            ),
                            "feature_type": "person",
                        },
                        {
                            "feature_id": "C",
                            "label": "Dr Osei",
                            "descriptor": (
                                "Focuses on curriculum integration and ensures lesson goals define how digital "
                                "tools are used."
                            ),
                            "feature_type": "person",
                        },
                        {
                            "feature_id": "D",
                            "label": "Learning Lab Team",
                            "descriptor": (
                                "Runs comparative pilots to test structured versus unstructured AI support "
                                "across multiple classrooms each term."
                            ),
                            "feature_type": "group",
                        },
                        {
                            "feature_id": "E",
                            "label": "Policy Unit",
                            "descriptor": (
                                "Develops school-wide guidance that balances innovation with transparent marking "
                                "standards, accountability, and implementation clarity."
                            ),
                            "feature_type": "organization",
                        },
                    ],
                    "statements": [
                        {
                            "statement_id": "1",
                            "text": "This profile emphasizes that evidence logs should guide grading decisions.",
                            "match_focus": "evidence",
                        },
                        {
                            "statement_id": "2",
                            "text": "This profile compares two implementation models to measure consistency across classes.",
                            "match_focus": "experience",
                        },
                        {
                            "statement_id": "3",
                            "text": "This profile links digital-tool use directly to lesson aims and curriculum design.",
                            "match_focus": "goal",
                        },
                        {
                            "statement_id": "4",
                            "text": "This profile monitors how teacher prompt choices influence student revision quality.",
                            "match_focus": "challenge",
                        },
                        {
                            "statement_id": "5",
                            "text": "This profile proposes standards that combine innovation and accountability in assessment.",
                            "match_focus": "recommendation",
                        },
                        {
                            "statement_id": "6",
                            "text": "This profile requires stronger reliability checks before final student submissions are accepted.",
                            "match_focus": "opinion",
                        },
                    ],
                    "mapping_policy": {"allow_feature_reuse": False},
                    "answer_map": [
                        {"statement_id": "1", "feature_id": "B"},
                        {"statement_id": "2", "feature_id": "D"},
                        {"statement_id": "3", "feature_id": "C"},
                        {"statement_id": "4", "feature_id": "A"},
                        {"statement_id": "5", "feature_id": "E"},
                        {"statement_id": "6", "feature_id": "B"},
                    ],
                    "explanation": "This fixture intentionally reuses one feature while reuse is forbidden.",
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
    assert any(item["code"] == "TMP_MF_FEATURE_REUSE_FORBIDDEN" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_matching_sentence_endings_reuse_forbidden(tmp_path: Path) -> None:
    item_file = tmp_path / "matching-sentence-endings-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "matching-sentence-endings.v1",
                "exercise_type": "MATCHING_SENTENCE_ENDINGS",
                "item": {
                    "item_id": "MSE-1",
                    "instructions": (
                        "Match each sentence beginning (1-6) with the correct ending (A-G). "
                        "There is one extra ending."
                    ),
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "sentence_starts": [
                        {
                            "start_id": "1",
                            "text": "Schools reported stronger retention when students reviewed feedback logs before redrafting,",
                            "relation_type": "cause_effect",
                        },
                        {
                            "start_id": "2",
                            "text": (
                                "In classes without structured prompting routines, learners often accepted "
                                "generated text too quickly,"
                            ),
                            "relation_type": "condition",
                        },
                        {
                            "start_id": "3",
                            "text": "Weekly coaching reduced quality gaps between classes during the pilot,",
                            "relation_type": "result",
                        },
                        {
                            "start_id": "4",
                            "text": "Policy teams moved away from speed-only metrics in high-stakes grading,",
                            "relation_type": "purpose",
                        },
                        {
                            "start_id": "5",
                            "text": "Pilot comparisons showed stronger gains in structured AI programs,",
                            "relation_type": "evidence",
                        },
                        {
                            "start_id": "6",
                            "text": "Teachers still accepted digital support in drafting under clear evidence rules,",
                            "relation_type": "contrast",
                        },
                    ],
                    "endings": [
                        {
                            "ending_id": "A",
                            "text": "which reduced transfer errors when learners faced unfamiliar question formats later.",
                        },
                        {
                            "ending_id": "B",
                            "text": "so assessment leaders introduced evidence-check checkpoints before final submission.",
                        },
                        {
                            "ending_id": "C",
                            "text": "because modelling rejection of weak suggestions improved decision quality during revision.",
                        },
                        {
                            "ending_id": "D",
                            "text": "and implementation quality became more consistent across different classrooms each week.",
                        },
                        {
                            "ending_id": "E",
                            "text": "which is why they combined product marks with process-evidence requirements.",
                        },
                        {
                            "ending_id": "F",
                            "text": "after data showed unstructured use produced smaller and less stable outcomes.",
                        },
                        {
                            "ending_id": "G",
                            "text": "while some districts postponed device procurement until the following school year.",
                        },
                    ],
                    "mapping_policy": {"allow_ending_reuse": False, "require_distractor": True},
                    "answer_map": [
                        {"start_id": "1", "ending_id": "A"},
                        {"start_id": "2", "ending_id": "C"},
                        {"start_id": "3", "ending_id": "D"},
                        {"start_id": "4", "ending_id": "E"},
                        {"start_id": "5", "ending_id": "B"},
                        {"start_id": "6", "ending_id": "B"},
                    ],
                    "explanation": "This fixture intentionally reuses one ending while reuse is forbidden.",
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
    assert any(item["code"] == "TMP_MSE_ENDING_REUSE_FORBIDDEN" for item in payload["FINDINGS"])


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
def test_template_pack_validator_blocks_note_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "note-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "note-completion.v1",
                "exercise_type": "NOTE_COMPLETION",
                "item": {
                    "item_id": "NOTE-1",
                    "instructions": "Complete the notes using NO MORE THAN TWO WORDS AND/OR A NUMBER.",
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
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "note": {
                        "title": "Pilot implementation notes",
                        "note_text": (
                            "Pilot schools tracked classroom routines over one term. Students who applied an {{1}} "
                            "check before submission produced fewer transfer mistakes in later tasks. Consistency "
                            "improved when teacher support followed a {{2}} schedule, especially in mixed-ability "
                            "classes. Outcome reports also showed that unstructured tool use led to {{3}} gains "
                            "across classrooms. To improve reliability, policy teams required process evidence such "
                            "as {{4}} alongside final product scores in routine assessment cycles."
                        ),
                        "blanks": [
                            {
                                "blank_id": "1",
                                "answer_key": ["evidence", "evidence check"],
                                "rationale": "The passage describes an evidence check routine completed before final submission.",
                                "information_type": "process_step",
                            },
                            {
                                "blank_id": "2",
                                "answer_key": ["very large weekly schedule"],
                                "rationale": "This key is intentionally too long to trigger answer-limit regression behavior.",
                                "information_type": "factual_detail",
                            },
                            {
                                "blank_id": "3",
                                "answer_key": ["smaller", "less consistent"],
                                "rationale": "The comparative finding reports smaller gains for unstructured implementation contexts.",
                                "information_type": "comparison",
                            },
                            {
                                "blank_id": "4",
                                "answer_key": ["revision logs", "logs"],
                                "rationale": "Policy guidance identifies revision logs as required process evidence in scoring.",
                                "information_type": "policy_recommendation",
                            },
                        ],
                    },
                    "explanation": "The fixture intentionally violates answer-length policy for one blank.",
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
    assert any(item["code"] == "TMP_NOTE_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_table_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "table-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "table-completion.v1",
                "exercise_type": "TABLE_COMPLETION",
                "item": {
                    "item_id": "TABLE-1",
                    "instructions": "Complete the table using NO MORE THAN TWO WORDS AND/OR A NUMBER.",
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
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "table": {
                        "title": "Implementation comparison",
                        "columns": ["Classroom model", "Support pattern", "Observed outcome"],
                        "rows": [
                            {
                                "row_id": "A",
                                "cells": [
                                    "Structured pilot",
                                    "{{1}} coaching sessions for teachers",
                                    "More stable transfer performance across tasks",
                                ],
                            },
                            {
                                "row_id": "B",
                                "cells": [
                                    "Unstructured rollout",
                                    "Irregular prompt-quality support",
                                    "{{2}} gains across classes in follow-up tests",
                                ],
                            },
                            {
                                "row_id": "C",
                                "cells": [
                                    "Assessment policy update",
                                    "Process evidence requirement: {{3}}",
                                    "Reliability checks through learner {{4}}",
                                ],
                            },
                        ],
                        "blanks": [
                            {
                                "blank_id": "1",
                                "answer_key": ["weekly"],
                                "rationale": "Teacher support cadence in the successful pilot is identified as weekly.",
                                "information_type": "factual_detail",
                            },
                            {
                                "blank_id": "2",
                                "answer_key": ["very large weekly schedule"],
                                "rationale": "This key is intentionally too long to trigger answer-limit regression behavior.",
                                "information_type": "comparison",
                            },
                            {
                                "blank_id": "3",
                                "answer_key": ["revision logs", "logs"],
                                "rationale": "Policy guidance lists revision logs as required process evidence in marking.",
                                "information_type": "policy_recommendation",
                            },
                            {
                                "blank_id": "4",
                                "answer_key": ["justification", "oral justification"],
                                "rationale": "Learner justification is required to verify AI-assisted decision quality reliably.",
                                "information_type": "result_outcome",
                            },
                        ],
                    },
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
    assert any(item["code"] == "TMP_TABLE_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_flowchart_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "flowchart-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "flowchart-completion.v1",
                "exercise_type": "FLOWCHART_COMPLETION",
                "item": {
                    "item_id": "FLOW-1",
                    "instructions": "Complete the flowchart using NO MORE THAN TWO WORDS AND/OR A NUMBER.",
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
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "flowchart": {
                        "title": "Classroom implementation process",
                        "steps": [
                            {
                                "step_id": "1",
                                "text": "Define lesson goals and set {{1}} checkpoints.",
                                "next_step_id": "2",
                            },
                            {
                                "step_id": "2",
                                "text": "Run teacher support in {{2}} cycles during pilot weeks.",
                                "next_step_id": "3",
                            },
                            {
                                "step_id": "3",
                                "text": "Collect process evidence including {{3}} for each submission.",
                                "next_step_id": "4",
                            },
                            {
                                "step_id": "4",
                                "text": "Require learner {{4}} before final grading decisions.",
                            },
                        ],
                        "blanks": [
                            {
                                "blank_id": "1",
                                "answer_key": ["evidence", "evidence check"],
                                "rationale": "The process begins with evidence checks aligned to lesson goals.",
                                "information_type": "process_step",
                            },
                            {
                                "blank_id": "2",
                                "answer_key": ["very large weekly cycle"],
                                "rationale": "This key is intentionally too long to trigger answer-limit regression behavior.",
                                "information_type": "factual_detail",
                            },
                            {
                                "blank_id": "3",
                                "answer_key": ["revision logs", "logs"],
                                "rationale": "Revision logs are named as required process evidence in policy guidance.",
                                "information_type": "policy_recommendation",
                            },
                            {
                                "blank_id": "4",
                                "answer_key": ["justification", "oral justification"],
                                "rationale": "Learner justification is used to verify reliability of decisions in practice.",
                                "information_type": "result_outcome",
                            },
                        ],
                    },
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
    assert any(item["code"] == "TMP_FLOW_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_diagram_label_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "diagram-label-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "diagram-label-completion.v1",
                "exercise_type": "DIAGRAM_LABEL_COMPLETION",
                "item": {
                    "item_id": "DIAG-1",
                    "instructions": "Complete the diagram labels using NO MORE THAN TWO WORDS AND/OR A NUMBER.",
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
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "diagram": {
                        "title": "School greenhouse water cycle",
                        "diagram_type": "process",
                        "visual_ref": "IMG-1",
                        "label_targets": [
                            {
                                "target_id": "1",
                                "prompt_text": "Rainwater enters the {{1}} tank before filtration.",
                            },
                            {
                                "target_id": "2",
                                "prompt_text": "The system pushes cleaned water through a {{2}} valve.",
                            },
                            {
                                "target_id": "3",
                                "prompt_text": "Sensors log {{3}} to track moisture changes.",
                            },
                            {
                                "target_id": "4",
                                "prompt_text": "Students compare weekly yields on a {{4}} board.",
                            },
                        ],
                        "blanks": [
                            {
                                "blank_id": "1",
                                "answer_key": ["storage", "storage tank"],
                                "rationale": "The source passage identifies storage as the first destination before filtration.",
                                "information_type": "process_step",
                            },
                            {
                                "blank_id": "2",
                                "answer_key": ["very complex control valve schedule"],
                                "rationale": "This key is intentionally too long to trigger answer-limit regression behavior.",
                                "information_type": "factual_detail",
                            },
                            {
                                "blank_id": "3",
                                "answer_key": ["soil data", "data"],
                                "rationale": "Sensor logs are reported as soil data used for weekly monitoring decisions.",
                                "information_type": "result_outcome",
                            },
                            {
                                "blank_id": "4",
                                "answer_key": ["display", "display board"],
                                "rationale": "The comparison stage is tied to a display board used in student review.",
                                "information_type": "policy_recommendation",
                            },
                        ],
                    },
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
    assert any(item["code"] == "TMP_DIAGRAM_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_summary_completion_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "summary-completion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "summary-completion.v1",
                "exercise_type": "SUMMARY_COMPLETION",
                "item": {
                    "item_id": "SUM-1",
                    "instructions": "Complete the summary using NO MORE THAN TWO WORDS.",
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
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "summary": {
                        "title": "Pilot outcomes",
                        "summary_text": (
                            "In structured classrooms, learners improved when they used {{1}} routines, "
                            "teachers had {{2}} support, and policies required {{3}} plus {{4}} checks "
                            "for reliability across implementations."
                        ),
                        "blanks": [
                            {
                                "blank_id": "1",
                                "answer_key": ["very large weekly routine"],
                                "rationale": "This key is intentionally too long to trigger answer-limit behavior.",
                            },
                            {
                                "blank_id": "2",
                                "answer_key": ["weekly"],
                                "rationale": "Teacher support cadence is listed as weekly in the implementation section.",
                            },
                            {
                                "blank_id": "3",
                                "answer_key": ["revision logs"],
                                "rationale": "Policy guidance lists revision logs as required process evidence.",
                            },
                            {
                                "blank_id": "4",
                                "answer_key": ["justification"],
                                "rationale": "Learners provide justification to support reliability of decisions.",
                            },
                        ],
                    },
                    "explanation": "The fixture intentionally violates answer-length policy for one blank.",
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
    assert any(item["code"] == "TMP_SUM_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_short_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "short-answer-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "short-answer.v1",
                "exercise_type": "SHORT_ANSWER",
                "item": {
                    "item_id": "SA-1",
                    "instructions": "Answer the questions using NO MORE THAN TWO WORDS.",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "response_policy": {
                        "max_words": 2,
                        "allow_number": True,
                        "source_constraint": "from_passage",
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "accept_minor_variants",
                    },
                    "questions": [
                        {
                            "question_id": "1",
                            "question": "What routine improved results before final submission?",
                            "answer_key": ["very large weekly routine"],
                            "rationale": "This key is intentionally too long to trigger answer-limit behavior.",
                        },
                        {
                            "question_id": "2",
                            "question": "How often was teacher coaching delivered in stable classes?",
                            "answer_key": ["weekly"],
                            "rationale": "Teacher coaching was delivered weekly in successful implementations.",
                        },
                        {
                            "question_id": "3",
                            "question": "What evidence did policy groups ask schools to store?",
                            "answer_key": ["revision logs"],
                            "rationale": "Policy guidance asked schools to store revision logs.",
                        },
                        {
                            "question_id": "4",
                            "question": "What learner response was used to verify reasoning?",
                            "answer_key": ["justification"],
                            "rationale": "Learner justification was used to verify reasoning in assessment.",
                        },
                    ],
                    "explanation": "The fixture intentionally violates answer-length policy for one question.",
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
    assert any(item["code"] == "TMP_SA_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_open_cloze_answer_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "open-cloze-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "open-cloze.v1",
                "exercise_type": "OPEN_CLOZE",
                "item": {
                    "item_id": "OC-1",
                    "instructions": "Complete each gap with ONE WORD only.",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "cloze_policy": {
                        "max_words": 1,
                        "allow_number": False,
                        "source_constraint": "open_lexical",
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "strict",
                        "blank_notation": "double_curly_numeric",
                    },
                    "passage": {
                        "title": "Controlled rollout",
                        "text": (
                            "Schools found that speed {{1}} was not enough for progress, and teachers met "
                            "{{2}} week to refine prompts. Teams selected strategies {{3}} aligned with goals, "
                            "policy groups emphasized process evidence {{4}} final products, and warned that "
                            "quality drops {{5}} routines are inconsistent across classes, {{6}} leaders should "
                            "monitor implementation regularly."
                        ),
                    },
                    "blanks": [
                        {
                            "blank_id": "1",
                            "answer_key": ["have been"],
                            "rationale": "This answer is intentionally overlong for one-word open-cloze policy.",
                            "grammar_focus": "auxiliary",
                        },
                        {
                            "blank_id": "2",
                            "answer_key": ["each"],
                            "rationale": "A quantifier is needed to modify week in recurring schedules.",
                            "grammar_focus": "quantifier",
                        },
                        {
                            "blank_id": "3",
                            "answer_key": ["that"],
                            "rationale": "A relative pronoun introduces the defining clause on strategies.",
                            "grammar_focus": "relative_pronoun",
                        },
                        {
                            "blank_id": "4",
                            "answer_key": ["not"],
                            "rationale": "Negation marks the contrast with final products only.",
                            "grammar_focus": "discourse_marker",
                        },
                        {
                            "blank_id": "5",
                            "answer_key": ["if"],
                            "rationale": "A conditional conjunction introduces the risk condition.",
                            "grammar_focus": "conjunction",
                        },
                        {
                            "blank_id": "6",
                            "answer_key": ["as"],
                            "rationale": "A conjunction links the final clause with implementation oversight.",
                            "grammar_focus": "conjunction",
                        },
                    ],
                    "explanation": "The fixture intentionally violates one-word policy for blank 1.",
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
    assert any(item["code"] == "TMP_OC_ANSWER_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_word_formation_prompt_unchanged(tmp_path: Path) -> None:
    item_file = tmp_path / "word-formation-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "word-formation.v1",
                "exercise_type": "WORD_FORMATION",
                "item": {
                    "item_id": "WF-1",
                    "instructions": "For each gap, use the word in capitals to form ONE WORD that fits the text.",
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "formation_policy": {
                        "max_words": 1,
                        "allow_number": False,
                        "source_constraint": "derived_from_prompt",
                        "answer_order_policy": "usually_text_order",
                        "case_sensitive": False,
                        "spelling_policy": "strict",
                        "blank_notation": "double_curly_numeric",
                    },
                    "passage": {
                        "title": "From pilots to classroom systems",
                        "text": (
                            "Over the last decade, the {{1}} of digital feedback systems has changed classroom "
                            "routines. At first, many teachers showed {{2}} about automated suggestions because "
                            "early versions were inconsistent. Pilot schools improved results by introducing a "
                            "{{3}} review cycle in which staff checked prompts, learner responses, and follow-up "
                            "tasks each week. This routine reduced {{4}} between classes and made assessment "
                            "decisions more transparent. Students also became more {{5}} when they had to explain "
                            "why a suggestion was accepted or rejected. Researchers note that long-term progress "
                            "depends on consistent {{6}}, not on occasional workshops."
                        ),
                    },
                    "blanks": [
                        {
                            "blank_id": "1",
                            "prompt_word": "EXPAND",
                            "answer_key": ["expansion"],
                            "rationale": "A noun is required after the article in this sentence.",
                            "transformation_type": "suffix",
                        },
                        {
                            "blank_id": "2",
                            "prompt_word": "CAUTIOUS",
                            "answer_key": ["cautious"],
                            "rationale": "This intentionally keeps the prompt unchanged for regression validation coverage.",
                            "transformation_type": "part_of_speech_shift",
                        },
                        {
                            "blank_id": "3",
                            "prompt_word": "SYSTEM",
                            "answer_key": ["systematic"],
                            "rationale": "An adjective modifies review cycle in this context correctly.",
                            "transformation_type": "suffix",
                        },
                        {
                            "blank_id": "4",
                            "prompt_word": "DIFFER",
                            "answer_key": ["differences"],
                            "rationale": "A plural noun is required before between classes in context.",
                            "transformation_type": "suffix",
                        },
                        {
                            "blank_id": "5",
                            "prompt_word": "ACCOUNT",
                            "answer_key": ["accountable"],
                            "rationale": "The comparative frame became more requires an adjective form.",
                            "transformation_type": "suffix",
                        },
                        {
                            "blank_id": "6",
                            "prompt_word": "IMPLEMENT",
                            "answer_key": ["implementation"],
                            "rationale": "A noun is needed after consistent to name the process.",
                            "transformation_type": "suffix",
                        },
                    ],
                    "explanation": "The fixture intentionally keeps one answer equal to its prompt stem.",
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
    assert any(item["code"] == "TMP_WF_PROMPT_UNCHANGED" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_gapped_text_order_policy_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "gapped-text-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "gapped-text.v1",
                "exercise_type": "GAPPED_TEXT",
                "item": {
                    "item_id": "GT-1",
                    "instructions": (
                        "Choose the correct sentence from options A-G for each gap (1-6). "
                        "There is ONE extra sentence."
                    ),
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "gap_policy": {
                        "unit_type": "sentence",
                        "allow_option_reuse": False,
                        "source_constraint": "from_option_bank",
                        "answer_order_policy": "usually_text_order",
                        "require_distractor": True,
                        "blank_notation": "double_curly_numeric",
                    },
                    "passage": {
                        "title": "Why classroom pilots fail without process design",
                        "text": (
                            "School leaders often assume that introducing new digital tools will quickly improve "
                            "performance. {{1}} Teachers in pilot programs reported that early gains appeared only "
                            "after routines were redesigned around lesson goals. They started by mapping where "
                            "students hesitated and then aligned prompts with the reasoning patterns expected in class "
                            "tasks. {{3}} Once this planning stage was complete, teachers met weekly to compare "
                            "evidence and adjust support strategies for different learner groups. The meetings did "
                            "not focus on software features alone or on superficial speed indicators in marking "
                            "dashboards. {{2}} Instead, staff discussed how each prompt affected revision quality, "
                            "explanation depth, and confidence over several weeks. Over time, this process produced "
                            "more stable outcomes across classes and reduced unnecessary workload linked to repeated "
                            "misunderstandings. {{4}} Students also learned to justify why a suggestion was accepted "
                            "or rejected, which strengthened independent thinking and self-monitoring habits. Some "
                            "schools initially skipped this reflection step and expected automation to solve "
                            "implementation gaps without extra coordination. {{5}} Their results were less stable, "
                            "and teachers reported confusion about assessment decisions and inconsistent feedback "
                            "language. Programs became reliable only when leaders connected training, feedback, and "
                            "curriculum goals in one coherent cycle. {{6}} By the end of the year, schools with this "
                            "approach showed stronger retention and clearer evidence of progress across classes."
                        ),
                    },
                    "options": [
                        {
                            "option_id": "A",
                            "text": "As a result, teams stopped treating feedback as a purely technical feature.",
                        },
                        {
                            "option_id": "B",
                            "text": "In contrast, a small group delayed changes until exam season began.",
                        },
                        {
                            "option_id": "C",
                            "text": "This expectation quickly proved unrealistic in most teaching departments initially.",
                        },
                        {
                            "option_id": "D",
                            "text": "At that point, they could identify patterns invisible in isolated lessons.",
                        },
                        {
                            "option_id": "E",
                            "text": (
                                "Consequently, professional development became an ongoing process rather than a "
                                "single workshop."
                            ),
                        },
                        {
                            "option_id": "F",
                            "text": "However, several teams believed that faster marking alone would be enough.",
                        },
                        {
                            "option_id": "G",
                            "text": "That is why the same tool produced very different outcomes at first.",
                        },
                    ],
                    "answer_map": [
                        {"gap_id": "1", "option_id": "C"},
                        {"gap_id": "2", "option_id": "D"},
                        {"gap_id": "3", "option_id": "A"},
                        {"gap_id": "4", "option_id": "G"},
                        {"gap_id": "5", "option_id": "F"},
                        {"gap_id": "6", "option_id": "E"},
                    ],
                    "explanation": "This fixture intentionally violates ascending placeholder order only.",
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
    assert any(item["code"] == "TMP_GT_ORDER_POLICY_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_insert_paragraph_order_policy_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "insert-paragraph-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "insert-paragraph.v1",
                "exercise_type": "INSERT_PARAGRAPH",
                "item": {
                    "item_id": "IP-1",
                    "instructions": (
                        "Look at the four squares [A]-[D] in the paragraph. Insert the sentence in the best position."
                    ),
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "insertion_policy": {
                        "option_count": 4,
                        "allow_multiple_correct": False,
                        "source_constraint": "from_passage",
                        "answer_order_policy": "usually_text_order",
                        "position_id_format": "A-D",
                    },
                    "passage": {
                        "title": "Pilot implementation in school departments",
                        "text": (
                            "School departments often adopt learning tools with strong expectations but uneven planning. "
                            "Leaders usually begin by selecting software, yet early pilot outcomes vary across classes. "
                            "Teachers who align prompts with lesson objectives report fewer revisions and clearer student "
                            "explanations over time. In contrast, teams that treat prompts as isolated shortcuts often "
                            "struggle to maintain consistent assessment decisions. Weekly staff meetings also matter "
                            "because they convert scattered observations into shared criteria for feedback quality and "
                            "task design. As the term continues, departments that combine planning, evidence checks, and "
                            "reflection routines tend to show stronger transfer across unfamiliar writing tasks. By "
                            "midyear, schools that documented each revision decision could compare whether improvements "
                            "came from clearer prompts or from stronger self-check routines. Departments also rotated "
                            "peer observations so teachers could see how the same prompt sequence performed in mixed-"
                            "ability groups, which reduced local bias and improved consistency of grading language. "
                            "Leaders then used monthly moderation reviews to verify that feedback criteria remained "
                            "stable when curricula and assessment tasks changed."
                        ),
                    },
                    "candidate_sentence": (
                        "Without a shared implementation routine, the same tool can produce conflicting classroom results."
                    ),
                    "position_options": [
                        {
                            "position_id": "C",
                            "anchor_hint": "After the contrast between aligned and shortcut prompt use.",
                        },
                        {
                            "position_id": "A",
                            "anchor_hint": "After the opening claim about expectations and planning.",
                        },
                        {
                            "position_id": "B",
                            "anchor_hint": "After the sentence introducing varied pilot outcomes.",
                        },
                        {
                            "position_id": "D",
                            "anchor_hint": "After the sentence describing weekly staff meetings.",
                        },
                    ],
                    "correct_position_id": "B",
                    "explanation": "This fixture intentionally shuffles option order to trigger order-policy validation.",
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
    assert any(item["code"] == "TMP_IP_ORDER_POLICY_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_prose_summary_select_count_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "prose-summary-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "prose-summary.v1",
                "exercise_type": "PROSE_SUMMARY",
                "item": {
                    "item_id": "PS-1",
                    "instructions": (
                        "An introductory sentence for a brief summary of the passage is provided. "
                        "Select the THREE answer choices that express the most important ideas."
                    ),
                    "passage_ref": "P-1",
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "summary_policy": {
                        "select_count": 2,
                        "scoring_policy": "partial_credit",
                        "source_constraint": "from_passage",
                        "answer_order_policy": "not_required",
                    },
                    "prompt": (
                        "The passage explains why implementation routines matter more than tool availability when "
                        "schools adopt AI-supported writing support."
                    ),
                    "choices": [
                        {
                            "choice_id": "A",
                            "text": (
                                "Teachers who align prompts with lesson goals and review cycles produce more "
                                "consistent student outcomes."
                            ),
                        },
                        {
                            "choice_id": "B",
                            "text": "Most schools reduce all teacher workload in the first week after software rollout.",
                        },
                        {
                            "choice_id": "C",
                            "text": (
                                "Weekly evidence-focused meetings help departments convert scattered observations into "
                                "shared feedback criteria."
                            ),
                        },
                        {
                            "choice_id": "D",
                            "text": (
                                "The passage argues that software quality alone is enough to guarantee reliable "
                                "transfer across classes."
                            ),
                        },
                        {
                            "choice_id": "E",
                            "text": (
                                "Programs are more stable when training, evidence checks, and reflection are "
                                "connected in one cycle."
                            ),
                        },
                        {
                            "choice_id": "F",
                            "text": (
                                "The author recommends replacing all formative assessment with automated scoring "
                                "dashboards."
                            ),
                        },
                    ],
                    "correct_choice_ids": ["A", "C", "E"],
                    "option_rationales": [
                        {
                            "choice_id": "A",
                            "is_correct": True,
                            "rationale": "This statement captures the passage core claim about aligned routines.",
                            "trap_type": "none",
                        },
                        {
                            "choice_id": "B",
                            "is_correct": False,
                            "rationale": "The passage does not claim immediate workload reduction after rollout.",
                            "trap_type": "unsupported_inference",
                        },
                        {
                            "choice_id": "C",
                            "is_correct": True,
                            "rationale": "Evidence-focused weekly meetings are presented as a key mechanism.",
                            "trap_type": "none",
                        },
                        {
                            "choice_id": "D",
                            "is_correct": False,
                            "rationale": "The text rejects software-only explanations and stresses implementation design.",
                            "trap_type": "contradiction",
                        },
                        {
                            "choice_id": "E",
                            "is_correct": True,
                            "rationale": "The conclusion highlights integrated cycles of training and reflection.",
                            "trap_type": "none",
                        },
                        {
                            "choice_id": "F",
                            "is_correct": False,
                            "rationale": "This overstates a minor detail and conflicts with the blended view.",
                            "trap_type": "overgeneralization",
                        },
                    ],
                    "explanation": "This fixture intentionally mismatches select_count and correct_choice_ids length.",
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
    assert any(item["code"] == "TMP_PS_SELECT_COUNT_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_email_writing_word_limit(tmp_path: Path) -> None:
    item_file = tmp_path / "email-writing-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "email-writing.v1",
                "exercise_type": "EMAIL_WRITING",
                "item": {
                    "item_id": "EW-1",
                    "instructions": (
                        "Write an email in 75-90 words. Address all required points and "
                        "keep the register consistent."
                    ),
                    "prompt": (
                        "You are helping your school plan a community learning event about responsible AI use. "
                        "Write to the program coordinator to propose one workshop idea, explain why it helps "
                        "students, describe what support teachers need, and request a short planning meeting next week."
                    ),
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                    },
                    "task_profile": {
                        "register": "semi_formal",
                        "target_reader": "Program coordinator",
                        "purpose": "Propose event design and coordination needs",
                        "required_points": [
                            {"point_id": "P1", "requirement": "Propose one workshop idea for the event"},
                            {"point_id": "P2", "requirement": "Explain why the workshop helps students"},
                            {"point_id": "P3", "requirement": "Describe what support teachers need"},
                            {"point_id": "P4", "requirement": "Request a short planning meeting next week"},
                        ],
                        "word_limit_min": 75,
                        "word_limit_max": 90,
                        "required_greeting": "Dear Ms Patel",
                        "required_signoff": "Best regards",
                        "allow_bullets": False,
                    },
                    "reference_emails": [
                        {
                            "email_id": "A",
                            "subject_line": "Workshop idea for the AI learning event",
                            "body": (
                                "Dear Ms Patel, I suggest a workshop where students compare AI answers and decide "
                                "which one is more reliable. This would help them practise checking evidence "
                                "instead of accepting fast results. Teachers need a shared checklist, short training "
                                "notes, and one model lesson plan. Could we meet next Tuesday to confirm the "
                                "schedule and assign tasks? I can prepare sample materials before the session. "
                                "Please tell me if I should collect class examples too. Best regards, Minh"
                            ),
                            "covered_point_ids": ["P1", "P2", "P3", "P4"],
                        },
                        {
                            "email_id": "B",
                            "subject_line": "Planning support for the community AI session",
                            "body": (
                                "Dear Ms Patel, For the event, I suggest a workshop on improving prompts and "
                                "evaluating responses with clear criteria. Students would benefit because better "
                                "prompts usually produce stronger reasoning and fewer mistakes. Teachers will need "
                                "printed rubrics, sample responses, and a short briefing so each class uses the same "
                                "process. Could we arrange a short meeting next Wednesday to finalise roles and "
                                "timing, agree budget priorities, assign facilitation leads, review printed "
                                "resources, and confirm communication steps for parents and partner groups? I can "
                                "share a draft agenda in advance and coordinate volunteers for setup. Best regards, Minh"
                            ),
                            "covered_point_ids": ["P1", "P2", "P3", "P4"],
                        },
                    ],
                    "scoring_rubric": {
                        "task_achievement": "Response addresses all required points with clear purpose.",
                        "coherence_and_cohesion": "Ideas are logically sequenced with effective linking.",
                        "lexical_resource": "Vocabulary is appropriate for topic and register.",
                        "grammatical_range_accuracy": "Sentence control is accurate with sufficient variation.",
                        "register_control": "Tone and style remain consistent with a semi-formal email.",
                    },
                    "explanation": "This fixture intentionally exceeds configured word limit in one reference.",
                    "lo_refs": ["LO1"],
                    "difficulty": "easy",
                },
            }
        ),
        encoding="utf-8",
    )

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_EMAIL_WORD_LIMIT_EXCEEDED" for item in payload["FINDINGS"])


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
