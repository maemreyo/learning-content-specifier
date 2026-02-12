#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireSequence,
    [switch]$IncludeSequence,
    [switch]$PathsOnly,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./check-workflow-prereqs.ps1 [-Json] [-RequireSequence] [-IncludeSequence] [-PathsOnly]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$paths = Get-UnitPathsEnv

if (-not (Test-UnitBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) { exit 1 }

if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT = $paths.REPO_ROOT
            BRANCH = $paths.CURRENT_BRANCH
            UNIT_DIR = $paths.UNIT_DIR
            BRIEF_FILE = $paths.BRIEF_FILE
            DESIGN_FILE = $paths.DESIGN_FILE
            SEQUENCE_FILE = $paths.SEQUENCE_FILE
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "UNIT_DIR: $($paths.UNIT_DIR)"
        Write-Output "BRIEF_FILE: $($paths.BRIEF_FILE)"
        Write-Output "DESIGN_FILE: $($paths.DESIGN_FILE)"
        Write-Output "SEQUENCE_FILE: $($paths.SEQUENCE_FILE)"
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

$docs = @()
if (Test-Path $paths.RESEARCH_FILE) { $docs += 'research.md' }
if (Test-Path $paths.CONTENT_MODEL_FILE) { $docs += 'content-model.md' }
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
