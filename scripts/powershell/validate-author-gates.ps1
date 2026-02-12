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

$pythonBin = if (Get-Command python -ErrorAction SilentlyContinue) {
    'python'
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    'python3'
}
else {
    throw 'python or python3 is required for validate-author-gates.ps1'
}

$auditFile = $paths.AUDIT_REPORT_FILE
$auditJsonFile = $paths.AUDIT_REPORT_JSON_FILE
$rubricUnchecked = 0
$rubricBlockers = 0
$rubricParseErrors = 0
$auditDecision = 'MISSING'
$auditOpenCritical = 0
$auditOpenHigh = 0
$contractStatus = 'BLOCK'
$contractSummary = 'validation-not-run'
$blockers = @()

try {
    $contractRaw = & (Join-Path $PSScriptRoot 'validate-artifact-contracts.ps1') -Json -UnitDir $paths.UNIT_DIR
    $contractObj = $contractRaw | ConvertFrom-Json
    $contractStatus = [string]$contractObj.STATUS
    $missingCount = @($contractObj.MISSING_FILES).Count + @($contractObj.MISSING_SCHEMAS).Count
    $errorCount = @($contractObj.ERRORS).Count
    $contractSummary = "missing=$missingCount,errors=$errorCount"
    if ($contractStatus -ne 'PASS') {
        $blockers += "Artifact contract validation is BLOCK ($contractSummary)"
    }
}
catch {
    $blockers += 'Artifact contract validation failed to execute'
}

if (-not (Test-Path $paths.RUBRICS_DIR -PathType Container)) {
    $blockers += "Missing rubrics directory: $($paths.RUBRICS_DIR)"
}
else {
    try {
        $rubricRaw = & $pythonBin (Join-Path $paths.REPO_ROOT 'scripts/validate_rubric_gates.py') --rubrics-dir $paths.RUBRICS_DIR --json
        $rubricObj = $rubricRaw | ConvertFrom-Json
        $rubricUnchecked = [int]$rubricObj.UNCHECKED_COUNT
        $rubricBlockers = [int]$rubricObj.NON_PASS_COUNT
        $rubricParseErrors = [int]$rubricObj.PARSE_ERROR_COUNT

        if ([string]$rubricObj.STATUS -ne 'PASS') {
            $details = @($rubricObj.BLOCKERS + $rubricObj.PARSE_ERRORS) -join '; '
            if ([string]::IsNullOrWhiteSpace($details)) {
                $details = 'unknown-parse-error'
            }
            $blockers += "Rubric format validation is BLOCK ($details)"
        }
    }
    catch {
        $blockers += 'Rubric parser failed to execute'
    }
}

if ($rubricUnchecked -gt 0) {
    $blockers += "Rubric has $rubricUnchecked unchecked item(s)"
}

if ($rubricBlockers -gt 0) {
    $blockers += "Rubric has $rubricBlockers non-pass status item(s)"
}

if (Test-Path $auditJsonFile -PathType Leaf) {
    try {
        $auditObj = Get-Content -Path $auditJsonFile -Encoding utf8 | ConvertFrom-Json
        $decision = ([string]$auditObj.gate_decision).ToUpper()
        if ($decision -notin @('PASS', 'BLOCK')) {
            throw "missing-or-invalid-gate_decision"
        }

        $critical = [int]$auditObj.open_critical
        $high = [int]$auditObj.open_high
        if ($critical -lt 0) {
            throw "missing-or-invalid-open_critical"
        }
        if ($high -lt 0) {
            throw "missing-or-invalid-open_high"
        }

        $auditDecision = $decision
        $auditOpenCritical = $critical
        $auditOpenHigh = $high
    }
    catch {
        $blockers += "Audit JSON invalid: $($_.Exception.Message)"
    }
}
elseif (Test-Path $auditFile -PathType Leaf) {
    $auditLines = Get-Content -Path $auditFile -Encoding utf8

    $decisionLine = $auditLines | Where-Object { $_ -match '^Gate Decision:\s*(PASS|BLOCK)$' } | Select-Object -First 1
    if ($decisionLine) {
        $auditDecision = ($decisionLine -replace '^Gate Decision:\s*', '').Trim().ToUpper()
    }
    else {
        $blockers += "Audit report missing 'Gate Decision: PASS|BLOCK'"
    }

    $criticalLine = $auditLines | Where-Object { $_ -match '^Open Critical:\s*\d+' } | Select-Object -First 1
    if ($criticalLine) {
        $auditOpenCritical = [int](($criticalLine -replace '^Open Critical:\s*', '').Trim())
    }
    else {
        $blockers += "Audit report missing 'Open Critical: <number>'"
    }

    $highLine = $auditLines | Where-Object { $_ -match '^Open High:\s*\d+' } | Select-Object -First 1
    if ($highLine) {
        $auditOpenHigh = [int](($highLine -replace '^Open High:\s*', '').Trim())
    }
    else {
        $blockers += "Audit report missing 'Open High: <number>'"
    }
}
else {
    $blockers += "Missing audit report: $auditFile"
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
    CONTRACT_STATUS = $contractStatus
    CONTRACT_SUMMARY = $contractSummary
    RUBRIC_UNCHECKED = $rubricUnchecked
    RUBRIC_BLOCKERS = $rubricBlockers
    RUBRIC_PARSE_ERRORS = $rubricParseErrors
    AUDIT_DECISION = $auditDecision
    AUDIT_OPEN_CRITICAL = $auditOpenCritical
    AUDIT_OPEN_HIGH = $auditOpenHigh
    BLOCKERS = ($blockers -join '; ')
}

if ($Json) {
    $result | ConvertTo-Json -Compress
}
else {
    Write-Output "STATUS: $($result.STATUS)"
    Write-Output "UNIT_DIR: $($result.UNIT_DIR)"
    Write-Output "CONTRACT_STATUS: $($result.CONTRACT_STATUS)"
    Write-Output "CONTRACT_SUMMARY: $($result.CONTRACT_SUMMARY)"
    Write-Output "RUBRIC_UNCHECKED: $($result.RUBRIC_UNCHECKED)"
    Write-Output "RUBRIC_BLOCKERS: $($result.RUBRIC_BLOCKERS)"
    Write-Output "RUBRIC_PARSE_ERRORS: $($result.RUBRIC_PARSE_ERRORS)"
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
