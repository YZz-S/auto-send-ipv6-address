@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo         心跳监控客户端启动脚本 (Windows)
echo ================================================

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH环境变量
    echo 请安装Python 3.6或更高版本
    pause
    exit /b 1
)

REM 检查配置文件是否存在
if not exist "heartbeat_client_config.json" (
    echo 配置文件不存在，正在创建示例配置...
    python heartbeat_client.py --create-example
    if errorlevel 1 (
        echo 创建示例配置失败
        pause
        exit /b 1
    )
    echo.
    echo 请编辑 heartbeat_client_config_example.json 文件
    echo 并重命名为 heartbeat_client_config.json
    echo 配置服务器地址等信息后重新运行此脚本
    echo.
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查Python依赖...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 安装依赖失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo 正在启动心跳客户端...
echo 按 Ctrl+C 停止客户端
echo.

REM 启动客户端（带重启机制）
:restart
python heartbeat_client.py
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% equ 0 (
    echo 客户端正常退出
    goto end
) else (
    echo 客户端异常退出，错误代码: %EXIT_CODE%
    echo 10秒后自动重启...
    timeout /t 10 /nobreak >nul
    goto restart
)

:end
echo 按任意键退出...
pause >nul 