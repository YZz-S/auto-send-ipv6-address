@echo off
chcp 65001 > nul
echo 正在移除IPv6地址自动发送程序的开机自启动...

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"

:: 检查配置文件是否存在
if not exist "%CONFIG_FILE%" (
    echo 错误: 配置文件不存在: %CONFIG_FILE%
    echo 无法继续操作。
    pause
    exit /b 1
)

:: 读取配置文件中的路径
echo 正在读取配置文件...
setlocal EnableDelayedExpansion

:: 获取启动文件夹路径
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "startup_folder"') do (
    set "tmp=%%b"
    set "STARTUP_FOLDER_PATH=!tmp:~2,-2!"
)

:: 获取快捷方式名称
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "shortcut_name"') do (
    set "tmp=%%b"
    set "SHORTCUT_NAME=!tmp:~2,-2!"
)

:: 获取VBS脚本名称
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "vbs_script"') do (
    set "tmp=%%b"
    set "VBS_SCRIPT_NAME=!tmp:~2,-2!"
)

:: 设置路径变量
set "STARTUP_FOLDER=%STARTUP_FOLDER_PATH%"
set "STARTUP_FOLDER=%STARTUP_FOLDER:%%APPDATA%%=%APPDATA%%%"
set "SHORTCUT=%STARTUP_FOLDER%\%SHORTCUT_NAME%"
set "VBS_SCRIPT=%SCRIPT_DIR%%VBS_SCRIPT_NAME%"
set "BAT_SCRIPT=%STARTUP_FOLDER%\start_ipv6_sender.bat"

echo 启动文件夹: %STARTUP_FOLDER%
echo 快捷方式: %SHORTCUT%
echo VBS脚本: %VBS_SCRIPT%
echo BAT脚本: %BAT_SCRIPT%

:: 删除快捷方式
if exist "%SHORTCUT%" (
    echo 正在删除快捷方式: %SHORTCUT%
    del "%SHORTCUT%" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo 警告: 无法删除快捷方式，可能需要管理员权限。
    ) else (
        echo 已成功删除快捷方式。
    )
) else (
    echo 未找到快捷方式: %SHORTCUT%
)

:: 删除VBS脚本
if exist "%VBS_SCRIPT%" (
    echo 正在删除VBS脚本: %VBS_SCRIPT%
    del "%VBS_SCRIPT%" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo 警告: 无法删除VBS脚本，可能需要管理员权限。
    ) else (
        echo 已成功删除VBS脚本。
    )
) else (
    echo 未找到VBS脚本: %VBS_SCRIPT%
)

:: 删除可能存在的BAT脚本
if exist "%BAT_SCRIPT%" (
    echo 正在删除BAT脚本: %BAT_SCRIPT%
    del "%BAT_SCRIPT%" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo 警告: 无法删除BAT脚本，可能需要管理员权限。
    ) else (
        echo 已成功删除BAT脚本。
    )
) else (
    echo 未找到BAT脚本: %BAT_SCRIPT%
)

echo.
echo 移除操作完成！
echo 如果有任何文件无法删除，请尝试以管理员身份运行此脚本。
echo.
pause