# Spec-Driven Learning Content

## Why This Workflow

LCS treats learning artifacts as executable contracts. Instead of jumping directly into authoring, teams define outcomes, design strategy, sequencing, and quality gates first.

## Workflow

1. `/lcs.charter`: define governance and gate policy.
2. `/lcs.define`: create learner/outcome brief.
3. `/lcs.refine`: remove high-impact ambiguity.
4. `/lcs.design`: produce design + content model + assessment map + delivery guide.
5. `/lcs.sequence`: create dependency-ordered authoring sequence.
6. `/lcs.rubric`: generate machine-parseable quality gates.
7. `/lcs.audit`: generate `audit-report.md` + `audit-report.json` with PASS/BLOCK decision.
8. `/lcs.author`: produce local outputs only when gates pass.
9. `/lcs.issueize`: publish sequence tasks as GitHub issues.

## Quality Model

Hard gates enforce:

- Objective-Activity-Assessment alignment.
- Pedagogy consistency.
- Accessibility/readability coverage.
- Metadata completeness.
- Cross-artifact consistency.

## Local-First Output Strategy

All deliverables are produced under `programs/<program-id>/units/<unit-id>/outputs/` so downstream repositories or pipelines can consume deterministic artifacts.

Machine-consumable contracts are versioned json sidecars validated by schema, with `outputs/manifest.json` as the downstream entrypoint.

## Extension Hooks (Clean Break)

Supported core hook events:

- `after_charter`
- `after_define`
- `after_refine`
- `after_design`
- `after_sequence`
- `after_rubric`
- `after_audit`
- `after_author`
- `after_issueize`
