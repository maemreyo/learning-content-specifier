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
$rubricValidatorTool = Resolve-PythonTool -ToolName 'validate_rubric_gates.py'

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

$auditJsonFile = $paths.AUDIT_REPORT_JSON_FILE
$rubricUnchecked = 0
$rubricBlockers = 0
$rubricParseErrors = 0
$auditDecision = 'MISSING'
$auditOpenCritical = 0
$auditOpenHigh = 0
$contractStatus = 'BLOCK'
$contractSummary = 'validation-not-run'
$contractResponseVersion = ''
$contractPipeline = ''
$contractBlockingSteps = ''
$blockers = @()

try {
    $contractRaw = & (Join-Path $PSScriptRoot 'validate-artifact-contracts.ps1') -Json -UnitDir $paths.UNIT_DIR
    $contractObj = $contractRaw | ConvertFrom-Json
    $contractStatus = [string]$contractObj.STATUS
    $missingCount = @($contractObj.MISSING_FILES).Count + @($contractObj.MISSING_SCHEMAS).Count
    $errorCount = @($contractObj.ERRORS).Count
    $openCritical = 0
    $openHigh = 0
    if ($contractObj.PHASE_SUMMARY) {
        $openCritical = [int]$contractObj.PHASE_SUMMARY.open_critical
        $openHigh = [int]$contractObj.PHASE_SUMMARY.open_high
    }
    $contractSummary = "missing=$missingCount,errors=$errorCount,blockers=$($openCritical + $openHigh)"
    $contractResponseVersion = [string]$contractObj.RESPONSE_VERSION
    if ($contractObj.PIPELINE -and $contractObj.PIPELINE.name) {
        $contractPipeline = [string]$contractObj.PIPELINE.name
    }
    if ($contractObj.AGENT_REPORT -and $contractObj.AGENT_REPORT.blocking_steps) {
        $contractBlockingSteps = (@($contractObj.AGENT_REPORT.blocking_steps) | ForEach-Object { [string]$_ }) -join ','
    }
    if ($contractStatus -ne 'PASS') {
        $detail = $contractSummary
        if ($contractBlockingSteps) {
            $detail = "$detail,steps=$contractBlockingSteps"
        }
        $blockers += "Artifact contract validation is BLOCK ($detail)"
    }
}
catch {
    $blockers += 'Artifact contract validation failed to execute'
}

try {
    $rubricRaw = & $pythonBin $rubricValidatorTool --rubric-gates-file $paths.RUBRIC_GATES_FILE --rubrics-dir $paths.RUBRICS_DIR --json
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
else {
    $blockers += "Missing audit report JSON: $auditJsonFile"
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
    CONTRACT_RESPONSE_VERSION = $contractResponseVersion
    CONTRACT_PIPELINE = $contractPipeline
    CONTRACT_BLOCKING_STEPS = $contractBlockingSteps
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
    Write-Output "CONTRACT_RESPONSE_VERSION: $($result.CONTRACT_RESPONSE_VERSION)"
    Write-Output "CONTRACT_PIPELINE: $($result.CONTRACT_PIPELINE)"
    Write-Output "CONTRACT_BLOCKING_STEPS: $($result.CONTRACT_BLOCKING_STEPS)"
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
