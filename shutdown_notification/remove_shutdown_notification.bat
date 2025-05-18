@echo off
chcp 65001 > nul
echo "正在移除关机通知程序..."

:: 管理员权限检查
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo "此脚本需要管理员权限来修改任务计划程序。请以管理员身份运行。"
    pause
    exit /b 1
)

:: 设置任务名称
set "TASK_NAME=IPv6ShutdownNotification"

:: 检查任务是否存在
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo "未找到名为 '%TASK_NAME%' 的任务，可能已被删除。"
    pause
    exit /b
)

:: 删除任务
echo "正在删除任务 '%TASK_NAME%'..."
schtasks /delete /tn "%TASK_NAME%" /f

:: 检查任务是否成功删除
if %errorlevel% equ 0 (
    echo "任务 '%TASK_NAME%' 已成功删除。"
) else (
    echo "任务删除失败，错误代码: %errorlevel%"
)

pause 