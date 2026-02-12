# LCS Flow Improvements Proposal (Greenfield, Learning-Content First)

## Status

- Status: Proposal v2
- Date: 2026-02-12
- Scope: Greenfield system (no backward-compatibility requirement)

## Executive Summary

This proposal reframes LCS as a deterministic learning-content production system.

Core direction:

1. Keep public command surface simple:
   - `/lcs.charter -> /lcs.define -> /lcs.refine -> /lcs.design -> /lcs.sequence -> /lcs.rubric -> /lcs.audit -> /lcs.author -> /lcs.issueize`
2. Run parallelism inside orchestration, not as extra public commands.
3. Add role-aware, instructional quality contracts (teacher/creator/learner/ops), not only technical gates.
4. Define machine-readable artifact standards so downstream apps can integrate reliably.

## Why the previous structure is not enough

The previous version correctly identified sequential bottlenecks, but it still had these risks:

- Over-exposes implementation details to users (`/lcs.design.*` subcommands), increasing complexity for teachers and creators.
- Lacks a deterministic policy for selecting pedagogy.
- Lacks a strong, standardized artifact API contract for other consuming systems.
- Uses migration framing, while this system is greenfield.

## Role-Based Requirements (Non-negotiable)

### Teacher perspective

- Needs minimal command complexity and clear readiness signals.
- Needs lesson timing realism and practical facilitation guidance.

### Learning creator / instructional designer perspective

- Needs explicit constructive alignment traceability (Outcome -> Activity -> Assessment).
- Needs design rationale for modality/pedagogy decisions.

### Accessibility / inclusion perspective

- Needs verifiable accessibility/readability checks mapped to outputs.

### Program/L&D ops perspective

- Needs stable, machine-readable outputs for LMS/app analytics and automation.

## Proposed Architecture

## 1) Command Model (Public API remains simple)

Public commands remain unchanged.

Parallelization happens inside these stages:

- `design` internally parallelizes creation of:
  - `content-model.md`
  - `assessment-map.md`
  - `delivery-guide.md`
- `audit` internally parallelizes artifact analysis, then merges into one deterministic decision.

Reason: keeps user workflow simple while still reducing runtime.

## 2) Decision Engine: How system determines `content model`

The system should not "guess" structure ad hoc. It should follow a policy stack:

1. Charter constraints (hard rules)
2. Brief constraints (audience, level, duration, modality)
3. Outcome decomposition rules
4. Domain evidence and pedagogy evidence (web-researched when needed)

### Deterministic algorithm (proposal)

Input:

- `brief.md`
- `charter.md`
- optional domain context

Steps:

1. Parse outcomes into skill units (knowledge, procedure, performance evidence).
2. Estimate instructional load per outcome (time + complexity).
3. Cluster outcomes into modules by conceptual dependency.
4. Split modules into lessons by a max duration budget and dependency order.
5. Emit `content-model` with explicit references to LO IDs.

Output constraints:

- Every lesson must map to at least one LO.
- No LO may be orphaned.
- Duration sum must match budget tolerance.

## 3) Decision Engine: How system chooses pedagogy

Question addressed:

- "Dạy theo phương pháp nào?"

### Recommended policy

Pedagogy is selected by "fit scoring", not fixed templates.

Scoring dimensions:

- Learner profile fit (prior knowledge, constraints, language, modality).
- Outcome type fit (recall, conceptual transfer, performance task).
- Evidence fit (assessment feasibility and validity).
- Delivery constraints (time, synchronous/asynchronous, class size).

### Source-of-truth hierarchy

1. Local artifacts (charter + brief + existing unit docs) as primary.
2. Web research as dynamic evidence layer when confidence is low or domain is changing.
3. No hidden static DB assumptions in core decision logic.

### Web-research trigger policy

Must trigger web research if any of these are true:

- Domain appears time-sensitive (regulation, platform, tooling, standards).
- Team confidence score below threshold.
- Conflicting pedagogy signals across artifacts.
- User explicitly asks to validate with current external evidence.

### Recommended teaching-method baseline

For most creator workflows, prefer evidence-backed defaults and then adapt:

- Active learning activities.
- Retrieval practice opportunities.
- Spaced reinforcement (if multi-session).
- Scaffolding/worked examples for novices.

These are defaults, not hard-coded dogma.

## 4) Output Standard: Artifact Contract for downstream apps

Question addressed:

- "Chuẩn đầu ra thế nào để app khác consume?"

### Proposal: LCS Artifact Contract v1

For each unit:

- Human-readable markdown artifacts (authoring UX)
- Machine-readable JSON sidecars (integration API)

Required machine-readable files:

- `specs/<unit>/brief.json`
- `specs/<unit>/design.json`
- `specs/<unit>/sequence.json`
- `specs/<unit>/rubrics/<name>.json`
- `specs/<unit>/audit-report.json`
- `specs/<unit>/outputs/manifest.json`

### Schema strategy

- Use JSON Schema 2020-12 for validation.
- Publish versioned schema IDs: `lcs.artifact.<type>.v1`.
- Add compatibility policy: major/minor/patch for contract evolution.

### Suggested interoperability standards mapping

- Competency/outcome exchange: 1EdTech CASE alignment IDs where relevant.
- Assessment portability: 1EdTech QTI mapping when assessment items are exported.
- Learning event telemetry: xAPI/cmi5-compatible statement mapping for runtime analytics.
- Platform integration: LTI 1.3 / LTI services when launching tools into LMS.
- Discoverability metadata: schema.org `LearningResource` fields for public catalogs.

## 5) Validation and gates (distributed + deterministic)

Keep distributed gates, but add instructional quality gates.

Required gate families:

1. Alignment gate: LO -> Activity -> Assessment integrity.
2. Pedagogy fit gate: method-to-audience suitability.
3. Accessibility/readability gate: WCAG + plain-language checks.
4. Workload realism gate: estimated vs target duration sanity.
5. Metadata completeness gate: downstream integration fields complete.
6. Cross-artifact consistency gate: no contradictions across brief/design/sequence/rubric.

Author hard-stop condition:

- Any unresolved CRITICAL/HIGH OR unresolved rubric blocker => `BLOCK`.

## 6) Proposal changes vs previous version

- Remove backward-compatibility/migration rollout section.
- Keep single `/lcs.design` public command; move parallelism internally.
- Add explicit decision engines for content model and pedagogy.
- Add standardized artifact API contract (JSON + schema versioning).
- Add role-readiness outputs in audit:
  - `teacher_ready`
  - `creator_ready`
  - `ops_ready`

## Gaps still open (to clarify before implementation)

1. Confidence scoring formula for pedagogy decisions.
2. Minimum metadata set for `outputs/manifest.json` accepted by all future consumers.
3. Which interoperability mappings are mandatory in v1 vs optional adapters.
4. Performance benchmark protocol (unit sizes, p50/p95, rework cost).

## Recommended implementation plan (greenfield)

1. Implement deterministic schemas (`*.json` + JSON Schema).
2. Implement internal-parallel design orchestrator.
3. Implement web-research trigger policy and source citation in `design`/`audit`.
4. Extend audit output with role-readiness and machine-readable decision objects.
5. Add contract tests for artifact JSON and schema validation.

## Research Basis (used for this proposal)

- Constructive alignment (UNSW):
  - https://www.teaching.unsw.edu.au/aligning-assessment-learning-outcomes
- UDL 3.0 (CAST):
  - https://udlguidelines.cast.org/
- WCAG 2.2:
  - https://www.w3.org/TR/WCAG22/
- Plain language (NIH):
  - https://www.nih.gov/institutes-nih/nih-office-director/office-communications-public-liaison/clear-communication/plain-language-nih
- OpenAI prompt engineering (structure, examples, context, retrieval):
  - https://developers.openai.com/api/docs/guides/prompt-engineering
- Anthropic prompting clarity + XML structuring:
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/be-clear-and-direct
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags
- Competency standard exchange (1EdTech CASE):
  - https://www.1edtech.org/standards/case
- Assessment portability (1EdTech QTI):
  - https://www.1edtech.org/standards/qti
- LMS integration (1EdTech LTI):
  - https://www.1edtech.org/standards/lti
- Learning telemetry interoperability:
  - https://github.com/adlnet/xAPI-Spec
  - https://aicc.github.io/CMI-5_Spec_Current/
- JSON Schema spec:
  - https://json-schema.org/specification
- OpenAPI spec versions:
  - https://spec.openapis.org/oas/
