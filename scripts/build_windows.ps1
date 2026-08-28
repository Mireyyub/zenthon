param(
    [switch]$Installer,
    [switch]$SkipVenv
)

# Phase 11 — hybrid Leon packaging
# Produces: dist/Zenthon/Zenthon.exe  (+ optional dist/Zenthon-Setup.exe)
# Requires: Windows + Python 3.10+
# Optional: NSIS for -Installer

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "Windows package build only supported on Windows."
}

$SystemPython = (Get-Command python.exe -ErrorAction Stop).Source
$BuildPython = Join-Path $Root ".build-venv\Scripts\python.exe"

if (-not $SkipVenv) {
    if (-not (Test-Path $BuildPython)) {
        Write-Host "Creating .build-venv ..."
        & $SystemPython -m venv .build-venv
    }
    & $BuildPython -m pip install --upgrade pip
    # Cognitive core deps — avoid pulling full torch if user uses lean env
    if (Test-Path "$Root\requirements.txt") {
        & $BuildPython -m pip install -r "$Root\requirements.txt"
    }
    & $BuildPython -m pip install -r "$Root\requirements-windows-build.txt"
} else {
    $BuildPython = $SystemPython
}

$DistDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

Write-Host "PyInstaller → Zenthon.exe (entry: leon_desktop.py)"
& $BuildPython -m PyInstaller --noconfirm --clean --windowed --name Zenthon `
    --paths $Root `
    --add-data "curriculum;curriculum" `
    --add-data "data;data" `
    --add-data "ui;ui" `
    --hidden-import uvicorn `
    --hidden-import fastapi `
    --hidden-import pydantic `
    --hidden-import core.supervisor `
    --hidden-import interfaces.gui.main_gui `
    --hidden-import interfaces.api.main `
    --collect-submodules core `
    --collect-submodules brain `
    --collect-submodules interfaces `
    leon_desktop.py

# Portable launchers into dist folder
$OutApp = Join-Path $DistDir "Zenthon"
if (Test-Path $OutApp) {
    Copy-Item "$Root\windows\Leon.cmd" -Destination $OutApp -Force -ErrorAction SilentlyContinue
    Copy-Item "$Root\windows\Leon-API.cmd" -Destination $OutApp -Force -ErrorAction SilentlyContinue
    Copy-Item "$Root\docs\PACKAGING.md" -Destination (Join-Path $OutApp "PACKAGING.md") -Force -ErrorAction SilentlyContinue
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
        throw "NSIS not found. Install NSIS, then re-run with -Installer."
    }
    & $MakeNsis "$Root\windows\Zenthon.nsi"
    Write-Host "Installer: $Root\dist\Zenthon-Setup.exe"
}

Write-Host "Build done: $Root\dist\Zenthon\Zenthon.exe"
Write-Host "Note: Tauri shell is still seed-only (desktop/tauri). This is PyInstaller + NSIS path."
