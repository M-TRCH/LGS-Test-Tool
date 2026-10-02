# Build the soak uploader as one portable exe: dist-uploader\LGS-Soak-Uploader-v<ver>.exe
#
# Usage:  powershell -ExecutionPolicy Bypass -File build_uploader.ps1
#
# Output goes to dist-uploader\, NOT dist\: build_exe.ps1 deletes dist\ on
# every build, and dist\data\ is where local soak exports live.
# Copy the exe and install-soak-uploader.cmd/.ps1 into the SAME folder as
# LGS-Test-Tool-v*.exe on the test server; the uploader then finds the tool's
# data\ folder on its own.

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: venv missing - run the setup commands in README.md first"
    exit 1
}

Write-Host "ensuring pyinstaller (build-time only)..."
.venv\Scripts\python.exe -m pip install --quiet pyinstaller
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: pip install pyinstaller failed"; exit 1 }

$version = & ".venv\Scripts\python.exe" -c "import re,pathlib;print(re.search(r'VERSION = \""(.+?)\""', pathlib.Path('tools/soak_uploader.py').read_text()).group(1))"
if ($LASTEXITCODE -ne 0 -or -not $version) { Write-Host "ERROR: cannot read VERSION from tools/soak_uploader.py"; exit 1 }
$name = "LGS-Soak-Uploader-v$version"

foreach ($dir in @("build-uploader", "dist-uploader")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue }
}

# --paths . lets PyInstaller follow `from app.soak_csv import ...`; both app
# modules it pulls in (soak_csv, config_store) are standard-library only.
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --console `
    --name $name --paths . `
    --distpath dist-uploader --workpath build-uploader --specpath build-uploader `
    tools\soak_uploader.py
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: PyInstaller failed"; exit 1 }

Copy-Item install-soak-uploader.cmd, install-soak-uploader.ps1 dist-uploader\
Write-Host ""
Write-Host "built: dist-uploader\$name.exe"
Write-Host "copy dist-uploader\* next to LGS-Test-Tool-v*.exe on the test server, then"
Write-Host "double-click install-soak-uploader.cmd there."
