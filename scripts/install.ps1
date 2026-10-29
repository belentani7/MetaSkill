$ErrorActionPreference = 'Stop'

$installRoot = $env:METASKILL_INSTALL_ROOT
if ([string]::IsNullOrWhiteSpace($installRoot)) {
    $installRoot = [Environment]::GetFolderPath('UserProfile')
}
$sourceDir = Split-Path -Parent $PSScriptRoot
$targets = @('.qwen', '.claude') | ForEach-Object {
    Join-Path $installRoot "$_/skills/metaskill"
}

function Assert-NoLinkedPath([string]$path) {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item -and (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "Unsafe linked install path: $path"
    }
}

# Preflight both destinations before creating either one.
foreach ($target in $targets) {
    $skillsDir = Split-Path -Parent $target
    $agentDir = Split-Path -Parent $skillsDir
    Assert-NoLinkedPath $installRoot
    Assert-NoLinkedPath $agentDir
    Assert-NoLinkedPath $skillsDir
    if ((Test-Path -LiteralPath $target) -or
        $null -ne (Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue)) {
        throw "Already installed: $target"
    }
}

foreach ($target in $targets) {
    $skillsDir = Split-Path -Parent $target
    $agentDir = Split-Path -Parent $skillsDir
    Assert-NoLinkedPath $installRoot
    Assert-NoLinkedPath $agentDir
    Assert-NoLinkedPath $skillsDir
    New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
    Assert-NoLinkedPath $skillsDir
    New-Item -ItemType Directory -Path $target | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceDir 'SKILL.md'), (Join-Path $sourceDir 'index.json') -Destination $target
    Write-Output "Installed MetaSkill: $target"
}
