#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$ForceReset,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./setup-design.ps1 [-Json] [-ForceReset]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$paths = Get-UnitPathsEnv
$contractVersion = Get-ContractVersion
$selectorTool = Resolve-PythonTool -ToolName 'generate_template_selection.py'

if (-not (Test-UnitBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) { exit 1 }

New-Item -ItemType Directory -Path $paths.UNIT_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $paths.RUBRICS_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $paths.OUTPUTS_DIR -Force | Out-Null

$template = Join-Path $paths.REPO_ROOT '.lcs/templates/design-template.md'
if ($ForceReset -or -not (Test-Path $paths.DESIGN_FILE)) {
    if (Test-Path $template) {
        Copy-Item $template $paths.DESIGN_FILE -Force
    } else {
        New-Item -ItemType File -Path $paths.DESIGN_FILE -Force | Out-Null
    }
}

foreach ($f in @($paths.CONTENT_MODEL_FILE, $paths.ASSESSMENT_MAP_FILE, $paths.DELIVERY_GUIDE_FILE)) {
    if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force | Out-Null }
}
if (-not (Test-Path $paths.SEQUENCE_FILE)) { New-Item -ItemType File -Path $paths.SEQUENCE_FILE -Force | Out-Null }
if (-not (Test-Path $paths.AUDIT_REPORT_FILE)) { New-Item -ItemType File -Path $paths.AUDIT_REPORT_FILE -Force | Out-Null }

$unitId = Split-Path $paths.UNIT_DIR -Leaf
$nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

if (-not (Test-Path $paths.BRIEF_FILE -PathType Leaf)) {
    New-Item -ItemType File -Path $paths.BRIEF_FILE -Force | Out-Null
}
$briefChecksum = (Get-FileHash -Path $paths.BRIEF_FILE -Algorithm SHA256).Hash.ToLowerInvariant()

if ($ForceReset -or -not (Test-Path $paths.BRIEF_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "title": "$unitId",
  "audience": {
    "primary": "general learners",
    "entry_level": "beginner",
    "delivery_context": "self-paced"
  },
  "duration_minutes": 60,
  "learning_outcomes": [
    {
      "lo_id": "LO1",
      "priority": "P1",
      "statement": "Learner will be able to demonstrate LO1 with measurable evidence.",
      "evidence": "Assessment evidence mapped to LO1 is available in artifacts.",
      "acceptance_criteria": [
        "Given the learning context, When the learner attempts LO1 practice, Then observable evidence meets the completion criteria."
      ]
    }
  ],
  "scope": {
    "in_scope": [],
    "out_of_scope": []
  }
}
"@ | Set-Content -Path $paths.BRIEF_JSON_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.DESIGN_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "generated_at": "$nowUtc",
  "instructional_strategy": {
    "primary_method": "retrieval-practice",
    "secondary_methods": ["worked-examples"],
    "rationale": "Corporate L&D default; refine with design evidence."
  },
  "pedagogy_decisions": {
    "profile": "corporate-lnd-v1",
    "confidence_threshold": 0.7,
    "confidence": 0.0,
    "candidate_methods": [
      "direct-instruction",
      "worked-examples",
      "retrieval-practice",
      "problem-based-learning",
      "project-based-learning",
      "case-based-learning",
      "peer-instruction",
      "simulation-lab"
    ],
    "scores": {
      "learner_fit": 0.0,
      "outcome_fit": 0.0,
      "evidence_fit": 0.0,
      "delivery_fit": 0.0,
      "accessibility_fit": 0.0
    },
    "selection_rules": {
      "max_secondary_methods": 2,
      "score_delta_threshold": 0.4
    },
    "research": {
      "required": false,
      "triggers": [],
      "evidence_refs": []
    }
  },
  "metadata": {
    "audience": "unspecified",
    "duration_minutes": 60,
    "modality": "unspecified"
  }
}
"@ | Set-Content -Path $paths.DESIGN_JSON_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.CONTENT_MODEL_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "course": {
    "id": "course-01",
    "title": "Populate from design.md"
  },
  "modules": [
    {
      "id": "module-01",
      "title": "Populate from design.md",
      "lessons": [
        {
          "id": "lesson-01",
          "title": "Populate from design.md",
          "lo_refs": ["LO1"],
          "estimated_minutes": 30
        }
      ]
    }
  ],
  "dependency_graph": {
    "nodes": ["LO1"],
    "edges": [],
    "cycle_check_passed": true
  },
  "duration_tolerance": {
    "lower_percent": -10,
    "upper_percent": 15
  }
}
"@ | Set-Content -Path $paths.CONTENT_MODEL_JSON_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.DESIGN_DECISIONS_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "profile": "corporate-lnd-v1",
  "weights": {
    "outcome_fit": 0.3,
    "evidence_fit": 0.25,
    "learner_fit": 0.2,
    "delivery_fit": 0.15,
    "accessibility_fit": 0.1
  },
  "candidate_methods": [
    "direct-instruction",
    "worked-examples",
    "retrieval-practice",
    "problem-based-learning",
    "project-based-learning",
    "case-based-learning",
    "peer-instruction",
    "simulation-lab"
  ],
  "scores": {
    "direct-instruction": 0.0,
    "worked-examples": 0.0,
    "retrieval-practice": 0.0,
    "problem-based-learning": 0.0,
    "project-based-learning": 0.0,
    "case-based-learning": 0.0,
    "peer-instruction": 0.0,
    "simulation-lab": 0.0
  },
  "selected_primary": "",
  "selected_secondary": [],
  "rationale": "Populate from /lcs.design decision process.",
  "confidence_threshold": 0.7,
  "confidence": 0.0,
  "web_research_triggers": [
    "time-sensitive domain/tooling",
    "confidence below threshold",
    "conflicting artifact signals",
    "explicit validation request"
  ],
  "research_evidence_refs": []
}
"@ | Set-Content -Path $paths.DESIGN_DECISIONS_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.ASSESSMENT_BLUEPRINT_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "subject": "english",
  "template_pack_version": "1.0.0",
  "target_distribution": [
    {
      "template_id": "mcq.v1",
      "exercise_type": "MCQ",
      "ratio_percent": 25
    },
    {
      "template_id": "multiple-response.v1",
      "exercise_type": "MULTIPLE_RESPONSE",
      "ratio_percent": 20
    },
    {
      "template_id": "tfng.v1",
      "exercise_type": "TFNG",
      "ratio_percent": 20
    },
    {
      "template_id": "matching-headings.v1",
      "exercise_type": "MATCHING_HEADINGS",
      "ratio_percent": 15
    },
    {
      "template_id": "matching-information.v1",
      "exercise_type": "MATCHING_INFORMATION",
      "ratio_percent": 10
    },
    {
      "template_id": "sentence-rewrite.v1",
      "exercise_type": "SENTENCE_REWRITE",
      "ratio_percent": 10
    }
  ],
  "tolerance_percent": 10,
  "lo_mapping": {
    "LO1": [
      "mcq.v1",
      "multiple-response.v1",
      "tfng.v1",
      "matching-headings.v1",
      "matching-information.v1",
      "sentence-rewrite.v1"
    ]
  }
}
"@ | Set-Content -Path $paths.ASSESSMENT_BLUEPRINT_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.TEMPLATE_SELECTION_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "subject": "english",
  "catalog_version": "1.0.0",
  "top_k": 3,
  "selected_templates": [
    {
      "template_id": "mcq.v1",
      "exercise_type": "MCQ",
      "score": 0.9,
      "score_breakdown": {
        "lo_fit": 1.0,
        "level_fit": 0.9,
        "duration_fit": 0.8,
        "diversity_fit": 0.9
      },
      "rationale": "Balanced starter item for broad LO coverage."
    },
    {
      "template_id": "multiple-response.v1",
      "exercise_type": "MULTIPLE_RESPONSE",
      "score": 0.88,
      "score_breakdown": {
        "lo_fit": 0.95,
        "level_fit": 0.85,
        "duration_fit": 0.85,
        "diversity_fit": 0.9
      },
      "rationale": "Supports multi-select reasoning and discrimination quality."
    },
    {
      "template_id": "tfng.v1",
      "exercise_type": "TFNG",
      "score": 0.85,
      "score_breakdown": {
        "lo_fit": 0.9,
        "level_fit": 0.82,
        "duration_fit": 0.9,
        "diversity_fit": 0.83
      },
      "rationale": "Supports evidence-based reading validation."
    }
  ],
  "selection_rationale": "Default English starter selection; refine with unit-specific intent."
}
"@ | Set-Content -Path $paths.TEMPLATE_SELECTION_FILE -Encoding utf8
}

# Attempt deterministic template auto-select (English-first). If template pack is
# not found, selector exits SKIP and current scaffolds remain.
$selectorArgs = @(
    $selectorTool,
    '--repo-root', $paths.REPO_ROOT,
    '--unit-dir', $paths.UNIT_DIR,
    '--json'
)

$selectorRaw = ''
if (Get-Command uv -ErrorAction SilentlyContinue) {
    try {
        $selectorRaw = (& uv run python @selectorArgs 2>$null)
    } catch {
        $selectorRaw = ''
    }
} else {
    $selectorPython = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
    try {
        $selectorRaw = (& $selectorPython @selectorArgs 2>$null)
    } catch {
        $selectorRaw = ''
    }
}

if ($selectorRaw) {
    try {
        $selectorObj = $selectorRaw | ConvertFrom-Json
        if ([string]$selectorObj.STATUS -eq 'BLOCK') {
            throw "template selector blocked setup-design for $($paths.UNIT_DIR)"
        }
    } catch {
        throw
    }
}

if ($ForceReset -or -not (Test-Path $paths.SEQUENCE_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "tasks": []
}
"@ | Set-Content -Path $paths.SEQUENCE_JSON_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.AUDIT_REPORT_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "gate_decision": "BLOCK",
  "open_critical": 0,
  "open_high": 0,
  "findings": [],
  "role_readiness": {
    "teacher_ready": false,
    "creator_ready": false,
    "ops_ready": false
  }
}
"@ | Set-Content -Path $paths.AUDIT_REPORT_JSON_FILE -Encoding utf8
}

$assessmentBlueprintChecksum = (Get-FileHash -Path $paths.ASSESSMENT_BLUEPRINT_FILE -Algorithm SHA256).Hash.ToLowerInvariant()
$templateSelectionChecksum = (Get-FileHash -Path $paths.TEMPLATE_SELECTION_FILE -Algorithm SHA256).Hash.ToLowerInvariant()

if ($ForceReset -or -not (Test-Path $paths.MANIFEST_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "title": "$unitId",
  "locale": "en-US",
  "generated_at": "$nowUtc",
  "outcomes": [
    {
      "lo_id": "LO1",
      "priority": "P1",
      "evidence_refs": ["brief:LO1"]
    }
  ],
  "artifacts": [
    {
      "id": "brief-md",
      "type": "brief",
      "path": "brief.md",
      "media_type": "text/markdown",
      "checksum": "sha256:$briefChecksum"
    },
    {
      "id": "assessment-blueprint-json",
      "type": "assessment-blueprint",
      "path": "assessment-blueprint.json",
      "media_type": "application/json",
      "checksum": "sha256:$assessmentBlueprintChecksum"
    },
    {
      "id": "template-selection-json",
      "type": "template-selection",
      "path": "template-selection.json",
      "media_type": "application/json",
      "checksum": "sha256:$templateSelectionChecksum"
    }
  ],
  "gate_status": {
    "decision": "BLOCK",
    "open_critical": 0,
    "open_high": 0
  },
  "interop": {
    "xapi": {
      "version": "2.0.0",
      "activity_id_set": ["https://example.org/xapi/activity/LO1"],
      "statement_template_refs": ["https://example.org/xapi/template/LO1"]
    }
  }
}
"@ | Set-Content -Path $paths.MANIFEST_FILE -Encoding utf8
}

if ($Json) {
    [PSCustomObject]@{
        PROGRAM_ID = $paths.PROGRAM_ID
        UNIT_ID = $paths.CURRENT_UNIT
        BRIEF_FILE = $paths.BRIEF_FILE
        DESIGN_FILE = $paths.DESIGN_FILE
        UNIT_DIR = $paths.UNIT_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $($paths.PROGRAM_ID)"
    Write-Output "UNIT_ID: $($paths.CURRENT_UNIT)"
    Write-Output "BRIEF_FILE: $($paths.BRIEF_FILE)"
    Write-Output "DESIGN_FILE: $($paths.DESIGN_FILE)"
    Write-Output "UNIT_DIR: $($paths.UNIT_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
