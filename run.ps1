# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "================================================================" -ForegroundColor Green
Write-Host "                V I D E O   F A C T O R Y" -ForegroundColor Green
Write-Host "            PowerShell Startup Native Script" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

$pythonExe = "python"
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "[Info] Using local virtual environment (venv)..." -ForegroundColor Cyan
    $pythonExe = "venv\Scripts\python.exe"
} else {
    Write-Host "[Warning] Virtual environment not found. Using system Python..." -ForegroundColor Yellow
}

Write-Host "[Info] Starting Web Dashboard Server..." -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------"
& $pythonExe "src/web/server.py"
