# Build a portable one-file Windows executable: dist\LGS-Test-Tool.exe
# Copy that single file to any Windows PC and double-click — no Python needed,
# COM ports work natively. Close its console window to stop the server.
#
# Usage:  powershell -ExecutionPolicy Bypass -File build_exe.ps1
#
# Note: no $ErrorActionPreference=Stop here — PowerShell 5.1 turns harmless
# native stderr (pip/PyInstaller log lines) into fatal errors under it.
# Each step is checked via exit code instead.

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: venv missing - run the setup commands in README.md first"
    exit 1
}

Write-Host "ensuring pyinstaller (build-time only)..."
.venv\Scripts\python.exe -m pip install --quiet pyinstaller
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: pip install pyinstaller failed"; exit 1 }

# Pre-clean previous build output ourselves: OneDrive can hold locks inside
# build/ that make nicegui-pack's own cleanup die with Access denied.
foreach ($dir in @("build", "dist")) {
    if (Test-Path $dir) {
        foreach ($try in 1..5) {
            try { Remove-Item $dir -Recurse -Force -ErrorAction Stop; break }
            catch { Start-Sleep -Seconds 2 }
        }
        if (Test-Path $dir) {
            Write-Host "ERROR: cannot remove $dir (OneDrive lock?) - pause sync and retry"
            exit 1
        }
    }
}

# nicegui-pack = NiceGUI's PyInstaller wrapper (adds its static assets etc.)
# It shells out to the bare `pyinstaller` command, so the venv Scripts dir
# must be on PATH for the child process to find it.
$env:PATH = "$PSScriptRoot\.venv\Scripts;$env:PATH"
& ".venv\Scripts\nicegui-pack.exe" --onefile --name "LGS-Test-Tool" run.py
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: nicegui-pack failed"; exit 1 }

if (Test-Path "dist\LGS-Test-Tool.exe") {
    $size = [math]::Round((Get-Item "dist\LGS-Test-Tool.exe").Length / 1MB, 1)
    Write-Host ""
    Write-Host "OK: dist\LGS-Test-Tool.exe ($size MB)"
    Write-Host "Deploy: copy the exe anywhere and double-click. Data (config +"
    Write-Host "CSV exports) is written to a 'data' folder next to the exe."
} else {
    Write-Host "ERROR: build finished but dist\LGS-Test-Tool.exe not found"
    exit 1
}
