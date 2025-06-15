# 需要管理员权限运行
#Requires -RunAsAdministrator

# 设置错误处理和编码
$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $Host.UI.RawUI.OutputEncoding = [System.Text.Encoding]::UTF8
    # 尝试设置控制台代码页为UTF-8
    chcp 65001 | Out-Null
} catch {
    Write-Host "Warning: Could not set UTF-8 encoding" -ForegroundColor Yellow
}

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
Write-Host "     心跳监控客户端 - Windows服务卸载工具" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 检查是否以管理员身份运行
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "此脚本需要管理员权限运行"
    Write-Host "请右键点击PowerShell并选择'以管理员身份运行'" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 服务配置
$ServiceName = "HeartbeatClient"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$nssmPath = Join-Path $ScriptDir "nssm.exe"

# 检查服务是否存在
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $existingService) {
    Write-Warning "服务 '$ServiceName' 不存在"
    Read-Host "按回车键退出"
    exit 0
}

Write-Info "当前服务状态: $($existingService.Status)"

# 确认卸载
Write-Warning "即将卸载心跳监控客户端服务"
$choice = Read-Host "确定要继续吗? (y/N)"
if ($choice.ToLower() -ne 'y') {
    Write-Info "卸载已取消"
    exit 0
}

try {
    # 停止服务
    Write-Info "停止服务..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    
    # 使用NSSM卸载服务（如果NSSM存在）
    if (Test-Path $nssmPath) {
        Write-Info "使用NSSM卸载服务..."
        & $nssmPath remove $ServiceName confirm
    } else {
        # 使用sc命令卸载服务
        Write-Info "卸载服务..."
        sc.exe delete $ServiceName
    }
    
    Start-Sleep -Seconds 2
    
    # 验证服务是否已删除
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Warning "服务可能未完全删除，请重启后再次检查"
    } else {
        Write-Success "服务已成功卸载!"
    }
    
    # 清理相关文件
    Write-Info "清理相关文件..."
    $serviceWrapper = Join-Path $ScriptDir "service_wrapper.py"
    if (Test-Path $serviceWrapper) {
        Remove-Item $serviceWrapper -Force
        Write-Info "已删除服务包装脚本"
    }
    
    $logsDir = Join-Path $ScriptDir "logs"
    if (Test-Path $logsDir) {
        $cleanLogs = Read-Host "是否删除日志文件? (y/N)"
        if ($cleanLogs.ToLower() -eq 'y') {
            Remove-Item $logsDir -Recurse -Force
            Write-Info "已删除日志目录"
        }
    }
    
} catch {
    Write-Error "卸载服务时发生错误: $_"
    Write-Host "可以尝试手动删除服务:" -ForegroundColor Yellow
    Write-Host "  sc.exe delete $ServiceName" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Success "=== 卸载完成 ==="
Write-Host "如需重新安装服务，请运行: .\install_service.ps1" -ForegroundColor Yellow
Write-Host ""

Read-Host "按回车键退出" 