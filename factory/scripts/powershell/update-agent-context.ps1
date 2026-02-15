#!/usr/bin/env pwsh
param(
    [Parameter(Position=0)]
    [ValidateSet('claude','gemini','copilot','cursor-agent','qwen','opencode','codex','windsurf','kilocode','auggie','roo','codebuddy','amp','shai','q','bob','qoder')]
    [string]$AgentType
)
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"
$paths = Get-UnitPathsEnv

$CLAUDE_FILE = Join-Path $paths.REPO_ROOT 'CLAUDE.md'
$GEMINI_FILE = Join-Path $paths.REPO_ROOT 'GEMINI.md'
$COPILOT_FILE = Join-Path $paths.REPO_ROOT '.github/agents/copilot-instructions.md'
$CURSOR_FILE = Join-Path $paths.REPO_ROOT '.cursor/rules/lcs-rules.mdc'
$QWEN_FILE = Join-Path $paths.REPO_ROOT 'QWEN.md'
$OPENCODE_FILE = Join-Path $paths.REPO_ROOT 'AGENTS.md'
$CODEX_FILE = Join-Path $paths.REPO_ROOT 'AGENTS.md'
$WINDSURF_FILE = Join-Path $paths.REPO_ROOT '.windsurf/rules/lcs-rules.md'
$KILOCODE_FILE = Join-Path $paths.REPO_ROOT '.kilocode/rules/lcs-rules.md'
$AUGGIE_FILE = Join-Path $paths.REPO_ROOT '.augment/rules/lcs-rules.md'
$ROO_FILE = Join-Path $paths.REPO_ROOT '.roo/rules/lcs-rules.md'
$CODEBUDDY_FILE = Join-Path $paths.REPO_ROOT 'CODEBUDDY.md'
$QODER_FILE = Join-Path $paths.REPO_ROOT 'QODER.md'
$AMP_FILE = Join-Path $paths.REPO_ROOT 'AGENTS.md'
$SHAI_FILE = Join-Path $paths.REPO_ROOT 'SHAI.md'
$Q_FILE = Join-Path $paths.REPO_ROOT 'AGENTS.md'
$BOB_FILE = Join-Path $paths.REPO_ROOT 'AGENTS.md'

$template = Join-Path $paths.REPO_ROOT '.lcs/templates/agent-file-template.md'
if (-not (Test-Path $template)) { Write-Error "Missing template: $template"; exit 1 }

function Extract-LearningField([string]$Field) {
    $pattern = '^\s*-?\s*(\*\*' + [Regex]::Escape($Field) + '\*\*|' + [Regex]::Escape($Field) + ')\s*:\s*(.+)$'
    foreach ($sourceFile in @($paths.DESIGN_FILE, $paths.BRIEF_FILE)) {
        if (-not (Test-Path $sourceFile)) { continue }
        foreach ($line in Get-Content -Path $sourceFile -Encoding utf8) {
            if ($line -match $pattern) { return $matches[2].Trim() }
        }
    }
    return ''
}

$audience = Extract-LearningField 'Audience Profile'
$level = Extract-LearningField 'Entry Level'
$duration = Extract-LearningField 'Duration Budget'
$modality = Extract-LearningField 'Modality Mix'
$mode = Extract-LearningField 'Delivery Mode'

$structurePath = "programs/$($paths.PROGRAM_ID ? $paths.PROGRAM_ID : '<program-id>')/units/$($paths.CURRENT_UNIT ? $paths.CURRENT_UNIT : '<unit-id>')"
$techLine = "- Audience: $($audience ? $audience : 'unknown') | Level: $($level ? $level : 'unknown') | Duration: $($duration ? $duration : 'unknown') | Modality: $($modality ? $modality : 'unknown') | Mode: $($mode ? $mode : 'unknown') ($structurePath)"
$recentLine = "- $structurePath: Updated unit learning profile ($($modality ? $modality : 'unknown'))"

function New-AgentFile([string]$TargetFile) {
    $content = Get-Content -Path $template -Raw -Encoding utf8
    $content = $content.Replace('[PROJECT NAME]', (Split-Path $paths.REPO_ROOT -Leaf))
    $content = $content.Replace('[DATE]', (Get-Date -Format 'yyyy-MM-dd'))
    $content = $content.Replace('[EXTRACTED FROM ALL DESIGN.MD FILES]', $techLine)
    $content = $content.Replace('[ACTUAL STRUCTURE FROM PLANS]', $structurePath + '/' + [Environment]::NewLine + '  outputs/')
    $content = $content.Replace('[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', '/lcs.define, /lcs.design, /lcs.sequence, /lcs.rubric, /lcs.audit, /lcs.author')
    $content = $content.Replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]', 'Use concise, learner-centered writing and consistent terminology.')
    $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', $recentLine)
    $parent = Split-Path -Parent $TargetFile
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Set-Content -Path $TargetFile -Value $content -Encoding utf8
}

function Update-AgentFile([string]$TargetFile) {
    if (-not (Test-Path $TargetFile)) {
        New-AgentFile $TargetFile
        Write-Host "✓ Created: $TargetFile"
        return
    }

    $content = Get-Content -Path $TargetFile -Raw -Encoding utf8
    if ($content -notmatch [Regex]::Escape($techLine)) {
        $content = $content -replace '## Active Learning Profiles\s*', "## Active Learning Profiles`n`n$techLine`n"
    }
    if ($content -notmatch [Regex]::Escape($recentLine)) {
        $content = $content -replace '## Recent Unit Changes\s*', "## Recent Unit Changes`n`n$recentLine`n"
    }
    Set-Content -Path $TargetFile -Value $content -Encoding utf8
    Write-Host "✓ Updated: $TargetFile"
}

$map = @{
    'claude' = $CLAUDE_FILE
    'gemini' = $GEMINI_FILE
    'copilot' = $COPILOT_FILE
    'cursor-agent' = $CURSOR_FILE
    'qwen' = $QWEN_FILE
    'opencode' = $OPENCODE_FILE
    'codex' = $CODEX_FILE
    'windsurf' = $WINDSURF_FILE
    'kilocode' = $KILOCODE_FILE
    'auggie' = $AUGGIE_FILE
    'roo' = $ROO_FILE
    'codebuddy' = $CODEBUDDY_FILE
    'qoder' = $QODER_FILE
    'amp' = $AMP_FILE
    'shai' = $SHAI_FILE
    'q' = $Q_FILE
    'bob' = $BOB_FILE
}

if ($AgentType) {
    Update-AgentFile $map[$AgentType]
} else {
    foreach ($pair in $map.GetEnumerator()) {
        if (Test-Path $pair.Value) { Update-AgentFile $pair.Value }
    }
}
