#Requires -Version 5.1
param(
    [switch]$Apply,
    [switch]$Update,
    [string]$UserHome = $env:USERPROFILE
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$entries = @()

function Get-ContentHash([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try { return [System.BitConverter]::ToString($sha256.ComputeHash($stream)) }
    finally { $sha256.Dispose(); $stream.Dispose() }
}

foreach ($name in @('create-auditable-meeting-minutes', 'meeting-transcript-to-open-items')) {
    $source = Join-Path $root "skills/meeting-and-records/$name"
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
        $sourceHash = Get-ContentHash $entry.Source
        $targetHash = Get-ContentHash $entry.Target
        if ($sourceHash -eq $targetHash) { $state = 'OK' } else { $state = 'CONFLICT' }
    }
    [pscustomobject]@{ State = $state; Source = $entry.Source; Target = $entry.Target }
}
$plan | Select-Object State, Target | Format-Table -AutoSize | Out-String -Width 240 | Write-Output
if (-not $Apply) {
    Write-Output 'PREVIEW: no files changed. Use -Apply to install; -Apply -Update to approve replacements.'
    exit 0
}
if (@($plan | Where-Object { $_.State -eq 'CONFLICT' }).Count -gt 0 -and -not $Update) {
    throw 'CONFLICT: no files changed. Review differences before using -Apply -Update.'
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
Write-Output 'INSTALL_PASS: two Skills and one Agent installed. No files were deleted.'