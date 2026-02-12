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
