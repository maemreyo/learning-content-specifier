# Consumer API v1 (Headless Backbone)

This is the normative API surface for the standalone consumer platform MVP.

## Ingestion API

### `POST /v1/ingestions/fs`

Request:

```json
{
  "repo_path": "/absolute/path/to/project",
  "unit_glob": "specs/*",
  "contract_version": "1.0.0"
}
```

Behavior:

- Discover units from filesystem.
- Require `specs/<unit>/outputs/manifest.json`.
- Validate contract checksum policy before ingestion.
- Run schema + consistency + gate checks.

### `POST /v1/validations/unit`

Request:

```json
{
  "unit_path": "/absolute/path/to/project/specs/993-e2e-golden-path"
}
```

Behavior:

- Execute full deterministic validation for one unit.
- Return `PASS|BLOCK` with typed issues.

## Query API

### `GET /v1/units`

Supports filters:

- `gate_status=PASS|BLOCK`
- `entry_level=beginner|intermediate|advanced|mixed`
- `modality=self-paced|instructor-led|blended|cohort-based|virtual-led|unspecified`
- `duration_min`, `duration_max`

### `GET /v1/units/{unit_id}`

Returns normalized unit summary, ingest metadata, and latest validation status.

### `GET /v1/units/{unit_id}/manifest`

Returns indexed `outputs/manifest.json` payload.

### `GET /v1/units/{unit_id}/gates`

Returns gate decision snapshot:

- audit decision
- open severity counters
- rubric parse status
- final author-eligibility status

### `GET /v1/units/{unit_id}/artifacts`

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
