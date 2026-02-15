# LCS Documentation

Learning Content Specifier documentation.

## Getting Started

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Upgrade Guide](upgrade.md)
- [Local Development](local-development.md)
- [Follow-up UX Standards](follow-up-ux.md)

## Workflow Summary

LCS provides a hard-gated command chain for spec-driven learning content:

`charter -> define -> refine -> design -> sequence -> rubric -> audit -> author -> issueize`

Artifacts are generated under `programs/<program-id>/units/<###-slug>/` with markdown + json contracts and local-first outputs in `outputs/manifest.json`.  
For multi-unit programs (>=8 study sessions), charter scaffolding also generates `programs/<program-id>/roadmap.json` and `programs/<program-id>/roadmap.md` with session ranges and cadence-flexible day estimates.
Use `/lcs.programs` to inspect/switch active program and unit context before running refine/design on a specific unit.
Use `/lcs.programs workflow-status` to get per-unit pending stages and ready-to-run follow-up prompts.

## Consumer Contract Sync

- [Contract Sync Overview](../contracts/docs/README.md)
- [Consumer API v1](../contracts/docs/CONSUMER-API-V1.md)
- [Tutoring BFF API v1](../contracts/docs/TUTORING-BFF-API-V1.md)
- [Compatibility Matrix](../contracts/docs/COMPATIBILITY-MATRIX.md)
- [Standalone Consumer Blueprint](system/architect/lcs-output-consumer-standalone-blueprint.md)
- [Tutoring Platform Blueprint](system/architect/tutoring-platform-monorepo-blueprint.md)
