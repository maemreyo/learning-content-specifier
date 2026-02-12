# LCS Output Consumer: Standalone Blueprint

## Goal

Build a standalone, headless integration backbone that consumes LCS artifacts deterministically via `outputs/manifest.json`.

## Why standalone repository

- Independent release cadence from LCS runtime/templates.
- Better fit for multiple downstream app types (Next.js UI, BI jobs, LMS connectors).
- Keeps LCS core repository focused on spec/runtime/contracts.

## Context-safe sync strategy

Use versioned contract package emitted by LCS:

- `contracts/index.json`
- `contracts/schemas/*.schema.json`
- `contracts/docs/*.md`
- `contracts/fixtures/*.json`

Release artifact:

- `.genreleases/lcs-contracts-vX.Y.Z.zip`

## MVP Scope (v1)

- Filesystem ingestion (`specs/*`).
- Deterministic contract validation.
- Unit index and query API.
- Gate status projection.
- xAPI readiness projection.

Non-goals:

- Learner UI / creator UI.
- Direct production LMS publishing.
- Full LTI launch flows.
- Production-grade QTI export.

## API Surface (v1)

Ingestion:

- `POST /v1/ingestions/fs`
- `POST /v1/validations/unit`

Query:

- `GET /v1/units`
- `GET /v1/units/{unit_id}`
- `GET /v1/units/{unit_id}/manifest`
- `GET /v1/units/{unit_id}/gates`
- `GET /v1/units/{unit_id}/artifacts`

## Deterministic Rules

- Manifest-first resolution only.
- No path-guessing outside manifest references.
- Block when schema/consistency/gate checks fail.
- xAPI block required in manifest; optional adapters remain experimental (`case`, `qti`, `lti`, `cmi5`).

## Storage and runtime defaults

- Backend: Python FastAPI.
- Validation: JSON Schema + parity checks compatible with LCS validators.
- Storage: PostgreSQL with JSONB payloads.
- Background ingestion runner for batches.

## Validation taxonomy

- `IO_*`
- `SCHEMA_*`
- `CONSISTENCY_*`
- `GATE_*`

## Rollout sequence

1. Contract package pin + checksum verify.
2. Core ingestion/validation service.
3. Query API and filtering.
4. Adapter framework with `xapi_adapter`.
5. Drift checks in CI between consumer and contract package.

## Bootstrap command (from LCS core repo)

```bash
uv run python factory/scripts/python/bootstrap_consumer.py --consumer-version v0.1.0 --target ../lcs-output-consumer
```
