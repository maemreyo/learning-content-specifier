#!/usr/bin/env pwsh
# Common PowerShell functions for learning-content workflow scripts

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) { return (@($result) | Select-Object -First 1) }
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

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-ContextValue {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath -PathType Leaf)) { return $null }
    $raw = Get-Content -Path $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $raw) { return $null }
    return $raw.Trim()
}

function Set-ContextValue {
    param(
        [string]$FilePath,
        [string]$Value
    )
    $parent = Split-Path -Parent $FilePath
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -Path $FilePath -Value $Value -Encoding utf8
}

function Get-ProgramFromPwd {
    param([string]$RepoRoot)
    $cwd = (Get-Location).Path
    $prefix = Join-Path $RepoRoot 'programs'
    if (-not $cwd.StartsWith($prefix)) { return $null }
    $rest = $cwd.Substring($prefix.Length).TrimStart('/','\\')
    if (-not $rest) { return $null }
    return ($rest -split '[\\/]')[0]
}

function Get-UnitFromPwd {
    param([string]$RepoRoot)
    $cwd = (Get-Location).Path
    $prefix = Join-Path $RepoRoot 'programs'
    if (-not $cwd.StartsWith($prefix)) { return $null }

    $rest = $cwd.Substring($prefix.Length).TrimStart('/','\\')
    if (-not $rest) { return $null }

    $parts = $rest -split '[\\/]'
    if ($parts.Count -ge 3 -and $parts[1] -eq 'units') {
        return $parts[2]
    }

    return $null
}

function Get-CurrentProgram {
    param([string]$RepoRoot)

    if ($env:LCS_PROGRAM) {
        return $env:LCS_PROGRAM.Trim()
    }

    $contextFile = Join-Path $RepoRoot '.lcs/context/current-program'
    $fromContext = Get-ContextValue -FilePath $contextFile
    if ($fromContext) { return $fromContext }

    return Get-ProgramFromPwd -RepoRoot $RepoRoot
}

function Get-CurrentUnit {
    param([string]$RepoRoot)

    if ($env:LCS_UNIT) {
        return $env:LCS_UNIT.Trim()
    }

    $contextFile = Join-Path $RepoRoot '.lcs/context/current-unit'
    $fromContext = Get-ContextValue -FilePath $contextFile
    if ($fromContext) { return $fromContext }

    return Get-UnitFromPwd -RepoRoot $RepoRoot
}

function Get-InferredSingleUnitFromProgram {
    param([string]$ProgramDir)

    $unitsDir = Join-Path $ProgramDir 'units'
    if (-not (Test-Path $unitsDir -PathType Container)) { return $null }

    $matches = Get-ChildItem -Path $unitsDir -Directory | Where-Object { $_.Name -match '^[0-9]{3}-' }
    if ($matches.Count -eq 1) {
        return $matches[0].Name
    }

    return $null
}

function Test-UnitBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )

    if ([string]::IsNullOrWhiteSpace($Branch)) {
        Write-Output 'ERROR: No active unit context found.'
        Write-Output 'Run /lcs.define first or set .lcs/context/current-unit.'
        return $false
    }

    return $true
}

function Get-UnitPathsEnv {
    param([switch]$AllowMissingUnit)

    $repoRoot = Get-RepoRoot
    $programsRoot = Join-Path $repoRoot 'programs'
    $contextDir = Join-Path $repoRoot '.lcs/context'

    $programId = Get-CurrentProgram -RepoRoot $repoRoot
    $programDir = if ($programId) { Join-Path $programsRoot $programId } else { '' }

    $currentUnit = Get-CurrentUnit -RepoRoot $repoRoot
    if (-not $currentUnit -and $programDir) {
        $currentUnit = Get-InferredSingleUnitFromProgram -ProgramDir $programDir
    }

    if (-not $AllowMissingUnit) {
        if (-not $programId) {
            throw 'No active program context found. Run /lcs.charter first or set .lcs/context/current-program.'
        }
        if (-not (Test-Path $programDir -PathType Container)) {
            throw "Active program directory not found: $programDir"
        }
        if (-not $currentUnit) {
            throw "No active unit context found for program '$programId'. Run /lcs.define first or set .lcs/context/current-unit."
        }
    }

    $unitDir = ''
    if ($programId -and $currentUnit) {
        $unitDir = Join-Path $programDir "units/$currentUnit"
    }

    [PSCustomObject]@{
        REPO_ROOT = $repoRoot
        PROGRAMS_ROOT = $programsRoot
        CONTEXT_DIR = $contextDir
        CONTEXT_PROGRAM_FILE = Join-Path $contextDir 'current-program'
        CONTEXT_UNIT_FILE = Join-Path $contextDir 'current-unit'
        PROGRAM_ID = $programId
        PROGRAM_DIR = $programDir
        PROGRAM_FILE = if ($programDir) { Join-Path $programDir 'program.json' } else { '' }
        PROGRAM_CHARTER_FILE = if ($programDir) { Join-Path $programDir 'charter.md' } else { '' }
        PROGRAM_ROADMAP_JSON_FILE = if ($programDir) { Join-Path $programDir 'roadmap.json' } else { '' }
        PROGRAM_ROADMAP_MD_FILE = if ($programDir) { Join-Path $programDir 'roadmap.md' } else { '' }
        CURRENT_BRANCH = $currentUnit
        CURRENT_UNIT = $currentUnit
        HAS_GIT = Test-HasGit
        UNIT_DIR = $unitDir
        BRIEF_FILE = if ($unitDir) { Join-Path $unitDir 'brief.md' } else { '' }
        BRIEF_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'brief.json' } else { '' }
        DESIGN_FILE = if ($unitDir) { Join-Path $unitDir 'design.md' } else { '' }
        DESIGN_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'design.json' } else { '' }
        SEQUENCE_FILE = if ($unitDir) { Join-Path $unitDir 'sequence.md' } else { '' }
        SEQUENCE_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'sequence.json' } else { '' }
        RESEARCH_FILE = if ($unitDir) { Join-Path $unitDir 'research.md' } else { '' }
        CONTENT_MODEL_FILE = if ($unitDir) { Join-Path $unitDir 'content-model.md' } else { '' }
        CONTENT_MODEL_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'content-model.json' } else { '' }
        EXERCISE_DESIGN_FILE = if ($unitDir) { Join-Path $unitDir 'exercise-design.md' } else { '' }
        EXERCISE_DESIGN_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'exercise-design.json' } else { '' }
        ASSESSMENT_MAP_FILE = if ($unitDir) { Join-Path $unitDir 'assessment-map.md' } else { '' }
        DELIVERY_GUIDE_FILE = if ($unitDir) { Join-Path $unitDir 'delivery-guide.md' } else { '' }
        DESIGN_DECISIONS_FILE = if ($unitDir) { Join-Path $unitDir 'design-decisions.json' } else { '' }
        ASSESSMENT_BLUEPRINT_FILE = if ($unitDir) { Join-Path $unitDir 'assessment-blueprint.json' } else { '' }
        TEMPLATE_SELECTION_FILE = if ($unitDir) { Join-Path $unitDir 'template-selection.json' } else { '' }
        AUDIT_REPORT_FILE = if ($unitDir) { Join-Path $unitDir 'audit-report.md' } else { '' }
        AUDIT_REPORT_JSON_FILE = if ($unitDir) { Join-Path $unitDir 'audit-report.json' } else { '' }
        RUBRIC_GATES_FILE = if ($unitDir) { Join-Path $unitDir 'rubric-gates.json' } else { '' }
        RUBRICS_DIR = if ($unitDir) { Join-Path $unitDir 'rubrics' } else { '' }
        OUTPUTS_DIR = if ($unitDir) { Join-Path $unitDir 'outputs' } else { '' }
        MANIFEST_FILE = if ($unitDir) { Join-Path (Join-Path $unitDir 'outputs') 'manifest.json' } else { '' }
        CHARTER_FILE = Join-Path $repoRoot '.lcs/memory/charter.md'
        SUBJECT_CHARTER_FILE = Join-Path $repoRoot '.lcs/memory/charter.md'
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
        $indexPath = Join-Path $repoRoot '.lcs/contracts/index.json'
    }
    if (-not (Test-Path -Path $indexPath -PathType Leaf)) {
        throw "Missing contract index. Checked: $repoRoot/contracts/index.json and $repoRoot/.lcs/contracts/index.json"
    }

    $payload = Get-Content -Path $indexPath -Raw -Encoding utf8 | ConvertFrom-Json
    $version = [string]$payload.contract_version
    if (-not $version) {
        throw 'contracts/index.json missing contract_version'
    }
    if ($version -notmatch '^\d+\.\d+\.\d+$') {
        throw "Invalid contract_version '$version' in contracts/index.json (expected X.Y.Z)"
    }
    return $version
}
