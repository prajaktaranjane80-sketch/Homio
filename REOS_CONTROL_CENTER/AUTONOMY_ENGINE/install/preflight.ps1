
param(
    [string]$ControlCenter = "D:\HOMIO\REOS_CONTROL_CENTER"
)

$ErrorActionPreference = "Stop"

$engine = Join-Path $ControlCenter "REOS_AUTONOMOUS_ENGINE"

if (-not (Test-Path $engine)) {
    throw "Autonomous engine not installed: $engine"
}

Push-Location $engine
try {
    python cli.py context
    python cli.py doctor
    python cli.py next
}
finally {
    Pop-Location
}
