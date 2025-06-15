@echo off
echo ================================================
echo      Heartbeat Client - Startup Folder Setup
echo ================================================

echo [INFO] This method adds the client to your startup folder
echo [INFO] No special permissions required
echo [INFO] Client will start when you log in to Windows
echo.

REM Get current directory
set "SCRIPT_DIR=%~dp0"

REM Check if PowerShell startup script exists
if not exist "%SCRIPT_DIR%start_client.ps1" (
    echo [ERROR] start_client.ps1 not found in current directory
    echo [INFO] Please make sure all files are in the same folder
    pause
    exit /b 1
)

REM Create VBS script for hidden startup
echo [INFO] Creating startup script...
echo Set WshShell = CreateObject("WScript.Shell") > "%SCRIPT_DIR%start_client_hidden.vbs"
echo WshShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""%SCRIPT_DIR%start_client.ps1""", 0, False >> "%SCRIPT_DIR%start_client_hidden.vbs"

REM Get startup folder path
for /f "tokens=3*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%i %%j"

if "%STARTUP_FOLDER%"=="" (
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)

echo [INFO] Startup folder: %STARTUP_FOLDER%

REM Create shortcut in startup folder
echo [INFO] Creating startup shortcut...
powershell -Command "& {$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\HeartbeatClient.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%start_client_hidden.vbs'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'Heartbeat Client Autostart'; $Shortcut.Save()}"

if errorlevel 1 (
    echo [ERROR] Failed to create startup shortcut
    echo [INFO] You can manually copy start_client_hidden.vbs to your startup folder:
    echo [INFO] %STARTUP_FOLDER%
    pause
    exit /b 1
)

echo [SUCCESS] Startup shortcut created successfully!
echo [INFO] The heartbeat client will now start automatically when you log in
echo [INFO] Shortcut location: %STARTUP_FOLDER%\HeartbeatClient.lnk
echo.

echo [INFO] To remove autostart:
echo   1. Delete the shortcut: %STARTUP_FOLDER%\HeartbeatClient.lnk
echo   2. Delete the VBS file: %SCRIPT_DIR%start_client_hidden.vbs
echo.

echo [INFO] To test the startup:
echo   1. Log out and log back in, or
echo   2. Double-click the shortcut in your startup folder
echo.

pause 