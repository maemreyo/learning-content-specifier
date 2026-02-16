#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$ForceReset,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./setup-design.ps1 [-Json] [-ForceReset]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$repoRoot = Get-RepoRoot
$pythonBin = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
$renderMdSidecar = @('1', 'true', 'yes', 'on') -contains (($env:LCS_RENDER_MD_SIDECAR ?? '0').ToLowerInvariant())

$loaderArgs = @("$PSScriptRoot/load-stage-context.ps1", '-Stage', 'design', '-Json')
if ($RemainingArgs -and $RemainingArgs.Count -gt 0) {
    $intent = ($RemainingArgs -join ' ').Trim()
    if ($intent) {
        $loaderArgs += @('-Intent', $intent)
    }
}
$loaderRaw = & $loaderArgs[0] $loaderArgs[1..($loaderArgs.Count - 1)]
if (-not $loaderRaw) {
    throw 'design preflight failed to execute'
}
try {
    $loaderObj = $loaderRaw | ConvertFrom-Json
} catch {
    throw 'Invalid design preflight payload'
}
if ([string]$loaderObj.STATUS -ne 'PASS') {
    $missing = @($loaderObj.MISSING_INPUTS)
    $blockers = @($loaderObj.BLOCKERS)
    $parts = @()
    if ($missing.Count -gt 0) { $parts += ('missing=' + ($missing -join ',')) }
    if ($blockers.Count -gt 0) { $parts += ('blockers=' + ($blockers -join '; ')) }
    $summary = if ($parts.Count -gt 0) { $parts -join ' | ' } else { 'unknown preflight blockers' }
    throw "design preflight BLOCK ($summary)"
}

$paths = Get-UnitPathsEnv
$contractVersion = Get-ContractVersion
$selectorTool = Resolve-PythonTool -ToolName 'generate_template_selection.py'
$validatorTool = Resolve-PythonTool -ToolName 'validate_artifact_contracts.py'

if (-not (Test-UnitBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) { exit 1 }

New-Item -ItemType Directory -Path $paths.UNIT_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $paths.RUBRICS_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $paths.OUTPUTS_DIR -Force | Out-Null

if ($renderMdSidecar) {
    $designTemplate = Join-Path $paths.REPO_ROOT '.lcs/templates/design-template.md'
    $exerciseTemplate = Join-Path $paths.REPO_ROOT '.lcs/templates/exercise-design-template.md'
    $briefTemplate = Join-Path $paths.REPO_ROOT '.lcs/templates/brief-template.md'

    if (-not (Test-Path $paths.DESIGN_FILE -PathType Leaf)) {
        if (Test-Path $designTemplate -PathType Leaf) {
            Copy-Item -Path $designTemplate -Destination $paths.DESIGN_FILE -Force
        } else {
            New-Item -ItemType File -Path $paths.DESIGN_FILE -Force | Out-Null
        }
    }
    foreach ($f in @($paths.CONTENT_MODEL_FILE, $paths.ASSESSMENT_MAP_FILE, $paths.DELIVERY_GUIDE_FILE, $paths.SEQUENCE_FILE, $paths.AUDIT_REPORT_FILE)) {
        if (-not (Test-Path $f -PathType Leaf)) { New-Item -ItemType File -Path $f -Force | Out-Null }
    }
    if (-not (Test-Path $paths.EXERCISE_DESIGN_FILE -PathType Leaf)) {
        if (Test-Path $exerciseTemplate -PathType Leaf) {
            Copy-Item -Path $exerciseTemplate -Destination $paths.EXERCISE_DESIGN_FILE -Force
        } else {
            New-Item -ItemType File -Path $paths.EXERCISE_DESIGN_FILE -Force | Out-Null
        }
    }
    if (-not (Test-Path $paths.BRIEF_FILE -PathType Leaf)) {
        if (Test-Path $briefTemplate -PathType Leaf) {
            Copy-Item -Path $briefTemplate -Destination $paths.BRIEF_FILE -Force
        } else {
            New-Item -ItemType File -Path $paths.BRIEF_FILE -Force | Out-Null
        }
    }
}

$unitId = Split-Path $paths.UNIT_DIR -Leaf
$nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

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

try {
    $briefObj = Get-Content -Path $paths.BRIEF_JSON_FILE -Raw -Encoding utf8 | ConvertFrom-Json
    $openQuestions = 0
    if ($briefObj.open_questions -is [int]) {
        $openQuestions = [Math]::Max($openQuestions, [int]$briefObj.open_questions)
    }
    if ($briefObj.refinement -and $briefObj.refinement.open_questions -is [int]) {
        $openQuestions = [Math]::Max($openQuestions, [int]$briefObj.refinement.open_questions)
    }
    if ($openQuestions -gt 0) {
        throw "brief.json has $openQuestions unresolved clarification question(s). Run /lcs.refine before /lcs.design."
    }
} catch {
    throw
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
    "confidence": 0.7,
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
    "title": "Populate from design.json"
  },
  "modules": [
    {
      "id": "module-01",
      "title": "Populate from design.json",
      "lessons": [
        {
          "id": "lesson-01",
          "title": "Populate from design.json",
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

if ($ForceReset -or -not (Test-Path $paths.EXERCISE_DESIGN_JSON_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "generated_at": "$nowUtc",
  "source_files": {
    "assessment_blueprint": "assessment-blueprint.json",
    "template_selection": "template-selection.json"
  },
  "exercises": [
    {
      "exercise_id": "EX001",
      "lo_id": "LO1",
      "template_id": "mcq.v1",
      "day": 1,
      "target_path": "outputs/module-01/exercises/ex001.json",
      "status": "TODO",
      "template_schema_ref": "schemas/mcq.v1.schema.json",
      "template_rules_ref": "rules/mcq.v1.rules.md",
      "scoring_rubric_required_keys": [],
      "scoring_rubric_source": "template-pack"
    }
  ]
}
"@ | Set-Content -Path $paths.EXERCISE_DESIGN_JSON_FILE -Encoding utf8
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
  "confidence": 0.7,
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

# Attempt deterministic template auto-select (English-first).
# Template pack is mandatory for fail-closed design setup.
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
    try {
        $selectorRaw = (& $pythonBin @selectorArgs 2>$null)
    } catch {
        $selectorRaw = ''
    }
}

if ($selectorRaw) {
    try {
        $selectorObj = $selectorRaw | ConvertFrom-Json
        if ([string]$selectorObj.STATUS -ne 'PASS') {
            throw "template selector must return PASS for setup-design ($($paths.UNIT_DIR)); got '$($selectorObj.STATUS)'"
        }
    } catch {
        throw
    }
} else {
    throw "template selector produced no output; setup-design cannot continue for $($paths.UNIT_DIR)"
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

if ($ForceReset -or -not (Test-Path $paths.RUBRIC_GATES_FILE)) {
    @"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitId",
  "generated_at": "$nowUtc",
  "gates": [
    {
      "gate_id": "RB001",
      "group": "alignment",
      "status": "TODO",
      "severity": "HIGH",
      "evidence": "pending",
      "checked": false
    }
  ]
}
"@ | Set-Content -Path $paths.RUBRIC_GATES_FILE -Encoding utf8
}

$assessmentBlueprintChecksum = (Get-FileHash -Path $paths.ASSESSMENT_BLUEPRINT_FILE -Algorithm SHA256).Hash.ToLowerInvariant()
$templateSelectionChecksum = (Get-FileHash -Path $paths.TEMPLATE_SELECTION_FILE -Algorithm SHA256).Hash.ToLowerInvariant()
$exerciseDesignJsonChecksum = (Get-FileHash -Path $paths.EXERCISE_DESIGN_JSON_FILE -Algorithm SHA256).Hash.ToLowerInvariant()
$briefJsonChecksum = (Get-FileHash -Path $paths.BRIEF_JSON_FILE -Algorithm SHA256).Hash.ToLowerInvariant()
$rubricGatesChecksum = (Get-FileHash -Path $paths.RUBRIC_GATES_FILE -Algorithm SHA256).Hash.ToLowerInvariant()

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
      "id": "brief-json",
      "type": "brief",
      "path": "brief.json",
      "media_type": "application/json",
      "checksum": "sha256:$briefJsonChecksum"
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
    },
    {
      "id": "exercise-design-json",
      "type": "exercise-design",
      "path": "exercise-design.json",
      "media_type": "application/json",
      "checksum": "sha256:$exerciseDesignJsonChecksum"
    },
    {
      "id": "rubric-gates-json",
      "type": "rubric-gates",
      "path": "rubric-gates.json",
      "media_type": "application/json",
      "checksum": "sha256:$rubricGatesChecksum"
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

$validatorArgs = @(
    $validatorTool,
    '--repo-root', $paths.REPO_ROOT,
    '--unit-dir', $paths.UNIT_DIR,
    '--json'
)
$validatorRaw = ''
if (Get-Command uv -ErrorAction SilentlyContinue) {
    try {
        $validatorRaw = (& uv run python @validatorArgs 2>$null)
    } catch {
        $validatorRaw = ''
    }
} else {
    try {
        $validatorRaw = (& $pythonBin @validatorArgs 2>$null)
    } catch {
        $validatorRaw = ''
    }
}

if (-not $validatorRaw) {
    throw "artifact contract validator produced no output for $($paths.UNIT_DIR)"
}

try {
    $validatorObj = $validatorRaw | ConvertFrom-Json
} catch {
    throw "artifact contract validator returned invalid JSON for $($paths.UNIT_DIR)"
}

if ([string]$validatorObj.STATUS -ne 'PASS') {
    throw "setup-design contract validation must PASS for $($paths.UNIT_DIR); got '$($validatorObj.STATUS)'"
}

if ($Json) {
    [PSCustomObject]@{
        PROGRAM_ID = $paths.PROGRAM_ID
        UNIT_ID = $paths.CURRENT_UNIT
        BRIEF_JSON_FILE = $paths.BRIEF_JSON_FILE
        DESIGN_JSON_FILE = $paths.DESIGN_JSON_FILE
        BRIEF_FILE = $paths.BRIEF_FILE
        DESIGN_FILE = $paths.DESIGN_FILE
        UNIT_DIR = $paths.UNIT_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $($paths.PROGRAM_ID)"
    Write-Output "UNIT_ID: $($paths.CURRENT_UNIT)"
    Write-Output "BRIEF_JSON_FILE: $($paths.BRIEF_JSON_FILE)"
    Write-Output "DESIGN_JSON_FILE: $($paths.DESIGN_JSON_FILE)"
    Write-Output "BRIEF_FILE: $($paths.BRIEF_FILE)"
    Write-Output "DESIGN_FILE: $($paths.DESIGN_FILE)"
    Write-Output "UNIT_DIR: $($paths.UNIT_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
