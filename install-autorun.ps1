# Install, update or remove the LGS Test Tool as a Windows scheduled task that
# starts at boot -- for the hospital's server PC, where nobody logs in.
#
# You normally do not call this directly: double-click install-autorun.cmd. It
# asks for administrator rights, runs this, and keeps the window open so the
# whole report can be read.
#
#     install-autorun.cmd                 # newest exe here, port 8080
#     install-autorun.cmd -Port 8090
#     install-autorun.cmd -Firewall       # also open the port inbound
#     install-autorun.cmd -Remove         # take it all out again
#
# Why a scheduled task and not the Startup folder: the Startup folder needs a
# login, and this PC reboots after patches with nobody there. Why SYSTEM: no
# password to store or expire, it runs before any login, and it may bind the
# NTP server's privileged UDP port. The task starts the exe headless
# (--no-browser) with an explicit --port, 60 s after boot so the NIC is up.
#
# Updating to a new build is the SAME command: drop the new exe in this folder
# and run it again. The task is re-pointed at the newest version and the data
# folder beside the exe -- settings, logs, CSV exports -- is left untouched.
#
# NOTE: keep this file ASCII-only. It has no BOM, so PowerShell 5.1 reads it as
# ANSI, where a UTF-8 dash or curly quote becomes bytes that end a string early
# and break the parse in a way that points at the wrong line.

#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$ExePath = "",
    [int]$Port = 8080,
    [string]$TaskName = "LGS Test Tool",
    [int]$DelaySeconds = 60,
    [switch]$Firewall,
    [switch]$Remove,
    [switch]$SkipAclFix,
    [switch]$NoStart,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$fwRuleName = "LGS Test Tool web ($TaskName)"
$here = $PSScriptRoot

function Step($n, $text) { Write-Host ""; Write-Host "[$n] $text" -ForegroundColor Cyan }
function Ok($text)       { Write-Host "    OK    $text" -ForegroundColor Green }
function Info($text)     { Write-Host "          $text" -ForegroundColor Gray }
function Note($text)     { Write-Host "    WARN  $text" -ForegroundColor Yellow }
function Bad($text)      { Write-Host "    FAIL  $text" -ForegroundColor Red }

function Get-ToolVersion($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 4
        if ($r.Content -match '<title>\s*(.*?)\s*</title>') { return $Matches[1] }
        return "running (page has no title)"
    } catch { return $null }
}

function Test-PortFree($p) {
    # Bind it ourselves for a moment. Cheaper and more honest than parsing
    # netstat, and it answers the question that matters: can the tool have it.
    try {
        $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $p)
        $l.Start(); $l.Stop(); return $true
    } catch { return $false }
}

function Get-PortOwner($p) {
    try {
        $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop | Select-Object -First 1
        $pr = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($pr) { return "$($pr.ProcessName) (PID $($pr.Id))" }
        return "PID $($c.OwningProcess)"
    } catch { return "another program" }
}

function Stop-Everything {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t -and $t.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Ok "scheduled task stopped"
    } elseif ($t) {
        Info "scheduled task was not running"
    }
    # A copy someone started by hand is not the task's child, so stopping the
    # task does not close it. It would keep the exe file locked and hold the
    # single-instance mutex, which makes the new copy exit at once saying
    # "already running" -- looking exactly like nothing happened.
    $procs = @(Get-Process "LGS-Test-Tool*" -ErrorAction SilentlyContinue)
    if ($procs.Count -gt 0) {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
        Ok "closed $($procs.Count) hand-started copy/copies"
    } else {
        Info "no copies running by hand"
    }
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor White
Write-Host " LGS Test Tool - server install" -ForegroundColor White
Write-Host " folder: $here" -ForegroundColor Gray
Write-Host "==============================================================" -ForegroundColor White

# ----------------------------------------------------------------- 1 survey
Step 1 "What is here now"

$exes = @(Get-ChildItem -Path $here -Filter "LGS-Test-Tool-v*.exe" -ErrorAction SilentlyContinue |
    Sort-Object { try { [version]($_.BaseName -replace '^LGS-Test-Tool-v','') } catch { [version]"0.0.0" } } -Descending)
if ($exes.Count -eq 0) {
    Info "executables    : none found"
} else {
    Info "executables    :"
    foreach ($e in $exes) {
        $mark = "  "
        if ($e.FullName -eq $exes[0].FullName) { $mark = "->" }
        Info ("   {0} {1}   {2:N0} MB   {3:yyyy-MM-dd HH:mm}" -f $mark, $e.Name, ($e.Length/1MB), $e.LastWriteTime)
    }
    Info "   (-> newest, this is the one that gets installed)"
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$taskPort = $null
if ($task) {
    $act = @($task.Actions)[0]
    if ($act.Arguments -match '--port\s+(\d+)') { $taskPort = [int]$Matches[1] }
    Info "scheduled task : present, state $($task.State)"
    Info "   points at   : $(Split-Path $act.Execute -Leaf)"
    Info "   arguments   : $($act.Arguments)"
} else {
    Info "scheduled task : not installed yet"
}
# Probe whatever the installed task actually serves, not the parameter
# default -- otherwise an update on port 8090 reports "no answer" on 8080
# and reads as if the tool were down.
$probePort = $Port
if ($taskPort) { $probePort = $taskPort }

$running = @(Get-Process "LGS-Test-Tool*" -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    foreach ($p in $running) { Info "running now    : PID $($p.Id)  $($p.Path)" }
} else {
    Info "running now    : nothing"
}

$live = Get-ToolVersion "http://localhost:$probePort"
if ($live) { Info "port $probePort      : answering - $live" }
else        { Info "port $probePort      : no answer" }

$dataDir = Join-Path $here "data"
if (Test-Path $dataDir) {
    $n = @(Get-ChildItem $dataDir -Recurse -File -ErrorAction SilentlyContinue).Count
    Info "data folder    : present, $n files - settings and logs will be kept"
} else {
    Info "data folder    : none yet, created on first run"
}

# ----------------------------------------------------------------- remove
if ($Remove) {
    Step 2 "Removing"
    Stop-Everything
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Ok "scheduled task '$TaskName' unregistered"
    } else { Info "no scheduled task to remove" }
    if (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue) {
        Remove-NetFirewallRule -DisplayName $fwRuleName
        Ok "firewall rule removed"
    } else { Info "no firewall rule to remove" }
    Info "the exe and the data folder were left where they are"
    Write-Host ""
    Write-Host " Removed. It will not start at boot any more." -ForegroundColor Green
    exit 0
}

# ----------------------------------------------------------------- 2 pick
Step 2 "Choosing the executable"
if (-not $ExePath) {
    if ($exes.Count -eq 0) {
        Bad "no LGS-Test-Tool-v*.exe in this folder"
        Info "copy the exe next to this script and run again, or pass -ExePath"
        exit 1
    }
    $ExePath = $exes[0].FullName
}
$resolved = Resolve-Path $ExePath -ErrorAction SilentlyContinue
if (-not $resolved) { Bad "not found: $ExePath"; exit 1 }
$ExePath = $resolved.Path
Ok "installing $(Split-Path $ExePath -Leaf)"
if ($task) {
    $old = @($task.Actions)[0].Execute
    if ($old -ne $ExePath) { Info "replacing  $(Split-Path $old -Leaf)" }
    else                   { Info "same file the task already used - re-registering anyway" }
}
$exeDir = Split-Path $ExePath -Parent

# ----------------------------------------------------------------- 3 checks
Step 3 "Safety checks"

$isOneDrive = ($env:OneDrive -and $ExePath.StartsWith($env:OneDrive)) -or ($ExePath -like "*\OneDrive*")
if ($isOneDrive -and -not $Force) {
    Bad "this folder is inside OneDrive"
    Info "Files-On-Demand can leave the exe unavailable at boot and the sync"
    Info "client fights the open log files. The failure only appears at the"
    Info "NEXT reboot, long after anyone is watching."
    Info "Copy the exe and this script to a local folder such as"
    Info "C:\LGS-Test-Tool\ and run again, or pass -Force to override."
    exit 1
} elseif ($isOneDrive) {
    Note "inside OneDrive - continuing because -Force was given"
} else {
    Ok "not a OneDrive folder"
}

$writable = @((Get-Acl $exeDir).Access | Where-Object {
    $_.AccessControlType -eq "Allow" -and
    ($_.FileSystemRights -match "Write|Modify|FullControl") -and
    ($_.IdentityReference.Value -match '\\Users$|^Everyone$|Authenticated Users$|INTERACTIVE$')
})
if ($writable.Count -gt 0) {
    $who = ($writable | ForEach-Object { $_.IdentityReference.Value } | Select-Object -Unique) -join ", "
    Note "folder is writable by non-admin users ($who)"
    Info "the task runs this exe as SYSTEM at every boot, so a local user could"
    Info "swap the file and gain SYSTEM. On a stock Windows install even"
    Info "C:\LGS-Test-Tool inherits Modify for Authenticated Users from C:\."
    if ($SkipAclFix) {
        if (-not $Force) {
            Bad "refusing because -SkipAclFix was given; harden the ACL or add -Force"
            exit 1
        }
        Note "left as it is because -Force was given"
    } else {
        icacls "$exeDir" /inheritance:r /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F" "Users:(OI)(CI)RX" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Bad "icacls failed ($LASTEXITCODE) - harden manually or use -SkipAclFix -Force"
            exit 1
        }
        Ok "folder ACL hardened - admins and SYSTEM write, users read only"
    }
} else {
    Ok "folder is not writable by ordinary users"
}

# ----------------------------------------------------------------- 4 stop
Step 4 "Stopping what is running"
Stop-Everything

# ----------------------------------------------------------------- 5 port
Step 5 "Web UI port"
if ($PSBoundParameters.ContainsKey('Port')) {
    Info "using -Port $Port from the command line"
} else {
    # Asked here rather than at the top because everything of ours is now
    # stopped: a port that still looks busy is genuinely somebody else's.
    $suggest = $Port
    if ($taskPort) { $suggest = $taskPort }
    while ($true) {
        Write-Host ""
        if ($taskPort) { Info "the installed task serves port $taskPort" }
        Info "8080 is the usual choice; pick another if it is already taken"
        $ans = Read-Host "    Port to use [$suggest]"
        if ([string]::IsNullOrWhiteSpace($ans)) {
            $Port = $suggest
        } elseif ($ans -match '^\d+$' -and [int]$ans -ge 1 -and [int]$ans -le 65535) {
            $Port = [int]$ans
        } else {
            Bad "'$ans' is not a port number (1-65535)"
            continue
        }
        if (Test-PortFree $Port) { Ok "port $Port is free"; break }
        Note "port $Port is already held by $(Get-PortOwner $Port)"
        Info "the tool would exit with code 2 at boot and never come up"
        $again = Read-Host "    Choose a different port? [Y/n]"
        if ($again -match '^[Nn]') { Note "keeping $Port anyway"; break }
    }
}

# ----------------------------------------------------------------- 6 task
Step 6 "Registering the scheduled task"
$action = New-ScheduledTaskAction -Execute $ExePath -Argument "--port $Port --no-browser" -WorkingDirectory $exeDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT$($DelaySeconds)S"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Info "previous task unregistered"
}
$reg = Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -ErrorAction SilentlyContinue
# Check it, do not assume. ErrorActionPreference is Continue so a failure here
# only prints a red block and carries on -- and an unconditional "OK" line
# underneath would then be a lie in the one report someone relies on.
if (-not $reg -or -not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    Bad "could not register the task"
    Info "the usual cause is that this window is not elevated - close it and"
    Info "double-click install-autorun.cmd, which asks for admin rights itself"
    exit 1
}
Ok "task '$TaskName' registered"
Info "runs as SYSTEM, at boot + $DelaySeconds s, headless, port $Port"
Info "restarts up to 3 times, 5 min apart, on failure; no run-time limit"

# ----------------------------------------------------------------- 6 firewall
Step 7 "Firewall"
if ($Firewall) {
    if (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue) {
        Remove-NetFirewallRule -DisplayName $fwRuleName
    }
    $rule = New-NetFirewallRule -DisplayName $fwRuleName -Direction Inbound `
            -Action Allow -Protocol TCP -LocalPort $Port -ErrorAction SilentlyContinue
    if ($rule) { Ok "inbound TCP $Port opened for other PCs on the LAN" }
    else       { Note "could not add the firewall rule - open TCP $Port by hand" }
} else {
    if (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue) {
        Info "an earlier rule for this tool is still in place"
    } else {
        Info "untouched - pass -Firewall to open TCP $Port for other PCs"
    }
}

# ----------------------------------------------------------------- 7 verify
Step 8 "Starting and verifying"
$seen = $null
if ($NoStart) {
    Info "-NoStart given; start it with: Start-ScheduledTask -TaskName '$TaskName'"
} else {
    Start-ScheduledTask -TaskName $TaskName
    Info "waiting for it to answer on http://localhost:$Port ..."
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 2
        $seen = Get-ToolVersion "http://localhost:$Port"
        if ($seen) { break }
    }
    if ($seen) {
        Ok "answering: $seen"
    } else {
        Bad "no answer after 80 seconds"
        Info "look at Task Scheduler history, and the newest file in"
        Info "$exeDir\data\logs"
        Info "if the port is taken by another program the tool exits with code 2"
        Info "- run this again with a different -Port"
    }
}

# ----------------------------------------------------------------- summary
$ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
       Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
       Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "==============================================================" -ForegroundColor White
if ($NoStart -or $seen) { Write-Host " Done." -ForegroundColor Green }
else                    { Write-Host " Installed, but it did not come up - see above." -ForegroundColor Yellow }
Write-Host "   installed : $(Split-Path $ExePath -Leaf)"
Write-Host "   open      : http://localhost:$Port"
if ($ip) { Write-Host "   from LAN  : http://${ip}:$Port" }
Write-Host "   settings  : kept in $exeDir\data"
Write-Host "   at boot   : yes, as SYSTEM, $DelaySeconds s after startup"
Write-Host ""
Write-Host "   update later : put the new exe here and run this again"
Write-Host "   uninstall    : install-autorun.cmd -Remove"
Write-Host "==============================================================" -ForegroundColor White
