@echo off
setlocal
title LGS Soak Uploader - install / update

rem Double-click this in the folder that holds LGS-Test-Tool-v*.exe and
rem LGS-Soak-Uploader-v*.exe. It registers the uploader as a boot-time task
rem and keeps the window open so the report can be read.
rem
rem      install-soak-uploader.cmd            install or update
rem      install-soak-uploader.cmd -Remove    take it out again
rem
rem Same two Windows defaults as install-autorun.cmd: ExecutionPolicy is
rem lifted for this one run only, and we relaunch through UAC when needed.

net session >nul 2>&1
if not errorlevel 1 goto :elevated

echo.
echo  Administrator rights are needed to register a boot-time task.
echo  Approve the Windows prompt; a new window will open and do the work.
echo.
if "%~1"=="" (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
) else (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
)
exit /b

:elevated
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-soak-uploader.ps1" %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo  The installer reported a problem (exit code %RC%). Read the FAIL line above.
echo.
echo  Press any key to close this window.
pause >nul
endlocal
