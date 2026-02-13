#!/usr/bin/env pwsh
# Common PowerShell functions for learning-content workflow scripts

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) { return $result }
    } catch {}
    return (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
}

function Resolve-PythonTool {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ToolName
    )

    $repoRoot = Get-RepoRoot
    $candidates = @(
        (Join-Path $repoRoot "factory/scripts/python/$ToolName"),
        (Join-Path $repoRoot ".lcs/scripts/$ToolName")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw "Could not locate python tool '$ToolName'"
}

function Get-CurrentBranch {
    if ($env:LCS_UNIT) { return $env:LCS_UNIT }

    function Get-LatestUnitFromSpecs {
        param([string]$RepoRoot)
        $specsDir = Join-Path $RepoRoot 'specs'
        if (-not (Test-Path $specsDir)) { return $null }

        $latest = $null
        $highest = -1
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $latest = $_.Name
                }
            }
        }
        return $latest
    }

    $repoRoot = Get-RepoRoot
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            $branch = (@($result) | Where-Object { $_ -and "$_".Trim() } | Select-Object -First 1)
            if ($branch -match '^[0-9]{3}-') { return $branch }
            $latest = Get-LatestUnitFromSpecs -RepoRoot $repoRoot
            if ($latest) { return $latest }
            return $branch
        }
    } catch {}

    $latestFallback = Get-LatestUnitFromSpecs -RepoRoot $repoRoot
    if ($latestFallback) { return $latestFallback }

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

    throw "Multiple unit directories found with prefix '$prefix': $($matchesDirs -join ', ')"
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
        BRIEF_JSON_FILE = Join-Path $unitDir 'brief.json'
        DESIGN_FILE = Join-Path $unitDir 'design.md'
        DESIGN_JSON_FILE = Join-Path $unitDir 'design.json'
        SEQUENCE_FILE = Join-Path $unitDir 'sequence.md'
        SEQUENCE_JSON_FILE = Join-Path $unitDir 'sequence.json'
        RESEARCH_FILE = Join-Path $unitDir 'research.md'
        CONTENT_MODEL_FILE = Join-Path $unitDir 'content-model.md'
        CONTENT_MODEL_JSON_FILE = Join-Path $unitDir 'content-model.json'
        ASSESSMENT_MAP_FILE = Join-Path $unitDir 'assessment-map.md'
        DELIVERY_GUIDE_FILE = Join-Path $unitDir 'delivery-guide.md'
        DESIGN_DECISIONS_FILE = Join-Path $unitDir 'design-decisions.json'
        AUDIT_REPORT_FILE = Join-Path $unitDir 'audit-report.md'
        AUDIT_REPORT_JSON_FILE = Join-Path $unitDir 'audit-report.json'
        RUBRICS_DIR = Join-Path $unitDir 'rubrics'
        OUTPUTS_DIR = Join-Path $unitDir 'outputs'
        MANIFEST_FILE = Join-Path (Join-Path $unitDir 'outputs') 'manifest.json'
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

function Get-ContractVersion {
    $repoRoot = Get-RepoRoot
    $indexPath = Join-Path $repoRoot 'contracts/index.json'
    if (-not (Test-Path -Path $indexPath -PathType Leaf)) {
        throw "Missing contract index: $indexPath"
    }

    $payload = Get-Content -Path $indexPath -Raw -Encoding utf8 | ConvertFrom-Json
    $version = [string]$payload.contract_version
    if (-not $version) {
        throw "contracts/index.json missing contract_version"
    }
    if ($version -notmatch '^\d+\.\d+\.\d+$') {
        throw "Invalid contract_version '$version' in contracts/index.json (expected X.Y.Z)"
    }
    return $version
}
