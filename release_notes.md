This is the latest set of releases that you can use with your agent of choice. We recommend using the LCS CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Changelog

- feat(workflow): add exercise design artifacts and multi-unit roadmap support
- Update
- test(template-pack): require taxonomy coverage
- test(proficiency): add crosswalk invariants
- docs: document proficiency targets in brief
- feat(proficiency): add proficiency layer for CEFR/IELTS/TOEIC targets
- feat(templates): add keyword hints and validation tests for new exercise types
- feat(templates): add keyword hints and validation tests for new exercise types
- feat(templates): add trending topics fetcher and expand exercise type support
- test(validation): add template pack example validation tests
- feat(validation): add template selection system and pipeline response envelope
- feat(release): implement release integrity verification and multi-repo namespace support
- feat(contracts): implement installer-first contract sync with release-first mode
- chore(core): remove legacy consumer scaffold and tighten boundary checks
- feat: add scaffolding tooling for standalone consumer and tutoring platform repos
- feat(contracts): add consumer contract version pinning and compatibility gates
- refactor: restructure repository into factory, contracts, and tooling directories
- fix(build): improve validation and error handling in contract package build
- feat: Add scaffold template and CLI for standalone LCS output consumer repos
- feat(contract): add contract package system for standalone consumer sync
- docs(readme): add installation and usage guide for working in another repository
- fix(ci): reset powershell native exit code after smoke checks
- fix(ci): relax powershell author-gates smoke assertion
- fix(ci): relax powershell contract smoke status assertion
- fix(ci): align ps contract paths with setup-design unit dir
- fix(ci): correct powershell cleanup condition syntax
- fix(powershell): harden create-new-unit repo-root resolution
- fix(ci): precompute powershell script paths before push-location
- fix(ci): normalize powershell repo root to single path
- fix(ci): make powershell contract script root detection deterministic
- fix(ci): resolve powershell contract script repo root on gha
- fix(ci): limit bash smoke to bash checks and harden ps repo root
- fix(ci): avoid premature pwsh exits in contract smoke
- fix(ci): harden script contract checks for bash and powershell
- fix(ci): robust json extraction and stabilize windows lint scope
- fix(ci): stabilize contract smoke parsing and windows uv deps
- fix(ci): harden JSON capture and windows pytest import path
- fix(ci): improve JSON capture and use pip directly for Windows
- fix(ci): use uv pip install for Windows pytest installation
- fix(ci): use portable temp dir creation instead of mktemp
- fix(ci): use uv run python3 in script contract smoke test
- fix(ci): install test dependencies before running pytest
- ci(release): tag-driven strict release with env approval and artifact upload

