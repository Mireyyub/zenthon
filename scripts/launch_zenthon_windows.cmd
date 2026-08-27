@echo off
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"
python run.py --desktop
popd
endlocal
