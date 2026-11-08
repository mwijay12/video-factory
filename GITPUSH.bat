@echo off
:: Commit and push VideoFactory to GitHub (run from anywhere; uses script folder)
cd /d "%~dp0"
title VideoFactory - Git Push

echo ================================================================
echo                 V I D E O F A C T O R Y  -  GIT PUSH
echo ================================================================
echo.

if not exist ".git" (
    echo [Error] This script must live in the repo root.
    pause
    exit /b 1
)

echo [1/4] Staging changes...
git add -A
if errorlevel 1 goto FAIL

echo.
echo [2/4] Pending commit summary:
git status --short
echo.

set /p msg="Commit message: "
if "%msg%"=="" set msg=chore: update VideoFactory

echo.
echo [3/4] Committing...
git commit -m "%msg%"
if errorlevel 1 (
    echo [Info] Nothing to commit (or commit failed).
)

echo.
echo [4/4] Pushing current branch to origin...
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%b
git push origin %BRANCH%
if errorlevel 1 goto FAIL

echo.
echo Push complete! Branch: %BRANCH%
pause
exit /b 0

:FAIL
echo.
echo [Error] Git command failed. Review the output above.
pause
exit /b 1
