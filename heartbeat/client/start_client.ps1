# PowerShell执行策略设置
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 设置错误处理
$ErrorActionPreference = "Continue"

# 设置控制台编码为UTF-8
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $Host.UI.RawUI.OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    Write-Host "Warning: Could not set UTF-8 encoding" -ForegroundColor Yellow
}

# 设置颜色输出函数
function Write-ColoredText {
    param(
        [string]$Text,
        [ConsoleColor]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColoredText "[INFO] $Message" -Color Cyan
}

function Write-Success {
    param([string]$Message)
    Write-ColoredText "[SUCCESS] $Message" -Color Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColoredText "[WARNING] $Message" -Color Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColoredText "[ERROR] $Message" -Color Red
}

Write-ColoredText "================================================" -Color Blue
Write-ColoredText "      心跳监控客户端启动脚本 (PowerShell)" -Color Blue
Write-ColoredText "================================================" -Color Blue
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# 检查Python是否安装
Write-Info "检查Python环境..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python已安装: $pythonVersion"
    } else {
        throw "Python命令执行失败"
    }
} catch {
    Write-Error "Python未安装或未添加到PATH环境变量"
    Write-Host "请安装Python 3.6或更高版本" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 检查配置文件
Write-Info "检查配置文件..."
if (-not (Test-Path "heartbeat_client_config.json")) {
    Write-Warning "配置文件不存在，正在创建示例配置..."
    
    try {
        python heartbeat_client.py --create-example
        if ($LASTEXITCODE -ne 0) {
            throw "创建示例配置失败"
        }
        
        Write-Host ""
        Write-Warning "请完成以下步骤："
        Write-Host "1. 编辑 heartbeat_client_config_example.json 文件" -ForegroundColor Yellow
        Write-Host "2. 重命名为 heartbeat_client_config.json" -ForegroundColor Yellow
        Write-Host "3. 配置服务器地址等信息后重新运行此脚本" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "按回车键退出"
        exit 1
    } catch {
        Write-Error "创建示例配置失败: $_"
        Read-Host "按回车键退出"
        exit 1
    }
} else {
    Write-Success "配置文件存在"
}

# 检查依赖包
Write-Info "检查Python依赖包..."
try {
    $result = pip show requests 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "依赖包已安装"
    } else {
        Write-Warning "正在安装依赖包..."
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "安装依赖失败"
        }
        Write-Success "依赖包安装完成"
    }
} catch {
    Write-Error "安装依赖失败，请检查网络连接: $_"
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Success "环境检查完成，正在启动心跳客户端..."
Write-Info "按 Ctrl+C 停止客户端"
Write-Host ""

# 启动客户端（带重启机制）
$restartCount = 0
$maxRestarts = 10

do {
    try {
        # 启动Python客户端
        python heartbeat_client.py
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "客户端正常退出"
            break
        } else {
            $restartCount++
            Write-Warning "客户端异常退出，错误代码: $exitCode"
            
            if ($restartCount -le $maxRestarts) {
                Write-Info "第 $restartCount 次重启尝试 (最多 $maxRestarts 次)"
                Write-Info "10秒后自动重启..."
                Start-Sleep -Seconds 10
            } else {
                Write-Error "重启次数已达上限 ($maxRestarts 次)，程序终止"
                break
            }
        }
    } catch {
        Write-Error "启动客户端时发生异常: $_"
        $restartCount++
        
        if ($restartCount -le $maxRestarts) {
            Write-Info "10秒后尝试重启..."
            Start-Sleep -Seconds 10
        } else {
            Write-Error "重启次数已达上限，程序终止"
            break
        }
    }
} while ($restartCount -le $maxRestarts)

Write-Host ""
Read-Host "按回车键退出" 