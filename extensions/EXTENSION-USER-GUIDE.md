# Extension User Guide

Complete guide for using LCS extensions to enhance your workflow.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Finding Extensions](#finding-extensions)
4. [Installing Extensions](#installing-extensions)
5. [Using Extensions](#using-extensions)
6. [Managing Extensions](#managing-extensions)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction

### What are Extensions?

Extensions are modular packages that add new commands and functionality to LCS without bloating the core framework. They allow you to:

- **Integrate** with external tools (Jira, Linear, GitHub, etc.)
- **Automate** repetitive tasks with hooks
- **Customize** workflows for your team
- **Share** solutions across projects

### Why Use Extensions?

- **Clean Core**: Keeps learning-content-specifier lightweight and focused
- **Optional Features**: Only install what you need
- **Community Driven**: Anyone can create and share extensions
- **Version Controlled**: Extensions are versioned independently

---

## Getting Started

### Prerequisites

- LCS version 0.1.0 or higher
- A learning-content-specifier project (directory with `.lcs/` folder)

### Check Your Version

```bash
lcs --version
# Should show 0.1.0 or higher
```

### First Extension

Let's install the Jira extension as an example:

```bash
# 1. Search for the extension
lcs extension search jira

# 2. Get detailed information
lcs extension info jira

# 3. Install it
lcs extension add jira

# 4. Configure it
vim .lcs/extensions/jira/jira-config.yml

# 5. Use it
# (Commands are now available in Claude Code)
/lcs.jira.specstoissues
```

---

## Finding Extensions

### Browse All Extensions

```bash
lcs extension search
```

Shows all available extensions in the catalog.

### Search by Keyword

```bash
# Search for "jira"
lcs extension search jira

# Search for "issue tracking"
lcs extension search issue
```

### Filter by Tag

```bash
# Find all issue-tracking extensions
lcs extension search --tag issue-tracking

# Find all Atlassian tools
lcs extension search --tag atlassian
```

### Filter by Author

```bash
# Extensions by Stats Perform
lcs extension search --author "Stats Perform"
```

### Show Verified Only

```bash
# Only show verified extensions
lcs extension search --verified
```

### Get Extension Details

```bash
# Detailed information
lcs extension info jira
```

Shows:

- Description
- Requirements
- Commands provided
- Hooks available
- Links (documentation, repository, changelog)
- Installation status

---

## Installing Extensions

### Install from Catalog

```bash
# By name (from catalog)
lcs extension add jira
```

This will:

1. Download the extension from GitHub
2. Validate the manifest
3. Check compatibility with your learning-content-specifier version
4. Install to `.lcs/extensions/jira/`
5. Register commands with your AI agent
6. Create config template

### Install from URL

```bash
# From GitHub release
lcs extension add --from https://github.com/org/learning-content-specifier-ext/archive/refs/tags/v1.0.0.zip
```

### Install from Local Directory (Development)

```bash
# For testing or development
lcs extension add --dev /path/to/extension
```

### Installation Output

```text
✓ Extension installed successfully!

Jira Integration (v1.0.0)
  Create Jira Epics, Stories, and Issues from learning-content-specifier artifacts

Provided commands:
  • lcs.jira.specstoissues - Create Jira hierarchy from spec and tasks
  • lcs.jira.discover-fields - Discover Jira custom fields for configuration
  • lcs.jira.sync-status - Sync task completion status to Jira

⚠  Configuration may be required
   Check: .lcs/extensions/jira/
```

---

## Using Extensions

### Using Extension Commands

Extensions add commands that appear in your AI agent (Claude Code):

```text
# In Claude Code
> /lcs.jira.specstoissues

# Or use short alias (if provided)
> /lcs.specstoissues
```

### Extension Configuration

Most extensions require configuration:

```bash
# 1. Find the config file
ls .lcs/extensions/jira/

# 2. Copy template to config
cp .lcs/extensions/jira/jira-config.template.yml \
   .lcs/extensions/jira/jira-config.yml

# 3. Edit configuration
vim .lcs/extensions/jira/jira-config.yml

# 4. Use the extension
# (Commands will now work with your config)
```

### Extension Hooks

Some extensions provide hooks that execute after core commands:

**Example**: Jira extension hooks into `/lcs.sequence`

```text
# Run core command
> /lcs.sequence

# Output includes:
## Extension Hooks

**Optional Hook**: jira
Command: `/lcs.jira.specstoissues`
Description: Automatically create Jira hierarchy after task generation

Prompt: Create Jira issues from tasks?
To execute: `/lcs.jira.specstoissues`
```

You can then choose to run the hook or skip it.

---

## Managing Extensions

### List Installed Extensions

```bash
lcs extension list
```

Output:

```text
Installed Extensions:

  ✓ Jira Integration (v1.0.0)
     Create Jira Epics, Stories, and Issues from learning-content-specifier artifacts
     Commands: 3 | Hooks: 1 | Status: Enabled
```

### Update Extensions

```bash
# Check for updates (all extensions)
lcs extension update

# Update specific extension
lcs extension update jira
```

Output:

```text
🔄 Checking for updates...

Updates available:

  • jira: 1.0.0 → 1.1.0

Update these extensions? [y/N]:
```

### Disable Extension Temporarily

```bash
# Disable without removing
lcs extension disable jira

✓ Extension 'jira' disabled

Commands will no longer be available. Hooks will not execute.
To re-enable: lcs extension enable jira
```

### Re-enable Extension

```bash
lcs extension enable jira

✓ Extension 'jira' enabled
```

### Remove Extension

```bash
# Remove extension (with confirmation)
lcs extension remove jira

# Keep configuration when removing
lcs extension remove jira --keep-config

# Force removal (no confirmation)
lcs extension remove jira --force
```

---

## Configuration

### Configuration Files

Extensions can have multiple configuration files:

```text
.lcs/extensions/jira/
├── jira-config.yml           # Main config (version controlled)
├── jira-config.local.yml     # Local overrides (gitignored)
└── jira-config.template.yml  # Template (reference)
```

### Configuration Layers

Configuration is merged in this order (highest priority last):

1. **Extension defaults** (from `extension.yml`)
2. **Project config** (`jira-config.yml`)
3. **Local overrides** (`jira-config.local.yml`)
4. **Environment variables** (`SPECKIT_JIRA_*`)

### Example: Jira Configuration

**Project config** (`.lcs/extensions/jira/jira-config.yml`):

```yaml
project:
  key: "MSATS"

defaults:
  epic:
    labels: ["spec-driven"]
```

**Local override** (`.lcs/extensions/jira/jira-config.local.yml`):

```yaml
project:
  key: "MYTEST"  # Override for local development
```

**Environment variable**:

```bash
export SPECKIT_JIRA_PROJECT_KEY="DEVTEST"
```

Final resolved config uses `DEVTEST` from environment variable.

### Project-Wide Extension Settings

File: `.lcs/extensions.yml`

```yaml
# Extensions installed in this project
installed:
  - jira
  - linear

# Global settings
settings:
  auto_execute_hooks: true

# Hook configuration
hooks:
  after_tasks:
    - extension: jira
      command: lcs.jira.specstoissues
      enabled: true
      optional: true
      prompt: "Create Jira issues from tasks?"
```

### Core Environment Variables

In addition to extension-specific environment variables (`SPECKIT_{EXT_ID}_*`), learning-content-specifier supports core environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SPECKIT_CATALOG_URL`       | Override the extension catalog URL | GitHub-hosted catalog |
| `GH_TOKEN` / `GITHUB_TOKEN` | GitHub API token for downloads     | None                  |

#### Example: Using a custom catalog for testing

```bash
# Point to a local or alternative catalog
export SPECKIT_CATALOG_URL="http://localhost:8000/catalog.json"

# Or use a staging catalog
export SPECKIT_CATALOG_URL="https://example.com/staging/catalog.json"
```

---

## Organization Catalog Customization

### Why the Default Catalog is Empty

The default learning-content-specifier catalog ships empty by design. This allows organizations to:

- **Control available extensions** - Curate which extensions your team can install
- **Host private extensions** - Internal tools that shouldn't be public
- **Customize for compliance** - Meet security/audit requirements
- **Support air-gapped environments** - Work without internet access

### Setting Up a Custom Catalog

#### 1. Create Your Catalog File

Create a `catalog.json` file with your extensions:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-02-03T00:00:00Z",
  "catalog_url": "https://your-org.com/learning-content-specifier/catalog.json",
  "extensions": {
    "jira": {
      "name": "Jira Integration",
      "id": "jira",
      "description": "Create Jira issues from learning-content-specifier artifacts",
      "author": "Your Organization",
      "version": "2.1.0",
      "download_url": "https://github.com/your-org/learning-content-specifier-jira/archive/refs/tags/v2.1.0.zip",
      "repository": "https://github.com/your-org/learning-content-specifier-jira",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.1.0",
        "tools": [
          {"name": "atlassian-mcp-server", "required": true}
        ]
      },
      "provides": {
        "commands": 3,
        "hooks": 1
      },
      "tags": ["jira", "atlassian", "issue-tracking"],
      "verified": true
    },
    "internal-tool": {
      "name": "Internal Tool Integration",
      "id": "internal-tool",
      "description": "Connect to internal company systems",
      "author": "Your Organization",
      "version": "1.0.0",
      "download_url": "https://internal.your-org.com/extensions/internal-tool-1.0.0.zip",
      "repository": "https://github.internal.your-org.com/learning-content-specifier-internal",
      "license": "Proprietary",
      "requires": {
        "speckit_version": ">=0.1.0"
      },
      "provides": {
        "commands": 2
      },
      "tags": ["internal", "proprietary"],
      "verified": true
    }
  }
}
```

#### 2. Host the Catalog

Options for hosting your catalog:

| Method | URL Example | Use Case |
| ------ | ----------- | -------- |
| GitHub Pages | `https://your-org.github.io/learning-content-specifier-catalog/catalog.json` | Public or org-visible |
| Internal web server | `https://internal.company.com/learning-content-specifier/catalog.json` | Corporate network |
| S3/Cloud storage | `https://s3.amazonaws.com/your-bucket/catalog.json` | Cloud-hosted teams |
| Local file server | `http://localhost:8000/catalog.json` | Development/testing |

**Security requirement**: URLs must use HTTPS (except `localhost` for testing).

#### 3. Configure Your Environment

##### Option A: Environment variable (recommended for CI/CD)

```bash
# In ~/.bashrc, ~/.zshrc, or CI pipeline
export SPECKIT_CATALOG_URL="https://your-org.com/learning-content-specifier/catalog.json"
```

##### Option B: Per-project configuration

Create `.env` or set in your shell before running learning-content-specifier commands:

```bash
SPECKIT_CATALOG_URL="https://your-org.com/learning-content-specifier/catalog.json" lcs extension search
```

#### 4. Verify Configuration

```bash
# Search should now show your catalog's extensions
lcs extension search

# Install from your catalog
lcs extension add jira
```

### Catalog JSON Schema

Required fields for each extension entry:

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `name` | string | Yes | Human-readable name |
| `id` | string | Yes | Unique identifier (lowercase, hyphens) |
| `version` | string | Yes | Semantic version (X.Y.Z) |
| `download_url` | string | Yes | URL to ZIP archive |
| `repository` | string | Yes | Source code URL |
| `description` | string | No | Brief description |
| `author` | string | No | Author/organization |
| `license` | string | No | SPDX license identifier |
| `requires.speckit_version` | string | No | Version constraint |
| `requires.tools` | array | No | Required external tools |
| `provides.commands` | number | No | Number of commands |
| `provides.hooks` | number | No | Number of hooks |
| `tags` | array | No | Search tags |
| `verified` | boolean | No | Verification status |

### Use Cases

#### Private/Internal Extensions

Host proprietary extensions that integrate with internal systems:

```json
{
  "internal-auth": {
    "name": "Internal SSO Integration",
    "download_url": "https://artifactory.company.com/learning-content-specifier/internal-auth-1.0.0.zip",
    "verified": true
  }
}
```

#### Curated Team Catalog

Limit which extensions your team can install:

```json
{
  "extensions": {
    "jira": { "..." },
    "github": { "..." }
  }
}
```

Only `jira` and `github` will appear in `lcs extension search`.

#### Air-Gapped Environments

For networks without internet access:

1. Download extension ZIPs to internal file server
2. Create catalog pointing to internal URLs
3. Host catalog on internal web server

```json
{
  "jira": {
    "download_url": "https://files.internal/learning-content-specifier/jira-2.1.0.zip"
  }
}
```

#### Development/Testing

Test new extensions before publishing:

```bash
# Start local server
python -m http.server 8000 --directory ./my-catalog/

# Point learning-content-specifier to local catalog
export SPECKIT_CATALOG_URL="http://localhost:8000/catalog.json"

# Test installation
lcs extension add my-new-extension
```

### Combining with Direct Installation

You can still install extensions not in your catalog using `--from`:

```bash
# From catalog
lcs extension add jira

# Direct URL (bypasses catalog)
lcs extension add --from https://github.com/someone/learning-content-specifier-ext/archive/v1.0.0.zip

# Local development
lcs extension add --dev /path/to/extension
```

**Note**: Direct URL installation shows a security warning since the extension isn't from your configured catalog.

---

## Troubleshooting

### Extension Not Found

**Error**: `Extension 'jira' not found in catalog

**Solutions**:

1. Check spelling: `lcs extension search jira`
2. Refresh catalog: `lcs extension search --help`
3. Check internet connection
4. Extension may not be published yet

### Configuration Not Found

**Error**: `Jira configuration not found`

**Solutions**:

1. Check if extension is installed: `lcs extension list`
2. Create config from template:

   ```bash
   cp .lcs/extensions/jira/jira-config.template.yml \
      .lcs/extensions/jira/jira-config.yml
   ```

3. Reinstall extension: `lcs extension remove jira && lcs extension add jira`

### Command Not Available

**Issue**: Extension command not appearing in AI agent

**Solutions**:

1. Check extension is enabled: `lcs extension list`
2. Restart AI agent (Claude Code)
3. Check command file exists:

   ```bash
   ls .claude/commands/lcs.jira.*.md
   ```

4. Reinstall extension

### Incompatible Version

**Error**: `Extension requires learning-content-specifier >=0.2.0, but you have 0.1.0`

**Solutions**:

1. Upgrade learning-content-specifier:

   ```bash
   uv tool upgrade lcs-cli
   ```

2. Install older version of extension:

   ```bash
   lcs extension add --from https://github.com/org/ext/archive/v1.0.0.zip
   ```

### MCP Tool Not Available

**Error**: `Tool 'jira-mcp-server/epic_create' not found`

**Solutions**:

1. Check MCP server is installed
2. Check AI agent MCP configuration
3. Restart AI agent
4. Check extension requirements: `lcs extension info jira`

### Permission Denied

**Error**: `Permission denied` when accessing Jira

**Solutions**:

1. Check Jira credentials in MCP server config
2. Verify project permissions in Jira
3. Test MCP server connection independently

---

## Best Practices

### 1. Version Control

**Do commit**:

- `.lcs/extensions.yml` (project extension config)
- `.lcs/extensions/*/jira-config.yml` (project config)

**Don't commit**:

- `.lcs/extensions/.cache/` (catalog cache)
- `.lcs/extensions/.backup/` (config backups)
- `.lcs/extensions/*/*.local.yml` (local overrides)
- `.lcs/extensions/.registry` (installation state)

Add to `.gitignore`:

```gitignore
.lcs/extensions/.cache/
.lcs/extensions/.backup/
.lcs/extensions/*/*.local.yml
.lcs/extensions/.registry
```

### 2. Team Workflows

**For teams**:

1. Agree on which extensions to use
2. Commit extension configuration
3. Document extension usage in README
4. Keep extensions updated together

**Example README section**:

```markdown
## Extensions

This project uses:
- **jira** (v1.0.0) - Jira integration
  - Config: `.lcs/extensions/jira/jira-config.yml`
  - Requires: jira-mcp-server

To install: `lcs extension add jira`
```

### 3. Local Development

Use local config for development:

```yaml
# .lcs/extensions/jira/jira-config.local.yml
project:
  key: "DEVTEST"  # Your test project

defaults:
  task:
    custom_fields:
      customfield_10002: 1  # Lower story points for testing
```

### 4. Environment-Specific Config

Use environment variables for CI/CD:

```bash
# .github/workflows/deploy.yml
env:
  SPECKIT_JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT }}

- name: Create Jira Issues
  run: lcs extension add jira && ...
```

### 5. Extension Updates

**Check for updates regularly**:

```bash
# Weekly or before major releases
lcs extension update
```

**Pin versions for stability**:

```yaml
# .lcs/extensions.yml
installed:
  - id: jira
    version: "1.0.0"  # Pin to specific version
```

### 6. Minimal Extensions

Only install extensions you actively use:

- Reduces complexity
- Faster command loading
- Less configuration

### 7. Documentation

Document extension usage in your project:

```markdown
# PROJECT.md

## Working with Jira

After creating tasks, sync to Jira:
1. Run `/lcs.sequence` to generate tasks
2. Run `/lcs.jira.specstoissues` to create Jira issues
3. Run `/lcs.jira.sync-status` to update status
```

---

## FAQ

### Q: Can I use multiple extensions at once?

**A**: Yes! Extensions are designed to work together. Install as many as you need.

### Q: Do extensions slow down learning-content-specifier?

**A**: No. Extensions are loaded on-demand and only when their commands are used.

### Q: Can I create private extensions?

**A**: Yes. Install with `--dev` or `--from` and keep private. Public catalog submission is optional.

### Q: How do I know if an extension is safe?

**A**: Look for the ✓ Verified badge. Verified extensions are reviewed by maintainers. Always review extension code before installing.

### Q: Can extensions modify learning-content-specifier core?

**A**: No. Extensions can only add commands and hooks. They cannot modify core functionality.

### Q: What happens if two extensions have the same command name?

**A**: Extensions use namespaced commands (`lcs.{extension}.{command}`), so conflicts are very rare. The extension system will warn you if conflicts occur.

### Q: Can I contribute to existing extensions?

**A**: Yes! Most extensions are open source. Check the repository link in `lcs extension info {extension}`.

### Q: How do I report extension bugs?

**A**: Go to the extension's repository (shown in `lcs extension info`) and create an issue.

### Q: Can extensions work offline?

**A**: Once installed, extensions work offline. However, some extensions may require internet for their functionality (e.g., Jira requires Jira API access).

### Q: How do I backup my extension configuration?

**A**: Extension configs are in `.lcs/extensions/{extension}/`. Back up this directory or commit configs to git.

---

## Support

- **Extension Issues**: Report to extension repository (see `lcs extension info`)
- **LCS Issues**: <https://github.com/statsperform/learning-content-specifier/issues>
- **Extension Catalog**: <https://github.com/statsperform/learning-content-specifier/tree/main/extensions>
- **Documentation**: See EXTENSION-DEVELOPMENT-GUIDE.md and EXTENSION-PUBLISHING-GUIDE.md

---

*Last Updated: 2026-01-28*
*LCS Version: 0.1.0*
