# Extension Migration Notes (Breaking)

## Required Manifest Changes

- Replace `requires.speckit_version` with `requires.lcs_version`.
- Use hook events from the new allowlist only:
  - `after_charter`, `after_define`, `after_refine`, `after_design`,
  - `after_sequence`, `after_rubric`, `after_audit`, `after_author`, `after_issueize`.

## Removed Legacy Events

- `after_tasks` (removed)
- `after_implement` (removed)

## Agent Path Conventions

Follow `AGENTS.md` as source of truth. Notable paths:

- codex: `.codex/commands/`
- kilocode: `.kilocode/workflows/`
- opencode: `.opencode/commands/`
- auggie: `.augment/commands/`
- roo: `.roo/commands/`

## Environment Prefix

Use `LCS_<EXTENSION>_*` for extension config overrides.
