# Extension Development Guide

This guide is the implementation contract for building LCS extensions in clean-break mode.

## Intent

Build extensions that are deterministic, schema-valid, and compatible with the spec-driven learning-content workflow.

## Mandatory Rules

- You MUST use manifest schema `1.0`.
- You MUST set `requires.lcs_version` (do not use the legacy version key).
- You MUST use command naming pattern: `lcs.<extension-id>.<command>`.
- You MUST use only supported hook events:
  - `after_charter`, `after_define`, `after_refine`, `after_design`,
  - `after_sequence`, `after_rubric`, `after_audit`, `after_author`, `after_issueize`.
- You MUST keep command behavior deterministic (explicit input, output, failure handling).
- You MUST keep extension config under `.lcs/extensions/<extension-id>/`.

## Quick Start

1. Copy template:

```bash
cp -r extensions/template my-extension
cd my-extension
```

2. Edit `extension.yml`:
- set `extension.id`, `extension.name`, `extension.version`
- set `requires.lcs_version`
- declare commands and optional hooks

3. Implement command files in `commands/`.

4. Install locally:

```bash
lcs extension add --dev /path/to/my-extension
```

5. Validate:
- manifest loads without validation errors
- command files are generated for active agents
- hook events resolve correctly

## Recommended Command File Structure

Use this structure for extension command docs:

1. `Intent`
2. `Inputs`
3. `Mandatory Rules (YOU MUST / MUST NOT)`
4. `Execution Steps`
5. `Failure Modes`
6. `Output Contract`
7. `Examples`

## Hook Design

### Optional Hook Example

```yaml
hooks:
  after_sequence:
    command: "lcs.my-extension.sync"
    optional: true
    prompt: "Run extension sync after sequence?"
```

### Mandatory Hook Example

```yaml
hooks:
  after_author:
    command: "lcs.my-extension.publish-local"
    optional: false
    description: "Publish extension metadata after authoring"
```

## Configuration Layers

Precedence (highest first):

1. Environment: `LCS_<EXTENSION>_*`
2. Local config: `.lcs/extensions/<id>/<id>-config.local.yml`
3. Project config: `.lcs/extensions/<id>/<id>-config.yml`
4. Manifest defaults

## Failure Modes to Handle

- Missing required config file.
- Invalid manifest schema.
- Unsupported hook event.
- Missing command source file declared in manifest.
- Incompatible `requires.lcs_version`.

## Test Checklist

- Manifest validation pass.
- Legacy version-key manifest rejected.
- Legacy hook events rejected.
- Command registration for active agents verified.
- Hook registration/unregistration verified.

## Migration Notes (from legacy)

- Rename legacy version key to `requires.lcs_version`.
- Rename legacy sequence hook to `after_sequence`.
- Rename legacy author hook to `after_author`.
- Rename env prefix `SPECKIT_` -> `LCS_`.
