@echo off
echo 正在设置自动启动...

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%auto_send_ipv6.py"

:: 使用VBS脚本创建一个后台运行的启动器
set "VBS_SCRIPT=%SCRIPT_DIR%start_ipv6_sender.vbs"

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo WshShell.Run "pythonw ""%PYTHON_SCRIPT%""", 0, False >> "%VBS_SCRIPT%"

:: 创建开机启动快捷方式
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\IPv6地址发送器.lnk"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%VBS_SCRIPT%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "IPv6地址自动发送程序" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"
cscript /nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 警告: 未检测到Python安装。请确保已安装Python并将其添加到系统PATH中。
    pause
    exit /b
)

:: 安装所需的Python库
echo 正在安装所需的Python库...
pip install socket smtplib

echo 设置完成！程序将在下次系统启动时自动运行。
echo 您也可以通过运行 start_ipv6_sender.vbs 手动启动程序。
echo 请确保先修改 config.json 文件中的邮箱设置！

pause 