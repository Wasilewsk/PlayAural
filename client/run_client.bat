@echo off
cd /d "%~dp0"
echo Starting PlayAural Client...
echo.
echo Installing dependencies, including development test tools...
call uv sync --extra dev
if errorlevel 1 goto install_failed
echo.
echo Launching...
uv run python client.py
pause
exit /b 0

:install_failed
echo.
echo Failed to install PlayAural Client dependencies.
pause
exit /b 1
