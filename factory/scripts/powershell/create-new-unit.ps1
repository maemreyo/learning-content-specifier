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
$renderMdSidecar = @('1', 'true', 'yes', 'on') -contains (($env:LCS_RENDER_MD_SIDECAR ?? '0').ToLowerInvariant())
$repoRoot = Get-RepoRoot
$contextDir = Join-Path $repoRoot '.lcs/context'
$programsRoot = Join-Path $repoRoot 'programs'
New-Item -ItemType Directory -Path $contextDir -Force | Out-Null
New-Item -ItemType Directory -Path $programsRoot -Force | Out-Null

if ($unitDesc -and $unitDesc.TrimStart().StartsWith('{')) {
    try {
        $intentPayload = $unitDesc | ConvertFrom-Json
        if ($intentPayload) {
            if (-not $Program -and $intentPayload.program -is [string] -and $intentPayload.program.Trim()) {
                $Program = [string]$intentPayload.program
            }
            if (-not $ShortName -and $intentPayload.short_name -is [string] -and $intentPayload.short_name.Trim()) {
                $ShortName = [string]$intentPayload.short_name
            }
            if ($Number -eq 0 -and $intentPayload.number) {
                $digits = (($intentPayload.number | Out-String) -replace '[^0-9]', '').Trim()
                if ($digits -match '^\d+$') {
                    $Number = [int]$digits
                }
            }
            if ($intentPayload.description -is [string] -and $intentPayload.description.Trim()) {
                $unitDesc = [string]$intentPayload.description
            } elseif ($intentPayload.title -is [string] -and $intentPayload.title.Trim()) {
                $unitDesc = [string]$intentPayload.title
            } elseif ($intentPayload.intent -is [string] -and $intentPayload.intent.Trim()) {
                $unitDesc = [string]$intentPayload.intent
            }
        }
    } catch {
        # Fall back to raw unit description text.
    }
}

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

function Get-RoadmapSlotInfo {
    param(
        [string]$RoadmapFile,
        [int]$Slot
    )

    if (-not (Test-Path $RoadmapFile -PathType Leaf)) {
        return $null
    }

    try {
        $payload = Get-Content -Path $RoadmapFile -Raw -Encoding utf8 | ConvertFrom-Json
    } catch {
        return $null
    }

    if (-not $payload.units) {
        return $null
    }

    foreach ($item in $payload.units) {
        if ([int]$item.slot -eq $Slot) {
            return [PSCustomObject]@{
                SessionStart = [int]($item.session_start ?? $item.day_start)
                SessionEnd = [int]($item.session_end ?? $item.day_end)
                EstimatedDayStart = [int]($item.estimated_day_start ?? $item.day_start)
                EstimatedDayEnd = [int]($item.estimated_day_end ?? $item.day_end)
                ExpectedUnits = [int]$payload.expected_units
            }
        }
    }

    return $null
}

$programId = Resolve-ProgramId
if (-not $programId) {
    Write-Error 'No active program context found. Run /lcs.charter first or pass -Program <id>.'
    exit 1
}

$loaderArgs = @("$PSScriptRoot/load-stage-context.ps1", '-Stage', 'define', '-Program', $programId, '-Json')
if ($unitDesc) {
    $loaderArgs += @('-Intent', $unitDesc)
}
$loaderRaw = & $loaderArgs[0] $loaderArgs[1..($loaderArgs.Count - 1)]
if (-not $loaderRaw) {
    throw 'define preflight failed to execute'
}
try {
    $loaderObj = $loaderRaw | ConvertFrom-Json
} catch {
    throw 'Invalid define preflight payload'
}
if ([string]$loaderObj.STATUS -ne 'PASS') {
    $missing = @($loaderObj.MISSING_INPUTS)
    $blockers = @($loaderObj.BLOCKERS)
    $parts = @()
    if ($missing.Count -gt 0) { $parts += ('missing=' + ($missing -join ',')) }
    if ($blockers.Count -gt 0) { $parts += ('blockers=' + ($blockers -join '; ')) }
    $summary = if ($parts.Count -gt 0) { $parts -join ' | ' } else { 'unknown preflight blocker' }
    throw "define preflight BLOCK ($summary)"
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
$roadmapFile = Join-Path $programDir 'roadmap.json'
$roadmapInfo = Get-RoadmapSlotInfo -RoadmapFile $roadmapFile -Slot $Number
$sessionStart = if ($roadmapInfo) { $roadmapInfo.SessionStart } else { 0 }
$sessionEnd = if ($roadmapInfo) { $roadmapInfo.SessionEnd } else { 0 }
$estimatedDayStart = if ($roadmapInfo) { $roadmapInfo.EstimatedDayStart } else { 0 }
$estimatedDayEnd = if ($roadmapInfo) { $roadmapInfo.EstimatedDayEnd } else { 0 }
$expectedUnits = if ($roadmapInfo) { $roadmapInfo.ExpectedUnits } else { 0 }

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
if ($renderMdSidecar) {
    if (Test-Path $template -PathType Leaf) {
        Copy-Item -Path $template -Destination $briefFile -Force
    } else {
        New-Item -ItemType File -Path $briefFile -Force | Out-Null
    }
}

if (-not (Test-Path $briefJsonFile -PathType Leaf)) {
    $briefPayload = [ordered]@{
        contract_version = $contractVersion
        unit_id = $unitName
        program_id = $programId
        title = $unitName
        audience = [ordered]@{
            primary = 'general learners'
            entry_level = 'beginner'
            delivery_context = 'self-paced'
        }
        duration_minutes = 60
        learning_outcomes = @(
            [ordered]@{
                lo_id = 'LO1'
                priority = 'P1'
                statement = 'Learner will be able to demonstrate LO1 with measurable evidence.'
                evidence = 'Assessment evidence mapped to LO1 is available in artifacts.'
                acceptance_criteria = @(
                    'Given the learning context, When the learner attempts LO1 practice, Then observable evidence meets the completion criteria.'
                )
            }
        )
        scope = [ordered]@{
            in_scope = @()
            out_of_scope = @()
        }
    }

    if ($sessionStart -gt 0 -and $sessionEnd -gt 0) {
        $briefPayload.program_scope = [ordered]@{
            session_start = $sessionStart
            session_end = $sessionEnd
            estimated_day_start = $estimatedDayStart
            estimated_day_end = $estimatedDayEnd
            slot_index = $Number
            expected_units = if ($expectedUnits -gt 0) { $expectedUnits } else { 1 }
        }
    }

    $briefPayload | ConvertTo-Json -Depth 8 | Set-Content -Path $briefJsonFile -Encoding utf8
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
        BRIEF_JSON_FILE = $briefJsonFile
        BRIEF_FILE = $briefFile
        UNIT_NUM = $unitNum
        SESSION_START = $sessionStart
        SESSION_END = $sessionEnd
        ESTIMATED_DAY_START = $estimatedDayStart
        ESTIMATED_DAY_END = $estimatedDayEnd
        EXPECTED_UNITS = $expectedUnits
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $programId"
    Write-Output "PROGRAM_DIR: $programDir"
    Write-Output "UNIT_NAME: $unitName"
    Write-Output "UNIT_DIR: $unitDir"
    Write-Output "BRIEF_JSON_FILE: $briefJsonFile"
    Write-Output "BRIEF_FILE: $briefFile"
    Write-Output "UNIT_NUM: $unitNum"
    Write-Output "SESSION_START: $sessionStart"
    Write-Output "SESSION_END: $sessionEnd"
    Write-Output "ESTIMATED_DAY_START: $estimatedDayStart"
    Write-Output "ESTIMATED_DAY_END: $estimatedDayEnd"
    Write-Output "EXPECTED_UNITS: $expectedUnits"
}
