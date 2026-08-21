@echo off
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"
python run.py --gui
popd
endlocal
