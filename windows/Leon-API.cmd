@echo off
REM Start only supervised API on 127.0.0.1:8000
setlocal
set "ROOT=%~dp0"
if exist "%ROOT%..\scripts\run_supervised_api.py" (
  set "ROOT=%~dp0.."
)
pushd "%ROOT%"
set LEON_API_HOST=127.0.0.1
set LEON_API_PORT=8000
python scripts\run_supervised_api.py
if errorlevel 1 python -m core.supervisor
popd
endlocal
