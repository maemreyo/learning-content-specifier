# Proficiency Governance (Crosswalks + Pivots)

This document defines change-control rules for the proficiency layer so that mappings (e.g., IELTS/TOEIC -> CEFR) behave like a versioned product surface.

## Scope

Applies to:

- `contracts/fixtures/proficiency.framework-registry.v1.json`
- `contracts/fixtures/proficiency.crosswalks.v1.json`
- `contracts/fixtures/proficiency.subject-pivots.v1.json`

## Principles (Non-Negotiable)

- Mappings MUST be deterministic and test-covered.
- Crosswalks MUST be provenance-backed (no anonymous mappings).
- Changes MUST be reviewable as data diffs, not implicit behavior changes in code.

## How To Add Or Modify A Mapping

1. Confirm the source and target frameworks/scales/dimensions exist in the registry:
   - Update `proficiency.framework-registry.v1.json` first if needed.
2. Add/modify entries in `proficiency.crosswalks.v1.json`:
   - Prefer disjoint numeric ranges for a given `(from.framework_id, from.scale_id, from.dimension)` group.
   - Keep ranges within the numeric scale bounds defined in the registry.
   - For ordinal targets, values MUST exist in `ordered_values`.
3. Ensure `subjects` can pivot:
   - Update `proficiency.subject-pivots.v1.json` when introducing a new subject pivot.

## Provenance Requirements (`source`)

Every mapping MUST include a non-empty `source` field.

Minimum acceptable formats:

- Public URL to an official or widely accepted reference (preferred).
- A stable internal doc ID with a durable location (acceptable for private deployments), e.g. `doc://proficiency/ielts-cefr-crosswalk/2026-02-15`.

If a mapping is approximate or derived, include an explanatory `notes` field describing the derivation method and intended use.

## Required Tests (No Silent Regressions)

Any change to the fixtures above MUST keep these tests green:

- Schema validation: `tests/test_proficiency_fixtures.py`
- Invariants + regressions: `tests/test_proficiency_crosswalk_invariants.py`

If you add a new framework or scale kind, you MUST extend invariant tests accordingly.

## Breaking Change Policy

Treat the proficiency layer as a contract:

- Breaking change examples:
  - Removing a framework/scale/dimension referenced by existing artifacts.
  - Changing ordinal `ordered_values` semantics or identifiers.
  - Introducing overlaps in numeric mappings that create ambiguous normalization.
- Non-breaking change examples:
  - Adding new mappings that do not overlap existing ranges.
  - Adding new subjects with explicit pivots and fixtures.

If a breaking change is unavoidable, bump the relevant contract versioning according to the project versioning rules, and publish a migration note.

