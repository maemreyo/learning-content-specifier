---
description: Convert sequence tasks into dependency-ordered GitHub issues.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## Intent

Publish executable sequence work to GitHub issues while preserving dependencies and LO mapping.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST verify remote origin is a GitHub repository.
- YOU MUST create one issue per actionable sequence task.
- YOU MUST preserve dependency order and LO tags in issue metadata.
- YOU MUST NOT create duplicate issues for already tracked tasks.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`.
2. Load `UNIT_DIR/sequence.md`.
3. Resolve repository from `git remote origin`.
4. Create issues with task ID, LO mapping, dependency notes, and artifact paths.
5. Return created issue URLs and skipped items.

## Hard Gates

- Gate G-IS-001: only GitHub remotes are allowed.
- Gate G-IS-002: no dependency task appears after dependent tasks in issue order.

## Failure Modes

- Non-GitHub remote: stop and explain requirement.
- Missing sequence: stop and require `/lcs.sequence`.

## Output Contract

- External output: GitHub issues.
- Local report in response: created links, skipped reasons.
- Local report MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.programs workflow-status --program <program_id>`
  - `/lcs.author ...` for tasks that remain local-only.

## Examples

- Success: all open sequence tasks converted into ordered issues.
- Fail: remote is not GitHub -> no issue creation.
