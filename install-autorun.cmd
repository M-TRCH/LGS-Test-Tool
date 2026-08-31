@echo off
setlocal
title LGS Test Tool - install / update

rem Double-click this. It does the whole job and keeps the window open.
rem
rem Two Windows defaults stand between a double-click and a working install,
rem and this file removes both:
rem
rem   1. ExecutionPolicy is Restricted out of the box, so Windows refuses to
rem      run any .ps1 at all -- the very first thing the real server install
rem      hit. -ExecutionPolicy Bypass lifts it for this one invocation only;
rem      no system setting is changed.
rem   2. Registering a task that runs as SYSTEM needs administrator rights,
rem      and a double-click does not have them. If we are not elevated we
rem      relaunch ourselves through the UAC prompt and let that copy work.
rem
rem Run with no arguments and it ASKS which port to serve the web UI on,
rem offering the port the installed task already uses (or 8080) and checking
rem that nothing else holds it. Pass -Port to answer that in advance:
rem      install-autorun.cmd -Port 8090
rem      install-autorun.cmd -Firewall
rem      install-autorun.cmd -Remove

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
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autorun.ps1" %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo  The installer reported a problem (exit code %RC%). Read the FAIL line above.
echo.
echo  Press any key to close this window.
pause >nul
endlocal
