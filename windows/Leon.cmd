@echo off
REM Portable Leon launcher (dev tree or installed folder)
setlocal
set "ROOT=%~dp0"
if exist "%ROOT%Zenthon.exe" (
  start "" "%ROOT%Zenthon.exe"
  exit /b 0
)
set "ROOT=%~dp0.."
pushd "%ROOT%"
if exist "leon_desktop.py" (
  python leon_desktop.py
) else if exist "zenthon_desktop.py" (
  python zenthon_desktop.py
) else (
  echo Leon entry not found.
  exit /b 1
)
popd
endlocal
