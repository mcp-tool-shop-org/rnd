@echo off
setlocal
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m rnd %*
exit /b %ERRORLEVEL%
