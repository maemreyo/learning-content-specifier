# Extension API Reference

## Manifest Schema (`extension.yml`)

### Required Top-Level Keys

- `schema_version` (must be `1.0`)
- `extension`
- `requires`
- `provides`

### `extension`

Required fields:

- `id`: lowercase alphanumeric + hyphen only
- `name`
- `version`: semantic version
- `description`

### `requires`

Required fields:

- `lcs_version`: version specifier (for example `>=0.3.0,<1.0.0`)

Optional fields:

- `tools`: external tool constraints

### `provides.commands`

Each command requires:

- `name`: `lcs.<extension-id>.<command-name>`
- `file`: relative path to source command file

Optional:

- `aliases`: list of alias command names

### `hooks`

Supported event names only:

- `after_charter`
- `after_define`
- `after_refine`
- `after_design`
- `after_sequence`
- `after_rubric`
- `after_audit`
- `after_author`
- `after_issueize`

Hook object fields:

- `command` (required)
- `optional` (default: true)
- `prompt` (optional)
- `description` (optional)
- `condition` (optional)

## Python Runtime APIs

### `ExtensionManifest`

- Validates schema and command naming.
- Validates `requires.lcs_version` presence.
- Validates hook events against allowlist.

### `ExtensionManager`

Main operations:

- `install_from_directory(source_dir, lcs_version, register_commands=True)`
- `install_from_zip(zip_path, lcs_version)`
- `remove(extension_id, keep_config=False)`
- `list_installed()`

### `CommandRegistrar`

- Registers extension commands to all detected agent directories.
- Converts placeholder formats per agent (`$ARGUMENTS` vs `{{args}}`).
- Adjusts script paths into `.lcs/scripts/*` at render time.

### `HookExecutor`

- Registers hooks into `.lcs/extensions.yml`.
- Filters hooks by event and optional condition.
- Returns execution instructions for agent-side invocation.

## Errors

- `ValidationError`: manifest/schema/format errors.
- `CompatibilityError`: incompatible `requires.lcs_version`.
- `ExtensionError`: operational errors (install/remove/register).

## Security Notes

- ZIP install performs path traversal protection.
- Catalog URL and download URL enforce HTTPS (except localhost for dev).

## Deprecated and Rejected

- Legacy version-key field (rejected)
- Legacy sequence/author hook event names (rejected)
