param(
    [string]$PythonExe = "python",
    [string]$PyInstallerExe = "pyinstaller",
    [string]$ISCC = "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    throw "python not found: $PythonExe"
}
if (-not (Get-Command $PyInstallerExe -ErrorAction SilentlyContinue)) {
    throw "pyinstaller not found: $PyInstallerExe. Install via pip."
}
if (-not (Test-Path $ISCC)) {
    throw "ISCC not found: $ISCC. Please install Inno Setup 6."
}

$Version = & $PythonExe scripts/make_release.py version
$ReleaseDir = & $PythonExe scripts/make_release.py prepare --platform win
& $PythonExe scripts/make_release.py clean-build

Write-Host "[win] building exe via PyInstaller..."
& $PyInstallerExe --noconfirm --clean build/autopaper.spec

$ExePath = Join-Path $Root "dist\AutoPaper\AutoPaper.exe"
if (-not (Test-Path $ExePath)) {
    throw "[win] build failed: exe not found at $ExePath"
}
$WorkerPath = Join-Path $Root "dist\AutoPaper\AutoPaperWorker.exe"
if (-not (Test-Path $WorkerPath)) {
    throw "[win] build failed: worker not found at $WorkerPath"
}
$ConfigPath = Join-Path $Root "dist\AutoPaper\config"
if (-not (Test-Path $ConfigPath)) {
    throw "[win] build failed: config folder missing at $ConfigPath"
}
$PhotosPath = Join-Path $Root "dist\AutoPaper\photos"
if (-not (Test-Path $PhotosPath)) {
    throw "[win] build failed: photos folder missing at $PhotosPath"
}

Write-Host "[win] building installer via Inno Setup..."
& $ISCC "packaging\windows\autopaper.iss" "/DMyAppVersion=$Version" "/DMyReleaseDir=$ReleaseDir"

Write-Host "[win] done"
Write-Host "EXE: $ExePath"
Write-Host "Worker: $WorkerPath"
Write-Host "Installer: $ReleaseDir\AutoPaper-$Version-win-setup.exe"
