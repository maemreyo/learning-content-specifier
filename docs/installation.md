# Installation Guide

## Prerequisites

- Python 3.11+
- `uv`
- Git
- One supported AI agent (see `AGENTS.md`)

## Install and Initialize

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init <PROJECT_NAME> --ai claude
```

Initialize in current directory:

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init --here --ai claude
```

## Script Variant

- `--script sh` for Bash/Zsh
- `--script ps` for PowerShell
- `--template-source auto|release|local` (default `auto`)

## Verify

```bash
lcs check
```

Your project should include:

- agent command files
- `.lcs/templates/`
- `.lcs/scripts/`
- `.lcs/memory/charter.md`
