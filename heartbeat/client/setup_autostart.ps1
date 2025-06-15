# 用户级自启动设置脚本（无需管理员权限）

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
Write-Host "       心跳监控客户端 - 用户自启动设置" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 获取脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StartupScript = Join-Path $ScriptDir "start_client.ps1"

# 检查启动脚本是否存在
if (-not (Test-Path $StartupScript)) {
    Write-Error "未找到启动脚本: $StartupScript"
    Read-Host "按回车键退出"
    exit 1
}

# 创建启动任务的VBS脚本（隐藏PowerShell窗口）
$VbsScript = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$StartupScript""", 0, False
"@

$VbsPath = Join-Path $ScriptDir "start_client_hidden.vbs"
$VbsScript | Out-File -FilePath $VbsPath -Encoding ASCII

# 获取启动文件夹路径
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "心跳监控客户端.lnk"

Write-Info "启动文件夹: $StartupFolder"

# 显示选项菜单
Write-Host "请选择操作:" -ForegroundColor Yellow
Write-Host "1. 添加到开机自启动" -ForegroundColor White
Write-Host "2. 从开机自启动中移除" -ForegroundColor White
Write-Host "3. 检查自启动状态" -ForegroundColor White
Write-Host "4. 添加到计划任务（推荐）" -ForegroundColor White
Write-Host "5. 从计划任务中移除" -ForegroundColor White
Write-Host "0. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项号码"

switch ($choice) {
    "1" {
        # 添加到启动文件夹
        try {
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
            $Shortcut.TargetPath = $VbsPath
            $Shortcut.WorkingDirectory = $ScriptDir
            $Shortcut.Description = "心跳监控客户端自启动"
            $Shortcut.Save()
            
            Write-Success "已添加到开机自启动"
            Write-Info "快捷方式位置: $ShortcutPath"
        } catch {
            Write-Error "添加自启动失败: $_"
        }
    }
    
    "2" {
        # 从启动文件夹移除
        if (Test-Path $ShortcutPath) {
            Remove-Item $ShortcutPath -Force
            Write-Success "已从开机自启动中移除"
        } else {
            Write-Warning "未找到自启动项"
        }
    }
    
    "3" {
        # 检查状态
        if (Test-Path $ShortcutPath) {
            Write-Success "已设置开机自启动"
            Write-Info "快捷方式: $ShortcutPath"
        } else {
            Write-Info "未设置开机自启动"
        }
        
        # 检查计划任务
        $TaskName = "HeartbeatClient"
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Success "已设置计划任务自启动"
            Write-Info "任务名称: $TaskName"
            Write-Info "任务状态: $($task.State)"
        } else {
            Write-Info "未设置计划任务自启动"
        }
    }
    
    "4" {
        # 添加到计划任务
        $TaskName = "HeartbeatClient"
        $TaskDescription = "心跳监控客户端自动启动任务"
        
        try {
            # 检查任务是否已存在
            $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($existingTask) {
                Write-Warning "计划任务已存在"
                $overwrite = Read-Host "是否要覆盖现有任务? (y/N)"
                if ($overwrite.ToLower() -ne 'y') {
                    Write-Info "操作已取消"
                    break
                }
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            }
            
            # 创建任务操作
            $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$StartupScript`""
            
            # 创建任务触发器（开机启动）
            $Trigger = New-ScheduledTaskTrigger -AtLogOn
            
            # 创建任务设置
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
            
            # 创建任务主体（以当前用户身份运行）
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            
            # 注册任务
            Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
            
            Write-Success "已添加到计划任务"
            Write-Info "任务名称: $TaskName"
            Write-Info "可以在'任务计划程序'中管理此任务"
            
        } catch {
            Write-Error "添加计划任务失败: $_"
        }
    }
    
    "5" {
        # 从计划任务中移除
        $TaskName = "HeartbeatClient"
        try {
            $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($task) {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Success "已从计划任务中移除"
            } else {
                Write-Warning "未找到计划任务"
            }
        } catch {
            Write-Error "移除计划任务失败: $_"
        }
    }
    
    "0" {
        Write-Info "退出"
        exit 0
    }
    
    default {
        Write-Warning "无效的选项"
    }
}

# 清理临时文件
if (Test-Path $VbsPath) {
    # 如果没有设置自启动，删除VBS文件
    if (-not (Test-Path $ShortcutPath)) {
        $TaskName = "HeartbeatClient"
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if (-not $task) {
            Remove-Item $VbsPath -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "• 启动文件夹方式: 简单但PowerShell窗口可能短暂显示" -ForegroundColor White
Write-Host "• 计划任务方式: 更专业，完全后台运行（推荐）" -ForegroundColor White
Write-Host "• Windows服务方式: 最稳定，需要管理员权限，运行 install_service.ps1" -ForegroundColor White
Write-Host ""

Read-Host "按回车键退出" 