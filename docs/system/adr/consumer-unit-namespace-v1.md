# ADR: Consumer Unit Namespace v1

## Status
Accepted

## Context
Factory artifacts are produced in many independent repos; downstream consumer must index without `unit_id` collisions.

## Decision
- Consumer-facing canonical paths are namespaced by `source_repo_id`.
- Factory-side integration docs and contract docs now treat `source_repo_id` as required ingestion metadata.

## Consequences
- Clean-break in downstream API consumers.
- Deterministic multi-repo indexing and retrieval.
