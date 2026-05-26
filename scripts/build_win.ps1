param(
    [string]$PythonExe = "",
    [string]$ISCC = "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not $PythonExe) {
    if (Test-Path $VenvPython) {
        $PythonExe = $VenvPython
    } else {
        $PythonExe = "python"
    }
}

if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    throw "python not found: $PythonExe"
}
if (-not (Test-Path $ISCC)) {
    throw "ISCC not found: $ISCC. Please install Inno Setup 6."
}

& $PythonExe -c "import PyInstaller, pyautogui, pyperclip, cv2, PIL"
if ($LASTEXITCODE -ne 0) {
    throw "[win] dependency check failed. Run: uv sync, or pass -PythonExe path\to\python.exe"
}

$Version = & $PythonExe scripts/make_release.py version
$ReleaseDir = & $PythonExe scripts/make_release.py prepare --platform win
& $PythonExe scripts/make_release.py clean-build

Write-Host "[win] building exe via PyInstaller..."
& $PythonExe -m PyInstaller --noconfirm --clean build/autopaper.spec
if ($LASTEXITCODE -ne 0) {
    throw "[win] PyInstaller failed with exit code $LASTEXITCODE"
}

$ExePath = Join-Path $Root "dist\AutoPaper\AutoPaper.exe"
if (-not (Test-Path $ExePath)) {
    throw "[win] build failed: exe not found at $ExePath"
}
$WorkerPath = Join-Path $Root "dist\AutoPaper\AutoPaperWorker.exe"
if (-not (Test-Path $WorkerPath)) {
    throw "[win] build failed: worker not found at $WorkerPath"
}
$ConfigPath = Join-Path $Root "dist\AutoPaper\config"
$InternalConfigPath = Join-Path $Root "dist\AutoPaper\_internal\config"
if (-not (Test-Path $ConfigPath) -and -not (Test-Path $InternalConfigPath)) {
    throw "[win] build failed: config folder missing at $ConfigPath or $InternalConfigPath"
}
$PhotosPath = Join-Path $Root "dist\AutoPaper\photos"
$InternalPhotosPath = Join-Path $Root "dist\AutoPaper\_internal\photos"
if (-not (Test-Path $PhotosPath) -and -not (Test-Path $InternalPhotosPath)) {
    throw "[win] build failed: photos folder missing at $PhotosPath or $InternalPhotosPath"
}

Write-Host "[win] building installer via Inno Setup..."
& $ISCC "packaging\windows\autopaper.iss" "/DMyAppVersion=""$Version"""
if ($LASTEXITCODE -ne 0) {
    throw "[win] Inno Setup failed with exit code $LASTEXITCODE"
}

Write-Host "[win] done"
Write-Host "EXE: $ExePath"
Write-Host "Worker: $WorkerPath"
Write-Host "Installer: $ReleaseDir\AutoPaper-$Version-win-setup.exe"
