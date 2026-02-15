#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

$repoRoot = Get-RepoRoot
$toolPath = Resolve-PythonTool -ToolName 'manage_program_context.py'

$pythonBin = 'python3'
if (-not (Get-Command $pythonBin -ErrorAction SilentlyContinue)) {
    $pythonBin = 'python'
}
if (-not (Get-Command $pythonBin -ErrorAction SilentlyContinue)) {
    throw 'python3/python is required to manage program context'
}

& $pythonBin $toolPath --repo-root $repoRoot @Args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
