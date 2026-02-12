# LCS Learning Content System: Detailed Architecture Diagram

**Scope:** Greenfield learning-content system with deterministic hard gates.  
**Canonical command chain:**  
`/lcs.charter -> /lcs.define -> /lcs.refine -> /lcs.design -> /lcs.sequence -> /lcs.rubric -> /lcs.audit -> /lcs.author -> /lcs.issueize`

## 1) End-to-End Runtime Architecture

```mermaid
flowchart TB
    subgraph U["User + Agent Runtime"]
        DEV["Teacher / Creator / Dev"]
        AI["AI Agent (Claude/Codex/Copilot/...)"]
    end

    subgraph C["Command Layer (Public API)"]
        C0["/lcs.charter"]
        C1["/lcs.define"]
        C2["/lcs.refine"]
        C3["/lcs.design"]
        C4["/lcs.sequence"]
        C5["/lcs.rubric"]
        C6["/lcs.audit"]
        C7["/lcs.author"]
        C8["/lcs.issueize"]
    end

    subgraph S["Script Orchestration Layer (Bash/PowerShell parity)"]
        S1["create-new-unit.*"]
        S2["setup-design.*"]
        S3["check-workflow-prereqs.*"]
        S4["update-agent-context.*"]
        S5["validate-artifact-contracts.* -> validate_artifact_contracts.py"]
        S6["validate-rubric-gates.py"]
        S7["validate-author-gates.*"]
    end

    subgraph A["Artifact Layer: specs/<unit>/"]
        A0["brief.md + brief.json"]
        A1["design.md + design.json"]
        A2["design-decisions.json"]
        A3["content-model.md + content-model.json"]
        A4["assessment-map.md"]
        A5["delivery-guide.md"]
        A6["sequence.md + sequence.json"]
        A7["rubrics/*.md"]
        A8["audit-report.md + audit-report.json"]
        A9["outputs/* + outputs/manifest.json"]
    end

    subgraph G["Validation + Hard-Gate Layer"]
        G0["Schema Validation (JSON Schema 2020-12)"]
        G1["Cross-Artifact Consistency"]
        G2["Rubric Deterministic Parse"]
        G3["Audit Decision Consistency"]
        G4["Author Block Rule:<br/>BLOCK if any CRITICAL/HIGH unresolved<br/>or rubric non-pass/unchecked/parse-error"]
    end

    subgraph GOV["Governance Layer"]
        GOV0[".lcs/memory/charter.md"]
    end

    DEV --> C0
    AI --> C0
    C0 --> GOV0

    C1 --> S1 --> A0
    C2 --> S3 --> A0
    C3 --> S2 --> A1
    C3 --> A2
    C3 --> A3
    C3 --> A4
    C3 --> A5
    C3 --> A9
    C3 --> S4

    C4 --> S3 --> A6
    C5 --> S3 --> A7
    C6 --> S3
    C6 --> A0
    C6 --> A1
    C6 --> A6
    C6 --> A7
    C6 --> A8

    C7 --> S3
    C7 --> S7
    S7 --> S5
    S7 --> S6
    S7 --> A8
    C7 --> A9
    C8 --> S3 --> A6

    S5 --> G0 --> G1
    S6 --> G2
    A8 --> G3
    G1 --> G4
    G2 --> G4
    G3 --> G4
    G4 --> C7
```

## 2) Artifact Contracts + Gate Decisions

```mermaid
flowchart LR
    subgraph Inputs["Required Machine Contracts"]
        I1["brief.json"]
        I2["design.json"]
        I3["sequence.json"]
        I4["audit-report.json"]
        I5["outputs/manifest.json"]
    end

    subgraph ContractRules["Contract Rules"]
        R1["unit_id matches unit directory"]
        R2["LO integrity:<br/>- LO IDs unique<br/>- manifest outcomes == brief outcomes<br/>- priority parity<br/>- evidence refs include brief:LO*"]
        R3["Sequence integrity:<br/>- task_id S###<br/>- known dependencies<br/>- no self-dependency<br/>- no dependency cycle"]
        R4["Artifact integrity:
- path inside unit dir
- file exists
- checksum matches"]
        R5["Audit/Manifest parity:<br/>- gate decision match<br/>- open counters match<br/>- PASS invalid if OPEN CRITICAL/HIGH"]
        R6["xAPI interop required:<br/>version 1.0.x or 2.0.x"]
    end

    subgraph Outputs["Validator Outputs"]
        O1["PASS -> authoring eligible"]
        O2["BLOCK -> authoring stopped deterministically"]
    end

    I1 --> R1
    I2 --> R1
    I3 --> R3
    I4 --> R5
    I5 --> R2
    I5 --> R4
    I5 --> R6
    I1 --> R2
    R1 --> O1
    R2 --> O1
    R3 --> O1
    R4 --> O1
    R5 --> O1
    R6 --> O1
    R1 --> O2
    R2 --> O2
    R3 --> O2
    R4 --> O2
    R5 --> O2
    R6 --> O2
```

## 3) Delivery, CI, and Packaging Topology

```mermaid
flowchart TB
    subgraph SRC["Source of Truth"]
        T0["factory/templates/commands/*.md"]
        T1["factory/templates/*-template.md"]
        T2["factory/scripts/bash/*"]
        T3["factory/scripts/powershell/*"]
        T4["contracts/schemas/*.schema.json"]
        T5["src/lcs_cli/*"]
    end

    subgraph CI["CI Gates"]
        CI1["pytest -q"]
        CI2["script contract smoke (bash/ps)"]
        CI3["release packaging smoke"]
        CI4["docs link check"]
        CI5["legacy token guard"]
    end

    subgraph REL["Release Packaging"]
        P1["create-release-packages.sh"]
        P2["Agent package layouts:
.claude/.codex/.github/.kilocode/.augment/.roo/..."]
        P3["create-github-release.sh"]
    end

    subgraph CONS["Consumers"]
        C1["AI agents (runtime commands)"]
        C2["Downstream apps via outputs/manifest.json"]
    end

    T0 --> P1
    T1 --> P1
    T2 --> P1
    T3 --> P1
    T4 --> CI1
    T5 --> CI1

    P1 --> P2 --> P3
    CI1 --> P1
    CI2 --> P1
    CI3 --> P3
    CI4 --> P3
    CI5 --> P3

    P2 --> C1
    C2 -->|"manifest-first lookup"| C2
```

## Source alignment

- `docs/system/codemaps/LCS_Commands/diagram.md`
- `docs/system/codemaps/LCS_Commands/LCS_Analysis_Command_Workflow_Cross-Artifact_Consistency_Validation_System.md`
- `docs/proposals/lcs-flow-improvements/LCS-Flow-Improvements-Proposal.md`
- `docs/proposals/lcs-flow-improvements/PLAN.md`
- `docs/system/architect/lcs-output-consumer-standalone-blueprint.md`
