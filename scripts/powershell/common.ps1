#!/usr/bin/env pwsh
# Common PowerShell functions for learning-content workflow scripts

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) { return $result }
    } catch {}
    return (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
}

function Get-CurrentBranch {
    if ($env:LCS_UNIT) { return $env:LCS_UNIT }
    if ($env:LCS_FEATURE) { return $env:LCS_FEATURE }

    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) { return $result }
    } catch {}

    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot 'specs'
    if (Test-Path $specsDir) {
        $latest = ''
        $highest = 0
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num; $latest = $_.Name }
            }
        }
        if ($latest) { return $latest }
    }

    return 'main'
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-UnitBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )

    if (-not $HasGit) {
        Write-Warning '[lcs] Warning: Git repository not detected; skipped branch validation'
        return $true
    }

    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a unit branch. Current branch: $Branch"
        Write-Output 'Unit branches should be named like: 001-unit-name'
        return $false
    }

    return $true
}

function Find-UnitDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$Branch
    )

    $specsDir = Join-Path $RepoRoot 'specs'
    if ($Branch -notmatch '^(\d{3})-') {
        return (Join-Path $specsDir $Branch)
    }

    $prefix = $matches[1]
    $matchesDirs = @()
    if (Test-Path $specsDir) {
        $matchesDirs = Get-ChildItem -Path $specsDir -Directory -Filter "$prefix-*" | Select-Object -ExpandProperty Name
    }

    if ($matchesDirs.Count -eq 0) {
        return (Join-Path $specsDir $Branch)
    }
    if ($matchesDirs.Count -eq 1) {
        return (Join-Path $specsDir $matchesDirs[0])
    }

    Write-Warning "Multiple unit directories found with prefix '$prefix': $($matchesDirs -join ', ')"
    return (Join-Path $specsDir $Branch)
}

function Get-UnitPathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $unitDir = Find-UnitDirByPrefix -RepoRoot $repoRoot -Branch $currentBranch

    [PSCustomObject]@{
        REPO_ROOT = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT = $hasGit
        UNIT_DIR = $unitDir
        BRIEF_FILE = Join-Path $unitDir 'brief.md'
        DESIGN_FILE = Join-Path $unitDir 'design.md'
        SEQUENCE_FILE = Join-Path $unitDir 'sequence.md'
        RESEARCH_FILE = Join-Path $unitDir 'research.md'
        CONTENT_MODEL_FILE = Join-Path $unitDir 'content-model.md'
        ASSESSMENT_MAP_FILE = Join-Path $unitDir 'assessment-map.md'
        DELIVERY_GUIDE_FILE = Join-Path $unitDir 'delivery-guide.md'
        RUBRICS_DIR = Join-Path $unitDir 'rubrics'
        OUTPUTS_DIR = Join-Path $unitDir 'outputs'
        CHARTER_FILE = Join-Path $repoRoot '.lcs/memory/charter.md'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    }
    Write-Output "  ✗ $Description"
    return $false
}
