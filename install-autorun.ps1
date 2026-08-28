# Install (or remove) LGS Test Tool as a Windows scheduled task that starts
# at boot -- for the hospital's server PC, where nobody logs in to start it.
#
#     .\install-autorun.ps1                     # newest exe here, port 8080
#     .\install-autorun.ps1 -Port 8090
#     .\install-autorun.ps1 -Firewall           # also open the port inbound
#     .\install-autorun.ps1 -Remove             # take it all out again
#
# Why a scheduled task and not the Startup folder: the Startup folder needs a
# login, and this PC reboots after patches with nobody there. Why SYSTEM: no
# password to store or expire, it runs before any login, and it may bind the
# NTP server's privileged UDP port. The task starts the exe headless
# (--no-browser) with an explicit --port, 60 s after boot so the NIC is up.
#
# The tool itself refuses to run twice (named mutex), so IgnoreNew here is a
# second belt, not the mechanism.

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
    [switch]$Force
)

$fwRuleName = "LGS Test Tool web ($TaskName)"

if ($Remove) {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'."
    } else {
        Write-Host "No scheduled task '$TaskName' found."
    }
    $r = Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
    if ($r) {
        Remove-NetFirewallRule -DisplayName $fwRuleName
        Write-Host "Removed firewall rule '$fwRuleName'."
    }
    exit 0
}

# -- find the exe -------------------------------------------------------------
if (-not $ExePath) {
    # Sort by the actual version, not the name: lexically v1.9.2 > v1.10.0.
    $candidate = Get-ChildItem -Path $PSScriptRoot -Filter "LGS-Test-Tool-v*.exe" |
        Sort-Object { [version]($_.BaseName -replace '^LGS-Test-Tool-v', '') } -Descending |
        Select-Object -First 1
    if (-not $candidate) {
        Write-Error "No LGS-Test-Tool-v*.exe next to this script. Pass -ExePath."
        exit 1
    }
    $ExePath = $candidate.FullName
}
$ExePath = (Resolve-Path $ExePath).Path
if (-not (Test-Path $ExePath)) { Write-Error "Not found: $ExePath"; exit 1 }

# -- refuse OneDrive ----------------------------------------------------------
# Files-On-Demand can dehydrate the exe before the task fires at boot, and the
# sync client fights the open log and data files. This is a hard stop, not a
# warning, because the failure only shows up at the NEXT reboot -- long after
# anyone is watching. -Force exists for dev boxes that know what they risk.
$isOneDrive = ($env:OneDrive -and $ExePath.StartsWith($env:OneDrive)) -or
              ($ExePath -like "*\OneDrive*")
if ($isOneDrive -and -not $Force) {
    Write-Error ("Refusing to autorun from a OneDrive folder:`n  $ExePath`n" +
                 "Copy the exe (and this script) to a local folder such as " +
                 "C:\LGS-Test-Tool\ and run again. Use -Force to override.")
    exit 1
}

# -- privilege-escalation check ----------------------------------------------
# The task runs this exe as SYSTEM at every boot. If ordinary users can write
# to the exe's folder, any local user can swap the binary and own the machine
# on the next reboot. Warn loudly; -Force proceeds (a bench PC may not care).
$exeDir = Split-Path $ExePath -Parent
$writable = (Get-Acl $exeDir).Access | Where-Object {
    $_.AccessControlType -eq "Allow" -and
    ($_.FileSystemRights -match "Write|Modify|FullControl") -and
    ($_.IdentityReference.Value -match '\\Users$|^Everyone$|Authenticated Users$|INTERACTIVE$')
}
if ($writable) {
    $who = ($writable | ForEach-Object { $_.IdentityReference.Value } | Select-Object -Unique) -join ", "
    Write-Warning "The exe's folder is writable by non-admin users ($who) - on a stock"
    Write-Warning "Windows install even C:\LGS-Test-Tool inherits Modify for Authenticated"
    Write-Warning "Users from C:\. A local user could swap the exe and run as SYSTEM at boot."
    if ($SkipAclFix) {
        if (-not $Force) {
            Write-Error "Refusing a SYSTEM task on a user-writable folder (-SkipAclFix was given). Pass -Force to accept the risk."
            exit 1
        }
    } else {
        # We are already elevated and this is a dedicated folder: harden it.
        Write-Host "Hardening the folder ACL (admins+SYSTEM write, users read)..."
        icacls "$exeDir" /inheritance:r `
            /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F" "Users:(OI)(CI)RX" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "icacls failed ($LASTEXITCODE) - harden manually or pass -SkipAclFix -Force."
            exit 1
        }
        Write-Host "  done: $exeDir is no longer writable by ordinary users"
    }
}

# -- register the task --------------------------------------------------------
$exeDir = Split-Path $ExePath -Parent
$action = New-ScheduledTaskAction -Execute $ExePath `
    -Argument "--port $Port --no-browser" -WorkingDirectory $exeDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT$($DelaySeconds)S"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
    -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Replacing existing task '$TaskName'."
}
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings | Out-Null

Write-Host "Installed '$TaskName':"
Write-Host "  exe      $ExePath"
Write-Host "  starts   at boot + $DelaySeconds s, as SYSTEM, headless"
Write-Host "  web UI   http://localhost:$Port  (and from the LAN)"
Write-Host "  restarts 3x every 5 min on failure; no run-time limit"

# -- firewall (opt-in: the hospital's IT owns firewall policy) ----------------
if ($Firewall) {
    $r = Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
    if ($r) { Remove-NetFirewallRule -DisplayName $fwRuleName }
    New-NetFirewallRule -DisplayName $fwRuleName -Direction Inbound `
        -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
    Write-Host "  firewall inbound TCP $Port opened ('$fwRuleName')"
} else {
    Write-Host "  firewall untouched (pass -Firewall to open TCP $Port inbound)"
}

Write-Host ""
Write-Host "Start it now without rebooting:  Start-ScheduledTask -TaskName '$TaskName'"
