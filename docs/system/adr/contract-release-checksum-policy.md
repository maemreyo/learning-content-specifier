# ADR: Contract Release Checksum Policy

## Status
Accepted

## Context
Installer-first workflows and consumer sync depend on release artifacts; integrity and compatibility checks are mandatory.

## Decision
- Contract and template release assets ship with `.sha256` sidecars.
- Bootstrap/sync default behavior validates checksums and contract major compatibility.
- Local path mode stays explicit development-only mode.

## Consequences
- Stronger deterministic release consumption and clearer failure diagnostics.
