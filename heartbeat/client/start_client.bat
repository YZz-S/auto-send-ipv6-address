@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo         Heartbeat Client Startup Script
echo ================================================

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is installed
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher
    pause
    exit /b 1
)

REM Check if config file exists
echo Checking config file...
if not exist "heartbeat_client_config.json" (
    echo Config file not found, creating example config...
    python heartbeat_client.py --create-example
    if errorlevel 1 (
        echo Failed to create example config
        pause
        exit /b 1
    )
    echo.
    echo Please edit heartbeat_client_config_example.json
    echo and rename it to heartbeat_client_config.json
    echo Configure server address and other settings
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking Python dependencies...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies, check network connection
        pause
        exit /b 1
    )
)

echo Starting heartbeat client...
echo Press Ctrl+C to stop the client
echo.

REM Start client with restart mechanism
:restart
python heartbeat_client.py
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% equ 0 (
    echo Client exited normally
    goto end
) else (
    echo Client exited with error code: %EXIT_CODE%
    echo Restarting in 10 seconds...
    timeout /t 10 /nobreak >nul
    goto restart
)

:end
echo Press any key to exit...
pause >nul 