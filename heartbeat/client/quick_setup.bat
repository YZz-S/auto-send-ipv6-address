@echo off
chcp 65001 >nul 2>&1
echo ================================================
echo      Heartbeat Client - Quick Setup Tool
echo ================================================

echo [INFO] This tool will help you set up autostart quickly
echo [INFO] All operations use English interface to avoid encoding issues
echo.

echo Available options:
echo 1. Run environment test
echo 2. Start heartbeat client (one-time)
echo 3. Set up startup folder autostart (No permissions needed)
echo 4. Set up scheduled task autostart (May require permissions)
echo 5. Install as Windows service (requires admin)
echo 0. Exit
echo.

set /p choice="Enter your choice (0-5): "

if "%choice%"=="1" (
    echo [INFO] Running environment test...
    call test_environment.bat
    goto end
)

if "%choice%"=="2" (
    echo [INFO] Starting heartbeat client...
    call start_client.bat
    goto end
)

if "%choice%"=="3" (
    echo [INFO] Setting up startup folder autostart...
    call setup_startup_folder.bat
    goto end
)

if "%choice%"=="4" (
    echo [INFO] Setting up scheduled task autostart...
    powershell -ExecutionPolicy Bypass -File "setup_autostart_en.ps1"
    goto end
)

if "%choice%"=="5" (
    echo [INFO] Installing Windows service...
    echo [WARNING] This requires administrator privileges
    pause
    powershell -ExecutionPolicy Bypass -File "install_service.ps1"
    goto end
)

if "%choice%"=="0" (
    echo [INFO] Goodbye!
    goto end
)

echo [ERROR] Invalid choice: %choice%

:end
echo.
echo [INFO] Operation completed
pause 