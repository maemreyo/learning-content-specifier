#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsFromCaller
)

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $PSScriptRoot 'common.ps1')
$buildTool = Resolve-PythonTool -ToolName 'build_contract_package.py'
$arguments = @(
    $buildTool,
    '--repo-root', $repoRoot
)
if ($ArgsFromCaller) {
    $arguments += $ArgsFromCaller
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
