
param(
    [string]$EngineSource = "$PSScriptRoot\..",
    [string]$ControlCenter = "D:\HOMIO\REOS_CONTROL_CENTER"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ControlCenter)) {
    throw "REOS Control Center not found: $ControlCenter"
}

$destination = Join-Path $ControlCenter "REOS_AUTONOMOUS_ENGINE"

if (Test-Path $destination) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backup = Join-Path $ControlCenter "snapshots\autonomous_engine_before_install_$timestamp"
    New-Item -ItemType Directory -Force -Path $backup | Out-Null
    Copy-Item $destination $backup -Recurse -Force
}

# Merge only the new autonomous-engine directory.
# Existing Control Center files are never deleted by this script.
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item (Join-Path $EngineSource "*") $destination -Recurse -Force

Write-Host "REOS AUTONOMOUS ENGINE installed/merged at:"
Write-Host $destination
Write-Host "Existing REOS_CONTROL_CENTER files were not deleted."
