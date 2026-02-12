---
description: "Example command that demonstrates extension functionality"
tools:
  - 'example-mcp-server/example_tool'
---

## Intent

Demonstrate a production-grade extension command with deterministic inputs/outputs.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST load extension config from `.lcs/extensions/my-extension/my-extension-config.yml`.
- YOU MUST support environment overrides with `LCS_MY_EXTENSION_*` keys.
- YOU MUST fail fast when required config is missing.
- YOU MUST NOT execute side effects without explicit confirmation in command flow.

## Execution Steps

1. Read configuration file and validate required keys.
2. Apply environment overrides:
   - `LCS_MY_EXTENSION_KEY`
   - `LCS_MY_EXTENSION_ANOTHER_KEY`
3. Execute MCP tool call with validated parameters.
4. Return a concise machine-readable summary.

## Output Contract

Return:

- status (`PASS` or `BLOCK`)
- action summary
- output path (if files are written)

## Example

```bash
export LCS_MY_EXTENSION_KEY="override-value"
/lcs.my-extension.example validate sequence alignment
```
