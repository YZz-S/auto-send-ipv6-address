# 需要管理员权限运行
#Requires -RunAsAdministrator

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host "================================================" -ForegroundColor Blue
Write-Host "     心跳监控客户端 - Windows服务安装工具" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 检查是否以管理员身份运行
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "此脚本需要管理员权限运行"
    Write-Host "请右键点击PowerShell并选择'以管理员身份运行'" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ClientPath = Join-Path $ScriptDir "heartbeat_client.py"
$ConfigPath = Join-Path $ScriptDir "heartbeat_client_config.json"

# 服务配置
$ServiceName = "HeartbeatClient"
$ServiceDisplayName = "心跳监控客户端"
$ServiceDescription = "自动发送设备心跳信息到监控服务器"

Write-Info "检查环境..."

# 检查Python是否安装
try {
    $pythonPath = (Get-Command python).Source
    Write-Success "Python路径: $pythonPath"
} catch {
    Write-Error "未找到Python，请确保Python已安装并添加到PATH"
    Read-Host "按回车键退出"
    exit 1
}

# 检查客户端文件
if (-not (Test-Path $ClientPath)) {
    Write-Error "未找到客户端文件: $ClientPath"
    Read-Host "按回车键退出"
    exit 1
}

# 检查配置文件
if (-not (Test-Path $ConfigPath)) {
    Write-Warning "配置文件不存在，请先运行 start_client.ps1 创建配置"
    Read-Host "按回车键退出"
    exit 1
}

# 创建服务包装脚本
$ServiceScript = @"
import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# 设置工作目录
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def run_client():
    """运行心跳客户端"""
    while True:
        try:
            logging.info("启动心跳客户端...")
            result = subprocess.run([sys.executable, 'heartbeat_client.py'], 
                                  capture_output=False, 
                                  text=True)
            
            if result.returncode == 0:
                logging.info("客户端正常退出")
                break
            else:
                logging.warning(f"客户端异常退出，返回码: {result.returncode}")
                logging.info("10秒后重启...")
                time.sleep(10)
                
        except Exception as e:
            logging.error(f"启动客户端时发生异常: {e}")
            logging.info("10秒后重试...")
            time.sleep(10)

if __name__ == "__main__":
    run_client()
"@

$ServiceScriptPath = Join-Path $ScriptDir "service_wrapper.py"
$ServiceScript | Out-File -FilePath $ServiceScriptPath -Encoding UTF8

# 检查服务是否已存在
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Warning "服务 '$ServiceName' 已存在"
    $choice = Read-Host "是否要重新安装? (y/N)"
    if ($choice.ToLower() -ne 'y') {
        Write-Info "安装已取消"
        exit 0
    }
    
    Write-Info "停止现有服务..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    
    Write-Info "删除现有服务..."
    sc.exe delete $ServiceName
    Start-Sleep -Seconds 2
}

# 安装NSSM（如果未安装）
$nssmPath = Join-Path $ScriptDir "nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Info "下载NSSM服务管理工具..."
    try {
        # 这里可以添加下载NSSM的逻辑，或者提示用户手动下载
        Write-Warning "请手动下载NSSM (Non-Sucking Service Manager)"
        Write-Host "下载地址: https://nssm.cc/download" -ForegroundColor Yellow
        Write-Host "将nssm.exe放在客户端目录中" -ForegroundColor Yellow
        Read-Host "下载完成后按回车继续"
        
        if (-not (Test-Path $nssmPath)) {
            Write-Error "未找到nssm.exe文件"
            exit 1
        }
    } catch {
        Write-Error "无法下载NSSM: $_"
        exit 1
    }
}

# 使用NSSM安装服务
Write-Info "安装Windows服务..."
try {
    # 安装服务
    & $nssmPath install $ServiceName $pythonPath $ServiceScriptPath
    
    # 设置服务描述
    & $nssmPath set $ServiceName Description $ServiceDescription
    
    # 设置服务启动目录
    & $nssmPath set $ServiceName AppDirectory $ScriptDir
    
    # 设置输出重定向
    $logDir = Join-Path $ScriptDir "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir | Out-Null
    }
    
    & $nssmPath set $ServiceName AppStdout (Join-Path $logDir "service_output.log")
    & $nssmPath set $ServiceName AppStderr (Join-Path $logDir "service_error.log")
    
    # 设置自动重启
    & $nssmPath set $ServiceName AppRestartDelay 10000
    & $nssmPath set $ServiceName AppExit Default Restart
    
    Write-Success "服务安装成功!"
    
    # 启动服务
    Write-Info "启动服务..."
    Start-Service -Name $ServiceName
    
    Write-Success "服务已启动!"
    Write-Info "服务名称: $ServiceName"
    Write-Info "显示名称: $ServiceDisplayName"
    Write-Info "状态: $($(Get-Service -Name $ServiceName).Status)"
    
} catch {
    Write-Error "安装服务失败: $_"
    exit 1
}

Write-Host ""
Write-Success "=== 安装完成 ==="
Write-Host "服务管理命令:" -ForegroundColor Yellow
Write-Host "  启动服务: Start-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  停止服务: Stop-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  重启服务: Restart-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  查看状态: Get-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  卸载服务: .\uninstall_service.ps1" -ForegroundColor White
Write-Host ""

Read-Host "按回车键退出" 