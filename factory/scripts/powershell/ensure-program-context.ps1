#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Program,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProgramIntent
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host 'Usage: ./ensure-program-context.ps1 [-Json] [-Program <id>] <program intent>'
    exit 0
}

. "$PSScriptRoot/common.ps1"

$intent = ($ProgramIntent -join ' ').Trim()
$repoRoot = Get-RepoRoot
$contextDir = Join-Path $repoRoot '.lcs/context'
$programsRoot = Join-Path $repoRoot 'programs'
$templateFile = Join-Path $repoRoot '.lcs/templates/charter-template.md'
$subjectCharterFile = Join-Path $repoRoot '.lcs/memory/charter.md'

New-Item -ItemType Directory -Path $contextDir -Force | Out-Null
New-Item -ItemType Directory -Path $programsRoot -Force | Out-Null

function Convert-ToSlug([string]$Value) {
    return ($Value.ToLower() -replace '[^a-z0-9]+', '-' -replace '^-+', '' -replace '-+$', '' -replace '-{2,}', '-')
}

function Get-ProgramBaseSlug([string]$ProgramId) {
    if (-not $ProgramId) { return '' }
    return ($ProgramId -replace '-\d{8}-\d{4}(-\d{2})?$', '')
}

function Get-ProgramMatchesForSlug([string]$IntentSlug) {
    $matches = @()
    if (-not (Test-Path $programsRoot -PathType Container)) {
        return $matches
    }

    Get-ChildItem -Path $programsRoot -Directory | ForEach-Object {
        $base = Get-ProgramBaseSlug -ProgramId $_.Name
        if ($base -eq $IntentSlug) {
            $matches += $_.Name
        }
    }

    return $matches | Sort-Object
}

function New-ProgramId([string]$Intent) {
    $slug = Convert-ToSlug $Intent
    if (-not $slug) { $slug = 'program' }

    $base = "$slug-$(Get-Date -Format 'yyyyMMdd-HHmm')"
    $candidate = $base
    $counter = 2
    while (Test-Path (Join-Path $programsRoot $candidate)) {
        $candidate = ('{0}-{1:00}' -f $base, $counter)
        $counter++
    }
    return $candidate
}

function Resolve-ProgramId {
    if ($Program) { return (Convert-ToSlug $Program) }
    if ($env:LCS_PROGRAM) { return (Convert-ToSlug $env:LCS_PROGRAM) }

    $fromContext = Get-ContextValue -FilePath (Join-Path $contextDir 'current-program')
    $hasContextProgram = $fromContext -and (Test-Path (Join-Path $programsRoot $fromContext))

    if (-not $intent) {
        if ($hasContextProgram) {
            return $fromContext
        }
        return (New-ProgramId -Intent $intent)
    }

    $intentSlug = Convert-ToSlug $intent
    if (-not $intentSlug) {
        if ($hasContextProgram) {
            return $fromContext
        }
        return (New-ProgramId -Intent $intent)
    }

    if ($hasContextProgram) {
        $contextBase = Get-ProgramBaseSlug -ProgramId $fromContext
        if ($contextBase -eq $intentSlug) {
            return $fromContext
        }
    }

    $matches = Get-ProgramMatchesForSlug -IntentSlug $intentSlug
    if ($matches.Count -eq 1) {
        return $matches[0]
    }
    if ($matches.Count -gt 1) {
        $selected = $matches[-1]
        Write-Warning "[lcs] Multiple program matches for intent '$intent'. Auto-selecting latest: $selected"
        return $selected
    }

    return (New-ProgramId -Intent $intent)
}

function Get-DurationDays([string]$Text) {
    if (-not $Text) { return 0 }
    $lower = $Text.ToLower()

    $matches = [regex]::Matches($lower, '([0-9]{1,3})\s*-?\s*(day|days|ngay|ngày)\b')
    if ($matches.Count -gt 0) {
        return [int]$matches[0].Groups[1].Value
    }

    $matches = [regex]::Matches($lower, '([0-9]{1,3})\s*d\b')
    if ($matches.Count -gt 0) {
        return [int]$matches[0].Groups[1].Value
    }

    return 0
}

function Get-TargetSessions([string]$Text) {
    if (-not $Text) { return 0 }
    $lower = $Text.ToLower()

    $matches = [regex]::Matches($lower, '([0-9]{1,3})\s*-?\s*(session|sessions|buoi|buổi)\b')
    if ($matches.Count -gt 0) {
        return [int]$matches[0].Groups[1].Value
    }

    return 0
}

function Write-RoadmapFiles {
    param(
        [string]$RoadmapJsonFile,
        [string]$RoadmapMdFile,
        [string]$ProgramId,
        [int]$TargetSessions,
        [int]$SessionSpan,
        [int]$SessionsPerWeek,
        [int]$ExpectedUnits,
        [int]$DurationDaysEstimate
    )

    $units = @()
    for ($i = 1; $i -le $ExpectedUnits; $i++) {
        $start = (($i - 1) * $SessionSpan) + 1
        $end = [Math]::Min($TargetSessions, $i * $SessionSpan)
        $dayStart = [int]([Math]::Floor((($start - 1) / [Math]::Max($SessionsPerWeek, 1)) * 7) + 1)
        $dayEnd = [int]([Math]::Floor((($end - 1) / [Math]::Max($SessionsPerWeek, 1)) * 7) + 7)
        $units += [PSCustomObject]@{
            slot = $i
            session_start = $start
            session_end = $end
            estimated_day_start = $dayStart
            estimated_day_end = $dayEnd
            suggested_unit_id = ('{0:000}-sessions-{1:000}-to-{2:000}' -f $i, $start, $end)
        }
    }

    $roadmapPayload = [ordered]@{
        program_id = $ProgramId
        progress_unit = 'study_session'
        target_sessions = $TargetSessions
        session_span = $SessionSpan
        sessions_per_week_assumption = $SessionsPerWeek
        expected_units = $ExpectedUnits
        duration_days_estimate = $DurationDaysEstimate
        units = $units
    }
    $roadmapPayload | ConvertTo-Json -Depth 6 | Set-Content -Path $RoadmapJsonFile -Encoding utf8

    $md = @()
    $md += "# Program Roadmap: $ProgramId"
    $md += ''
    $md += '- Progress unit: study session'
    $md += "- Target sessions: $TargetSessions"
    $md += "- Session span per unit: $SessionSpan"
    $md += "- Sessions/week assumption: $SessionsPerWeek"
    $md += "- Duration estimate (days): $DurationDaysEstimate"
    $md += "- Expected units: $ExpectedUnits"
    $md += ''
    $md += '| Slot | Session Range | Estimated Day Range | Suggested Unit ID |'
    $md += '|------|---------------|---------------------|-------------------|'
    foreach ($unit in $units) {
        $md += "| $($unit.slot) | $($unit.session_start)-$($unit.session_end) | $($unit.estimated_day_start)-$($unit.estimated_day_end) | ``$($unit.suggested_unit_id)`` |"
    }
    $md -join "`n" | Set-Content -Path $RoadmapMdFile -Encoding utf8
}

$programId = Resolve-ProgramId
if (-not $programId) {
    throw 'Could not determine program id'
}

$programDir = Join-Path $programsRoot $programId
$programFile = Join-Path $programDir 'program.json'
$programCharterFile = Join-Path $programDir 'charter.md'
$programRoadmapJsonFile = Join-Path $programDir 'roadmap.json'
$programRoadmapMdFile = Join-Path $programDir 'roadmap.md'
$sessionSpan = 4
$sessionsPerWeek = 3

$durationDays = Get-DurationDays -Text $intent
if ($durationDays -le 0 -and (Test-Path $programFile -PathType Leaf)) {
    try {
        $existingProgram = Get-Content -Path $programFile -Raw -Encoding utf8 | ConvertFrom-Json
        if ($existingProgram.duration_days -is [int] -and $existingProgram.duration_days -gt 0) {
            $durationDays = [int]$existingProgram.duration_days
        } elseif ($existingProgram.duration_days_estimate -is [int] -and $existingProgram.duration_days_estimate -gt 0) {
            $durationDays = [int]$existingProgram.duration_days_estimate
        }
    } catch {}
}
$targetSessions = Get-TargetSessions -Text $intent
if ($targetSessions -le 0 -and (Test-Path $programFile -PathType Leaf)) {
    try {
        $existingProgram = Get-Content -Path $programFile -Raw -Encoding utf8 | ConvertFrom-Json
        if ($existingProgram.target_sessions -is [int] -and $existingProgram.target_sessions -gt 0) {
            $targetSessions = [int]$existingProgram.target_sessions
        }
    } catch {}
}

$expectedUnits = 1
if ($targetSessions -le 0 -and $durationDays -gt 0) {
    $targetSessions = [int][Math]::Ceiling(($durationDays * $sessionsPerWeek) / 7.0)
}
if ($targetSessions -gt 0) {
    $expectedUnits = [int][Math]::Ceiling($targetSessions / [double]$sessionSpan)
} elseif ($durationDays -gt 0) {
    $expectedUnits = [int][Math]::Ceiling($durationDays / 7.0)
}

New-Item -ItemType Directory -Path (Join-Path $programDir 'units') -Force | Out-Null

if (-not (Test-Path $programFile -PathType Leaf)) {
    $nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $title = if ($intent) { $intent } else { $programId }
    $payload = [ordered]@{
        program_id = $programId
        title = $title
        status = 'draft'
        created_at = $nowUtc
        updated_at = $nowUtc
    }
    if ($targetSessions -gt 0) {
        $payload.progress_unit = 'study_session'
        $payload.target_sessions = $targetSessions
        $payload.session_span = $sessionSpan
        $payload.sessions_per_week_assumption = $sessionsPerWeek
        $payload.expected_units = $expectedUnits
    }
    if ($durationDays -gt 0) {
        $payload.duration_days_estimate = $durationDays
    }
    $payload | ConvertTo-Json -Depth 5 | Set-Content -Path $programFile -Encoding utf8
} elseif ($durationDays -gt 0 -or $targetSessions -gt 0) {
    try {
        $payload = Get-Content -Path $programFile -Raw -Encoding utf8 | ConvertFrom-Json
        if ($targetSessions -gt 0) {
            $payload.progress_unit = 'study_session'
            $payload.target_sessions = $targetSessions
            $payload.session_span = $sessionSpan
            $payload.sessions_per_week_assumption = $sessionsPerWeek
        }
        if ($durationDays -gt 0) {
            $payload.duration_days_estimate = $durationDays
        }
        $payload.expected_units = $expectedUnits
        if (-not $payload.updated_at) {
            $payload | Add-Member -NotePropertyName updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) -Force
        } else {
            $payload.updated_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        }
        $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $programFile -Encoding utf8
    } catch {}
}

if (-not (Test-Path $programCharterFile -PathType Leaf)) {
    if (Test-Path $templateFile -PathType Leaf) {
        Copy-Item -Path $templateFile -Destination $programCharterFile -Force
    } else {
        New-Item -ItemType File -Path $programCharterFile -Force | Out-Null
    }
}

if ($targetSessions -ge 8) {
    Write-RoadmapFiles -RoadmapJsonFile $programRoadmapJsonFile -RoadmapMdFile $programRoadmapMdFile -ProgramId $programId -TargetSessions $targetSessions -SessionSpan $sessionSpan -SessionsPerWeek $sessionsPerWeek -ExpectedUnits $expectedUnits -DurationDaysEstimate $durationDays
}

Set-ContextValue -FilePath (Join-Path $contextDir 'current-program') -Value $programId
Remove-Item -Path (Join-Path $contextDir 'current-unit') -ErrorAction SilentlyContinue
$env:LCS_PROGRAM = $programId

if ($Json) {
    [PSCustomObject]@{
        PROGRAM_ID = $programId
        PROGRAM_DIR = $programDir
        PROGRAM_FILE = $programFile
        PROGRAM_CHARTER_FILE = $programCharterFile
        PROGRAM_ROADMAP_JSON_FILE = $programRoadmapJsonFile
        PROGRAM_ROADMAP_MD_FILE = $programRoadmapMdFile
        TARGET_SESSIONS = $targetSessions
        DURATION_DAYS = $durationDays
        EXPECTED_UNITS = $expectedUnits
        SUBJECT_CHARTER_FILE = $subjectCharterFile
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $programId"
    Write-Output "PROGRAM_DIR: $programDir"
    Write-Output "PROGRAM_FILE: $programFile"
    Write-Output "PROGRAM_CHARTER_FILE: $programCharterFile"
    Write-Output "PROGRAM_ROADMAP_JSON_FILE: $programRoadmapJsonFile"
    Write-Output "PROGRAM_ROADMAP_MD_FILE: $programRoadmapMdFile"
    Write-Output "TARGET_SESSIONS: $targetSessions"
    Write-Output "DURATION_DAYS: $durationDays"
    Write-Output "EXPECTED_UNITS: $expectedUnits"
    Write-Output "SUBJECT_CHARTER_FILE: $subjectCharterFile"
}
