#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path

# 1) create-new-unit contract in temp non-git workspace
$tempRoot = Join-Path $env:RUNNER_TEMP ("lcs-contract-ps-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot '.lcs/templates') -Force | Out-Null
Copy-Item (Join-Path $repoRoot 'templates/brief-template.md') (Join-Path $tempRoot '.lcs/templates/brief-template.md') -Force

Push-Location $tempRoot
try {
    $createJson = & (Join-Path $repoRoot 'scripts/powershell/create-new-unit.ps1') -Json "temporary unit for contract test"
    $createObj = $createJson | ConvertFrom-Json
    foreach ($k in @('UNIT_NAME','BRIEF_FILE','UNIT_NUM')) {
        if (-not $createObj.PSObject.Properties.Name.Contains($k)) {
            throw "create-new-unit missing key: $k"
        }
    }
    $briefJson = [System.IO.Path]::ChangeExtension([string]$createObj.BRIEF_FILE, 'json')
    if (-not (Test-Path $briefJson)) {
        throw "create-new-unit missing brief json sidecar: $briefJson"
    }
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $tempRoot -ErrorAction SilentlyContinue
}

# 2) setup/check/validate contracts in repo workspace
$unit = '999-ci-contract-ps'
$unitDir = Join-Path $repoRoot "specs/$unit"
New-Item -ItemType Directory -Path (Join-Path $unitDir 'rubrics') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $unitDir 'outputs') -Force | Out-Null
'' | Set-Content (Join-Path $unitDir 'brief.md')
'' | Set-Content (Join-Path $unitDir 'design.md')
'' | Set-Content (Join-Path $unitDir 'sequence.md')
@"
# Audit Report: $unit
Gate Decision: PASS
Open Critical: 0
Open High: 0
## Findings
1. LOW | artifact: design.md | issue: none | remediation: n/a
"@ | Set-Content (Join-Path $unitDir 'audit-report.md')
'- [x] Gate ID: RB001 | Group: alignment | Status: PASS | Severity: LOW | Evidence: design.md' | Set-Content (Join-Path $unitDir 'rubrics/default.md')

$env:LCS_UNIT = $unit

try {
    $setupJson = & (Join-Path $repoRoot 'scripts/powershell/setup-design.ps1') -Json
    $setupObj = $setupJson | ConvertFrom-Json
    foreach ($k in @('BRIEF_FILE','DESIGN_FILE','UNIT_DIR','BRANCH','HAS_GIT')) {
        if (-not $setupObj.PSObject.Properties.Name.Contains($k)) {
            throw "setup-design missing key: $k"
        }
    }
    if ($setupObj.HAS_GIT.GetType().Name -ne 'Boolean') {
        throw 'setup-design HAS_GIT must be bool'
    }

    $auditJsonPath = Join-Path $unitDir 'audit-report.json'
    $auditObj = Get-Content -Path $auditJsonPath -Encoding utf8 | ConvertFrom-Json
    $auditObj.gate_decision = 'PASS'
    $auditObj.open_critical = 0
    $auditObj.open_high = 0
    $auditObj.findings = @()
    $auditObj | ConvertTo-Json -Depth 10 | Set-Content -Path $auditJsonPath -Encoding utf8
    $manifestPath = Join-Path $unitDir 'outputs/manifest.json'
    $manifestObj = Get-Content -Path $manifestPath -Encoding utf8 | ConvertFrom-Json
    $manifestObj.gate_status = [PSCustomObject]@{decision='PASS'; open_critical=0; open_high=0}
    $manifestObj | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath -Encoding utf8

    $contractJson = & (Join-Path $repoRoot 'scripts/powershell/validate-artifact-contracts.ps1') -Json -UnitDir $unitDir
    $contractObj = $contractJson | ConvertFrom-Json
    if ($contractObj.STATUS -ne 'PASS') {
        throw "validate-artifact-contracts expected PASS but got $($contractObj.STATUS)"
    }

    $pathsJson = & (Join-Path $repoRoot 'scripts/powershell/check-workflow-prereqs.ps1') -Json -PathsOnly -SkipBranchCheck
    $pathsObj = $pathsJson | ConvertFrom-Json
    foreach ($k in @(
        'UNIT_REPO_ROOT','UNIT_BRANCH','UNIT_HAS_GIT','UNIT_DIR',
        'UNIT_BRIEF_FILE','UNIT_BRIEF_JSON_FILE',
        'UNIT_DESIGN_FILE','UNIT_DESIGN_JSON_FILE',
        'UNIT_SEQUENCE_FILE','UNIT_SEQUENCE_JSON_FILE',
        'UNIT_AUDIT_REPORT_FILE','UNIT_AUDIT_REPORT_JSON_FILE',
        'UNIT_MANIFEST_FILE','UNIT_CHARTER_FILE'
    )) {
        if (-not $pathsObj.PSObject.Properties.Name.Contains($k)) {
            throw "check-workflow-prereqs missing key: $k"
        }
    }

    $gateJson = & (Join-Path $repoRoot 'scripts/powershell/validate-author-gates.ps1') -Json
    $gateObj = $gateJson | ConvertFrom-Json
    if ($gateObj.STATUS -ne 'PASS') {
        throw 'validate-author-gates expected PASS'
    }
}
finally {
    Remove-Item Env:LCS_UNIT -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $repoRoot 'specs/999-ci-contract-ps') -ErrorAction SilentlyContinue
    if (Test-Path (Join-Path $repoRoot 'specs') -and -not (Get-ChildItem (Join-Path $repoRoot 'specs') -Force | Measure-Object).Count) {
        Remove-Item (Join-Path $repoRoot 'specs') -Force -ErrorAction SilentlyContinue
    }
}

Write-Output 'PowerShell script contract checks passed'
