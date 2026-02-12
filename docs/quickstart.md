# Quick Start

## 1. Initialize

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init <PROJECT_NAME> --ai claude
```

## 2. Run the command chain

```text
/lcs.charter
/lcs.define Build a learning unit for ...
/lcs.refine
/lcs.design
/lcs.sequence
/lcs.rubric
/lcs.audit
/lcs.author
```

## 3. Confirm artifacts

Expected under `specs/<###-slug>/`:

- `brief.md`
- `design.md`
- `sequence.md`
- `content-model.md`
- `assessment-map.md`
- `delivery-guide.md`
- `rubrics/`
- `audit-report.md`
- `outputs/`

## Hard Gate Rule

Do not run `/lcs.author` unless:

- rubric items are resolved with evidence,
- audit decision is `PASS`,
- open `CRITICAL/HIGH` count is zero.
