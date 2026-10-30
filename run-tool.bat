@echo off
rem Start the LGS Test Tool from source and open the v2 pages in the browser.
rem Usage: run-tool.bat [port]     (default: the port saved in the tool's config, 8080)
rem Close this window (or press Ctrl+C) to stop the tool.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv not found in %CD%. Create it first: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
set LGS_TT_NO_BROWSER=1
set PYTHONIOENCODING=utf-8
if not "%~1"=="" set LGS_TT_PORT=%~1
if "%LGS_TT_PORT%"=="" (set URLPORT=8080) else (set URLPORT=%LGS_TT_PORT%)
rem Open the browser a few seconds after the server starts.
start "" /b cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:%URLPORT%/v2"
".venv\Scripts\python.exe" -m app.main
pause
