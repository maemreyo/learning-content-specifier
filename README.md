# LCS

Learning Content Specifier.

LCS is a spec-driven toolkit for producing learning content with deterministic quality gates. The workflow is built around `Course -> Module -> Lesson` and local-first artifacts.

## Core Command Flow

`/lcs.charter -> /lcs.define -> /lcs.refine -> /lcs.design -> /lcs.sequence -> /lcs.rubric -> /lcs.audit -> /lcs.author -> /lcs.issueize`

## Artifact Contract

For each unit under `specs/<###-slug>/`:

- `brief.md`
- `brief.json`
- `design.md`
- `design.json`
- `sequence.md`
- `sequence.json`
- `content-model.md`
- `content-model.json`
- `design-decisions.json`
- `assessment-map.md`
- `delivery-guide.md`
- `rubrics/`
- `audit-report.md`
- `audit-report.json`
- `outputs/`
- `outputs/manifest.json`

Governance source: `.lcs/memory/charter.md`.

## Hard Gates

Before `/lcs.author`:

- Rubric gates are complete and evidence-backed.
- Audit report artifacts exist with `PASS` decision (`audit-report.md` and/or `audit-report.json`).
- No unresolved `CRITICAL` or `HIGH` findings.

## Quick Start

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init <project-name> --ai claude
```

Then in your agent:

```text
/lcs.charter
/lcs.define Build a learning unit for ...
/lcs.refine
/lcs.design
/lcs.sequence
/lcs.rubric
/lcs.audit
/lcs.author
```

## Supported AI Agents

See `AGENTS.md` for the canonical matrix, conventions, and folder mappings.

## Docs

- `docs/installation.md`
- `docs/quickstart.md`
- `docs/upgrade.md`
- `spec-driven.md`
