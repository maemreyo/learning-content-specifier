# Extension Development Guide

A guide for creating LCS extensions.

---

## Quick Start

### 1. Create Extension Directory

```bash
mkdir my-extension
cd my-extension
```

### 2. Create `extension.yml` Manifest

```yaml
schema_version: "1.0"

extension:
  id: "my-ext"                          # Lowercase, alphanumeric + hyphens only
  name: "My Extension"
  version: "1.0.0"                      # Semantic versioning
  description: "My custom extension"
  author: "Your Name"
  repository: "https://github.com/you/learning-content-specifier-my-ext"
  license: "MIT"

requires:
  lcs_version: ">=0.1.0"            # Minimum learning-content-specifier version
  tools:                                # Optional: External tools required
    - name: "my-tool"
      required: true
      version: ">=1.0.0"
  commands:                             # Optional: Core commands needed
    - "lcs.sequence"

provides:
  commands:
    - name: "lcs.my-ext.hello"      # Must follow pattern: lcs.{ext-id}.{cmd}
      file: "commands/hello.md"
      description: "Say hello"
      aliases: ["lcs.hello"]        # Optional aliases

  config:                               # Optional: Config files
    - name: "my-ext-config.yml"
      template: "my-ext-config.template.yml"
      description: "Extension configuration"
      required: false

hooks:                                  # Optional: Integration hooks
  after_sequence:
    command: "lcs.my-ext.hello"
    optional: true
    prompt: "Run hello command?"

tags:                                   # Optional: For catalog search
  - "example"
  - "utility"
```

### 3. Create Commands Directory

```bash
mkdir commands
```

### 4. Create Command File

**File**: `commands/hello.md`

```markdown
---
description: "Say hello command"
tools:                              # Optional: AI tools this command uses
  - 'some-tool/function'
scripts:                            # Optional: Helper scripts
  sh: ../../scripts/bash/helper.sh
  ps: ../../scripts/powershell/helper.ps1
---

# Hello Command

This command says hello!

## User Input

$ARGUMENTS

## Steps

1. Greet the user
2. Show extension is working

```bash
echo "Hello from my extension!"
echo "Arguments: $ARGUMENTS"
```

## Extension Configuration

Load extension config from `.lcs/extensions/my-ext/my-ext-config.yml`.

### 5. Test Locally

```bash
cd /path/to/learning-content-specifier-project
lcs extension add --dev /path/to/my-extension
```

### 6. Verify Installation

```bash
lcs extension list

# Should show:
#  ✓ My Extension (v1.0.0)
#     My custom extension
#     Commands: 1 | Hooks: 1 | Status: Enabled
```

### 7. Test Command

If using Claude:

```bash
claude
> /lcs.my-ext.hello world
```

The command will be available in `.claude/commands/lcs.my-ext.hello.md`.

---

## Manifest Schema Reference

### Required Fields

#### `schema_version`

Extension manifest schema version. Currently: `"1.0"`

#### `extension`

Extension metadata block.

**Required sub-fields**:

- `id`: Extension identifier (lowercase, alphanumeric, hyphens)
- `name`: Human-readable name
- `version`: Semantic version (e.g., "1.0.0")
- `description`: Short description

**Optional sub-fields**:

- `author`: Extension author
- `repository`: Source code URL
- `license`: SPDX license identifier
- `homepage`: Extension homepage URL

#### `requires`

Compatibility requirements.

**Required sub-fields**:

- `lcs_version`: Semantic version specifier (e.g., ">=0.1.0,<2.0.0")

**Optional sub-fields**:

- `tools`: External tools required (array of tool objects)
- `commands`: Core learning-content-specifier commands needed (array of command names)
- `scripts`: Core scripts required (array of script names)

#### `provides`

What the extension provides.

**Required sub-fields**:

- `commands`: Array of command objects (must have at least one)

**Command object**:

- `name`: Command name (must match `lcs.{ext-id}.{command}`)
- `file`: Path to command file (relative to extension root)
- `description`: Command description (optional)
- `aliases`: Alternative command names (optional, array)

### Optional Fields

#### `hooks`

Integration hooks for automatic execution.

Available hook points:

- `after_sequence`: After `/lcs.sequence` completes
- `after_author`: After `/lcs.author` completes (future)

Hook object:

- `command`: Command to execute (must be in `provides.commands`)
- `optional`: If true, prompt user before executing
- `prompt`: Prompt text for optional hooks
- `description`: Hook description
- `condition`: Execution condition (future)

#### `tags`

Array of tags for catalog discovery.

#### `defaults`

Default extension configuration values.

#### `config_schema`

JSON Schema for validating extension configuration.

---

## Command File Format

### Frontmatter (YAML)

```yaml
---
description: "Command description"          # Required
tools:                                      # Optional
  - 'tool-name/function'
scripts:                                    # Optional
  sh: ../../scripts/bash/helper.sh
  ps: ../../scripts/powershell/helper.ps1
---
```

### Body (Markdown)

Use standard Markdown with special placeholders:

- `$ARGUMENTS`: User-provided arguments
- `{SCRIPT}`: Replaced with script path during registration

**Example**:

````markdown
## Steps

1. Parse arguments
2. Execute logic

```bash
args="$ARGUMENTS"
echo "Running with args: $args"
```
````

### Script Path Rewriting

Extension commands use relative paths that get rewritten during registration:

**In extension**:

```yaml
scripts:
  sh: ../../scripts/bash/helper.sh
```

**After registration**:

```yaml
scripts:
  sh: .lcs/scripts/bash/helper.sh
```

This allows scripts to reference core learning-content-specifier scripts.

---

## Configuration Files

### Config Template

**File**: `my-ext-config.template.yml`

```yaml
# My Extension Configuration
# Copy this to my-ext-config.yml and customize

# Example configuration
api:
  endpoint: "https://api.example.com"
  timeout: 30

features:
  feature_a: true
  feature_b: false

credentials:
  # DO NOT commit credentials!
  # Use environment variables instead
  api_key: "${MY_EXT_API_KEY}"
```

### Config Loading

In your command, load config with layered precedence:

1. Extension defaults (`extension.yml` → `defaults`)
2. Project config (`.lcs/extensions/my-ext/my-ext-config.yml`)
3. Local overrides (`.lcs/extensions/my-ext/my-ext-config.local.yml` - gitignored)
4. Environment variables (`LCS_MY_EXT_*`)

**Example loading script**:

```bash
#!/usr/bin/env bash
EXT_DIR=".lcs/extensions/my-ext"

# Load and merge config
config=$(yq eval '.' "$EXT_DIR/my-ext-config.yml" -o=json)

# Apply env overrides
if [ -n "${LCS_MY_EXT_API_KEY:-}" ]; then
  config=$(echo "$config" | jq ".api.api_key = \"$LCS_MY_EXT_API_KEY\"")
fi

echo "$config"
```

---

## Validation Rules

### Extension ID

- **Pattern**: `^[a-z0-9-]+$`
- **Valid**: `my-ext`, `tool-123`, `awesome-plugin`
- **Invalid**: `MyExt` (uppercase), `my_ext` (underscore), `my ext` (space)

### Extension Version

- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Valid**: `1.0.0`, `0.1.0`, `2.5.3`
- **Invalid**: `1.0`, `v1.0.0`, `1.0.0-beta`

### Command Name

- **Pattern**: `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`
- **Valid**: `lcs.my-ext.hello`, `lcs.tool.cmd`
- **Invalid**: `my-ext.hello` (missing prefix), `lcs.hello` (no extension namespace)

### Command File Path

- **Must be** relative to extension root
- **Valid**: `commands/hello.md`, `commands/subdir/cmd.md`
- **Invalid**: `/absolute/path.md`, `../outside.md`

---

## Testing Extensions

### Manual Testing

1. **Create test extension**
2. **Install locally**:

   ```bash
   lcs extension add --dev /path/to/extension
   ```

3. **Verify installation**:

   ```bash
   lcs extension list
   ```

4. **Test commands** with your AI agent
5. **Check command registration**:

   ```bash
   ls .claude/commands/lcs.my-ext.*
   ```

6. **Remove extension**:

   ```bash
   lcs extension remove my-ext
   ```

### Automated Testing

Create tests for your extension:

```python
# tests/test_my_extension.py
import pytest
from pathlib import Path
from specify_cli.extensions import ExtensionManifest

def test_manifest_valid():
    """Test extension manifest is valid."""
    manifest = ExtensionManifest(Path("extension.yml"))
    assert manifest.id == "my-ext"
    assert len(manifest.commands) >= 1

def test_command_files_exist():
    """Test all command files exist."""
    manifest = ExtensionManifest(Path("extension.yml"))
    for cmd in manifest.commands:
        cmd_file = Path(cmd["file"])
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"
```

---

## Distribution

### Option 1: GitHub Repository

1. **Create repository**: `learning-content-specifier-my-ext`
2. **Add files**:

   ```text
   learning-content-specifier-my-ext/
   ├── extension.yml
   ├── commands/
   ├── scripts/
   ├── docs/
   ├── README.md
   ├── LICENSE
   └── CHANGELOG.md
   ```

3. **Create release**: Tag with version (e.g., `v1.0.0`)
4. **Install from repo**:

   ```bash
   git clone https://github.com/you/learning-content-specifier-my-ext
   lcs extension add --dev learning-content-specifier-my-ext/
   ```

### Option 2: ZIP Archive (Future)

Create ZIP archive and host on GitHub Releases:

```bash
zip -r learning-content-specifier-my-ext-1.0.0.zip extension.yml commands/ scripts/ docs/
```

Users install with:

```bash
lcs extension add --from https://github.com/.../learning-content-specifier-my-ext-1.0.0.zip
```

### Option 3: Extension Catalog (Future)

Submit to official catalog:

1. **Fork** learning-content-specifier repository
2. **Add entry** to `extensions/catalog.json`
3. **Create PR**
4. **After merge**, users can install with:

   ```bash
   lcs extension add my-ext  # No URL needed!
   ```

---

## Best Practices

### Naming Conventions

- **Extension ID**: Use descriptive, hyphenated names (`jira-integration`, not `ji`)
- **Commands**: Use verb-noun pattern (`create-issue`, `sync-status`)
- **Config files**: Match extension ID (`jira-config.yml`)

### Documentation

- **README.md**: Overview, installation, usage
- **CHANGELOG.md**: Version history
- **docs/**: Detailed guides
- **Command descriptions**: Clear, concise

### Versioning

- **Follow SemVer**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features
- **PATCH**: Bug fixes

### Security

- **Never commit secrets**: Use environment variables
- **Validate input**: Sanitize user arguments
- **Document permissions**: What files/APIs are accessed

### Compatibility

- **Specify version range**: Don't require exact version
- **Test with multiple versions**: Ensure compatibility
- **Graceful degradation**: Handle missing features

---

## Example Extensions

### Minimal Extension

Smallest possible extension:

```yaml
# extension.yml
schema_version: "1.0"
extension:
  id: "minimal"
  name: "Minimal Extension"
  version: "1.0.0"
  description: "Minimal example"
requires:
  lcs_version: ">=0.1.0"
provides:
  commands:
    - name: "lcs.minimal.hello"
      file: "commands/hello.md"
```

````markdown
<!-- commands/hello.md -->
---
description: "Hello command"
---

# Hello World

```bash
echo "Hello, $ARGUMENTS!"
```
````

### Extension with Config

Extension using configuration:

```yaml
# extension.yml
# ... metadata ...
provides:
  config:
    - name: "tool-config.yml"
      template: "tool-config.template.yml"
      required: true
```

```yaml
# tool-config.template.yml
api_endpoint: "https://api.example.com"
timeout: 30
```

````markdown
<!-- commands/use-config.md -->
# Use Config

Load config:
```bash
config_file=".lcs/extensions/tool/tool-config.yml"
endpoint=$(yq eval '.api_endpoint' "$config_file")
echo "Using endpoint: $endpoint"
```
````

### Extension with Hooks

Extension that runs automatically:

```yaml
# extension.yml
hooks:
  after_sequence:
    command: "lcs.auto.analyze"
    optional: false  # Always run
    description: "Analyze tasks after generation"
```

---

## Troubleshooting

### Extension won't install

**Error**: `Invalid extension ID`

- **Fix**: Use lowercase, alphanumeric + hyphens only

**Error**: `Extension requires learning-content-specifier >=0.2.0`

- **Fix**: Update learning-content-specifier with `uv tool install lcs-cli --force`

**Error**: `Command file not found`

- **Fix**: Ensure command files exist at paths specified in manifest

### Commands not registered

**Symptom**: Commands don't appear in AI agent

**Check**:

1. `.claude/commands/` directory exists
2. Extension installed successfully
3. Commands registered in registry:

   ```bash
   cat .lcs/extensions/.registry
   ```

**Fix**: Reinstall extension to trigger registration

### Config not loading

**Check**:

1. Config file exists: `.lcs/extensions/{ext-id}/{ext-id}-config.yml`
2. YAML syntax is valid: `yq eval '.' config.yml`
3. Environment variables set correctly

---

## Getting Help

- **Issues**: Report bugs at GitHub repository
- **Discussions**: Ask questions in GitHub Discussions
- **Examples**: See `learning-content-specifier-jira` for full-featured example (Phase B)

---

## Next Steps

1. **Create your extension** following this guide
2. **Test locally** with `--dev` flag
3. **Share with community** (GitHub, catalog)
4. **Iterate** based on feedback

Happy extending! 🚀
