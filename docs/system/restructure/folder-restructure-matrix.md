# Folder Restructure Matrix (Factory -> Library -> Apps)

## Scope

Clean-break matrix for reorganizing this repository into factory-core concerns while keeping consumer delivery via standalone release assets.

## Naming Freeze

- `factory/`: authoring/runtime source assets for LCS core.
- `contracts/`: machine contract package source-of-truth and entrypoint (`contracts/index.json`).
- `tooling/ci/`: workflow helper scripts consumed by GitHub Actions.

## Mapping

| Old Path | New Path | Owner | Tests/Checks | Risk |
|---|---|---|---|---|
| `templates/` | `factory/templates/` | Factory Core | `pytest`, release smoke | Medium |
| `scripts/bash/` | `factory/scripts/bash/` | Factory Core | script contract smoke (bash) | High |
| `scripts/powershell/` | `factory/scripts/powershell/` | Factory Core | script contract smoke (ps) | High |
| `scripts/*.py` | `factory/scripts/python/*.py` | Factory Core | `pytest`, contract verify | Medium |
| `schemas/` | `contracts/schemas/` | Contracts | contract verify + zip smoke | High |
| `docs/contract/` | `contracts/docs/` | Contracts | docs link check + contract verify | Medium |
| `fixtures/contracts/` | `contracts/fixtures/` | Contracts | contract verify + pytest | Medium |
| `.github/workflows/scripts/` | `tooling/ci/` | Tooling/CI | lint/release workflows | High |
| `scaffolds/lcs-output-consumer/` | removed from core | Consumer | bootstrap tests | Medium |
| `scripts/scaffold_output_consumer.py` | replaced by `factory/scripts/python/bootstrap_consumer.py` | Consumer Integration | bootstrap unit tests | High |

## Non-goals in this batch

- No learner/mobile/LMS app code in this repo.
- No backward aliases for legacy folder paths.
- No in-repo consumer runtime source after extraction.

## Acceptance Gates

- No runtime references to removed paths in CI scripts, tests, or active docs.
- `contracts/index.json` resolves only `contracts/*` entries.
- Release package smoke verifies `contracts/*` payload layout.
- Bootstrap script operates via release tag + checksum verification.
