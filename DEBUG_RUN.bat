@echo off
cd /d "%~dp0"
title VideoFactory - Debug Startup
color 0E

echo ================================================================
echo             D E B U G   S T A R T U P   S C R I P T
echo ================================================================
echo.
echo Current Directory: %CD%
echo.

:: Check Python and Venv
where python >nul 2>nul
if %ERRORLEVEL%==0 (
    echo [Info] System Python is installed and in PATH.
    python --version
) else (
    echo [Warning] System Python is NOT in PATH.
)

if exist venv\Scripts\python.exe (
    echo [Info] Local virtual environment (venv) found.
    echo.
    echo [Info] Launching server using local venv Python...
    echo ----------------------------------------------------------------
    venv\Scripts\python.exe src\web\server.py
) else (
    echo [Error] Local virtual environment (venv) NOT found!
    echo Please run install_dependencies.bat first to set it up.
)

echo ----------------------------------------------------------------
echo Server exited with code: %ERRORLEVEL%
echo.
pause
