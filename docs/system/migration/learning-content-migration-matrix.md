# Learning Content Migration Matrix

| Area | File(s) | Drift | Severity | Target Fix |
|---|---|---|---|---|
| Command templates | `factory/templates/commands/*.md` | Short/underspecified workflows | High | Rewritten with strict sections and hard-gate contracts |
| Script contracts | `factory/scripts/bash/*`, `factory/scripts/powershell/*` | Branch check, schema drift, bool mismatch risk | High | Added skip branch check, UNIT_* schema, deterministic gate validator |
| Agent context | `scripts/*/update-agent-context.*` | Fragile metadata parsing | Medium | Robust field parsing from design/brief and unit vocabulary |
| Extension runtime | `src/lcs_cli/extensions.py` | Legacy hook events, missing codex mapping | High | Added hook allowlist and codex/cursor-agent alignment |
| Extension template/docs | `extensions/template/*`, `extensions/*.md` | `speckit_*`, old hooks | High | Migrated to `lcs_version`, `after_sequence`, `after_author` |
| Packaging | `tooling/ci/create-release-packages.*` | `.lcs.lcs` rewrite bug; agent dir mismatch | High | Safer rewrite regex; AGENTS.md folder conventions |
| Editor onboarding | `factory/templates/vscode-settings.json`, `.devcontainer/devcontainer.json` | Old command recommendations | Medium | Updated to charter/define/design/sequence/author |
| Core docs | `README.md`, `spec-driven.md`, `docs/*.md` | Software-first semantics and broken links | High | Rewrite to learning-content semantics + fixed links |
| CI/QA | `.github/workflows/lint.yml`, tests | Missing pytest/contracts smoke/docs checks | High | Added CI jobs and smoke scripts |

Owner: core maintainers
