@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ==============================================
REM iStoreOS 心跳监控服务器 Docker 一键更新脚本 (Windows版本)
REM 支持代码更新、重新构建和重启服务
REM ==============================================

REM 脚本配置
set "SCRIPT_DIR=%~dp0"
set "PROJECT_NAME=heartbeat-server"
set "IMAGE_NAME=heartbeat-server:latest"
set "CONTAINER_NAME=heartbeat-server"
set "COMPOSE_FILE=%SCRIPT_DIR%docker-compose.yml"
set "BACKUP_DIR=%SCRIPT_DIR%backup"
set "LOG_FILE=%SCRIPT_DIR%update.log"

REM 显示标题
echo ===============================================
echo 🚀 心跳监控服务器 Docker 一键更新脚本
echo ===============================================
echo.

REM 创建日志文件
if not exist "%SCRIPT_DIR%backup" mkdir "%SCRIPT_DIR%backup" >nul 2>&1
echo ============================================= > "%LOG_FILE%"
echo Docker 更新日志 - %date% %time% >> "%LOG_FILE%"
echo ============================================= >> "%LOG_FILE%"

REM 检查Docker
echo [INFO] 检查 Docker 服务状态...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker 未安装或未找到
    echo [ERROR] Docker 未安装或未找到 >> "%LOG_FILE%"
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker 服务未运行，请启动 Docker 服务
    echo [ERROR] Docker 服务未运行 >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [SUCCESS] Docker 环境检查通过
echo [SUCCESS] Docker 环境检查通过 >> "%LOG_FILE%"

REM 备份数据
echo [INFO] 备份当前配置和数据...
set "BACKUP_TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_TIMESTAMP=!BACKUP_TIMESTAMP: =0!"
set "CURRENT_BACKUP_DIR=%BACKUP_DIR%\backup_!BACKUP_TIMESTAMP!"

if not exist "!CURRENT_BACKUP_DIR!" mkdir "!CURRENT_BACKUP_DIR!" >nul 2>&1

if exist "%SCRIPT_DIR%data" (
    xcopy "%SCRIPT_DIR%data" "!CURRENT_BACKUP_DIR!\data\" /E /I /Q >nul 2>&1
    echo [SUCCESS] 数据目录已备份到: !CURRENT_BACKUP_DIR!\data
    echo [SUCCESS] 数据目录已备份到: !CURRENT_BACKUP_DIR!\data >> "%LOG_FILE%"
)

REM 停止现有容器
echo [INFO] 停止现有容器...
docker ps --format "table {{.Names}}" | findstr /C:"%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] 停止运行中的容器: %CONTAINER_NAME%
    docker stop "%CONTAINER_NAME%" >nul 2>&1
    echo [SUCCESS] 容器已停止
    echo [SUCCESS] 容器已停止 >> "%LOG_FILE%"
)

docker ps -a --format "table {{.Names}}" | findstr /C:"%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] 删除现有容器: %CONTAINER_NAME%
    docker rm "%CONTAINER_NAME%" >nul 2>&1
    echo [SUCCESS] 容器已删除
    echo [SUCCESS] 容器已删除 >> "%LOG_FILE%"
)

REM 清理旧镜像
echo [INFO] 清理旧镜像...
for /f "tokens=3" %%i in ('docker images -f "dangling=true" -q') do (
    docker rmi %%i >nul 2>&1
)
echo [SUCCESS] 已清理悬空镜像
echo [SUCCESS] 已清理悬空镜像 >> "%LOG_FILE%"

REM 重新构建镜像
echo [INFO] 重新构建 Docker 镜像...
cd /d "%SCRIPT_DIR%"

if exist "%COMPOSE_FILE%" (
    docker-compose build --no-cache
) else (
    docker build --no-cache -t "%IMAGE_NAME%" .
)

if errorlevel 1 (
    echo [ERROR] 镜像构建失败
    echo [ERROR] 镜像构建失败 >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [SUCCESS] 镜像构建成功
echo [SUCCESS] 镜像构建成功 >> "%LOG_FILE%"

REM 启动新容器
echo [INFO] 启动新容器...

if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data" >nul 2>&1

if exist "%COMPOSE_FILE%" (
    docker-compose up -d
) else (
    docker run -d ^
        --name "%CONTAINER_NAME%" ^
        --restart unless-stopped ^
        -p 18080:8080 ^
        -v "%SCRIPT_DIR%data:/data" ^
        -e TZ=Asia/Shanghai ^
        -e CONFIG_PATH=/data/heartbeat_config.json ^
        -e STATUS_PATH=/data/heartbeat_status.json ^
        -e LOG_PATH=/data/heartbeat_server.log ^
        "%IMAGE_NAME%"
)

if errorlevel 1 (
    echo [ERROR] 容器启动失败
    echo [ERROR] 容器启动失败 >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [SUCCESS] 容器启动成功
echo [SUCCESS] 容器启动成功 >> "%LOG_FILE%"

REM 检查服务状态
echo [INFO] 检查服务状态...
timeout /t 10 /nobreak >nul

docker ps --format "table {{.Names}}" | findstr /C:"%CONTAINER_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 容器未运行
    echo [ERROR] 容器未运行 >> "%LOG_FILE%"
    echo 最近的容器日志:
    docker logs "%CONTAINER_NAME%" --tail 20
    pause
    exit /b 1
)

echo [SUCCESS] ✅ 容器运行正常

REM 检查服务启动
docker logs "%CONTAINER_NAME%" --tail 20 | findstr /C:"心跳监控服务器启动成功" >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] ✅ 服务启动成功
    echo.
    echo 服务信息:
    echo   📡 心跳接收地址: http://localhost:18080/heartbeat
    echo   🖥️  监控页面: http://localhost:18080/
    echo   📊 Docker 日志: docker logs -f %CONTAINER_NAME%
) else (
    echo [WARN] ⚠️  服务可能未完全启动，请检查日志
    echo 最近的容器日志:
    docker logs "%CONTAINER_NAME%" --tail 20
)

REM 显示最终状态
echo.
echo ==============================================
echo 📊 更新完成状态
echo ==============================================
echo.
echo 容器状态:
docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo 镜像信息:
docker images --filter "reference=%PROJECT_NAME%" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo.
echo 日志位置:
echo   - 容器日志: docker logs -f %CONTAINER_NAME%
echo   - 应用日志: %SCRIPT_DIR%data\heartbeat_server.log
echo   - 更新日志: %LOG_FILE%
echo.
echo 访问地址:
echo   - 心跳接收: http://localhost:18080/heartbeat
echo   - 监控页面: http://localhost:18080/
echo.
echo [SUCCESS] 🎉 Docker 更新流程完成！
echo [SUCCESS] 🎉 Docker 更新流程完成！ >> "%LOG_FILE%"

echo.
echo 按任意键退出...
pause >nul 