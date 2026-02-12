# Tutoring Platform BFF API v1

This document defines the application-facing API for teacher and learner apps.

## Access model

- Frontends MUST call BFF endpoints only.
- BFF is responsible for calling `lcs-output-consumer`.
- Frontends MUST NOT call consumer APIs directly.

## Catalog

- `GET /api/v1/catalog/units`
- `GET /api/v1/catalog/units/{unit_id}`

## Assignment

- `POST /api/v1/assignments`
- `GET /api/v1/assignments`
- `GET /api/v1/assignments/{assignment_id}`

## Submission and grading

- `POST /api/v1/submissions`
- `POST /api/v1/grades`

## Progress and analytics

- `GET /api/v1/students/{student_id}/progress`
- `GET /api/v1/analytics/classrooms/{classroom_id}`

## Event ingestion

- `POST /api/v1/events/xapi`

Expected payload fields:

- `actor`
- `verb`
- `object`
- `timestamp`
- `context.assignment_id`
- `context.student_id`
- `result.score`
