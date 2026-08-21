param(
    [switch]$Installer
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
& $BuildPython -m pip install -r requirements.txt -r requirements-windows-build.txt
& $BuildPython -m PyInstaller --noconfirm --clean --windowed --name Zenthon `
    --add-data "curriculum;curriculum" --add-data "data;data" `
    --collect-data interfaces --hidden-import tkinter --hidden-import PIL `
    zenthon_desktop.py

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

Write-Host "Build tamamlandı: $Root\dist\Zenthon\Zenthon.exe"
