param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($env:OS -ne "Windows_NT") {
    throw "Windows .exe paketi yalnız Windows 11 mühitində build edilə bilər."
}

$BuildPython = Join-Path $Root ".build-venv\Scripts\python.exe"
if (-not (Test-Path $BuildPython)) {
    py -3 -m venv .build-venv
}

& $BuildPython -m pip install --upgrade pip
& $BuildPython -m pip install -r requirements.txt -r requirements-windows-build.txt
& $BuildPython -m PyInstaller --noconfirm --clean --windowed --name Zenthon `
    --add-data "curriculum;curriculum" --add-data "data;data" `
    --collect-data interfaces --hidden-import tkinter --hidden-import PIL `
    zenthon_desktop.py

if ($Installer) {
    $MakeNsis = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if (-not $MakeNsis) {
        throw "NSIS tapılmadı. NSIS quraşdırın, sonra yenidən -Installer parametrini istifadə edin."
    }
    & $MakeNsis.Source "$Root\windows\Zenthon.nsi"
}

Write-Host "Build tamamlandı: $Root\dist\Zenthon\Zenthon.exe"
