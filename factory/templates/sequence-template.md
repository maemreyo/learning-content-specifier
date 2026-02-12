---
description: "Production sequence template for learning unit authoring"
---

# Sequence: [UNIT NAME]

**Input**: Design docs from `/specs/[###-unit-name]/`
**Prerequisites**: design.md (required), brief.md (required), content-model.md, assessment-map.md, delivery-guide.md
**Machine Contract**: Keep `sequence.json` synchronized with task IDs, dependencies, and file targets.

**Quality mode**: Hard gates enabled. Rubric and audit checks are blocking before `/lcs.author`.

## Format: `[ID] [P?] [LO] Description`

- **[P]**: Can run in parallel (different files, no direct dependency)
- **[LO]**: Learning Outcome mapping (e.g., LO1, LO2)
- Include exact file paths in descriptions

## Phase 1: Foundation Setup

- [ ] S001 Define unit metadata in specs/[###-unit-name]/outputs/metadata.json
- [ ] S002 Create base directory structure for modules/lessons under specs/[###-unit-name]/outputs/
- [ ] S003 [P] Establish writing style and glossary in specs/[###-unit-name]/outputs/style-guide.md

## Phase 2: Core Learning Content

- [ ] S004 [LO1] Draft lesson narrative for LO1 in specs/[###-unit-name]/outputs/module-01/lesson-01.md
- [ ] S005 [P] [LO1] Draft practice activity for LO1 in specs/[###-unit-name]/outputs/module-01/activity-01.md
- [ ] S006 [LO2] Draft lesson narrative for LO2 in specs/[###-unit-name]/outputs/module-01/lesson-02.md
- [ ] S007 [P] [LO2] Draft practice activity for LO2 in specs/[###-unit-name]/outputs/module-01/activity-02.md

## Phase 3: Assessment Authoring

- [ ] S008 [LO1] Author assessment items mapped to LO1 in specs/[###-unit-name]/outputs/assessments/lo1.md
- [ ] S009 [LO2] Author assessment items mapped to LO2 in specs/[###-unit-name]/outputs/assessments/lo2.md
- [ ] S010 [LO3] Author assessment items mapped to LO3 in specs/[###-unit-name]/outputs/assessments/lo3.md

## Phase 4: Accessibility & Readability Hardening

- [ ] S011 Add alt text/transcripts and accessibility notes in specs/[###-unit-name]/outputs/accessibility.md
- [ ] S012 Validate readability targets and terminology consistency in specs/[###-unit-name]/outputs/readability-report.md

## Phase 5: Quality Gates

- [ ] S013 Run rubric checks and resolve all incomplete items in specs/[###-unit-name]/rubrics/
- [ ] S014 Run `/lcs.audit` and resolve critical/high findings in specs/[###-unit-name]/audit-report.md
- [ ] S015 Freeze publish-local package manifest in specs/[###-unit-name]/outputs/manifest.json

## Dependencies & Order

- Foundation (Phase 1) must complete before Phases 2-4
- Core content and assessments must map to every required LO
- Phase 5 is blocking; `/lcs.author` must stop if unresolved items exist
