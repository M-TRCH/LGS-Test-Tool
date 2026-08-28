@echo off
rem One-click wrapper: Windows ships with ExecutionPolicy=Restricted, which
rem refuses every .ps1 -- the first thing the real server install hit. This
rem bypasses the policy for THIS invocation only (no system setting changed)
rem and forwards all arguments, e.g.:  install-autorun.cmd -Port 8090
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autorun.ps1" %*
