@echo off
chcp 65001 > nul
echo "正在设置关机通知程序..."

:: 管理员权限检查
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo "此脚本需要管理员权限来设置任务计划程序。请以管理员身份运行。"
    pause
    exit /b 1
)

:: 获取当前脚本所在的绝对路径
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"
set "PYTHON_SCRIPT=%SCRIPT_DIR%shutdown_notification.py"

:: 检查Python脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo "错误: 找不到 %PYTHON_SCRIPT%"
    pause
    exit /b 1
)

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo "警告: 未检测到Python安装。请确保已安装Python并将其添加到系统PATH中。"
    pause
    exit /b 1
)

:: 安装所需的Python库
echo "正在安装所需的Python库..."
pip install -r "%SCRIPT_DIR%requirements.txt"

:: 设置任务名称
set "TASK_NAME=IPv6ShutdownNotification"

:: 删除现有的任务（如果存在）
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo "发现现有的关机通知任务，正在删除..."
    schtasks /delete /tn "%TASK_NAME%" /f
)

:: 创建临时XML文件来定义任务
set "XML_FILE=%TEMP%\shutdown_task.xml"
echo ^<?xml version="1.0" encoding="UTF-16"?^> > "%XML_FILE%"
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^> >> "%XML_FILE%"
echo   ^<RegistrationInfo^> >> "%XML_FILE%"
echo     ^<Description^>在系统关机时发送IPv6地址邮件通知^</Description^> >> "%XML_FILE%"
echo   ^</RegistrationInfo^> >> "%XML_FILE%"
echo   ^<Triggers^> >> "%XML_FILE%"
echo     ^<EventTrigger^> >> "%XML_FILE%"
echo       ^<Enabled^>true^</Enabled^> >> "%XML_FILE%"
echo       ^<Subscription^>^<QueryList^>^<Query Id="0" Path="System"^>^<Select Path="System"^>*[System[Provider[@Name='User32'] and (EventID=1074)]]^</Select^>^</Query^>^</QueryList^>^</Subscription^> >> "%XML_FILE%"
echo     ^</EventTrigger^> >> "%XML_FILE%"
echo   ^</Triggers^> >> "%XML_FILE%"
echo   ^<Principals^> >> "%XML_FILE%"
echo     ^<Principal id="Author"^> >> "%XML_FILE%"
echo       ^<UserId^>S-1-5-18^</UserId^> >> "%XML_FILE%"
echo       ^<RunLevel^>HighestAvailable^</RunLevel^> >> "%XML_FILE%"
echo     ^</Principal^> >> "%XML_FILE%"
echo   ^</Principals^> >> "%XML_FILE%"
echo   ^<Settings^> >> "%XML_FILE%"
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^> >> "%XML_FILE%"
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^> >> "%XML_FILE%"
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^> >> "%XML_FILE%"
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^> >> "%XML_FILE%"
echo     ^<StartWhenAvailable^>false^</StartWhenAvailable^> >> "%XML_FILE%"
echo     ^<RunOnlyIfNetworkAvailable^>true^</RunOnlyIfNetworkAvailable^> >> "%XML_FILE%"
echo     ^<IdleSettings^> >> "%XML_FILE%"
echo       ^<StopOnIdleEnd^>true^</StopOnIdleEnd^> >> "%XML_FILE%"
echo       ^<RestartOnIdle^>false^</RestartOnIdle^> >> "%XML_FILE%"
echo     ^</IdleSettings^> >> "%XML_FILE%"
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^> >> "%XML_FILE%"
echo     ^<Enabled^>true^</Enabled^> >> "%XML_FILE%"
echo     ^<Hidden^>false^</Hidden^> >> "%XML_FILE%"
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^> >> "%XML_FILE%"
echo     ^<WakeToRun^>false^</WakeToRun^> >> "%XML_FILE%"
echo     ^<ExecutionTimeLimit^>PT5M^</ExecutionTimeLimit^> >> "%XML_FILE%"
echo     ^<Priority^>7^</Priority^> >> "%XML_FILE%"
echo   ^</Settings^> >> "%XML_FILE%"
echo   ^<Actions Context="Author"^> >> "%XML_FILE%"
echo     ^<Exec^> >> "%XML_FILE%"
echo       ^<Command^>python^</Command^> >> "%XML_FILE%"
echo       ^<Arguments^>"%PYTHON_SCRIPT%"^</Arguments^> >> "%XML_FILE%"
echo       ^<WorkingDirectory^>%SCRIPT_DIR%^</WorkingDirectory^> >> "%XML_FILE%"
echo     ^</Exec^> >> "%XML_FILE%"
echo   ^</Actions^> >> "%XML_FILE%"
echo ^</Task^> >> "%XML_FILE%"

:: 导入任务
echo "正在创建计划任务..."
schtasks /create /tn "%TASK_NAME%" /xml "%XML_FILE%" /f

:: 检查任务是否成功创建
if %errorlevel% equ 0 (
    echo "任务 '%TASK_NAME%' 已成功创建。"
) else (
    echo "任务创建失败，错误代码: %errorlevel%"
)

:: 清理临时文件
del "%XML_FILE%"

echo "设置完成！关机通知程序将在系统关机时自动运行。"
echo "请确保已修改 config.json 文件中的邮箱设置！"

pause 