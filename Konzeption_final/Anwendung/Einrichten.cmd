@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Einrichten.ps1" %*
set "EinrichtungsErgebnis=%ERRORLEVEL%"
pause
exit /b %EinrichtungsErgebnis%
