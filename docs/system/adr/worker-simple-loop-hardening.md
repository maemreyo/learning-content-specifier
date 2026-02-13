# ADR: Worker Simple-Loop Hardening

## Status
Accepted

## Context
v1 keeps DB-backed queue orchestration (no Redis/Celery), but needs safe multi-worker behavior.

## Decision
- Keep simple worker loop architecture.
- Harden with atomic claiming, retry windows, and heartbeat telemetry.

## Consequences
- Maintains operational simplicity while improving concurrency safety.
