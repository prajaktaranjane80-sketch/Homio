Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ControlRoot = Split-Path -Parent $PSScriptRoot
$Core = Join-Path $ControlRoot "AUTONOMY_ENGINE\core"
$Backup = Join-Path $Core "CORE-006_FINAL_UPGRADE_BACKUP"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Modules = @("deal_transaction_events.py","deal_transaction_replay.py","deal_concurrency.py","deal_consistency.py","deal_authorization.py","deal_transaction_workflow.py","deal_integrity.py","deal_freeze.py","test_deal_final_hardening.py")
foreach ($Name in $Modules) {
    $src = Join-Path $PackageRoot $Name; $dst = Join-Path $Core $Name
    if (-not (Test-Path $src)) { throw "Package file missing: $Name" }
    if (Test-Path $dst) { Copy-Item $dst (Join-Path $Backup $Name) -Force }
    Copy-Item $src $dst -Force
}
$T07 = Join-Path $Core "test_deal_transaction_events.py"
if (Test-Path $T07) {
    $text = Get-Content $T07 -Raw
    if ($text -match 'def\s+make_deal\(\)\s*->\s*Deal:' -and $text -match 'advance_transaction_milestone\(\s*DealStatus\.BOOKING_PENDING') {
        $replacement = @'
def make_deal() -> Deal:
    deal = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        at=AT,
    )
    deal = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )
    for target in (
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    ):
        deal = deal.transition(
            target,
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )
    return deal
'@
        $pattern = '(?s)def\s+make_deal\(\)\s*->\s*Deal:.*?(?=\n(?:def|class)\s+)'
        $newText = [regex]::Replace($text, $pattern, $replacement)
        if ($newText -eq $text) { throw "T07 fixture detected but guarded replacement failed." }
        Set-Content -Path $T07 -Value $newText -Encoding UTF8
    }
}
Write-Host "=== CORE-006 FINAL UPGRADE: COMPILE ===" -ForegroundColor Cyan
python -m compileall -q $Core
if ($LASTEXITCODE -ne 0) { throw "Compile failed." }
Write-Host "=== CORE-006 HARDENING TESTS ===" -ForegroundColor Cyan
pytest -q $Core\test_deal_final_hardening.py
if ($LASTEXITCODE -ne 0) { throw "CORE-006 hardening tests failed." }
if (Test-Path $T07) {
    Write-Host "=== CORE-006 T07 FOCUSED TEST ===" -ForegroundColor Cyan
    pytest -q $T07
    if ($LASTEXITCODE -ne 0) { throw "CORE-006 T07 tests failed." }
}
Write-Host "=== CORE-006 FINAL UPGRADE APPLIED + VERIFIED ===" -ForegroundColor Green
Write-Host "Control Center state/gates were not modified." -ForegroundColor Green
Write-Host "Backup: $Backup" -ForegroundColor DarkGreen
