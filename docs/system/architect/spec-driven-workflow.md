```mermaid
flowchart LR
    A[/lcs.charter/] --> B[/lcs.define/]
    B --> C[/lcs.refine/]
    C --> D[/lcs.design/]
    D --> E[/lcs.sequence/]
    E --> F[/lcs.rubric/]
    F --> G[/lcs.audit/]
    G --> H[/lcs.author/]
    H --> I[/lcs.issueize/]

    G --> J[audit-report.md + audit-report.json\nGate Decision PASS|BLOCK]
    F --> K[rubrics/*.md\nGate fields: status/severity/evidence]
    H --> L[outputs/ + outputs/manifest.json]
```
