# lcs-output-consumer

Standalone, headless backbone for consuming LCS artifacts via manifest-first ingestion.

## Scope (MVP)

- Filesystem ingestion from `specs/*`.
- Deterministic validation (schema + consistency + gates).
- Unit catalog/query API.
- xAPI readiness projection from `outputs/manifest.json`.

## Quick Start

1. Install deps:

```bash
uv sync
```

2. Ensure contract assets exist (copy from LCS release package `lcs-contracts-vX.Y.Z.zip`):

- `contracts/index.json`
- `schemas/*.schema.json`
- `docs/contract/*.md`
- `fixtures/contracts/*.json`

3. Run API:

```bash
uv run uvicorn lcs_output_consumer.main:app --reload
```

## API v1

- `POST /v1/ingestions/fs`
- `POST /v1/validations/unit`
- `GET /v1/units`
- `GET /v1/units/{unit_id}`
- `GET /v1/units/{unit_id}/manifest`
- `GET /v1/units/{unit_id}/gates`
- `GET /v1/units/{unit_id}/artifacts`

## Environment Variables

- `LCS_CONSUMER_REPO_ROOT`: base path containing `contracts/` + `schemas/` (default: repo root)
- `LCS_CONSUMER_DB_PATH`: SQLite path (default: `<repo>/data/catalog.sqlite3`)

## Notes

- Manifest-first is strict: no path-guessing outside `outputs/manifest.json`.
- Ingestion is blocked when contract major version is incompatible.
- `xapi` interop block is required by contract.
