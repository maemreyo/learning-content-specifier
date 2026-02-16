#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Stage,
    [string]$Intent,
    [string]$Program,
    [string]$Unit,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output 'Usage: ./load-stage-context.ps1 -Stage <stage> [-Intent <text>] [-Program <id>] [-Unit <id>] [-Json]'
    exit 0
}

. "$PSScriptRoot/common.ps1"
$repoRoot = Get-RepoRoot
$loaderTool = Resolve-PythonTool -ToolName 'load_stage_context.py'
$pythonBin = if (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { 'python' }

$argsList = @(
    $loaderTool,
    '--repo-root', $repoRoot,
    '--stage', $Stage
)

if ($Intent) {
    $argsList += @('--intent', $Intent)
}
if ($Program) {
    $argsList += @('--program', $Program)
}
if ($Unit) {
    $argsList += @('--unit', $Unit)
}
if ($Json) {
    $argsList += '--json'
}

& $pythonBin @argsList
exit $LASTEXITCODE
