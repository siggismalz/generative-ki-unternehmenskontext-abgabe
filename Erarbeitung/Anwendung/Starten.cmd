@echo off
cd /d "%~dp0"
if not exist "%~dp0laufzeit\python\python.exe" goto einrichtung
if not exist "%~dp0laufzeit\llama\llama-server.exe" goto einrichtung
if not exist "%~dp0modelle\Qwen3-4B-Q4_K_M.gguf" goto einrichtung
"%~dp0laufzeit\python\python.exe" -B -X utf8 "%~dp0app.py" %*
if errorlevel 1 pause
exit /b
:einrichtung
echo Bitte zuerst Einrichten.cmd starten. Es laedt die festgelegten Laufzeiten und das Sprachmodell.
echo Danach laesst sich der Demonstrator ueber Starten.cmd lokal verwenden.
pause
exit /b 1
