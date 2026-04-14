@echo off
set SCRIPT_DIR=%~dp0
set ENTRY=%SCRIPT_DIR%analyze_repo.py

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python -B "%ENTRY%" %*
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 -B "%ENTRY%" %*
  exit /b %ERRORLEVEL%
)

echo Python was not found in PATH.
exit /b 1

