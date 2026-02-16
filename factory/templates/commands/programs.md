---
description: Manage active learning program and unit context before running workflow commands.
argument-hint: "[action plus options, e.g. list/current/recommend/activate/workflow-status]"
scripts:
  sh: factory/scripts/bash/manage-program-context.sh --json {ARGS}
  ps: factory/scripts/powershell/manage-program-context.ps1 --json {ARGS}
---

## Intent

Inspect, recommend, and switch active `program_id` / `unit_id` context for deterministic multi-program workflows.

## Inputs

```text
$ARGUMENTS
```

## Supported Actions

- `list` -> list all programs with active marker and metadata.
- `current` -> show current active context.
- `recommend --intent "..."` -> recommend whether to reuse existing or create new.
- `activate --program <program_id> [--unit <unit_id>] [--clear-unit]` -> switch active context.
- `list-units [--program <program_id>]` -> list units and readiness flags.
- `workflow-status [--program <program_id>]` -> summarize missing stages and emit ready-to-run follow-up tasks.
- `resolve-unit --intent "<free text>" [--for-stage design] [--activate-resolved]` -> resolve phrases like "next unit" to a concrete unit id.

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run `{SCRIPT}` exactly once.
- YOU MUST use this command before `/lcs.refine` or `/lcs.design` when the active program has multiple units.
- YOU MUST activate a target unit explicitly when authoring/designing a specific unit.
- YOU MUST NOT edit `.lcs/context/*` manually when this command is available.

## Output Contract

- JSON response from script with deterministic context fields.
- If action is `activate`, `.lcs/context/current-program` is updated and unit context is updated/cleared based on arguments.
- If action is `workflow-status`, output includes `follow_up_tasks` with actionable next command prompts.

## Examples

- `/lcs.programs list`
- `/lcs.programs recommend --intent "IELTS Writing 5.0 to 7.5 in 30 days"`
- `/lcs.programs activate --program ielts-writing-5-0-to-7-5-in-30-days-20260215-2122 --unit 003-unit-task-academic`
- `/lcs.programs workflow-status --program ielts-writing-5-0-to-7-5-in-30-days-20260215-2122`
- `/lcs.programs resolve-unit --intent "Generate design artifacts for next unit" --for-stage design --activate-resolved`
