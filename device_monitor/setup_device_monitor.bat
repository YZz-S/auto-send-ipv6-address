@echo off
chcp 65001 > nul
echo 设备监控服务设置工具

:: 管理员权限检查
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 此脚本需要管理员权限来设置系统服务。请以管理员身份运行。
    pause
    exit /b 1
)

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%device_monitor.py"
set "CONFIG_FILE=%SCRIPT_DIR%monitor_config.json"

:: 检查Python脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 找不到 %PYTHON_SCRIPT%
    pause
    exit /b 1
)

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 警告: 未检测到Python安装。请确保已安装Python并将其添加到系统PATH中。
    pause
    exit /b 1
)

:: 检查配置文件是否存在，如不存在则创建示例配置
if not exist "%CONFIG_FILE%" (
    echo 未找到配置文件，正在创建示例配置...
    python "%PYTHON_SCRIPT%" --create-example
    if exist "monitor_config_example.json" (
        copy "monitor_config_example.json" "%CONFIG_FILE%"
        echo 已创建配置文件: %CONFIG_FILE%
        echo 请在继续前编辑配置文件，设置正确的邮箱信息和设备列表。
        notepad "%CONFIG_FILE%"
    ) else (
        echo 创建示例配置失败。
        pause
        exit /b 1
    )
)

echo.
echo 请选择安装类型:
echo 1. 设置为系统服务（推荐，开机自动运行）
echo 2. 创建开机启动项
echo 3. 创建桌面快捷方式
echo 4. 取消安装
echo.

set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" (
    goto install_service
) else if "%choice%"=="2" (
    goto create_startup
) else if "%choice%"=="3" (
    goto create_shortcut
) else if "%choice%"=="4" (
    echo 安装已取消。
    pause
    exit /b 0
) else (
    echo 无效的选项，安装已取消。
    pause
    exit /b 1
)

:install_service
echo 正在创建系统服务...

:: 使用 NSSM (Non-Sucking Service Manager) 来创建服务
if not exist "%SCRIPT_DIR%\nssm.exe" (
    echo 未找到 NSSM 工具，正在下载...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"
    if %PROCESSOR_ARCHITECTURE%==AMD64 (
        copy "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" "%SCRIPT_DIR%"
    ) else (
        copy "%TEMP%\nssm\nssm-2.24\win32\nssm.exe" "%SCRIPT_DIR%"
    )
    del "%TEMP%\nssm.zip"
    rmdir /s /q "%TEMP%\nssm"
)

:: 检查是否成功下载nssm
if not exist "%SCRIPT_DIR%\nssm.exe" (
    echo 无法获取NSSM工具，请手动下载: https://nssm.cc/download
    goto alternative_service
)

:: 使用nssm创建服务
"%SCRIPT_DIR%\nssm.exe" install DeviceMonitor "%SystemRoot%\System32\cmd.exe" "/c python \"%PYTHON_SCRIPT%\" --config \"%CONFIG_FILE%\""
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor DisplayName "设备监控服务"
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor Description "监控设备在线状态并在设备离线时发送通知"
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor AppDirectory "%SCRIPT_DIR%"
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor AppStdout "%SCRIPT_DIR%\service_output.log"
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor AppStderr "%SCRIPT_DIR%\service_error.log"
"%SCRIPT_DIR%\nssm.exe" set DeviceMonitor Start SERVICE_AUTO_START

:: 启动服务
net start DeviceMonitor

echo 设备监控服务已安装并启动。
pause
exit /b 0

:alternative_service
echo 使用Windows任务计划程序创建自动启动任务...

:: 创建批处理文件来运行Python脚本
set "RUN_SCRIPT=%SCRIPT_DIR%run_device_monitor.bat"
echo @echo off > "%RUN_SCRIPT%"
echo cd /d "%SCRIPT_DIR%" >> "%RUN_SCRIPT%"
echo python "%PYTHON_SCRIPT%" --config "%CONFIG_FILE%" >> "%RUN_SCRIPT%"

:: 创建任务
schtasks /create /tn "DeviceMonitor" /tr "%RUN_SCRIPT%" /sc onstart /ru SYSTEM /f
if %ERRORLEVEL% NEQ 0 (
    echo 创建任务失败。
    pause
    exit /b 1
)

echo 设备监控任务已创建，将在系统启动时运行。
echo 您也可以手动运行任务：schtasks /run /tn "DeviceMonitor"
pause
exit /b 0

:create_startup
echo 正在创建开机启动项...

:: 创建批处理文件
set "STARTUP_SCRIPT=%SCRIPT_DIR%run_device_monitor.bat"
echo @echo off > "%STARTUP_SCRIPT%"
echo cd /d "%SCRIPT_DIR%" >> "%STARTUP_SCRIPT%"
echo start /min python "%PYTHON_SCRIPT%" --config "%CONFIG_FILE%" >> "%STARTUP_SCRIPT%"

:: 创建VBS脚本，用于隐藏命令窗口
set "VBS_SCRIPT=%TEMP%\create_startup.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sStartup = oWS.SpecialFolders("Startup") >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sStartup ^& "\DeviceMonitor.lnk") >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%STARTUP_SCRIPT%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "设备监控服务" >> "%VBS_SCRIPT%"
echo oLink.WindowStyle = 7 >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

:: 执行VBS脚本
cscript //nologo "%VBS_SCRIPT%"

:: 清理临时文件
del "%VBS_SCRIPT%"

echo 已创建开机启动项。
pause
exit /b 0

:create_shortcut
echo 正在创建桌面快捷方式...

:: 创建批处理文件
set "SHORTCUT_SCRIPT=%SCRIPT_DIR%run_device_monitor.bat"
echo @echo off > "%SHORTCUT_SCRIPT%"
echo cd /d "%SCRIPT_DIR%" >> "%SHORTCUT_SCRIPT%"
echo python "%PYTHON_SCRIPT%" --config "%CONFIG_FILE%" >> "%SHORTCUT_SCRIPT%"

:: 创建VBS脚本来创建快捷方式
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sDesktop = oWS.SpecialFolders("Desktop") >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sDesktop ^& "\设备监控.lnk") >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%SHORTCUT_SCRIPT%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "监控设备在线状态" >> "%VBS_SCRIPT%"
echo oLink.IconLocation = "%%SystemRoot%%\System32\SHELL32.dll,16" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

:: 执行VBS脚本
cscript //nologo "%VBS_SCRIPT%"

:: 清理临时文件
del "%VBS_SCRIPT%"

echo 已在桌面创建"设备监控"快捷方式！
pause
exit /b 0 