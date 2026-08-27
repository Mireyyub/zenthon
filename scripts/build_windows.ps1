param(
    [switch]$Installer,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "Windows .exe paketi yalnız Windows 11 mühitində build edilə bilər."
}

$SystemPython = (Get-Command python.exe -ErrorAction Stop).Source
$BuildPython = Join-Path $Root ".build-venv\Scripts\python.exe"
if (-not (Test-Path $BuildPython)) {
    & $SystemPython -m venv .build-venv
}

& $BuildPython -m pip install --upgrade pip
& $BuildPython -m pip install -r requirements-full.txt -r requirements-windows-build.txt
& $BuildPython -m compileall -q .
& $BuildPython -m PyInstaller --noconfirm --clean --windowed --name Zenthon `
    --add-data "curriculum;curriculum" --add-data "data\leon\.gitkeep;data\leon" `
    --collect-data interfaces --collect-submodules interfaces --collect-submodules core `
    --hidden-import tkinter --hidden-import PIL `
    zenthon_desktop.py

$ExePath = Join-Path $Root "dist\Zenthon\Zenthon.exe"
if (-not (Test-Path $ExePath)) {
    throw "PyInstaller output was not found: $ExePath"
}

if (-not $SkipSmoke) {
    Write-Host "Running packaged core smoke..."
    & $ExePath --smoke
    if ($LASTEXITCODE -ne 0) { throw "Packaged core smoke failed with exit code $LASTEXITCODE" }
    Write-Host "Running packaged loopback bridge smoke..."
    & $ExePath --bridge-smoke
    if ($LASTEXITCODE -ne 0) { throw "Packaged bridge smoke failed with exit code $LASTEXITCODE" }
}

if ($Installer) {
    $MakeNsis = (Get-Command makensis.exe -ErrorAction SilentlyContinue).Source
    if (-not $MakeNsis) {
        $MakeNsis = @(
            "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
            "$env:ProgramFiles\NSIS\makensis.exe"
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if (-not $MakeNsis) {
        throw "NSIS tapılmadı. NSIS quraşdırın, sonra yenidən -Installer parametrini istifadə edin."
    }
    & $MakeNsis "$Root\windows\Zenthon.nsi"
}

Write-Host "Build tamamlandı: $ExePath"
