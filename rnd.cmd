@echo off
setlocal
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m mcptoolshop_rnd %*
exit /b %ERRORLEVEL%
