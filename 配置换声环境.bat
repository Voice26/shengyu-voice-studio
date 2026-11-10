@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_platform.ps1" %*
set "setup_rc=%errorlevel%"
if "%~1"=="" pause
exit /b %setup_rc%
