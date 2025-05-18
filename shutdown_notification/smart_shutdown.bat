@echo off
chcp 65001 > nul
echo 智能关机工具

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%shutdown_helper.py"

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

echo.
echo 请选择操作:
echo 1. 关机
echo 2. 重启
echo 3. 注销
echo 4. 取消
echo.

set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" (
    set operation=shutdown
    set operation_name=关机
) else if "%choice%"=="2" (
    set operation=restart
    set operation_name=重启
) else if "%choice%"=="3" (
    set operation=logoff
    set operation_name=注销
) else if "%choice%"=="4" (
    echo 操作已取消。
    pause
    exit /b 0
) else (
    echo 无效的选项，操作已取消。
    pause
    exit /b 1
)

echo.
echo 请设置延迟时间 (默认为60秒)
set /p delay_time=请输入延迟时间 (秒): 

if "%delay_time%"=="" set delay_time=60

echo.
echo 将在发送邮件通知后执行%operation_name%操作，延迟%delay_time%秒...
echo 按任意键继续或按Ctrl+C取消...
pause > nul

:: 执行Python脚本
python "%PYTHON_SCRIPT%" --type %operation% --delay %delay_time%

if %ERRORLEVEL% NEQ 0 (
    echo 操作未成功完成，请查看日志了解详情。
    pause
)

exit /b 