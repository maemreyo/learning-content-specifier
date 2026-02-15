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
    if ($fromContext -and (Test-Path (Join-Path $programsRoot $fromContext))) {
        return $fromContext
    }

    return (New-ProgramId -Intent $intent)
}

$programId = Resolve-ProgramId
if (-not $programId) {
    throw 'Could not determine program id'
}

$programDir = Join-Path $programsRoot $programId
$programFile = Join-Path $programDir 'program.json'
$programCharterFile = Join-Path $programDir 'charter.md'

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
    } | ConvertTo-Json -Depth 5
    Set-Content -Path $programFile -Value $payload -Encoding utf8
}

if (-not (Test-Path $programCharterFile -PathType Leaf)) {
    if (Test-Path $templateFile -PathType Leaf) {
        Copy-Item -Path $templateFile -Destination $programCharterFile -Force
    } else {
        New-Item -ItemType File -Path $programCharterFile -Force | Out-Null
    }
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
        SUBJECT_CHARTER_FILE = $subjectCharterFile
    } | ConvertTo-Json -Compress
} else {
    Write-Output "PROGRAM_ID: $programId"
    Write-Output "PROGRAM_DIR: $programDir"
    Write-Output "PROGRAM_FILE: $programFile"
    Write-Output "PROGRAM_CHARTER_FILE: $programCharterFile"
    Write-Output "SUBJECT_CHARTER_FILE: $subjectCharterFile"
}
