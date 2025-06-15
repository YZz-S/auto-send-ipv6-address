@echo off
chcp 65001 > nul
echo 正在创建智能关机工具的快捷方式...

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "BATCH_SCRIPT=%SCRIPT_DIR%smart_shutdown.bat"

:: 检查批处理脚本是否存在
if not exist "%BATCH_SCRIPT%" (
    echo 错误: 找不到 %BATCH_SCRIPT%
    pause
    exit /b 1
)

:: 创建临时VBS脚本来创建快捷方式
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sDesktop = oWS.SpecialFolders("Desktop") >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sDesktop ^& "\智能关机工具.lnk") >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%BATCH_SCRIPT%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "在关机前发送邮件通知" >> "%VBS_SCRIPT%"
echo oLink.IconLocation = "%%SystemRoot%%\System32\shell32.dll,27" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

:: 执行VBS脚本
cscript //nologo "%VBS_SCRIPT%"

:: 清理临时文件
del "%VBS_SCRIPT%"

echo.
echo 已在桌面创建"智能关机工具"快捷方式！
pause 