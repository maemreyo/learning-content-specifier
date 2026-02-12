# Learning Design Plan: [UNIT]

**Branch**: `[###-unit-name]` | **Date**: [DATE] | **Brief**: [link]
**Input**: Unit brief from `/specs/[###-unit-name]/brief.md`

## Summary

[Learning strategy summary derived from brief priorities]

## Learning Design Context

**Audience Profile**: [learner background and constraints]  
**Delivery Mode**: [self-paced/instructor-led/blended]  
**Modality Mix**: [text/video/lab/discussion/quiz]  
**Assessment Style**: [formative/summative/performance-based]  
**Duration Budget**: [target duration and pacing assumptions]  
**Localization Needs**: [languages/regional constraints or N/A]  
**Accessibility Baseline**: [a11y requirements and accommodations]  
**Scale/Scope**: [cohort size, number of modules/lessons, update cadence]

## Charter Check

*GATE: Must pass before design artifacts are finalized. Re-check after sequencing.*

- [ ] Objective-Activity-Assessment alignment is explicit for every LO
- [ ] Pedagogy is consistent with audience level and delivery mode
- [ ] Accessibility/readability requirements are covered in design decisions
- [ ] Metadata is complete for downstream publishing workflows

## Content Architecture

### Documentation (this unit)

```text
specs/[###-unit]/
|-- design.md                # This file (/lcs.design output)
|-- design.json              # Machine-readable design contract
|-- research.md              # Optional background decisions
|-- content-model.md         # Content entities and mapping
|-- content-model.json       # Machine-readable content model
|-- design-decisions.json    # Pedagogy scoring + research triggers
|-- assessment-map.md        # LO to assessment coverage matrix
|-- delivery-guide.md        # Facilitation + learner runbook
|-- sequence.md              # Production sequence (/lcs.sequence output)
|-- sequence.json            # Machine-readable production sequence
|-- audit-report.json        # Machine-readable audit decision
|-- rubrics/                 # Quality gates (/lcs.rubric output)
`-- outputs/
    `-- manifest.json        # Publish-local entrypoint for downstream consumers
```

### Content Structure (Course -> Module -> Lesson)

```text
Course: [course-name]
|-- Module 1: [title]
|   |-- Lesson 1.1: [title]
|   `-- Lesson 1.2: [title]
|-- Module 2: [title]
`-- Module N: [title]
```

## Instructional Strategy

- **Learning progression**: [how learners move from foundational to advanced outcomes]
- **Practice strategy**: [guided -> independent progression]
- **Feedback strategy**: [timing, format, rubric criteria]
- **Remediation strategy**: [paths when learners fail checkpoints]

## Complexity Tracking

> Fill only when charter gates need explicit justification.

| Deviation | Why Needed | Alternative Rejected |
|-----------|------------|----------------------|
| [e.g., extra modality] | [reason] | [reason] |
