param(
    [string]$ControlCenter = "D:\HOMIO\REOS_CONTROL_CENTER",
    [string]$EngineSource = "$PSScriptRoot\.."
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ControlCenter)) {
    throw "Control Center not found: $ControlCenter"
}

$destination = Join-Path $ControlCenter "REOS_AUTONOMOUS_ENGINE"

if (Test-Path $destination) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupRoot = Join-Path $ControlCenter "snapshots"
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

    $backup = Join-Path $backupRoot "autonomous_engine_before_bridge_$timestamp"
    Copy-Item $destination $backup -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item (Join-Path $EngineSource "*") $destination -Recurse -Force

Write-Host "SAFE MERGE COMPLETE"
Write-Host "Destination: $destination"
Write-Host "Existing REOS_CONTROL_CENTER files were not deleted."
Write-Host "The bridge remains read-only."
