# LCS

Learning Content Specifier.

LCS is a spec-driven toolkit for producing learning content with deterministic quality gates. The workflow is built around `Course -> Module -> Lesson` and local-first artifacts.

## Install And Use In Another Repo

### Prerequisite

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/

### Option A: One-off usage (no global install)

From any folder where you want to create a new project:

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init <project-name> --ai codex
```

Then enter the project:

```bash
cd <project-name>
```

### Option B: Install `lcs` globally

```bash
uv tool install --from git+https://github.com/maemreyo/learning-content-specifier.git lcs-cli
```

Create or bootstrap from any folder:

```bash
lcs init <project-name> --ai codex
cd <project-name>
```

### Use LCS inside an existing repo

From the root of your existing repo:

```bash
lcs init . --ai codex
```

This will scaffold `.lcs/`, command files for your selected agent, templates, and workflow scripts so you can start authoring learning content immediately.

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

## Contract Package For Standalone Consumer

LCS publishes a context-safe contract package for external consumer platforms:

- `contracts/index.json` (checksums + compatibility policy)
- `contracts/schemas/*.schema.json`
- `contracts/docs/*.md`
- `contracts/fixtures/*.json`

Build/verify locally:

```bash
uv run python factory/scripts/python/build_contract_package.py --verify
uv run python factory/scripts/python/build_contract_package.py --sync --verify --package-version v0.0.0
```

Release artifact name:

- `.genreleases/lcs-contracts-vX.Y.Z.zip`

Bootstrap standalone consumer repo from this LCS core repo:

```bash
uv run python factory/scripts/python/bootstrap_consumer.py --consumer-version v0.1.0 --target ../lcs-output-consumer
```

## Hard Gates

Before `/lcs.author`:

- Rubric gates are complete and evidence-backed.
- Audit report artifacts exist with `PASS` decision (`audit-report.md` and/or `audit-report.json`).
- No unresolved `CRITICAL` or `HIGH` findings.

## Quick Start Workflow

In your agent:

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
- `contracts/docs/README.md`
- `docs/system/architect/lcs-output-consumer-standalone-blueprint.md`
- `spec-driven.md`
