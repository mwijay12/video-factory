@echo off
:: Change to the directory of this script
cd /d "%~dp0"
title VideoFactory Dependency Installer
color 0B
echo ================================================================
echo             VideoFactory Setup & Dependency Installer
echo ================================================================
echo.

:: 1. Check if virtual environment exists, if not create it
if not exist venv\Scripts\python.exe (
    echo [Info] No local virtual environment (venv) found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [Error] Failed to create virtual environment!
        echo Please ensure Python 3.10+ is installed and checked "Add to PATH".
        echo.
        pause
        exit /b 1
    )
    echo [Info] Virtual environment created successfully.
) else (
    echo [Info] Found existing virtual environment (venv).
)

:: 2. Determine Python executable inside venv
set PYTHON_BIN=venv\Scripts\python.exe

:: 3. Upgrade pip inside venv
echo.
echo [Info] Upgrading pip inside venv...
%PYTHON_BIN% -m pip install --upgrade pip

:: 4. Install requirements.txt
echo.
echo [Info] Installing requirements...
%PYTHON_BIN% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [Warning] Package installation encountered some errors.
    echo Please make sure you have internet access and standard build tools installed.
)

:: 5. Install Playwright Chrome
echo.
echo [Info] Installing Playwright Chromium browser...
%PYTHON_BIN% -m playwright install chrome
if errorlevel 1 (
    echo.
    echo [Warning] Playwright browser installation failed.
    echo You may need to run '%PYTHON_BIN% -m playwright install chrome' manually later.
)

echo.
echo ================================================================
echo             Installation & Setup Complete!
echo ================================================================
echo.
echo You can now run the web server dashboard using either:
echo   - Option 35 in RUN.bat
echo   - Running DEBUG_RUN.bat
echo.
pause
