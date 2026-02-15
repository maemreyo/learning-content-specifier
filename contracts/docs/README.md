# Contract Sync Layer

This folder defines the context-safe contract surface for the standalone `lcs-output-consumer` repository.

## Purpose

- Keep consumer context aligned with LCS runtime contracts.
- Provide a stable, versioned package for schemas, docs digest, and fixtures.
- Prevent drift via checksum-based verification in CI.

## Package Composition

- `contracts/index.json`
- `contracts/schemas/*.schema.json`
- `contracts/docs/*.md`
- `contracts/fixtures/*.json`

## Proficiency Layer (v1)

The contract package includes a subject-agnostic proficiency layer for targets such as CEFR/IELTS/TOEIC.

- Unit authors may optionally set `brief.json.proficiency_targets[]` to declare score/band/level targets.
- The validator will hard-block when targets are declared but cannot be normalized to the subject pivot framework.
- Reference data lives in fixtures:
  - `contracts/fixtures/proficiency.framework-registry.v1.json`
  - `contracts/fixtures/proficiency.crosswalks.v1.json`
  - `contracts/fixtures/proficiency.subject-pivots.v1.json`

## Included API Digests

- `CONSUMER-API-V1.md` for the standalone library backbone.
- `TUTORING-BFF-API-V1.md` for teacher/learner application integration.

## Local Verification

```bash
uv run python factory/scripts/python/build_contract_package.py --verify
```

## Consumer Rule

Consumer services MUST use `outputs/manifest.json` as the only ingestion entrypoint and resolve artifacts only via manifest references.
