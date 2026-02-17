@echo off
setlocal
cd /d "%~dp0web"
start "" "%cd%\index.html"
endlocal
