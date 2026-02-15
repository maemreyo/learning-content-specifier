#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireSequence,
    [switch]$RequireDesignContracts,
    [switch]$IncludeSequence,
    [switch]$PathsOnly,
    [switch]$SkipBranchCheck,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./check-workflow-prereqs.ps1 [-Json] [-RequireSequence] [-RequireDesignContracts] [-IncludeSequence] [-PathsOnly] [-SkipBranchCheck]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
if ($PathsOnly -and $SkipBranchCheck) {
    $paths = Get-UnitPathsEnv -AllowMissingUnit
} else {
    $paths = Get-UnitPathsEnv
}

if (-not $SkipBranchCheck) {
    if (-not (Test-UnitBranch -Branch $paths.CURRENT_UNIT -HasGit $paths.HAS_GIT)) { exit 1 }
}

if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            UNIT_REPO_ROOT = $paths.REPO_ROOT
            UNIT_BRANCH = $paths.CURRENT_BRANCH
            UNIT_ID = $paths.CURRENT_UNIT
            UNIT_HAS_GIT = $paths.HAS_GIT
            PROGRAM_ID = $paths.PROGRAM_ID
            PROGRAM_DIR = $paths.PROGRAM_DIR
            PROGRAM_CHARTER_FILE = $paths.PROGRAM_CHARTER_FILE
            PROGRAM_ROADMAP_JSON_FILE = $paths.PROGRAM_ROADMAP_JSON_FILE
            PROGRAM_ROADMAP_MD_FILE = $paths.PROGRAM_ROADMAP_MD_FILE
            UNIT_DIR = $paths.UNIT_DIR
            UNIT_BRIEF_FILE = $paths.BRIEF_FILE
            UNIT_BRIEF_JSON_FILE = $paths.BRIEF_JSON_FILE
            UNIT_DESIGN_FILE = $paths.DESIGN_FILE
            UNIT_DESIGN_JSON_FILE = $paths.DESIGN_JSON_FILE
            UNIT_EXERCISE_DESIGN_FILE = $paths.EXERCISE_DESIGN_FILE
            UNIT_EXERCISE_DESIGN_JSON_FILE = $paths.EXERCISE_DESIGN_JSON_FILE
            UNIT_SEQUENCE_FILE = $paths.SEQUENCE_FILE
            UNIT_SEQUENCE_JSON_FILE = $paths.SEQUENCE_JSON_FILE
            UNIT_AUDIT_REPORT_FILE = $paths.AUDIT_REPORT_FILE
            UNIT_AUDIT_REPORT_JSON_FILE = $paths.AUDIT_REPORT_JSON_FILE
            UNIT_MANIFEST_FILE = $paths.MANIFEST_FILE
            UNIT_CHARTER_FILE = $paths.PROGRAM_CHARTER_FILE
            SUBJECT_CHARTER_FILE = $paths.SUBJECT_CHARTER_FILE
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "UNIT_REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "UNIT_BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "UNIT_ID: $($paths.CURRENT_UNIT)"
        Write-Output "UNIT_HAS_GIT: $($paths.HAS_GIT)"
        Write-Output "PROGRAM_ID: $($paths.PROGRAM_ID)"
        Write-Output "PROGRAM_DIR: $($paths.PROGRAM_DIR)"
        Write-Output "PROGRAM_CHARTER_FILE: $($paths.PROGRAM_CHARTER_FILE)"
        Write-Output "PROGRAM_ROADMAP_JSON_FILE: $($paths.PROGRAM_ROADMAP_JSON_FILE)"
        Write-Output "PROGRAM_ROADMAP_MD_FILE: $($paths.PROGRAM_ROADMAP_MD_FILE)"
        Write-Output "UNIT_DIR: $($paths.UNIT_DIR)"
        Write-Output "UNIT_BRIEF_FILE: $($paths.BRIEF_FILE)"
        Write-Output "UNIT_BRIEF_JSON_FILE: $($paths.BRIEF_JSON_FILE)"
        Write-Output "UNIT_DESIGN_FILE: $($paths.DESIGN_FILE)"
        Write-Output "UNIT_DESIGN_JSON_FILE: $($paths.DESIGN_JSON_FILE)"
        Write-Output "UNIT_EXERCISE_DESIGN_FILE: $($paths.EXERCISE_DESIGN_FILE)"
        Write-Output "UNIT_EXERCISE_DESIGN_JSON_FILE: $($paths.EXERCISE_DESIGN_JSON_FILE)"
        Write-Output "UNIT_SEQUENCE_FILE: $($paths.SEQUENCE_FILE)"
        Write-Output "UNIT_SEQUENCE_JSON_FILE: $($paths.SEQUENCE_JSON_FILE)"
        Write-Output "UNIT_AUDIT_REPORT_FILE: $($paths.AUDIT_REPORT_FILE)"
        Write-Output "UNIT_AUDIT_REPORT_JSON_FILE: $($paths.AUDIT_REPORT_JSON_FILE)"
        Write-Output "UNIT_MANIFEST_FILE: $($paths.MANIFEST_FILE)"
        Write-Output "UNIT_CHARTER_FILE: $($paths.PROGRAM_CHARTER_FILE)"
        Write-Output "SUBJECT_CHARTER_FILE: $($paths.SUBJECT_CHARTER_FILE)"
    }
    exit 0
}

if (-not (Test-Path $paths.UNIT_DIR -PathType Container)) {
    Write-Output "ERROR: Unit directory not found: $($paths.UNIT_DIR)"
    exit 1
}

if (-not (Test-Path $paths.DESIGN_FILE -PathType Leaf)) {
    Write-Output "ERROR: design.md not found in $($paths.UNIT_DIR)"
    Write-Output 'Run /lcs.design first.'
    exit 1
}

if ($RequireSequence -and -not (Test-Path $paths.SEQUENCE_FILE -PathType Leaf)) {
    Write-Output "ERROR: sequence.md not found in $($paths.UNIT_DIR)"
    Write-Output 'Run /lcs.sequence first.'
    exit 1
}

if ($RequireDesignContracts) {
    $missingContracts = @()
    if (-not (Test-Path $paths.ASSESSMENT_BLUEPRINT_FILE -PathType Leaf)) { $missingContracts += 'assessment-blueprint.json' }
    if (-not (Test-Path $paths.TEMPLATE_SELECTION_FILE -PathType Leaf)) { $missingContracts += 'template-selection.json' }
    if (-not (Test-Path $paths.EXERCISE_DESIGN_JSON_FILE -PathType Leaf)) { $missingContracts += 'exercise-design.json' }

    if ($missingContracts.Count -gt 0) {
        Write-Output "ERROR: missing required design contract artifacts in $($paths.UNIT_DIR): $($missingContracts -join ', ')"
        Write-Output 'Run /lcs.design first and resolve design contract blockers.'
        exit 1
    }
}

$docs = @()
if (Test-Path $paths.RESEARCH_FILE) { $docs += 'research.md' }
if (Test-Path $paths.CONTENT_MODEL_FILE) { $docs += 'content-model.md' }
if (Test-Path $paths.EXERCISE_DESIGN_FILE) { $docs += 'exercise-design.md' }
if (Test-Path $paths.ASSESSMENT_MAP_FILE) { $docs += 'assessment-map.md' }
if (Test-Path $paths.DELIVERY_GUIDE_FILE) { $docs += 'delivery-guide.md' }
if ($IncludeSequence -and (Test-Path $paths.SEQUENCE_FILE)) { $docs += 'sequence.md' }

if ($Json) {
    [PSCustomObject]@{ UNIT_DIR = $paths.UNIT_DIR; AVAILABLE_DOCS = $docs } | ConvertTo-Json -Compress
} else {
    Write-Output "UNIT_DIR:$($paths.UNIT_DIR)"
    Write-Output 'AVAILABLE_DOCS:'
    Test-FileExists -Path $paths.RESEARCH_FILE -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.CONTENT_MODEL_FILE -Description 'content-model.md' | Out-Null
    Test-FileExists -Path $paths.ASSESSMENT_MAP_FILE -Description 'assessment-map.md' | Out-Null
    Test-FileExists -Path $paths.DELIVERY_GUIDE_FILE -Description 'delivery-guide.md' | Out-Null
    if ($IncludeSequence) { Test-FileExists -Path $paths.SEQUENCE_FILE -Description 'sequence.md' | Out-Null }
}
