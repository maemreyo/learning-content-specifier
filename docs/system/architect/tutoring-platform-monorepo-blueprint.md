# Tutoring Platform Monorepo Blueprint

## Purpose

Define the standalone application layer for tutoring use cases:

- `Teacher Studio`: assign, grade, track, remediate.
- `Learner Portal`: receive assignments, study, submit, review feedback.

This repo consumes `lcs-output-consumer` via BFF-only integration.

## Topology

1. `learning-content-specifier` (Factory): produces content artifacts and contracts.
2. `lcs-output-consumer` (Library): validates and exposes unit catalog APIs.
3. `tutoring-platform` (Apps): teacher + learner product surfaces.

## Monorepo Structure

```text
tutoring-platform/
├── apps/
│   ├── teacher/
│   └── learner/
├── services/
│   ├── bff/
│   └── workers/
├── packages/
│   ├── api-client/
│   ├── shared-ui/
│   └── types/
├── contracts/
│   └── consumer-contract-version.txt
├── infra/
│   ├── supabase/
│   └── ops/
└── integration-manifest.md
```

## Integration Rules

1. Frontends MUST call BFF only.
2. BFF is the only component that calls consumer endpoints.
3. Contract major compatibility is required between consumer package and pinned `contracts/consumer-contract-version.txt`.
4. Assignment creation MUST snapshot unit metadata (`unit_title`, `unit_version`, `outcomes_snapshot`, `manifest_ref`).

## API Contracts (BFF v1)

- `GET /api/v1/catalog/units`
- `GET /api/v1/catalog/units/{unit_id}`
- `POST /api/v1/assignments`
- `GET /api/v1/assignments`
- `GET /api/v1/assignments/{assignment_id}`
- `POST /api/v1/submissions`
- `GET /api/v1/students/{student_id}/progress`
- `POST /api/v1/grades`
- `GET /api/v1/analytics/classrooms/{classroom_id}`
- `POST /api/v1/events/xapi`

## Progress Pipeline

1. Learner events are posted to `/api/v1/events/xapi`.
2. Events land in `event_inbox`.
3. Worker aggregates by `assignment_id`, `student_id`, `lo_id`.
4. Dashboard reads aggregate tables (`outcome_progress`, `progress_snapshots`).

## Bootstrap

Use core script:

```bash
uv run python factory/scripts/python/scaffold_tutoring_platform.py --target ../tutoring-platform --consumer-base-url http://localhost:8000
```
