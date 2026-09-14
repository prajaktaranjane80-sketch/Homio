
@echo off
setlocal

cd /d "%~dp0"

python reos_control_center.py %*

if errorlevel 1 (
    echo.
    echo REOS CONTROL CENTER FAILED.
    echo.
    pause
    exit /b %errorlevel%
)

endlocal
