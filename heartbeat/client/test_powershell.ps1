# PowerShell环境测试脚本

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

function Write-TestError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host "================================================" -ForegroundColor Blue
Write-Host "         PowerShell环境测试脚本" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 测试基本信息
Write-Info "PowerShell版本: $($PSVersionTable.PSVersion)"
Write-Info "操作系统: $($PSVersionTable.OS)"
Write-Info "当前用户: $env:USERNAME"
Write-Info "脚本路径: $PSScriptRoot"
Write-Host ""

# 测试Python环境
Write-Info "检查Python环境..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python已安装: $pythonVersion"
    } else {
        throw "Python命令执行失败"
    }
} catch {
    Write-TestError "Python未安装或未添加到PATH环境变量"
}

# 测试pip
Write-Info "检查pip..."
try {
    $pipVersion = pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "pip可用: $($pipVersion.Split(' ')[1])"
    } else {
        throw "pip命令执行失败"
    }
} catch {
    Write-TestError "pip不可用"
}

# 测试requests模块
Write-Info "检查requests模块..."
try {
    $result = python -c "import requests; print('requests版本:', requests.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success $result
    } else {
        Write-Warning "requests模块未安装"
        Write-Info "尝试安装requests..."
        pip install requests
        if ($LASTEXITCODE -eq 0) {
            Write-Success "requests安装成功"
        } else {
            Write-TestError "requests安装失败"
        }
    }
} catch {
    Write-TestError "无法检查requests模块: $_"
}

# 测试文件权限
Write-Info "检查文件权限..."
$testFile = Join-Path $PSScriptRoot "test_write.tmp"
try {
    "test" | Out-File -FilePath $testFile -Encoding UTF8
    if (Test-Path $testFile) {
        Remove-Item $testFile -Force
        Write-Success "文件写入权限正常"
    } else {
        Write-TestError "无法创建文件"
    }
} catch {
    Write-TestError "文件权限测试失败: $_"
}

# 测试网络连接
Write-Info "测试网络连接..."
try {
    $response = Test-NetConnection -ComputerName "www.baidu.com" -Port 80 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($response) {
        Write-Success "网络连接正常"
    } else {
        Write-Warning "网络连接可能有问题"
    }
} catch {
    Write-Warning "无法测试网络连接: $_"
}

# 测试管理员权限
Write-Info "检查管理员权限..."
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Success "当前以管理员身份运行"
} else {
    Write-Info "当前以普通用户身份运行"
}

# 测试计划任务权限
Write-Info "测试计划任务权限..."
try {
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Select-Object -First 1
    Write-Success "可以访问计划任务"
} catch {
    Write-Warning "无法访问计划任务: $_"
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue
Write-Host "测试完成！如果看到中文乱码，说明编码有问题。" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

Read-Host "按回车键退出" 