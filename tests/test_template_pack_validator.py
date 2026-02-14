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
def test_template_pack_validator_blocks_yes_no_not_given_label_evidence_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "yes-no-not-given-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "yes-no-not-given.v1",
                "exercise_type": "YES_NO_NOT_GIVEN",
                "item": {
                    "item_id": "YNNG-1",
                    "passage_ref": "P-1",
                    "statement": "The writer supports replacing teacher moderation with automated scoring in all cases.",
                    "label": "YES",
                    "viewpoint_profile": {
                        "claim_focus": "policy_stance",
                        "evidence_basis": "explicit_disagreement",
                        "scope_anchor": "Paragraph 4",
                        "reasoning_path": (
                            "The writer rejects full automation and keeps teacher moderation in the evaluation process."
                        ),
                        "trap_type": "polarity_shift",
                    },
                    "evidence_hint": (
                        "The passage explicitly states that teachers remain responsible for final moderation "
                        "decisions across all assessed tasks."
                    ),
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
    assert any(item["code"] == "TMP_YNNG_LABEL_EVIDENCE_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_integrated_writing_claim_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "integrated-writing-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "integrated-writing.v1",
                "exercise_type": "INTEGRATED_WRITING",
                "item": {
                    "item_id": "IW-1",
                    "instructions": (
                        "Read the passage, listen to the lecture, then write 150-225 words summarizing the lecture "
                        "and explaining how it relates to the reading."
                    ),
                    "prompt_question": (
                        "Summarize the lecturer's points and explain how they challenge the claims in the reading passage."
                    ),
                    "reading_passage": (
                        "The proposal states that replacing discussion sections with AI tools improves speed, consistency, "
                        "and costs. Administrators believe immediate feedback helps students fix misunderstandings quickly, "
                        "uniform output ensures equal guidance, and automation lowers expenses enough to fund other priorities."
                    ),
                    "lecture_transcript": (
                        "The lecturer disputes all three claims. She says fast comments can still lead to repeated errors, "
                        "uniform output can scale the same mistake to many students, and implementation costs are higher than "
                        "expected once monitoring and appeals are included."
                    ),
                    "task_profile": {
                        "time_limit_minutes": 20,
                        "recommended_word_min": 150,
                        "recommended_word_max": 225,
                        "relation_expectation": "lecture_challenges_reading",
                        "expected_point_count": 3,
                    },
                    "source_alignment": [
                        {
                            "claim_id": "C1",
                            "reading_claim": "Immediate AI feedback improves correction speed.",
                            "lecture_point": "Students repeated errors despite immediate comments.",
                            "relation_type": "contradicts",
                        },
                        {
                            "claim_id": "C2",
                            "reading_claim": "Uniform AI guidance is consistently reliable.",
                            "lecture_point": "Uniform guidance can spread one flawed explanation.",
                            "relation_type": "challenges",
                        },
                        {
                            "claim_id": "C3",
                            "reading_claim": "Automation reduces teaching costs.",
                            "lecture_point": "Support and dispute handling costs removed expected savings.",
                            "relation_type": "refutes",
                        },
                    ],
                    "reference_responses": [
                        {
                            "response_id": "A",
                            "body": (
                                "The lecture argues that the reading overestimates the benefits of AI discussion modules. "
                                "First, quick feedback was not enough to improve understanding, because many students kept "
                                "making the same conceptual mistakes. Second, the lecturer explains that standardized output "
                                "can create standardized error: if one explanation is weak, every student receives that weak "
                                "version. Third, she states that implementation required monitoring and appeal workflows that "
                                "increased operating costs. As a result, the expected financial advantage was not confirmed."
                            ),
                            "covered_claim_ids": ["C1", "C2"],
                        },
                        {
                            "response_id": "B",
                            "body": (
                                "The lecture challenges the reading point by point. It says speed alone is not evidence of "
                                "learning, because students repeated mistakes even with immediate comments. It also says that "
                                "uniform guidance is risky, since one flawed explanation can affect everyone. Finally, it "
                                "rejects the cost argument and reports ongoing expenses for system oversight and disputes. "
                                "These details show the lecture does not support the reading's optimistic conclusion."
                            ),
                            "covered_claim_ids": ["C1", "C2", "C3"],
                        },
                    ],
                    "scoring_rubric": {
                        "content_accuracy": "Capture lecture points accurately.",
                        "source_integration": "Link lecture points to reading claims.",
                        "organization": "Present clear point-by-point structure.",
                        "language_use": "Use grammatically accurate academic English.",
                    },
                    "explanation": "Regression case for claim coverage mismatch.",
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
    assert any(item["code"] == "TMP_IW_CLAIM_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_essay_opinion_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "essay-opinion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "essay-opinion.v1",
                "exercise_type": "ESSAY_OPINION",
                "item": {
                    "item_id": "EO-REG-001",
                    "instructions": (
                        "Write an essay in 250-320 words. Give a clear opinion and support it with specific reasons "
                        "and examples."
                    ),
                    "prompt": (
                        "Some people believe schools should ban smartphone use for students under 16 during school days. "
                        "To what extent do you agree or disagree?"
                    ),
                    "task_profile": {
                        "context_type": "agree_disagree",
                        "stance_requirement": "opinion_required",
                        "register": "neutral_formal",
                        "word_limit_min": 250,
                        "word_limit_max": 320,
                        "time_limit_minutes": 40,
                        "allow_bullets": False,
                        "source_mode": "prompt_only",
                        "required_points": [
                            {
                                "point_id": "P1",
                                "requirement": "State a clear position on the policy (agree/disagree/qualified).",
                            },
                            {
                                "point_id": "P2",
                                "requirement": "Provide one reason linked to learning quality or classroom focus.",
                            },
                            {
                                "point_id": "P3",
                                "requirement": (
                                    "Provide one reason linked to student wellbeing, autonomy, "
                                    "or implementation feasibility."
                                ),
                            },
                        ],
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "Digital-device policy and adolescent learning outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["school smartphone policy", "student focus", "digital wellbeing"],
                    },
                    "reference_essays": [
                        {
                            "essay_id": "A",
                            "position_label": "qualified",
                            "body": (
                                "I partly agree that schools should restrict smartphone use for students under sixteen "
                                "during school days, but a full ban is less effective than a structured policy. In my "
                                "opinion, the main educational reason for limits is attention control. Unrestricted phone "
                                "access creates constant interruption through notifications, social messaging, and "
                                "entertainment loops that compete with instruction time. Even brief checking behavior "
                                "reduces working-memory continuity, so students need longer to return to complex tasks such "
                                "as problem solving and extended reading. However, treating all use as misuse ignores "
                                "legitimate learning functions. Teachers increasingly rely on digital platforms for quizzes, "
                                "feedback, and collaborative activities that can improve participation when used with clear "
                                "boundaries. A second reason is student wellbeing and implementation practicality. "
                                "Supporters of strict bans argue that removing phones lowers anxiety and peer comparison "
                                "pressure. This is often true, but enforcement becomes inconsistent when schools do not "
                                "provide alternatives for communication, safety updates, or supervised digital tasks. "
                                "A policy that stores phones during lessons and allows limited access in defined windows is "
                                "easier to monitor and more realistic for staff and families. Therefore, I believe schools "
                                "should apply strong restrictions, not absolute prohibition. The priority is to design rules "
                                "that protect concentration while still teaching students responsible technology habits before "
                                "they enter less structured environments. Such a model addresses academic risk and social "
                                "development at the same time."
                            ),
                            "covered_point_ids": ["P1", "P2"],
                        },
                        {
                            "essay_id": "B",
                            "position_label": "agree",
                            "body": (
                                "I agree that schools should ban smartphone use for students under sixteen during school "
                                "days because the academic and social costs of constant access are too high. In my view, "
                                "the strongest educational argument is cognitive focus. Adolescents are still developing "
                                "self-regulation, so frequent phone checking during class quickly fragments attention and "
                                "reduces depth of processing. Lessons that require sustained reasoning, such as science "
                                "explanation or essay planning, are especially vulnerable to this pattern. Teachers then "
                                "spend additional time rebuilding focus instead of advancing instruction. A second reason "
                                "concerns wellbeing and school culture. Phone-centered interaction can intensify social "
                                "comparison, exclusion, and online conflict that continues into classroom life. Limiting "
                                "access during school hours reduces immediate exposure to these pressures and creates a "
                                "safer environment for face-to-face participation. Critics argue that smartphones can "
                                "support learning tools, but schools can provide supervised digital resources without "
                                "allowing personal devices throughout the day. They also argue that bans are difficult to "
                                "enforce, yet consistency improves when rules are simple and universal rather than "
                                "negotiable across classes. For these reasons, I believe a school-day ban for younger "
                                "students is justified and practical. It protects instructional quality, supports healthier "
                                "peer interaction, and gives students space to build concentration habits before they are "
                                "expected to manage digital freedom independently in later stages of education."
                            ),
                            "covered_point_ids": ["P1", "P2", "P3"],
                        },
                    ],
                    "scoring_rubric": {
                        "task_response": "Essay states a clear position and addresses all required points with relevant support.",
                        "coherence_and_cohesion": "Ideas are organized logically with clear progression and linking.",
                        "lexical_resource": "Vocabulary is precise and suitable for formal argument writing.",
                        "grammatical_range_accuracy": "Sentence structures are varied and mostly accurate.",
                        "argument_quality": "Reasons are specific, defensible, and connected to the stated position.",
                    },
                    "explanation": "Regression case: reference essay A omits P3 in covered_point_ids.",
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
    assert any(item["code"] == "TMP_EO_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_essay_discussion_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "essay-discussion-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "essay-discussion.v1",
                "exercise_type": "ESSAY_DISCUSSION",
                "item": {
                    "item_id": "ED-1",
                    "instructions": (
                        "Write an essay in 250-320 words. Discuss both views, give your own opinion, "
                        "and support your position with clear reasons and examples."
                    ),
                    "prompt": (
                        "Some universities should replace most in-person tutorial discussions with "
                        "AI-supported study forums. Discuss both views and give your own opinion."
                    ),
                    "task_profile": {
                        "context_type": "discuss_both_views",
                        "stance_requirement": "opinion_required",
                        "register": "neutral_formal",
                        "word_limit_min": 250,
                        "word_limit_max": 320,
                        "time_limit_minutes": 40,
                        "allow_bullets": False,
                        "source_mode": "prompt_only",
                        "required_points": [
                            {"point_id": "P1", "requirement": "Explain one argument supporting replacement."},
                            {"point_id": "P2", "requirement": "Explain one argument against full replacement."},
                            {"point_id": "P3", "requirement": "State and justify your own position."},
                        ],
                    },
                    "reference_essays": [
                        {
                            "essay_id": "A",
                            "position_label": "qualified",
                            "body": (
                                "Many institutions see AI forums as a scalable solution because students can ask routine "
                                "questions at any time and receive immediate responses. This flexibility can reduce waiting "
                                "time and help teachers focus on high-value interventions. However, the core risk is that "
                                "automated explanations can sound convincing while missing the exact reason a learner is "
                                "confused. In live tutorials, instructors adjust examples, challenge weak assumptions, and "
                                "monitor whether students can defend their reasoning. In my opinion, universities should use "
                                "AI forums as supplementary support rather than a full replacement for tutorial dialogue."
                            ),
                            "covered_point_ids": ["P1", "P2"],
                        },
                        {
                            "essay_id": "B",
                            "position_label": "balanced",
                            "body": (
                                "Replacing in-person tutorials with AI forums offers real efficiency benefits, including "
                                "continuous access and consistent baseline guidance for large cohorts. Those strengths are "
                                "useful in administrative and revision contexts. Yet tutorial quality depends on adaptive "
                                "interaction, and that human dimension remains difficult to automate reliably. Tutors can "
                                "identify subtle misunderstandings, probe student logic, and modify discussion pathways in "
                                "real time. I believe a hybrid strategy is more sustainable: preserve in-person tutorials "
                                "for conceptual development while using AI forums for preparatory practice and follow-up."
                            ),
                            "covered_point_ids": ["P1", "P2", "P3"],
                        },
                    ],
                    "scoring_rubric": {
                        "task_response": "Address both views and maintain relevance.",
                        "coherence_and_cohesion": "Organize ideas with clear progression.",
                        "lexical_resource": "Use precise and varied vocabulary.",
                        "grammatical_range_accuracy": "Maintain mostly accurate sentence control.",
                        "argument_quality": "Defend a clear and justified position.",
                    },
                    "explanation": "Regression case for required-point coverage mismatch.",
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
    assert any(item["code"] == "TMP_ED_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_report_visual_data_observation_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "report-visual-data-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "report-visual-data.v1",
                "exercise_type": "REPORT_VISUAL_DATA",
                "item": {
                    "item_id": "RVD-1",
                    "instructions": (
                        "Write a report in 170-230 words. Summarize the key features of the visual data, "
                        "include an overall trend, and make relevant comparisons."
                    ),
                    "prompt": (
                        "The chart compares weekly hours spent on self-study by first-year and final-year students "
                        "between 2021 and 2024. Write a report describing the main trends and differences."
                    ),
                    "visual_dataset": {
                        "visual_id": "VD-1",
                        "visual_type": "line_chart",
                        "title": "Average weekly self-study hours by student cohort (2021-2024)",
                        "timeframe": "2021-2024",
                        "unit": "hours per week",
                        "data_series": [
                            {
                                "series_id": "S1",
                                "label": "First-year students",
                                "points": [
                                    {"x": "2021", "value": 6.5},
                                    {"x": "2022", "value": 7.2},
                                    {"x": "2023", "value": 8.0},
                                    {"x": "2024", "value": 8.7},
                                ],
                            },
                            {
                                "series_id": "S2",
                                "label": "Final-year students",
                                "points": [
                                    {"x": "2021", "value": 8.1},
                                    {"x": "2022", "value": 8.4},
                                    {"x": "2023", "value": 8.9},
                                    {"x": "2024", "value": 9.4},
                                ],
                            },
                        ],
                    },
                    "task_profile": {
                        "report_type": "academic_task1",
                        "register": "neutral_formal",
                        "word_limit_min": 170,
                        "word_limit_max": 230,
                        "time_limit_minutes": 20,
                        "include_overview": True,
                        "include_comparisons": True,
                        "allow_bullets": False,
                        "required_observations": [
                            {"observation_id": "O1", "requirement": "Identify overall trend for both cohorts."},
                            {"observation_id": "O2", "requirement": "Compare values at start and end."},
                            {"observation_id": "O3", "requirement": "Report one notable change in the gap."},
                        ],
                    },
                    "reference_reports": [
                        {
                            "report_id": "A",
                            "body": (
                                "The chart presents weekly self-study time for two cohorts from 2021 to 2024. "
                                "Overall, both groups increased their study hours across the period, while final-year "
                                "students remained higher in every year. First-year values rose from 6.5 to 8.7 hours, "
                                "whereas final-year values increased from 8.1 to 9.4 hours. The pattern shows that both "
                                "series moved upward, but the first-year line climbed more quickly. As a result, the "
                                "difference between groups became narrower over time, indicating partial convergence in "
                                "study behavior by 2024."
                            ),
                            "covered_observation_ids": ["O1", "O2"],
                        },
                        {
                            "report_id": "B",
                            "body": (
                                "The visual compares average weekly self-study hours in two student cohorts over four years. "
                                "In general, both cohorts recorded steady growth, and final-year students studied more than "
                                "first-year students throughout the period. In 2021, the figures were 6.5 and 8.1 hours, "
                                "while by 2024 they reached 8.7 and 9.4 hours respectively. Although both lines rose, the "
                                "increase was stronger for first-year students, which reduced the gap from 1.6 to 0.7 hours. "
                                "Therefore, the key trend is simultaneous growth with a smaller difference over time."
                            ),
                            "covered_observation_ids": ["O1", "O2", "O3"],
                        },
                    ],
                    "scoring_rubric": {
                        "task_achievement": "Select and summarize key features.",
                        "coherence_and_cohesion": "Organize report logically.",
                        "lexical_resource": "Use accurate trend vocabulary.",
                        "grammatical_range_accuracy": "Maintain accurate sentence control.",
                        "data_accuracy": "Keep values and comparisons consistent with dataset.",
                    },
                    "explanation": "Regression case for observation coverage mismatch.",
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
    assert any(item["code"] == "TMP_RVD_OBSERVATION_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_read_aloud_reference_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "read-aloud-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "read-aloud.v1",
                "exercise_type": "READ_ALOUD",
                "item": {
                    "item_id": "RA-1",
                    "instructions": (
                        "Read the text aloud as clearly and naturally as possible. "
                        "You have 45 seconds to prepare and 45 seconds to speak."
                    ),
                    "prompt_text": (
                        "In blended classrooms, students often use digital tools before discussing ideas face to face. "
                        "This sequence can improve confidence because learners arrive with organized notes and clearer "
                        "questions. However, teachers still need to monitor discussion quality, since fast digital "
                        "preparation does not always produce deep understanding or accurate reasoning in group tasks."
                    ),
                    "task_profile": {
                        "exam_profile": "toeic_speaking",
                        "prep_time_seconds": 45,
                        "response_time_seconds": 45,
                        "delivery_mode": "verbatim_reading",
                        "allow_paraphrase": False,
                        "expected_word_count_min": 50,
                        "expected_word_count_max": 75,
                        "required_features": [
                            {"feature_id": "F1", "requirement": "Maintain intelligible pronunciation."},
                            {"feature_id": "F2", "requirement": "Use clause-level pausing."},
                            {"feature_id": "F3", "requirement": "Keep steady pace and fluency."},
                        ],
                    },
                    "reference_renderings": [
                        {
                            "rendering_id": "A",
                            "transcript": (
                                "In blended classrooms, students often use digital tools before discussing ideas face to face. "
                                "This sequence can improve confidence because learners arrive with quick notes and simple "
                                "questions. However, teachers still need to monitor discussion quality, since fast digital "
                                "preparation does not always produce deep understanding or accurate reasoning in group tasks."
                            ),
                            "delivery_note": "Clear articulation with medium pace and clause-based pausing.",
                            "covered_feature_ids": ["F1", "F2", "F3"],
                        },
                        {
                            "rendering_id": "B",
                            "transcript": (
                                "In blended classrooms, students often use digital tools before discussing ideas face to face. "
                                "This sequence can improve confidence because learners arrive with organized notes and clearer "
                                "questions. However, teachers still need to monitor discussion quality, since fast digital "
                                "preparation does not always produce deep understanding or accurate reasoning in group tasks."
                            ),
                            "delivery_note": "Slightly slower tempo with strong stress on connectors.",
                            "covered_feature_ids": ["F1", "F2", "F3"],
                        },
                    ],
                    "scoring_rubric": {
                        "pronunciation": "Speech is generally intelligible.",
                        "intonation_and_stress": "Prosody supports meaning.",
                        "fluency": "Delivery is continuous with manageable hesitations.",
                        "accuracy": "Output preserves prompt text.",
                    },
                    "explanation": "Regression case for transcript mismatch under verbatim mode.",
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
    assert any(item["code"] == "TMP_RA_REFERENCE_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_describe_picture_detail_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "describe-picture-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "describe-picture.v1",
                "exercise_type": "DESCRIBE_PICTURE",
                "item": {
                    "item_id": "DP-REG-001",
                    "instructions": (
                        "Describe the picture in detail. You have 45 seconds to prepare and 30 seconds to speak. "
                        "Include key actions and spatial relationships."
                    ),
                    "picture_context": {
                        "picture_id": "PIC-001",
                        "scene_summary": (
                            "The image shows a busy train-station platform during the morning commute, with travelers "
                            "waiting, checking schedules, and organizing their belongings while people move through "
                            "different areas of the scene."
                        ),
                        "salient_details": [
                            {
                                "detail_id": "D1",
                                "detail_text": "A woman in a blue coat is checking her phone next to a red suitcase.",
                                "detail_type": "person",
                            },
                            {
                                "detail_id": "D2",
                                "detail_text": "A child is pointing at the departure board near the middle of the platform.",
                                "detail_type": "action",
                            },
                            {
                                "detail_id": "D3",
                                "detail_text": "Two cyclists are locking their bikes beside a ticket machine on the right.",
                                "detail_type": "interaction",
                            },
                            {
                                "detail_id": "D4",
                                "detail_text": "An older man stands behind the child and reads a newspaper.",
                                "detail_type": "person",
                            },
                        ],
                    },
                    "task_profile": {
                        "exam_profile": "toeic_speaking",
                        "prep_time_seconds": 45,
                        "response_time_seconds": 30,
                        "expected_word_count_min": 50,
                        "expected_word_count_max": 95,
                        "require_spatial_relations": True,
                        "allow_inference": False,
                        "required_detail_ids": ["D1", "D2", "D3"],
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "Commuter mobility and urban learning routines",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["public transport", "daily commute", "urban behavior"],
                    },
                    "reference_descriptions": [
                        {
                            "description_id": "A",
                            "transcript": (
                                "At this train station platform, several commuters are waiting for a morning train. "
                                "In the foreground, a woman in a blue coat is checking her phone beside a red suitcase. "
                                "To her left, a child points at the departure board while an older man stands behind "
                                "them and reads a newspaper. Near the right side, two cyclists are locking their bikes "
                                "next to a ticket machine."
                            ),
                            "delivery_note": "Steady pace with clear stress on location markers and actions.",
                            "covered_detail_ids": ["D1", "D2", "D4"],
                        },
                        {
                            "description_id": "B",
                            "transcript": (
                                "The picture captures a crowded platform during rush hour. In the front area, a woman "
                                "in a blue coat is using her phone, and her red suitcase is on the ground beside her. "
                                "Behind her, an older man is reading a newspaper, while a child near the center points "
                                "up at the departure board. On the right, two cyclists are locking their bicycles by "
                                "the ticket machine."
                            ),
                            "delivery_note": "Natural intonation with controlled pausing between detail clusters.",
                            "covered_detail_ids": ["D1", "D2", "D3", "D4"],
                        },
                    ],
                    "scoring_rubric": {
                        "pronunciation": "Speech is generally intelligible with controlled segmental accuracy.",
                        "intonation_and_stress": "Prosody supports meaning and highlights key picture details.",
                        "fluency": "Delivery is continuous with manageable hesitation and stable pace.",
                        "grammar": "Sentence forms remain controlled while describing actions and relations.",
                        "vocabulary": "Lexical choices for objects, actions, and locations are accurate and varied.",
                        "cohesion": "Description is organized logically with clear transitions between details.",
                    },
                    "explanation": "Regression case: reference description A does not include all required detail IDs.",
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
    assert any(item["code"] == "TMP_DP_DETAIL_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_repeat_sentence_reference_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "repeat-sentence-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "repeat-sentence.v1",
                "exercise_type": "REPEAT_SENTENCE",
                "item": {
                    "item_id": "RS-REG-001",
                    "instructions": (
                        "Listen to the sentence and repeat the sentence exactly after the beep. "
                        "You have 3 seconds to prepare and 15 seconds to respond."
                    ),
                    "prompt_audio_transcript": (
                        "Although online tutorials are flexible, students still benefit most when they "
                        "review feedback carefully before the next lesson."
                    ),
                    "task_profile": {
                        "exam_profile": "pte_academic",
                        "prep_time_seconds": 3,
                        "response_time_seconds": 15,
                        "delivery_mode": "verbatim_repetition",
                        "allow_paraphrase": False,
                        "expected_word_count_min": 14,
                        "expected_word_count_max": 20,
                        "required_features": [
                            {
                                "feature_id": "F1",
                                "requirement": "Preserve original lexical content without substitution.",
                            },
                            {
                                "feature_id": "F2",
                                "requirement": "Maintain intelligible pronunciation across all stressed words.",
                            },
                            {
                                "feature_id": "F3",
                                "requirement": "Deliver at steady pace with minimal hesitation.",
                            },
                        ],
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "AI-supported learning routines and classroom outcomes",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["learning feedback", "classroom language", "academic speaking"],
                    },
                    "reference_repetitions": [
                        {
                            "repetition_id": "A",
                            "transcript": (
                                "Although online tutorials are flexible, students benefit most when they review "
                                "feedback carefully before the next lesson."
                            ),
                            "delivery_note": "Clear stress on key content words with clause-level pausing.",
                            "covered_feature_ids": ["F1", "F2", "F3"],
                        },
                        {
                            "repetition_id": "B",
                            "transcript": (
                                "Although online tutorials are flexible, students still benefit most when they review "
                                "feedback carefully before the next lesson."
                            ),
                            "delivery_note": "Slightly slower pacing while preserving complete verbal fidelity.",
                            "covered_feature_ids": ["F1", "F2", "F3"],
                        },
                    ],
                    "scoring_rubric": {
                        "content_accuracy": "Response preserves original words and sequence with no omission.",
                        "pronunciation": "Speech is intelligible with controlled segmental production.",
                        "oral_fluency": "Utterance is smooth with manageable pauses and stable rhythm.",
                        "memory_control": "Sentence is retained and reproduced without major breakdown.",
                    },
                    "explanation": "Regression case: reference repetition A omits one required word.",
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
    assert any(item["code"] == "TMP_RS_REFERENCE_MISMATCH" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_retell_lecture_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "retell-lecture-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "retell-lecture.v1",
                "exercise_type": "RETELL_LECTURE",
                "item": {
                    "item_id": "RL-REG-001",
                    "instructions": (
                        "Listen to the lecture excerpt and retell the main ideas in your own words. "
                        "You have 30 seconds to prepare and 60 seconds to speak. Do not add personal opinions."
                    ),
                    "lecture_context": {
                        "lecture_id": "LEC-001",
                        "topic_title": "Why urban trees reduce heat exposure",
                        "lecture_transcript": (
                            "The lecturer explains that urban trees reduce heat exposure through three linked mechanisms. "
                            "First, tree canopies block direct sunlight, which lowers surface temperatures on streets and "
                            "building walls during peak afternoon hours. Second, trees cool surrounding air through "
                            "evapotranspiration, a process in which water released from leaves absorbs heat energy. Third, "
                            "shaded neighborhoods usually encourage more outdoor walking, which reduces short car trips and "
                            "can indirectly lower local heat generated by traffic and asphalt. The lecture emphasizes that "
                            "these benefits are strongest when city planners combine tree planting with maintenance, "
                            "irrigation, and species selection suited to local climate."
                        ),
                        "key_points": [
                            {
                                "point_id": "K1",
                                "point_text": "Canopies block direct sunlight and lower surface temperatures.",
                            },
                            {
                                "point_id": "K2",
                                "point_text": "Evapotranspiration cools nearby air by absorbing heat.",
                            },
                            {
                                "point_id": "K3",
                                "point_text": "Shade can reduce short car trips and heat from traffic.",
                            },
                            {
                                "point_id": "K4",
                                "point_text": "Planning quality and maintenance determine overall impact.",
                            },
                        ],
                    },
                    "task_profile": {
                        "exam_profile": "toefl_integrated_speaking",
                        "prep_time_seconds": 30,
                        "response_time_seconds": 60,
                        "expected_word_count_min": 95,
                        "expected_word_count_max": 155,
                        "required_point_ids": ["K1", "K2", "K4"],
                        "allow_personal_opinion": False,
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "Climate adaptation in urban education contexts",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["urban climate", "public health", "sustainable cities"],
                    },
                    "reference_retells": [
                        {
                            "retell_id": "A",
                            "transcript": (
                                "The lecture says urban trees reduce heat in several connected ways. First, tree canopies "
                                "block direct sunlight, so roads and walls become less hot in the afternoon. Second, leaves "
                                "release water and this evapotranspiration process absorbs heat, so nearby air gets cooler. "
                                "The speaker also notes a behavioral effect: when streets are shaded, people walk more and "
                                "depend less on short car trips, which can reduce additional local heat from traffic and "
                                "paved surfaces. Finally, the lecturer stresses that results depend on good planning, "
                                "including maintenance, irrigation, and choosing tree species that fit the local climate."
                            ),
                            "delivery_note": "Clear pacing with explicit transitions between each mechanism.",
                            "covered_point_ids": ["K1", "K2", "K3"],
                        },
                        {
                            "retell_id": "B",
                            "transcript": (
                                "According to the lecturer, urban trees lower heat exposure through direct cooling and "
                                "indirect behavioral change. One mechanism is shading, because canopies block sunlight and "
                                "keep street surfaces cooler during hot periods. Another mechanism is evapotranspiration, "
                                "where water from leaves helps remove heat from surrounding air. The lecture adds that "
                                "shaded areas can encourage walking and reduce very short car journeys, which may lessen "
                                "heat produced by traffic and asphalt. The closing point is that benefits are not automatic, "
                                "since cities need proper maintenance, irrigation, and appropriate species selection for "
                                "local conditions."
                            ),
                            "delivery_note": "Natural intonation and coherent summary progression from cause to implication.",
                            "covered_point_ids": ["K1", "K2", "K3", "K4"],
                        },
                    ],
                    "scoring_rubric": {
                        "delivery": "Speech is clear and paced naturally with manageable hesitation.",
                        "language_use": "Grammar and vocabulary support accurate summary of source ideas.",
                        "topic_development": "Response organizes and links key lecture ideas coherently.",
                        "content_accuracy": "Retell preserves main claims and examples without factual drift.",
                    },
                    "explanation": "Regression case: reference retell A does not cover all required point IDs.",
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
    assert any(item["code"] == "TMP_RL_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_answer_short_question_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "answer-short-question-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "answer-short-question.v1",
                "exercise_type": "ANSWER_SHORT_QUESTION",
                "item": {
                    "item_id": "ASQ-REG-001",
                    "instructions": (
                        "Answer the question clearly and directly. "
                        "You have 3 seconds to prepare and 30 seconds to speak."
                    ),
                    "question_context": {
                        "question_id": "Q-001",
                        "question_text": (
                            "What is one effective way for students to improve speaking fluency outside class, and why?"
                        ),
                        "question_type": "preference",
                        "expected_points": [
                            {"point_id": "P1", "point_text": "Describe one concrete out-of-class speaking routine."},
                            {"point_id": "P2", "point_text": "Explain why that routine improves fluency outcomes."},
                            {"point_id": "P3", "point_text": "Give one practical example of implementation."},
                        ],
                    },
                    "task_profile": {
                        "exam_profile": "toeic_speaking",
                        "prep_time_seconds": 3,
                        "response_time_seconds": 30,
                        "expected_word_count_min": 55,
                        "expected_word_count_max": 95,
                        "allow_personal_opinion": True,
                        "required_point_ids": ["P1", "P2"],
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "Self-directed speaking practice and feedback loops",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["speaking fluency", "language practice", "learning routine"],
                    },
                    "reference_responses": [
                        {
                            "response_id": "A",
                            "transcript": (
                                "One effective way is to schedule a short daily speaking routine where students summarize "
                                "their day out loud for two minutes. For example, a student can record a daily voice note, "
                                "listen again, and track repeated pauses to improve rhythm and confidence week by week."
                            ),
                            "delivery_note": "Direct answer and example, but missing explicit reason statement.",
                            "covered_point_ids": ["P1", "P3"],
                        },
                        {
                            "response_id": "B",
                            "transcript": (
                                "I recommend a partner speaking check-in three times a week. Students can choose one "
                                "familiar topic and explain it for one minute while a partner gives quick feedback. This "
                                "improves fluency because frequent practice under light pressure helps ideas come faster "
                                "and makes transitions smoother. A practical example is using a timer and rotating topics "
                                "like school projects, weekend plans, or local news."
                            ),
                            "delivery_note": "Natural intonation with clear link between method, reason, and example.",
                            "covered_point_ids": ["P1", "P2", "P3"],
                        },
                    ],
                    "scoring_rubric": {
                        "comprehension": "Response addresses the asked question without misunderstanding intent.",
                        "relevance": "Content remains focused on the requested method and justification.",
                        "fluency": "Delivery is continuous with manageable pauses and clear rhythm.",
                        "language_use": "Grammar and vocabulary are appropriate for short spoken explanation.",
                    },
                    "explanation": "Regression case: reference response A does not cover all required point IDs.",
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
    assert any(item["code"] == "TMP_ASQ_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_respond_to_information_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "respond-to-information-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "respond-to-information.v1",
                "exercise_type": "RESPOND_TO_INFORMATION",
                "item": {
                    "item_id": "RTI-REG-001",
                    "instructions": (
                        "Read the information and respond to the question clearly. "
                        "You have 45 seconds to prepare and 30 seconds to speak."
                    ),
                    "information_context": {
                        "info_id": "INFO-001",
                        "prompt_type": "service_notice",
                        "stimulus_text": (
                            "Campus Transit Notice: From Monday to Friday this month, Route B will stop operating "
                            "after 6:00 p.m. due to road repairs near West Gate. Students traveling from the library "
                            "to North Dorm should use Route C, which departs every 20 minutes until 10:00 p.m. A free "
                            "transfer from Route A to Route C is available at Science Center with the same student ID card."
                        ),
                        "prompt_question": (
                            "Your classmate asks about evening transport from the library to North Dorm. "
                            "Explain the updated plan using the notice."
                        ),
                        "info_points": [
                            {"point_id": "I1", "point_text": "Route B does not run after 6:00 p.m. on weekdays this month."},
                            {
                                "point_id": "I2",
                                "point_text": (
                                    "Route C runs every 20 minutes from the library area to North Dorm until 10:00 p.m."
                                ),
                            },
                            {
                                "point_id": "I3",
                                "point_text": (
                                    "Students can transfer for free from Route A to Route C at Science Center using ID."
                                ),
                            },
                        ],
                    },
                    "task_profile": {
                        "exam_profile": "toeic_speaking",
                        "prep_time_seconds": 45,
                        "response_time_seconds": 30,
                        "expected_word_count_min": 70,
                        "expected_word_count_max": 120,
                        "response_style": "question_response",
                        "allow_personal_opinion": False,
                        "required_point_ids": ["I1", "I2", "I3"],
                    },
                    "topic_context": {
                        "topic_id": "TREND-2026-02",
                        "topic_title": "Campus service updates and student mobility routines",
                        "source_type": "google_trends",
                        "source_url": "https://trends.google.com/trends/",
                        "captured_at": "2026-02-14",
                        "trend_window": "30d",
                        "keywords": ["campus transport", "service notice", "student commute"],
                    },
                    "reference_responses": [
                        {
                            "response_id": "A",
                            "transcript": (
                                "The notice says Route B is not available after six in the evening on weekdays this month, "
                                "so your usual plan will not work. You should use Route C from the library to North Dorm, "
                                "and it still runs every twenty minutes until ten p.m. That means evening travel is still "
                                "possible if you switch to the new route schedule for your study return trip. You can "
                                "check the bus app first so you do not miss departure time."
                            ),
                            "delivery_note": "Clear explanation of route change and replacement schedule, but no transfer detail.",
                            "covered_point_ids": ["I1", "I2"],
                        },
                        {
                            "response_id": "B",
                            "transcript": (
                                "For evening trips, the important update is that Route B stops after 6:00 p.m. this month "
                                "because of roadwork near West Gate. The notice recommends Route C for library to North "
                                "Dorm travel, and that bus comes every twenty minutes until 10:00 p.m. If you need to "
                                "connect from Route A, transfer at Science Center and keep your student card ready. The "
                                "transfer from A to C is free with the same ID, so you do not need to pay again."
                            ),
                            "delivery_note": "Keep a practical tone and organize the response as change, alternative, and transfer details.",
                            "covered_point_ids": ["I1", "I2", "I3"],
                        },
                    ],
                    "scoring_rubric": {
                        "comprehension": "Response reflects key details from the provided notice accurately.",
                        "relevance": "Content stays focused on answering the classmate's transport question.",
                        "task_completion": "Response includes the critical update, alternative route, and transfer condition.",
                        "fluency": "Delivery is steady with manageable pauses and clear progression.",
                        "language_use": "Grammar and vocabulary are appropriate for concise functional speaking.",
                    },
                    "explanation": "Regression case: reference response A does not include all required information points.",
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
    assert any(item["code"] == "TMP_RTI_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_oral_interview_qa_point_coverage_fixture() -> None:
    item_file = PACK_DIR / "examples" / "regression" / "oral-interview-qa.point-coverage.json"
    assert item_file.is_file(), "Missing oral interview QA regression fixture"

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_OIQ_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_cue_card_long_turn_point_coverage_fixture() -> None:
    item_file = PACK_DIR / "examples" / "regression" / "cue-card-long-turn.point-coverage.json"
    assert item_file.is_file(), "Missing cue-card-long-turn regression fixture"

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_CLT_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_collaborative_discussion_point_coverage_fixture() -> None:
    item_file = PACK_DIR / "examples" / "regression" / "collaborative-discussion.point-coverage.json"
    assert item_file.is_file(), "Missing collaborative-discussion regression fixture"

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_CD_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_respond_to_written_request_point_coverage_fixture() -> None:
    item_file = PACK_DIR / "examples" / "regression" / "respond-to-written-request.point-coverage.json"
    assert item_file.is_file(), "Missing respond-to-written-request regression fixture"

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_RTWR_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_write_sentence_from_picture_keyword_missing_fixture() -> None:
    item_file = PACK_DIR / "examples" / "regression" / "write-sentence-from-picture.keyword-missing.json"
    assert item_file.is_file(), "Missing write-sentence-from-picture regression fixture"

    code, payload = _run_validator(item_file)
    assert code != 0
    assert payload["STATUS"] == "BLOCK"
    assert any(item["code"] == "TMP_WSFP_KEYWORD_MISSING" for item in payload["FINDINGS"])


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


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_summarize_written_text_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "swt-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "summarize-written-text.v1",
                "exercise_type": "SUMMARIZE_WRITTEN_TEXT",
                "item": {
                    "item_id": "SWT-REG-001",
                    "instructions": (
                        "Read the passage and write one sentence summarizing the key points in 5-75 words "
                        "within 10 minutes."
                    ),
                    "source_text": (
                        "Many city governments are replacing fixed bus timetables with demand-responsive shuttle "
                        "systems that adjust routes according to real-time passenger requests. Advocates argue that "
                        "the model reduces waiting time in low-density neighborhoods and cuts fuel waste because "
                        "vehicles no longer run mostly empty routes. They also claim that data-driven routing can "
                        "improve service equity when authorities prioritize areas with limited public transport "
                        "access. However, critics note that on-demand systems require reliable mobile access and "
                        "digital literacy, which can exclude older residents and low-income riders if no phone-based "
                        "alternatives are provided. Operational complexity is another challenge, since agencies need "
                        "continuous monitoring staff, updated dispatch software, and transparent service standards to "
                        "prevent unpredictable delays. Some transport planners therefore recommend hybrid designs that "
                        "keep core fixed routes during peak periods while using on-demand shuttles for off-peak and "
                        "low-coverage zones."
                    ),
                    "source_points": [
                        {
                            "point_id": "P1",
                            "point_text": (
                                "The passage describes demand-responsive shuttles as an alternative to fixed bus timetables."
                            ),
                        },
                        {
                            "point_id": "P2",
                            "point_text": (
                                "Supporters expect lower waiting times, reduced fuel waste, and potentially better service "
                                "equity through data-driven routing."
                            ),
                        },
                        {
                            "point_id": "P3",
                            "point_text": (
                                "The text warns about digital-access barriers and operational complexity, recommending a "
                                "hybrid fixed-plus-demand model."
                            ),
                        },
                    ],
                    "task_profile": {
                        "exam_profile": "pte_academic",
                        "time_limit_minutes": 10,
                        "source_text_word_max": 300,
                        "summary_word_min": 5,
                        "summary_word_max": 75,
                        "sentence_count_required": 1,
                        "allow_multiple_sentences": False,
                        "required_point_ids": ["P1", "P2", "P3"],
                    },
                    "reference_summaries": [
                        {
                            "summary_id": "A",
                            "body": (
                                "The passage explains that demand-responsive shuttle systems may reduce waiting and fuel "
                                "use while improving route targeting in underserved neighborhoods, though implementation "
                                "quality still depends on practical policy choices."
                            ),
                            "covered_point_ids": ["P1", "P2"],
                        },
                        {
                            "summary_id": "B",
                            "body": (
                                "According to the text, cities view on-demand shuttles as a flexible substitute for fixed "
                                "routes and expect efficiency gains, but successful adoption requires careful planning and "
                                "clear operating standards."
                            ),
                            "covered_point_ids": ["P1", "P2"],
                        },
                    ],
                    "scoring_rubric": {
                        "content": "Summary captures topic and key claims without distortion.",
                        "form": "Response is one sentence within the required word range.",
                        "grammar": "Sentence structure is controlled and grammatical.",
                        "vocabulary": "Word choice is concise and appropriate.",
                    },
                    "explanation": "Regression case for required point coverage mismatch.",
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
    assert any(item["code"] == "TMP_SWT_POINT_COVERAGE" for item in payload["FINDINGS"])


@pytest.mark.skipif(not VALIDATOR.is_file(), reason="template pack validator missing")
def test_template_pack_validator_blocks_summarize_spoken_text_point_coverage_mismatch(tmp_path: Path) -> None:
    item_file = tmp_path / "sst-invalid.json"
    item_file.write_text(
        json.dumps(
            {
                "template_id": "summarize-spoken-text.v1",
                "exercise_type": "SUMMARIZE_SPOKEN_TEXT",
                "item": {
                    "item_id": "SST-REG-001",
                    "instructions": (
                        "Listen to the recording and write a 50-70 word summary in 10 minutes, "
                        "covering the main message and key supporting points."
                    ),
                    "lecture_context": {
                        "lecture_id": "LEC-SST-B2-001",
                        "topic_title": "Why hospitals use digital triage before in-person appointments",
                        "audio_length_seconds": 76,
                        "lecture_transcript": (
                            "The lecturer describes how digital triage systems are being used to manage patient flow "
                            "before in-person appointments. In this model, patients complete structured symptom forms "
                            "online, and the system categorizes urgency based on predefined risk indicators. "
                            "Supporters argue that this process reduces waiting-room congestion because low-risk cases "
                            "can be redirected to remote consultation or self-care guidance, while high-risk cases "
                            "receive faster clinical attention. The lecturer adds that digital triage can improve "
                            "documentation quality by capturing standardized symptom histories before patients meet a "
                            "clinician. However, the system is not effective without strong escalation rules and human "
                            "review pathways, since automated categorization can miss atypical cases. The final point "
                            "is that hospitals should combine digital screening with clinician oversight and periodic "
                            "audit, so patient safety is protected while operational efficiency improves."
                        ),
                        "key_points": [
                            {
                                "point_id": "K1",
                                "point_text": (
                                    "Digital triage pre-screens patients through structured symptom input and urgency "
                                    "categorization."
                                ),
                            },
                            {
                                "point_id": "K2",
                                "point_text": (
                                    "The approach can reduce congestion and improve documentation by routing cases "
                                    "more efficiently."
                                ),
                            },
                            {
                                "point_id": "K3",
                                "point_text": (
                                    "The lecturer stresses that human oversight and audit are necessary to avoid "
                                    "automation risks."
                                ),
                            },
                        ],
                    },
                    "task_profile": {
                        "exam_profile": "pte_academic",
                        "time_limit_minutes": 10,
                        "prompt_length_seconds_min": 60,
                        "prompt_length_seconds_max": 90,
                        "summary_word_min": 50,
                        "summary_word_max": 70,
                        "zero_score_below_words": 40,
                        "zero_score_above_words": 100,
                        "require_own_words": True,
                        "allow_bullets": False,
                        "required_point_ids": ["K1", "K2", "K3"],
                    },
                    "reference_summaries": [
                        {
                            "summary_id": "A",
                            "body": (
                                "The lecture explains that digital triage systems pre-screen patients through "
                                "structured symptom forms and urgency categorization to manage clinical flow, and this "
                                "approach can reduce waiting congestion while improving documentation quality before "
                                "in-person visits."
                            ),
                            "covered_point_ids": ["K1", "K2"],
                        },
                        {
                            "summary_id": "B",
                            "body": (
                                "According to the speaker, hospitals use digital triage to classify risk and route "
                                "cases more efficiently, which supports faster handling and cleaner symptom records, "
                                "but successful implementation still requires careful process design and dependable "
                                "escalation governance."
                            ),
                            "covered_point_ids": ["K1", "K2"],
                        },
                    ],
                    "scoring_rubric": {
                        "content": "Summary reflects lecture meaning and key support points.",
                        "form": "Response stays in the target word range.",
                        "grammar": "Sentence structures are controlled and grammatical.",
                        "vocabulary": "Word choice is precise and appropriate.",
                        "spelling": "Spelling is accurate and consistent.",
                    },
                    "explanation": "Regression case for required point coverage mismatch.",
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
    assert any(item["code"] == "TMP_SST_POINT_COVERAGE" for item in payload["FINDINGS"])
