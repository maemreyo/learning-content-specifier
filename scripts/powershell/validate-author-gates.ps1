#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./validate-author-gates.ps1 [-Json]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$paths = Get-UnitPathsEnv

if (-not (Test-UnitBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) {
    exit 1
}

$auditFile = Join-Path $paths.UNIT_DIR 'audit-report.md'
$rubricUnchecked = 0
$rubricBlockers = 0
$auditDecision = 'MISSING'
$auditOpenCritical = 0
$auditOpenHigh = 0
$blockers = @()

if (-not (Test-Path $paths.RUBRICS_DIR -PathType Container)) {
    $blockers += "Missing rubrics directory: $($paths.RUBRICS_DIR)"
} else {
    $rubricFiles = Get-ChildItem -Path $paths.RUBRICS_DIR -Filter '*.md' -File -ErrorAction SilentlyContinue
    if (-not $rubricFiles) {
        $blockers += "No rubric files found in $($paths.RUBRICS_DIR)"
    } else {
        foreach ($rubric in $rubricFiles) {
            $content = Get-Content -Path $rubric.FullName -Encoding utf8
            $rubricUnchecked += @($content | Where-Object { $_ -match '^\s*-\s*\[\s\]' }).Count
            $rubricBlockers += @($content | Where-Object { $_ -match 'status:\s*(FAIL|BLOCK|UNSET|TODO)' }).Count
        }
    }
}

if ($rubricUnchecked -gt 0) {
    $blockers += "Rubric has $rubricUnchecked unchecked item(s)"
}

if ($rubricBlockers -gt 0) {
    $blockers += "Rubric has $rubricBlockers non-pass status item(s)"
}

if (-not (Test-Path $auditFile -PathType Leaf)) {
    $blockers += "Missing audit report: $auditFile"
} else {
    $auditLines = Get-Content -Path $auditFile -Encoding utf8

    $decisionLine = $auditLines | Where-Object { $_ -match '^Gate Decision:\s*(PASS|BLOCK)$' } | Select-Object -First 1
    if ($decisionLine) {
        $auditDecision = ($decisionLine -replace '^Gate Decision:\s*', '').Trim().ToUpper()
    } else {
        $blockers += "Audit report missing 'Gate Decision: PASS|BLOCK'"
    }

    $criticalLine = $auditLines | Where-Object { $_ -match '^Open Critical:\s*\d+' } | Select-Object -First 1
    if ($criticalLine) {
        $auditOpenCritical = [int](($criticalLine -replace '^Open Critical:\s*', '').Trim())
    } else {
        $blockers += "Audit report missing 'Open Critical: <number>'"
    }

    $highLine = $auditLines | Where-Object { $_ -match '^Open High:\s*\d+' } | Select-Object -First 1
    if ($highLine) {
        $auditOpenHigh = [int](($highLine -replace '^Open High:\s*', '').Trim())
    } else {
        $blockers += "Audit report missing 'Open High: <number>'"
    }
}

if ($auditDecision -ne 'PASS') {
    $blockers += "Audit decision is $auditDecision"
}

if ($auditOpenCritical -gt 0) {
    $blockers += "Audit has $auditOpenCritical open CRITICAL finding(s)"
}

if ($auditOpenHigh -gt 0) {
    $blockers += "Audit has $auditOpenHigh open HIGH finding(s)"
}

$status = if ($blockers.Count -gt 0) { 'BLOCK' } else { 'PASS' }

$result = [PSCustomObject]@{
    STATUS = $status
    UNIT_DIR = $paths.UNIT_DIR
    RUBRIC_UNCHECKED = $rubricUnchecked
    RUBRIC_BLOCKERS = $rubricBlockers
    AUDIT_DECISION = $auditDecision
    AUDIT_OPEN_CRITICAL = $auditOpenCritical
    AUDIT_OPEN_HIGH = $auditOpenHigh
    BLOCKERS = ($blockers -join '; ')
}

if ($Json) {
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "STATUS: $($result.STATUS)"
    Write-Output "UNIT_DIR: $($result.UNIT_DIR)"
    Write-Output "RUBRIC_UNCHECKED: $($result.RUBRIC_UNCHECKED)"
    Write-Output "RUBRIC_BLOCKERS: $($result.RUBRIC_BLOCKERS)"
    Write-Output "AUDIT_DECISION: $($result.AUDIT_DECISION)"
    Write-Output "AUDIT_OPEN_CRITICAL: $($result.AUDIT_OPEN_CRITICAL)"
    Write-Output "AUDIT_OPEN_HIGH: $($result.AUDIT_OPEN_HIGH)"
    if ($blockers.Count -gt 0) {
        Write-Output 'BLOCKERS:'
        foreach ($blocker in $blockers) {
            Write-Output "  - $blocker"
        }
    }
}

if ($status -eq 'BLOCK') {
    exit 1
}
