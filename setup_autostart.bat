@echo off
chcp 65001 > nul
echo "正在设置自动启动..."

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"

:: 检查快捷方式是否已存在
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "startup_folder"') do (
    set "tmp=%%b"
    set "STARTUP_FOLDER_PATH=!tmp:~2,-2!"
)
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "shortcut_name"') do (
    set "tmp=%%b"
    set "SHORTCUT_NAME=!tmp:~2,-2!"
)
set "STARTUP_FOLDER=%STARTUP_FOLDER_PATH%"
set "SHORTCUT=%STARTUP_FOLDER%\%SHORTCUT_NAME%"

if exist "%SHORTCUT%" (
    echo "检测到程序已经设置为开机启动。"
    echo "如需重新设置，请先删除现有的快捷方式: %SHORTCUT%"
    echo "或者直接继续以更新现有设置。"
    choice /C YN /M "是否继续更新设置？(Y/N)"
    if errorlevel 2 (
        echo "操作已取消。"
        pause
        exit /b
    )
)

:: 读取配置文件中的路径
echo "正在读取配置文件..."
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "python_script"') do (
    set "tmp=%%b"
    set "PYTHON_SCRIPT_NAME=!tmp:~2,-2!"
)
for /f "tokens=1,* delims=:" %%a in ('type "%CONFIG_FILE%" ^| findstr "vbs_script"') do (
    set "tmp=%%b"
    set "VBS_SCRIPT_NAME=!tmp:~2,-2!"
)

:: 设置各路径变量
set "PYTHON_SCRIPT=%SCRIPT_DIR%%PYTHON_SCRIPT_NAME%"
set "VBS_SCRIPT=%SCRIPT_DIR%%VBS_SCRIPT_NAME%"

echo "Python脚本: %PYTHON_SCRIPT%"
echo "VBS脚本: %VBS_SCRIPT%"
echo "启动文件夹: %STARTUP_FOLDER%"
echo "快捷方式: %SHORTCUT%"

:: 创建VBS文件并支持UTF-8
> "%VBS_SCRIPT%" echo Option Explicit
>> "%VBS_SCRIPT%" echo '支持UTF-8和中文路径
>> "%VBS_SCRIPT%" echo Set WshShell = CreateObject("WScript.Shell")
>> "%VBS_SCRIPT%" echo Dim strCommand
>> "%VBS_SCRIPT%" echo strCommand = "pythonw """ & """%PYTHON_SCRIPT:"=%%""" & """"
>> "%VBS_SCRIPT%" echo WshShell.Run strCommand, 0, False

:: 创建开机启动快捷方式
if not exist "%STARTUP_FOLDER%" mkdir "%STARTUP_FOLDER%"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%VBS_SCRIPT%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "IPv6 Address Sender" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"
cscript /nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo "警告: 未检测到Python安装。请确保已安装Python并将其添加到系统PATH中。"
    pause
    exit /b
)

:: 安装所需的Python库
echo "正在安装所需的Python库..."
pip install -r "%SCRIPT_DIR%requirements.txt"

echo "设置完成！程序将在下次系统启动时自动运行。"
echo "您也可以通过运行 %VBS_SCRIPT_NAME% 手动启动程序。"
echo "请确保已修改 config.json 文件中的邮箱设置！"

pause