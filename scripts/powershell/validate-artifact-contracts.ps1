#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$UnitDir,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./validate-artifact-contracts.ps1 [-Json] [-UnitDir <path>]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$paths = Get-UnitPathsEnv

$unitTarget = if ($UnitDir) { $UnitDir } else { $paths.UNIT_DIR }
$arguments = @(
    (Join-Path $paths.REPO_ROOT 'scripts/validate_artifact_contracts.py'),
    '--repo-root', $paths.REPO_ROOT,
    '--unit-dir', $unitTarget
)

if ($Json) {
    $arguments += '--json'
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python @arguments
}
else {
    $pythonBin = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
    & $pythonBin @arguments
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
