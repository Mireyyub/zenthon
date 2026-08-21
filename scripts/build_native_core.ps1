param(
    [switch]$Release
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Crate = Join-Path $Root "native_core\rust\zenthon-native-core"
$Output = Join-Path $Root "native_core\bin"

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "Rust Cargo was not found. Install the official Rust toolchain, then rerun this script. Zenthon will keep using the safe Python fallback until a native binary exists."
}

Push-Location $Crate
try {
    if ($Release) {
        cargo build --release
        $Source = Join-Path $Crate "target\release\zenthon-native-core.exe"
    } else {
        cargo build
        $Source = Join-Path $Crate "target\debug\zenthon-native-core.exe"
    }
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$Target = Join-Path $Output "zenthon-native-core.exe"
Copy-Item -Force $Source $Target
[Environment]::SetEnvironmentVariable("ZENTHON_NATIVE_CORE_BIN", $Target, "User")
Write-Host "Native Core built: $Target"
Write-Host "Restart Zenthon to use the native binary."
