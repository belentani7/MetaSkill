$ErrorActionPreference = 'Stop'

$installRoot = $env:METASKILL_INSTALL_ROOT
if ([string]::IsNullOrWhiteSpace($installRoot)) {
    $installRoot = [Environment]::GetFolderPath('UserProfile')
}
$sourceDir = Split-Path -Parent $PSScriptRoot
$targets = @('.qwen', '.claude') | ForEach-Object {
    Join-Path $installRoot "$_/skills/metaskill"
}

foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) {
        throw "Already installed: $target"
    }
}

foreach ($target in $targets) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    New-Item -ItemType Directory -Path $target | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceDir 'SKILL.md'), (Join-Path $sourceDir 'index.json') -Destination $target
    Write-Output "Installed MetaSkill: $target"
}
