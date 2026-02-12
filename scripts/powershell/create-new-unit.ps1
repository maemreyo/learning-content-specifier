#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$UnitDescription
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host 'Usage: ./create-new-unit.ps1 [-Json] [-ShortName <name>] [-Number N] <unit description>'
    exit 0
}

if (-not $UnitDescription -or $UnitDescription.Count -eq 0) {
    Write-Error 'Usage: ./create-new-unit.ps1 [-Json] [-ShortName <name>] [-Number N] <unit description>'
    exit 1
}

$unitDesc = ($UnitDescription -join ' ').Trim()

function ConvertTo-CleanName([string]$Name) {
    return ($Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', '')
}

function Get-BranchName([string]$Description) {
    $stopWords = @('i','a','an','the','to','for','of','in','on','at','by','with','from','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','should','could','can','may','might','must','shall','this','that','these','those','my','your','our','their','want','need','add','get','set')
    $clean = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $clean -split '\s+' | Where-Object { $_ -and $_.Length -ge 3 -and ($stopWords -notcontains $_) }
    if ($words.Count -eq 0) {
        $fallback = ConvertTo-CleanName $Description
        return (($fallback -split '-') | Select-Object -First 3) -join '-'
    }
    return ($words | Select-Object -First 3) -join '-'
}

function Find-RepositoryRoot([string]$StartDir) {
    $current = Resolve-Path $StartDir
    while ($true) {
        if ((Test-Path (Join-Path $current '.git')) -or (Test-Path (Join-Path $current '.lcs'))) { return $current }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) { return $null }
        $current = $parent
    }
}

function Get-HighestFromSpecs([string]$SpecsDir) {
    $highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $n = [int]$matches[1]
                if ($n -gt $highest) { $highest = $n }
            }
        }
    }
    return $highest
}

function Get-HighestFromBranches() {
    $highest = 0
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($branch in $branches) {
                $clean = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                if ($clean -match '^(\d+)-') {
                    $n = [int]$matches[1]
                    if ($n -gt $highest) { $highest = $n }
                }
            }
        }
    } catch {}
    return $highest
}

$fallbackRoot = Find-RepositoryRoot -StartDir $PSScriptRoot
if (-not $fallbackRoot) { Write-Error 'Could not determine repository root.'; exit 1 }

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    $hasGit = ($LASTEXITCODE -eq 0)
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot
$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

$unitSuffix = if ($ShortName) { ConvertTo-CleanName $ShortName } else { Get-BranchName $unitDesc }

if ($Number -eq 0) {
    if ($hasGit) {
        try { git fetch --all --prune 2>$null | Out-Null } catch {}
        $max = [Math]::Max((Get-HighestFromBranches), (Get-HighestFromSpecs $specsDir))
        $Number = $max + 1
    } else {
        $Number = (Get-HighestFromSpecs $specsDir) + 1
    }
}

$unitNum = ('{0:000}' -f $Number)
$unitName = "$unitNum-$unitSuffix"

if ($hasGit) {
    try { git checkout -b $unitName | Out-Null } catch { Write-Warning "Failed to create git branch: $unitName" }
} else {
    Write-Warning "[lcs] Warning: Git repository not detected; skipped branch creation for $unitName"
}

$unitDir = Join-Path $specsDir $unitName
New-Item -ItemType Directory -Path $unitDir -Force | Out-Null

$template = Join-Path $repoRoot '.lcs/templates/brief-template.md'
$briefFile = Join-Path $unitDir 'brief.md'
$briefJsonFile = Join-Path $unitDir 'brief.json'
if (Test-Path $template) { Copy-Item $template $briefFile -Force } else { New-Item -ItemType File -Path $briefFile -Force | Out-Null }

if (-not (Test-Path $briefJsonFile)) {
@"
{
  "contract_version": "1.0.0",
  "unit_id": "$unitName",
  "title": "$unitName",
  "audience": {
    "primary": "unspecified",
    "entry_level": "unspecified",
    "delivery_context": "unspecified"
  },
  "duration_minutes": 60,
  "learning_outcomes": [
    {
      "lo_id": "LO1",
      "priority": "P1",
      "statement": "Populate from brief.md",
      "evidence": "Populate from brief.md",
      "acceptance_criteria": ["Populate from brief.md"]
    }
  ],
  "scope": {
    "in_scope": [],
    "out_of_scope": []
  }
}
"@ | Set-Content -Path $briefJsonFile -Encoding utf8
}

$env:LCS_UNIT = $unitName

if ($Json) {
    [PSCustomObject]@{ UNIT_NAME=$unitName; BRIEF_FILE=$briefFile; UNIT_NUM=$unitNum } | ConvertTo-Json -Compress
} else {
    Write-Output "UNIT_NAME: $unitName"
    Write-Output "BRIEF_FILE: $briefFile"
    Write-Output "UNIT_NUM: $unitNum"
}
