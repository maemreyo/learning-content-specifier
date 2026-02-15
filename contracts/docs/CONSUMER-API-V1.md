# Consumer API v1 (Headless Backbone)

This is the normative API surface for the standalone consumer platform MVP.

## Ingestion API

### `POST /v1/ingestions/fs`

Request:

```json
{
  "source_repo_id": "repo.math",
  "source_repo_ref": {"repo": "math-content", "branch": "main"},
  "repo_path": "/absolute/path/to/project",
  "unit_glob": "programs/*/units/*",
  "contract_version": "1.0.0"
}
```

Behavior:

- Discover units from filesystem.
- Require `programs/<program-id>/units/<unit>/outputs/manifest.json`.
- Validate contract checksum policy before ingestion.
- Run schema + consistency + gate checks.

### `POST /v1/validations/unit`

Request:

```json
{
  "unit_path": "/absolute/path/to/project/programs/seed-001/units/993-e2e-golden-path",
  "source_repo_id": "repo.math"
}
```

Behavior:

- Execute full deterministic validation for one unit.
- Return `PASS|BLOCK` with typed issues.

## Query API

### `GET /v1/units`

Supports filters:

- `source_repo_id=<repo-id>`
- `gate_status=PASS|BLOCK`
- `offset`, `limit`
- `sort=updated_at_desc|updated_at_asc|title_asc|title_desc`

### `GET /v1/repos/{source_repo_id}/units`

Returns units for one producer repo namespace.

### `GET /v1/repos/{source_repo_id}/units/{unit_id}`

Returns normalized unit summary, ingest metadata, and latest validation status.

### `GET /v1/repos/{source_repo_id}/units/{unit_id}/manifest`

Returns indexed `outputs/manifest.json` payload.

### `GET /v1/repos/{source_repo_id}/units/{unit_id}/gates`

Returns gate decision snapshot:

- audit decision
- open severity counters
- rubric parse status
- final author-eligibility status

### `GET /v1/repos/{source_repo_id}/units/{unit_id}/artifacts`

Returns resolved artifact list from manifest:

- `id`, `type`, `path`, `media_type`, `checksum`, `exists`, `checksum_ok`

## Error Taxonomy

- `IO_*`: filesystem/read/manifest missing errors
- `SCHEMA_*`: JSON Schema violations
- `CONSISTENCY_*`: cross-artifact parity violations
- `GATE_*`: rubric/audit/gate-decision violations

## Adapter Interface v1

### AdapterInput

- normalized unit summary
- manifest payload
- artifact index
- gate snapshot

### AdapterOutput

- export metadata
- status (`PASS|BLOCK|WARN`)
- warnings/errors list

V1 default implementation: `xapi_adapter`.  
`case/qti/lti/cmi5` remain optional and experimental in this repository.
