@echo off
setlocal
title Neon FPS Booster - Installer
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0installer.py" %*
    goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0installer.py" %*
    goto :end
)

echo.
echo  [X] Python 3.9+ was not found.
echo      Install it from https://www.python.org/downloads/
echo      (tick "Add python.exe to PATH") and run this file again.
echo.

:end
endlocal
pause
