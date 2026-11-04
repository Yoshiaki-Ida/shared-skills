#Requires -Version 5.1
param(
    [switch]$Apply,
    [switch]$Update,
    [string]$UserHome = $env:USERPROFILE
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$UserHome = [System.IO.Path]::GetFullPath($UserHome)
$root = Split-Path $PSScriptRoot -Parent
$entries = @()

function Get-ContentHash([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try { return [System.BitConverter]::ToString($sha256.ComputeHash($stream)) }
    finally { $sha256.Dispose(); $stream.Dispose() }
}

function Test-SameContent([string]$Source, [string]$Target) {
    if ((Get-ContentHash $Source) -eq (Get-ContentHash $Target)) { return $true }
    if ([System.IO.Path]::GetExtension($Source) -notin @('.md', '.json', '.yaml', '.yml', '.py', '.txt', '.html')) {
        return $false
    }
    $encoding = [System.Text.UTF8Encoding]::new($false, $true)
    try {
        $sourceText = $encoding.GetString([System.IO.File]::ReadAllBytes($Source))
        $targetText = $encoding.GetString([System.IO.File]::ReadAllBytes($Target))
    }
    catch [System.Text.DecoderFallbackException] { return $false }
    return [string]::Equals($sourceText.Replace("`r`n", "`n"),
        $targetText.Replace("`r`n", "`n"), [System.StringComparison]::Ordinal)
}

$skillPaths = @(
    'skills/meeting-and-records/create-auditable-meeting-minutes',
    'skills/meeting-and-records/meeting-transcript-to-open-items',
    'skills/skill-management/skill-creator',
    'skills/software-development/safe-refactoring',
    'skills/software-development/reverse-engineer-specification',
    'skills/software-development/generate-tests-from-spec'
)
foreach ($relativePath in $skillPaths) {
    $source = Join-Path $root $relativePath
    $name = Split-Path $source -Leaf
    $definition = Join-Path $source 'SKILL.md'
    if (-not (Test-Path -LiteralPath $definition)) { throw "Missing Skill: $name" }
    if ((Get-Content -LiteralPath $definition -Raw -Encoding UTF8) -notmatch "(?m)^name: $name\s*$") {
        throw "Invalid Skill name: $name"
    }
    $destination = Join-Path $UserHome ".agents/skills/$name"
    foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
        if ($file.FullName -match '[\\/]__pycache__[\\/]' -or $file.Extension -eq '.pyc') { continue }
        $relative = $file.FullName.Substring($source.Length + 1)
        $entries += [pscustomobject]@{ Source = $file.FullName; Target = Join-Path $destination $relative }
    }
}
$entries += [pscustomobject]@{
    Source = Join-Path $root 'agents/redmine/redmine-meeting-orchestrator.agent.md'
    Target = Join-Path $UserHome '.copilot/agents/redmine-meeting-orchestrator.agent.md'
}

$plan = foreach ($entry in $entries) {
    if (-not (Test-Path -LiteralPath $entry.Source -PathType Leaf)) { throw "Missing source: $($entry.Source)" }
    $state = 'NEW'
    if (Test-Path -LiteralPath $entry.Target) {
        if (-not (Test-Path -LiteralPath $entry.Target -PathType Leaf)) { throw "Not a file: $($entry.Target)" }
        if (Test-SameContent $entry.Source $entry.Target) { $state = 'OK' } else { $state = 'CONFLICT' }
    }
    [pscustomobject]@{ State = $state; Source = $entry.Source; Target = $entry.Target }
}
$plan | Select-Object State, Target | Format-Table -AutoSize | Out-String -Width 240 | Write-Output
if (-not $Apply) {
    Write-Output 'PREVIEW: no files changed. Use -Apply to install; -Apply -Update to approve replacements.'
    exit 0
}
$conflicts = @($plan | Where-Object { $_.State -eq 'CONFLICT' })
if ($conflicts.Count -gt 0 -and -not $Update) {
    throw 'CONFLICT: no files changed. Do not delete existing files. See README conflict instructions before using -Apply -Update.'
}
if ($conflicts.Count -gt 0) {
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [guid]::NewGuid().ToString('N')
    $backupRoot = Join-Path $UserHome ".agents/backups/shared-skills/$stamp"
    $manifest = @()
    foreach ($entry in $conflicts) {
        $relative = $entry.Target.Substring($UserHome.Length).TrimStart('\', '/')
        $backupTarget = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path $backupTarget -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $entry.Target -Destination $backupTarget
        if ((Get-ContentHash $entry.Target) -ne (Get-ContentHash $backupTarget)) {
            throw "Backup verification failed: $($entry.Target). No installation files changed."
        }
        $manifest += [pscustomobject]@{ Target = $entry.Target; Backup = $backupTarget }
    }
    $manifestPath = Join-Path $backupRoot 'manifest.json'
    ConvertTo-Json -InputObject $manifest -Depth 3 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Output "BACKUP: $backupRoot"
}

foreach ($entry in $plan) {
    if ($entry.State -eq 'OK') { continue }
    $parent = Split-Path $entry.Target -Parent
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $entry.Source -Destination $entry.Target -Force
    if ((Get-ContentHash $entry.Source) -ne (Get-ContentHash $entry.Target)) {
        throw "Verification failed: $($entry.Target)"
    }
}
Write-Output "INSTALL_PASS: $($skillPaths.Count) Skills and one Agent installed. No files were deleted."
