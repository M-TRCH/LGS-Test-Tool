@echo off
setlocal
title LGS Soak Uploader - uninstall

rem Double-click this to take the soak uploader off this PC: it stops the
rem boot-time task, closes any running copy and unregisters the task, then
rem checks that both are really gone. It needs nothing else beside it, so it
rem also works on a PC that only has the exe left.
rem
rem The exe, data\soak_uploader.ini (holds the INGEST_TOKEN) and the log are
rem left in place; delete them by hand if the PC is leaving the test set.
rem
rem Keep this file ASCII-only.

net session >nul 2>&1
if not errorlevel 1 goto :elevated

echo.
echo  Administrator rights are needed to remove a boot-time task.
echo  Approve the Windows prompt; a new window will open and do the work.
echo.
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b

:elevated
echo ==============================================================
echo  LGS Soak Uploader - uninstall
echo ==============================================================

set "P=$n='LGS Soak Uploader'; $pn='LGS-Soak-Uploader*';"
set "P=%P% $t=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue;"
set "P=%P% if ($t -and $t.State -eq 'Running') { Stop-ScheduledTask -TaskName $n; Write-Host '    OK    scheduled task stopped' -ForegroundColor Green };"
set "P=%P% $p=@(Get-Process $pn -ErrorAction SilentlyContinue);"
set "P=%P% if ($p.Count -gt 0) { $p | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 800; Write-Host ('    OK    closed ' + $p.Count + ' running copy/copies') -ForegroundColor Green } else { Write-Host '          no uploader process was running' -ForegroundColor Gray };"
set "P=%P% if ($t) { Unregister-ScheduledTask -TaskName $n -Confirm:$false; Write-Host ('    OK    scheduled task ''' + $n + ''' unregistered') -ForegroundColor Green } else { Write-Host '          no scheduled task to remove' -ForegroundColor Gray };"
set "P=%P% $rc=0;"
set "P=%P% if (Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue) { Write-Host '    FAIL  the task is still registered' -ForegroundColor Red; $rc=1 };"
set "P=%P% if (@(Get-Process $pn -ErrorAction SilentlyContinue).Count -gt 0) { Write-Host '    FAIL  an uploader process is still running' -ForegroundColor Red; $rc=1 };"
set "P=%P% if ($rc -eq 0) { Write-Host '    OK    removed: it will not start again at boot' -ForegroundColor Green };"
set "P=%P% Write-Host '          the exe, data\soak_uploader.ini and the log were left in place' -ForegroundColor Gray;"
set "P=%P% exit $rc"

powershell -NoProfile -ExecutionPolicy Bypass -Command "%P%"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo  The uninstall did not finish (exit code %RC%). Read the FAIL line above.
echo.
echo  Press any key to close this window.
pause >nul
endlocal
