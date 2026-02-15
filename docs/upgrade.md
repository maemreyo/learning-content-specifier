# Upgrade Guide

## Upgrade CLI

```bash
uv tool install lcs-cli --force --from git+https://github.com/maemreyo/learning-content-specifier.git
```

## Refresh Project Templates

Run in project root:

```bash
lcs init --here --force --ai <your-agent>
```

This updates:

- agent command files
- `.lcs/scripts/`
- `.lcs/templates/`
- `.lcs/memory/`

This does not update your authored unit artifacts under `programs/<program-id>/units/`.

## Recommended Backup

Before upgrade, commit or back up:

- `.lcs/memory/charter.md`
- any custom `.lcs/templates/*`

## Post-upgrade Validation

1. Run `lcs check`.
2. Confirm new command files (`lcs.charter`, `lcs.define`, `lcs.design`, `lcs.sequence`, `lcs.author`).
3. Run one workflow smoke on a test unit through `/lcs.audit`.
4. For multi-unit programs, confirm `programs/<program-id>/roadmap.json` and `programs/<program-id>/roadmap.md` are generated with `session_start/session_end`.
5. Confirm `/lcs.design` now scaffolds `exercise-design.md` and `exercise-design.json`.
