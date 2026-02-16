#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireSequence,
    [switch]$RequireDesignContracts,
    [switch]$IncludeSequence,
    [switch]$PathsOnly,
    [switch]$SkipBranchCheck,
    [string]$Stage,
    [string]$Intent,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./check-workflow-prereqs.ps1 [-Json] [-RequireSequence] [-RequireDesignContracts] [-IncludeSequence] [-PathsOnly] [-SkipBranchCheck] [-Stage <stage>] [-Intent <text>]'
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

$stageExplicit = $PSBoundParameters.ContainsKey('Stage') -and -not [string]::IsNullOrWhiteSpace($Stage)
if (-not $Stage) {
    if ($RequireDesignContracts -and $RequireSequence) {
        $Stage = 'author'
    } elseif ($RequireDesignContracts) {
        $Stage = 'sequence'
    } elseif ($RequireSequence) {
        $Stage = 'issueize'
    } else {
        $Stage = 'refine'
    }
}

function Invoke-StagePreflight {
    param(
        [Parameter(Mandatory = $true)][string]$RequestedStage
    )

    $loader = Join-Path $PSScriptRoot 'load-stage-context.ps1'
    $loaderArgs = @('-Stage', $RequestedStage, '-Json')
    if ($Intent) {
        $loaderArgs += @('-Intent', $Intent)
    }

    $loaderOutput = & $loader @loaderArgs
    if (-not $loaderOutput) {
        Write-Output 'ERROR: load-stage-context failed to execute'
        return $false
    }

    try {
        $loaderPayload = $loaderOutput | ConvertFrom-Json
    } catch {
        Write-Output 'ERROR: Invalid load-stage-context output'
        return $false
    }

    if ($loaderPayload.STATUS -ne 'PASS') {
        $missing = @($loaderPayload.MISSING_INPUTS)
        $blockers = @($loaderPayload.BLOCKERS)
        $parts = @()
        if ($missing.Count -gt 0) { $parts += ('missing=' + ($missing -join ',')) }
        if ($blockers.Count -gt 0) { $parts += ('blockers=' + ($blockers -join '; ')) }
        $summary = if ($parts.Count -gt 0) { $parts -join ' | ' } else { 'Unknown preflight blockers' }
        Write-Output "ERROR: stage preflight BLOCK ($summary)"
        return $false
    }

    return $true
}

if ($PathsOnly) {
    # Maintain legacy paths-only behavior unless caller explicitly requests stage preflight.
    if ($stageExplicit) {
        if (-not (Invoke-StagePreflight -RequestedStage $Stage)) { exit 1 }
    }

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
            UNIT_RUBRIC_GATES_FILE = $paths.RUBRIC_GATES_FILE
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
        Write-Output "UNIT_RUBRIC_GATES_FILE: $($paths.RUBRIC_GATES_FILE)"
        Write-Output "UNIT_MANIFEST_FILE: $($paths.MANIFEST_FILE)"
        Write-Output "UNIT_CHARTER_FILE: $($paths.PROGRAM_CHARTER_FILE)"
        Write-Output "SUBJECT_CHARTER_FILE: $($paths.SUBJECT_CHARTER_FILE)"
    }
    exit 0
}

if (-not (Invoke-StagePreflight -RequestedStage $Stage)) { exit 1 }

$availableDocs = @(
    'brief.json',
    'design.json',
    'content-model.json',
    'design-decisions.json',
    'assessment-blueprint.json',
    'template-selection.json',
    'exercise-design.json',
    'sequence.json',
    'rubric-gates.json',
    'audit-report.json',
    'outputs/manifest.json'
) | Where-Object { Test-Path (Join-Path $paths.UNIT_DIR $_) -PathType Leaf }

if ($Json) {
    [PSCustomObject]@{ UNIT_DIR = $paths.UNIT_DIR; STAGE = $Stage; AVAILABLE_DOCS = $availableDocs } | ConvertTo-Json -Compress
} else {
    Write-Output "UNIT_DIR:$($paths.UNIT_DIR)"
    Write-Output "STAGE:$Stage"
    Write-Output 'AVAILABLE_DOCS:'
    foreach ($doc in $availableDocs) {
        Write-Output "  ✓ $doc"
    }
}
