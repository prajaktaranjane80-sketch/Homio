$ErrorActionPreference = "Stop"
Set-Location "D:\HOMIO"

Write-Host "== HOMIO / REOS CORE-004-T01 =="
Write-Host "Applying project-domain patch..."

git switch reos-development
git status --short

git apply --index "CORE-004-T01-project-domain.patch"

Write-Host "`n== Running focused tests =="
python -m pytest REOS_CONTROL_CENTER/AUTONOMY_ENGINE/tests/test_project_domain.py -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "TESTS FAILED. No commit created." -ForegroundColor Red
    git reset
    exit $LASTEXITCODE
}

Write-Host "`n== Test gate passed =="
git status --short

git commit -m "feat(core-004): implement project domain"
git push origin reos-development

Write-Host "`nCORE-004-T01 code pushed successfully."
Write-Host "Do NOT advance the Control Center gate manually until the focused test result is confirmed."
