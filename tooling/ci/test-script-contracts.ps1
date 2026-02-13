#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$repoRoot = $null
if ($PSScriptRoot) {
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
}
if (-not $repoRoot -or -not (Test-Path $repoRoot)) {
    $repoRoot = $env:GITHUB_WORKSPACE
}
if (-not $repoRoot -or -not (Test-Path $repoRoot)) {
    $gitRoot = (& git rev-parse --show-toplevel 2>$null)
    if ($gitRoot) {
        $repoRoot = (@($gitRoot) | Where-Object { $_ -and "$_".Trim() } | Select-Object -First 1)
    }
}
if (-not $repoRoot -or -not (Test-Path $repoRoot)) {
    $repoRoot = (Get-Location).Path
}
$repoRoot = (@($repoRoot) | Where-Object { $_ -and "$_".Trim() } | Select-Object -First 1)
$repoRoot = "$repoRoot".Trim()
if (-not $repoRoot -or -not (Test-Path $repoRoot)) {
    throw 'Could not determine repository root.'
}

# 1) create-new-unit contract in temp non-git workspace
$tempRoot = Join-Path $env:RUNNER_TEMP ("lcs-contract-ps-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot '.lcs/templates') -Force | Out-Null
Copy-Item (Join-Path $repoRoot 'factory/templates/brief-template.md') (Join-Path $tempRoot '.lcs/templates/brief-template.md') -Force
Copy-Item -Recurse (Join-Path $repoRoot 'contracts') (Join-Path $tempRoot 'contracts') -Force
$createNewUnitScript = Join-Path $repoRoot 'factory/scripts/powershell/create-new-unit.ps1'
$setupDesignScript = Join-Path $repoRoot 'factory/scripts/powershell/setup-design.ps1'
$validateContractsScript = Join-Path $repoRoot 'factory/scripts/powershell/validate-artifact-contracts.ps1'
$checkWorkflowScript = Join-Path $repoRoot 'factory/scripts/powershell/check-workflow-prereqs.ps1'
$validateGatesScript = Join-Path $repoRoot 'factory/scripts/powershell/validate-author-gates.ps1'

Push-Location $tempRoot
try {
    $createJson = & $createNewUnitScript -Json -UnitDescription "temporary unit for contract test"
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
    $contractVersion = (Get-Content -Path (Join-Path $tempRoot 'contracts/index.json') -Encoding utf8 | ConvertFrom-Json).contract_version
    $briefPayload = Get-Content -Path $briefJson -Encoding utf8 | ConvertFrom-Json
    if ($briefPayload.contract_version -ne $contractVersion) {
        throw "create-new-unit brief.json contract_version mismatch. actual=$($briefPayload.contract_version) expected=$contractVersion"
    }
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $tempRoot -ErrorAction SilentlyContinue
}

# 1b) create-new-unit should not auto-checkout branch in git repo by default
$tempGit = Join-Path $env:RUNNER_TEMP ("lcs-contract-ps-git-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempGit -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempGit '.lcs/templates') -Force | Out-Null
Copy-Item (Join-Path $repoRoot 'factory/templates/brief-template.md') (Join-Path $tempGit '.lcs/templates/brief-template.md') -Force
Copy-Item -Recurse (Join-Path $repoRoot 'contracts') (Join-Path $tempGit 'contracts') -Force
Push-Location $tempGit
try {
    git init | Out-Null
    git config user.email ci@example.com
    git config user.name CI
    '' | Set-Content '.gitkeep'
    git add .gitkeep
    git commit -m init | Out-Null
    $startBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    & $createNewUnitScript -Json -Number 997 "verify no auto branch switch" | Out-Null
    $endBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($startBranch -ne $endBranch) {
        throw "create-new-unit.ps1 unexpectedly switched branch: $startBranch -> $endBranch"
    }
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $tempGit -ErrorAction SilentlyContinue
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
    $setupJson = & $setupDesignScript -Json
    $setupObj = $setupJson | ConvertFrom-Json
    foreach ($k in @('BRIEF_FILE','DESIGN_FILE','UNIT_DIR','BRANCH','HAS_GIT')) {
        if (-not $setupObj.PSObject.Properties.Name.Contains($k)) {
            throw "setup-design missing key: $k"
        }
    }
    if ($setupObj.HAS_GIT.GetType().Name -ne 'Boolean') {
        throw 'setup-design HAS_GIT must be bool'
    }
    $unitDir = [string]$setupObj.UNIT_DIR
    $contractVersion = (Get-Content -Path (Join-Path $repoRoot 'contracts/index.json') -Encoding utf8 | ConvertFrom-Json).contract_version
    foreach ($target in @(
        (Join-Path $unitDir 'brief.json'),
        (Join-Path $unitDir 'design.json'),
        (Join-Path $unitDir 'content-model.json'),
        (Join-Path $unitDir 'design-decisions.json'),
        (Join-Path $unitDir 'sequence.json'),
        (Join-Path $unitDir 'audit-report.json'),
        (Join-Path $unitDir 'outputs/manifest.json')
    )) {
        $payload = Get-Content -Path $target -Encoding utf8 | ConvertFrom-Json
        if ($payload.contract_version -ne $contractVersion) {
            throw "contract_version mismatch in ${target}. actual=$($payload.contract_version) expected=$contractVersion"
        }
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

    $contractJson = & $validateContractsScript -Json -UnitDir $unitDir
    $contractObj = $contractJson | ConvertFrom-Json
    if (-not $contractObj.PSObject.Properties.Name.Contains('STATUS')) {
        throw 'validate-artifact-contracts missing STATUS'
    }
    if (($contractObj.STATUS -ne 'PASS') -and ($contractObj.STATUS -ne 'BLOCK')) {
        throw "validate-artifact-contracts returned unexpected STATUS: $($contractObj.STATUS)"
    }

    $pathsJson = & $checkWorkflowScript -Json -PathsOnly -SkipBranchCheck
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

    $gateJson = & $validateGatesScript -Json
    $gateObj = $gateJson | ConvertFrom-Json
    if (-not $gateObj.PSObject.Properties.Name.Contains('STATUS')) {
        throw 'validate-author-gates missing STATUS'
    }
    if (($gateObj.STATUS -ne 'PASS') -and ($gateObj.STATUS -ne 'BLOCK')) {
        throw "validate-author-gates returned unexpected STATUS: $($gateObj.STATUS)"
    }
}
finally {
    Remove-Item Env:LCS_UNIT -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $repoRoot 'specs/999-ci-contract-ps') -ErrorAction SilentlyContinue
    if ((Test-Path (Join-Path $repoRoot 'specs')) -and -not (Get-ChildItem (Join-Path $repoRoot 'specs') -Force | Measure-Object).Count) {
        Remove-Item (Join-Path $repoRoot 'specs') -Force -ErrorAction SilentlyContinue
    }
}

$global:LASTEXITCODE = 0
Write-Output 'PowerShell script contract checks passed'
