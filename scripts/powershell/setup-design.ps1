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

if ($ForceReset -or -not (Test-Path $paths.BRIEF_JSON_FILE)) {
    @"
{
  "contract_version": "1.0.0",
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
  "contract_version": "1.0.0",
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
  "contract_version": "1.0.0",
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

if ($ForceReset -or -not (Test-Path $paths.SEQUENCE_JSON_FILE)) {
    @"
{
  "contract_version": "1.0.0",
  "unit_id": "$unitId",
  "tasks": []
}
"@ | Set-Content -Path $paths.SEQUENCE_JSON_FILE -Encoding utf8
}

if ($ForceReset -or -not (Test-Path $paths.AUDIT_REPORT_JSON_FILE)) {
    @"
{
  "contract_version": "1.0.0",
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

if ($ForceReset -or -not (Test-Path $paths.MANIFEST_FILE)) {
    @"
{
  "contract_version": "1.0.0",
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
      "checksum": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    }
  ],
  "gate_status": {
    "decision": "BLOCK",
    "open_critical": 0,
    "open_high": 0
  },
  "interop": {
    "xapi": {
      "version": "1.0.3",
      "activity_id_set": ["https://example.org/xapi/activity/LO1"],
      "statement_template_refs": ["https://example.org/xapi/template/LO1"]
    }
  }
}
"@ | Set-Content -Path $paths.MANIFEST_FILE -Encoding utf8
}

if ($Json) {
    [PSCustomObject]@{
        BRIEF_FILE = $paths.BRIEF_FILE
        DESIGN_FILE = $paths.DESIGN_FILE
        UNIT_DIR = $paths.UNIT_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    } | ConvertTo-Json -Compress
} else {
    Write-Output "BRIEF_FILE: $($paths.BRIEF_FILE)"
    Write-Output "DESIGN_FILE: $($paths.DESIGN_FILE)"
    Write-Output "UNIT_DIR: $($paths.UNIT_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
