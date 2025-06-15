@echo off
REM 设置代码页为UTF-8
chcp 65001 >nul 2>&1

echo ================================================
echo         心跳监控客户端启动脚本 (Windows)
echo ================================================

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查Python是否安装
echo [信息] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH环境变量
    echo [提示] 请安装Python 3.6或更高版本
    pause
    exit /b 1
)

REM 检查配置文件是否存在
echo [信息] 检查配置文件...
if not exist "heartbeat_client_config.json" (
    echo [警告] 配置文件不存在，正在创建示例配置...
    python heartbeat_client.py --create-example
    if errorlevel 1 (
        echo [错误] 创建示例配置失败
        pause
        exit /b 1
    )
    echo.
    echo [提示] 请编辑 heartbeat_client_config_example.json 文件
    echo [提示] 并重命名为 heartbeat_client_config.json
    echo [提示] 配置服务器地址等信息后重新运行此脚本
    echo.
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo [信息] 检查Python依赖包...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 安装依赖失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [成功] 依赖包安装完成
)

echo [成功] 环境检查完成
echo [信息] 正在启动心跳客户端...
echo [提示] 按 Ctrl+C 停止客户端
echo.

REM 启动客户端（带重启机制）
set /a RESTART_COUNT=0
set /a MAX_RESTARTS=10

:restart
set /a RESTART_COUNT+=1
if %RESTART_COUNT% gtr 1 (
    echo [信息] 第 %RESTART_COUNT% 次启动尝试...
)

python heartbeat_client.py
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% equ 0 (
    echo [信息] 客户端正常退出
    goto end
) else (
    echo [警告] 客户端异常退出，错误代码: %EXIT_CODE%
    
    if %RESTART_COUNT% lss %MAX_RESTARTS% (
        echo [信息] 10秒后自动重启...
        timeout /t 10 /nobreak >nul
        goto restart
    ) else (
        echo [错误] 重启次数已达上限 (%MAX_RESTARTS% 次)，程序终止
        goto end
    )
)

:end
echo [信息] 程序结束
echo 按任意键退出...
pause >nul 