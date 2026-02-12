# Extension User Guide

## What Extensions Add

Extensions add custom `/lcs.<extension>.*` commands and optional workflow hooks.

## Install

### From local directory (dev)

```bash
lcs extension add --dev /path/to/extension
```

### From catalog

```bash
lcs extension add <extension-id>
```

## List / Inspect

```bash
lcs extension list
lcs extension info <extension-id>
lcs extension search <query>
```

## Enable / Disable / Remove

```bash
lcs extension enable <extension-id>
lcs extension disable <extension-id>
lcs extension remove <extension-id>
```

## Configuration

Config location:

- `.lcs/extensions/<extension-id>/<extension-id>-config.yml`

Optional local override:

- `.lcs/extensions/<extension-id>/<extension-id>-config.local.yml`

Environment overrides:

- `LCS_<EXTENSION>_*`

Example:

```bash
export LCS_JIRA_PROJECT_KEY="LEARN"
```

## Hook Behavior

Hooks run on supported events such as `after_sequence` and `after_author`.

- Optional hook: agent prompts user before running.
- Mandatory hook (`optional: false`): agent should auto-run.

## Troubleshooting

### "Missing requires.lcs_version"

Your extension manifest still uses legacy schema. Replace with `requires.lcs_version`.

### "Invalid hook event"

Use only allowed hook events in clean-break mode.

### "Command not found after install"

- Verify your agent folder exists.
- Re-run `lcs extension add --dev ...`.
- Restart IDE/agent session if command cache persists.

### "Config not applied"

Check override precedence:

1. `LCS_<EXTENSION>_*`
2. `*-config.local.yml`
3. `*-config.yml`
4. defaults
