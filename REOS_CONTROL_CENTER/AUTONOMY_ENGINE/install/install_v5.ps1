param(
    [string]$ControlCenter = "D:\HOMIO\REOS_CONTROL_CENTER",
    [string]$EngineSource = "$PSScriptRoot\.."
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $ControlCenter)) { throw "REOS Control Center not found: $ControlCenter" }
$destination = Join-Path $ControlCenter "REOS_AUTONOMOUS_ENGINE"
if (Test-Path $destination) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $snapshotRoot = Join-Path $ControlCenter "snapshots"
    New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null
    Copy-Item $destination (Join-Path $snapshotRoot "autonomous_engine_before_v5_$stamp") -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item (Join-Path $EngineSource "*") $destination -Recurse -Force
Write-Host "AUTONOMOUS ENGINE MERGED: $destination"
Write-Host "Existing REOS Control Center files were NOT deleted."
