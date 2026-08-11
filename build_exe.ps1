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

# exe name carries the app version (from app/version.py) so deployed copies
# are distinguishable at a glance, e.g. LGS-Test-Tool-v1.1.0.exe
$version = & ".venv\Scripts\python.exe" -c "from app.version import APP_VERSION; print(APP_VERSION)"
if ($LASTEXITCODE -ne 0 -or -not $version) { Write-Host "ERROR: cannot read app/version.py"; exit 1 }
$name = "LGS-Test-Tool-v$version"

# nicegui-pack = NiceGUI's PyInstaller wrapper (adds its static assets etc.)
# It shells out to the bare `pyinstaller` command, so the venv Scripts dir
# must be on PATH for the child process to find it.
$env:PATH = "$PSScriptRoot\.venv\Scripts;$env:PATH"

# The control table travels inside the exe: commissioning happens on site with
# no network, so a link to GitHub would be useless exactly when it is needed.
# --add-data appends to nicegui-pack's own defaults rather than replacing them.
if (-not (Test-Path "app\docs\LGS-Control-Table.md")) {
    Write-Host "ERROR: app\docs\LGS-Control-Table.md missing - run tools\sync_reference.py"
    exit 1
}
# Preparing a factory-fresh Opta needs Arduino's QSPIFormat image on site,
# where there is no PlatformIO to build it from. See app\blobs\README.md.
# The firmware images are bundled for the same reason, and are checked here by
# content: a truncated or swapped image must stop the build, not reach a
# cabinet. app\firmware_bundle.py holds the same hashes and re-checks at load.
$blobs = @{
    "qspiformat_opta.bin"            = "62003812"
    "gateway_opta_v1.9.0.bin"        = "19ae8721"
    "module_g070_v3.2.0_factory.bin" = "7972a50a"
    "module_g070_v3.2.0_ota.bin"     = "d0a27512"
}
foreach ($blob in $blobs.Keys) {
    $path = "app\blobs\$blob"
    if (-not (Test-Path $path)) {
        Write-Host "ERROR: $path missing - see app\blobs\README.md"
        exit 1
    }
    $hash = (Get-FileHash $path -Algorithm SHA256).Hash.ToLower()
    if (-not $hash.StartsWith($blobs[$blob])) {
        Write-Host "ERROR: $path is not the expected image (sha256 starts $($hash.Substring(0,8)), expected $($blobs[$blob]))"
        exit 1
    }
}
& ".venv\Scripts\nicegui-pack.exe" --onefile --name $name `
    --add-data "app\docs;app/docs" `
    --add-data "app\blobs;app/blobs" run.py
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: nicegui-pack failed"; exit 1 }

if (Test-Path "dist\$name.exe") {
    $size = [math]::Round((Get-Item "dist\$name.exe").Length / 1MB, 1)
    Write-Host ""
    Write-Host "OK: dist\$name.exe ($size MB)"
    Write-Host "Deploy: copy the exe anywhere and double-click. Data (config +"
    Write-Host "CSV exports) is written to a 'data' folder next to the exe."
} else {
    Write-Host "ERROR: build finished but dist\$name.exe not found"
    exit 1
}
