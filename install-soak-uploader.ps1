# Install, update or remove the soak uploader as a Windows scheduled task
# that starts at boot, beside the LGS Test Tool task. Double-click
# install-soak-uploader.cmd rather than calling this directly.
#
# The uploader only READS the tool's data\exports folder and sends soak
# results out over HTTPS to the monitor (lgs.teerachot.cc). It opens no port.
#
# Updating is the same command: drop the new exe here and run it again.
#
# NOTE: keep this file ASCII-only (PowerShell 5.1 reads a BOM-less file as
# ANSI; see install-autorun.ps1).

#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$TaskName = "LGS Soak Uploader",
    [int]$DelaySeconds = 90,
    [switch]$Remove,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$here = $PSScriptRoot

function Step($n, $text) { Write-Host ""; Write-Host "[$n] $text" -ForegroundColor Cyan }
function Ok($text)       { Write-Host "    OK    $text" -ForegroundColor Green }
function Info($text)     { Write-Host "          $text" -ForegroundColor Gray }
function Note($text)     { Write-Host "    WARN  $text" -ForegroundColor Yellow }
function Bad($text)      { Write-Host "    FAIL  $text" -ForegroundColor Red }

function Stop-Uploader {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t -and $t.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Ok "scheduled task stopped"
    }
    $procs = @(Get-Process "LGS-Soak-Uploader*" -ErrorAction SilentlyContinue)
    if ($procs.Count -gt 0) {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
        Ok "closed $($procs.Count) hand-started copy/copies"
    }
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor White
Write-Host " LGS Soak Uploader - server install" -ForegroundColor White
Write-Host " folder: $here" -ForegroundColor Gray
Write-Host "==============================================================" -ForegroundColor White

if ($Remove) {
    Step 1 "Removing"
    Stop-Uploader
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Ok "scheduled task '$TaskName' unregistered"
    } else { Info "no scheduled task to remove" }
    Info "the exe, data\soak_uploader.ini and the log were left in place"
    exit 0
}

# ----------------------------------------------------------------- 1 files
Step 1 "Finding the files"
$exes = @(Get-ChildItem -Path $here -Filter "LGS-Soak-Uploader-v*.exe" -ErrorAction SilentlyContinue |
    Sort-Object { try { [version]($_.BaseName -replace '^LGS-Soak-Uploader-v','') } catch { [version]"0.0.0" } } -Descending)
if ($exes.Count -eq 0) {
    Bad "no LGS-Soak-Uploader-v*.exe in this folder"
    exit 1
}
$ExePath = $exes[0].FullName
Ok "uploader     : $(Split-Path $ExePath -Leaf)"

$tool = @(Get-ChildItem -Path $here -Filter "LGS-Test-Tool-v*.exe" -ErrorAction SilentlyContinue)
if ($tool.Count -gt 0) { Ok "test tool    : found beside it - it will read the same data folder" }
else { Note "no LGS-Test-Tool-v*.exe here - the uploader reads THIS folder's data\exports" }

$isOneDrive = ($env:OneDrive -and $ExePath.StartsWith($env:OneDrive)) -or ($ExePath -like "*\OneDrive*")
if ($isOneDrive -and -not $Force) {
    Bad "this folder is inside OneDrive - copy everything to a local folder (pass -Force to override)"
    exit 1
}

# ----------------------------------------------------------------- 2 settings
Step 2 "Settings"
$dataDir = Join-Path $here "data"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$ini = Join-Path $dataDir "soak_uploader.ini"
$token = ""
$tokenRe = '^[A-Za-z0-9_-]{32,128}$'
if (Test-Path $ini) {
    $line = Select-String -Path $ini -Pattern '^\s*token\s*=\s*(\S+)' | Select-Object -First 1
    if ($line) { $token = $line.Matches[0].Groups[1].Value }
}
if ($token -and $token -match $tokenRe) {
    Ok "data\soak_uploader.ini already has a valid-looking token - keeping it"
} else {
    if ($token) {
        Note "the token in data\soak_uploader.ini is not valid (length $($token.Length)) - it will be replaced"
        Info "a hidden prompt can store a literal ^V instead of pasting; this prompt is visible"
    }
    Info "the upload token is the INGEST_TOKEN secret of the lgs-monitor Worker"
    Info "paste with right-click (or Ctrl+V), then press Enter"
    for ($try = 1; $try -le 3; $try++) {
        $token = (Read-Host "    Upload token").Trim()
        if ($token -match $tokenRe) { break }
        Bad "that does not look like the token (length $($token.Length)) - try again"
        $token = ""
    }
    if (-not $token) { Bad "no valid token given"; exit 1 }
    $proxyLine = "proxy ="
    if (Test-Path $ini) {
        $p = Select-String -Path $ini -Pattern '^\s*proxy\s*=.*' | Select-Object -First 1
        if ($p) { $proxyLine = $p.Line.Trim() }
    }
    $text = "[monitor]`r`nurl = https://lgs.teerachot.cc`r`ntoken = $token`r`n$proxyLine`r`n`r`n[source]`r`nexports_dir =`r`ninterval_s = 30`r`nmax_age_hours = 24`r`n"
    [IO.File]::WriteAllText($ini, $text, (New-Object Text.UTF8Encoding($false)))
    # The token lets anyone post data to the monitor: admins and SYSTEM only.
    icacls "$ini" /inheritance:r /grant:r "Administrators:F" "SYSTEM:F" | Out-Null
    Ok "wrote data\soak_uploader.ini (readable by admins and SYSTEM only)"
}

# ----------------------------------------------------------------- 3 one pass
Step 3 "Test run (one pass)"
Stop-Uploader
$logPath = Join-Path $dataDir "soak_uploader.log"
$before = 0
if (Test-Path $logPath) { $before = @(Get-Content $logPath).Count }
& $ExePath --once 2>$null
$rc = $LASTEXITCODE
# Show what this pass logged: the folder it watched and the files it found
# are the first thing to check when the dashboard stays empty.
if (Test-Path $logPath) {
    Get-Content $logPath | Select-Object -Skip $before | ForEach-Object { Info $_ }
}
if ($rc -eq 0) {
    Ok "the monitor is reachable and accepted the token"
} elseif ($rc -eq 1) {
    Bad "the monitor rejected the token - delete data\soak_uploader.ini and run again"
    exit 1
} elseif ($rc -eq 4) {
    Bad "the token in data\soak_uploader.ini is malformed - run this installer again to re-enter it"
    exit 1
} elseif ($rc -eq 3) {
    Bad "cannot reach https://lgs.teerachot.cc from this PC"
    # The task runs as SYSTEM, which does not get the logged-in user's proxy.
    # Show what this PC is configured with so it can go into the ini.
    $ie = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -ErrorAction SilentlyContinue
    if ($ie -and $ie.ProxyEnable -eq 1 -and $ie.ProxyServer) { Info "this user's proxy : $($ie.ProxyServer)" }
    elseif ($ie -and $ie.AutoConfigURL) { Info "this user's proxy : auto-config script $($ie.AutoConfigURL)" }
    else { Info "this user's proxy : none set" }
    $wh = (netsh winhttp show proxy) -join " "
    Info "machine (WinHTTP) : $($wh -replace '\s+', ' ')"
    Info "if the company uses a proxy, put it in data\soak_uploader.ini as"
    Info "   proxy = http://<proxy-host>:<port>"
    Info "and run this installer again"
    exit 1
} else {
    Bad "test pass failed (exit $rc) - see $logPath"
    exit 1
}

# ----------------------------------------------------------------- 4 task
Step 4 "Registering the scheduled task"
$action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT$($DelaySeconds)S"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1)
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
$reg = Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -ErrorAction SilentlyContinue
if (-not $reg -or -not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    Bad "could not register the task (is this window elevated?)"
    exit 1
}
Ok "task '$TaskName' registered: SYSTEM, at boot + $DelaySeconds s, restarts on failure"

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
$state = (Get-ScheduledTask -TaskName $TaskName).State
if ($state -eq "Running") { Ok "running now" } else { Note "task state is $state - see data\soak_uploader.log" }

Write-Host ""
Write-Host "==============================================================" -ForegroundColor White
Write-Host " Done. Soak runs from this PC now appear on https://lgs.teerachot.cc" -ForegroundColor Green
Write-Host "   log       : $dataDir\soak_uploader.log"
Write-Host "   update    : put the new exe here and run this again"
Write-Host "   uninstall : install-soak-uploader.cmd -Remove"
Write-Host "==============================================================" -ForegroundColor White
