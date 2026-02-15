#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [string]$Program,
    [switch]$CheckoutBranch,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$UnitDescription
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host 'Usage: ./create-new-unit.ps1 [-Json] [-Program <id>] [-ShortName <name>] [-Number N] [-CheckoutBranch] <unit description>'
    exit 0
}

if (-not $UnitDescription -or $UnitDescription.Count -eq 0) {
    Write-Error 'Usage: ./create-new-unit.ps1 [-Json] [-Program <id>] [-ShortName <name>] [-Number N] [-CheckoutBranch] <unit description>'
    exit 1
}

. "$PSScriptRoot/common.ps1"

$unitDesc = ($UnitDescription -join ' ').Trim()
$repoRoot = Get-RepoRoot
$contextDir = Join-Path $repoRoot '.lcs/context'
$programsRoot = Join-Path $repoRoot 'programs'
New-Item -ItemType Directory -Path $contextDir -Force | Out-Null
New-Item -ItemType Directory -Path $programsRoot -Force | Out-Null

function Convert-ToSlug([string]$Name) {
    return ($Name.ToLower() -replace '[^a-z0-9]+', '-' -replace '^-+', '' -replace '-+$', '' -replace '-{2,}', '-')
}

function Get-UnitSuffix([string]$Description) {
    $stopWords = @('i','a','an','the','to','for','of','in','on','at','by','with','from','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','should','could','can','may','might','must','shall','this','that','these','those','my','your','our','their','want','need','add','get','set')
    $clean = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $clean -split '\s+' | Where-Object { $_ -and $_.Length -ge 3 -and ($stopWords -notcontains $_) }
    if ($words.Count -eq 0) {
        $fallback = Convert-ToSlug $Description
        if (-not $fallback) { return 'unit' }
        return (($fallback -split '-') | Select-Object -First 3) -join '-'
    }
    return (($words | Select-Object -First 3) -join '-')
}

function Get-HighestUnitNumber([string]$UnitsDir) {
    $highest = 0
    if (Test-Path $UnitsDir -PathType Container) {
        Get-ChildItem -Path $UnitsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $n = [int]$matches[1]
                if ($n -gt $highest) { $highest = $n }
            }
        }
    }
    return $highest
}

function Resolve-ProgramId {
    if ($Program) { return (Convert-ToSlug $Program) }
    if ($env:LCS_PROGRAM) { return (Convert-ToSlug $env:LCS_PROGRAM) }

    $fromContext = Get-ContextValue -FilePath (Join-Path $contextDir 'current-program')
    if ($fromContext) { return $fromContext }

    $fromPwd = Get-ProgramFromPwd -RepoRoot $repoRoot
    if ($fromPwd) { return $fromPwd }

    return $null
}

$programId = Resolve-ProgramId
if (-not $programId) {
    Write-Error 'No active program context found. Run /lcs.charter first or pass -Program <id>.'
    exit 1
}

$programDir = Join-Path $programsRoot $programId
if (-not (Test-Path $programDir -PathType Container)) {
    Write-Error "Program directory does not exist: $programDir`nRun /lcs.charter first to scaffold the program."
    exit 1
}

$unitsDir = Join-Path $programDir 'units'
New-Item -ItemType Directory -Path $unitsDir -Force | Out-Null

$unitSuffix = if ($ShortName) { Convert-ToSlug $ShortName } else { Get-UnitSuffix $unitDesc }
if (-not $unitSuffix) { $unitSuffix = 'unit' }

if ($Number -eq 0) {
    $Number = (Get-HighestUnitNumber -UnitsDir $unitsDir) + 1
}

$unitNum = ('{0:000}' -f $Number)
$unitName = "$unitNum-$unitSuffix"
$unitDir = Join-Path $unitsDir $unitName
New-Item -ItemType Directory -Path $unitDir -Force | Out-Null

if ((Test-HasGit) -and $CheckoutBranch) {
    $branchName = "$programId-$unitName"
    git checkout -b $branchName | Out-Null
} elseif (Test-HasGit) {
    Write-Warning '[lcs] Branch auto-checkout disabled. Staying on current branch.'
}

$contractVersion = Get-ContractVersion
$template = Join-Path $repoRoot '.lcs/templates/brief-template.md'
$briefFile = Join-Path $unitDir 'brief.md'
$briefJsonFile = Join-Path $unitDir 'brief.json'
if (Test-Path $template -PathType Leaf) {
    Copy-Item -Path $template -Destination $briefFile -Force
} else {
    New-Item -ItemType File -Path $briefFile -Force | Out-Null
}

if (-not (Test-Path $briefJsonFile -PathType Leaf)) {
@"
{
  "contract_version": "$contractVersion",
  "unit_id": "$unitName",
  "program_id": "$programId",
  "title": "$unitName",
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
"@ | Set-Content -Path $briefJsonFile -Encoding utf8
}

Set-ContextValue -FilePath (Join-Path $contextDir 'current-program') -Value $programId
Set-ContextValue -FilePath (Join-Path $contextDir 'current-unit') -Value $unitName
$env:LCS_PROGRAM = $programId
$env:LCS_UNIT = $unitName

if ($Json) {
    [PSCustomObject]@{
        PROGRAM_ID = $programId
        PROGRAM_DIR = $programDir
        UNIT_NAME = $unitName
        UNIT_DIR = $unitDir
        BRIEF_FILE = $briefFile
        UNIT_NUM = $unitNum
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $programId"
    Write-Output "PROGRAM_DIR: $programDir"
    Write-Output "UNIT_NAME: $unitName"
    Write-Output "UNIT_DIR: $unitDir"
    Write-Output "BRIEF_FILE: $briefFile"
    Write-Output "UNIT_NUM: $unitNum"
}
