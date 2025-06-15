# User-level autostart setup script (No admin privileges required)

# Set error handling and encoding
$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $Host.UI.RawUI.OutputEncoding = [System.Text.Encoding]::UTF8
    # Try to set console code page to UTF-8
    chcp 65001 | Out-Null
} catch {
    Write-Host "Warning: Could not set UTF-8 encoding" -ForegroundColor Yellow
}

# Color output functions
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
Write-Host "    Heartbeat Client - Autostart Setup Tool" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StartupScript = Join-Path $ScriptDir "start_client.ps1"

# Check if startup script exists
if (-not (Test-Path $StartupScript)) {
    Write-Error "Startup script not found: $StartupScript"
    Read-Host "Press Enter to exit"
    exit 1
}

# Create VBS script for startup task (hide PowerShell window)
$VbsScript = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$StartupScript""", 0, False
"@

$VbsPath = Join-Path $ScriptDir "start_client_hidden.vbs"
$VbsScript | Out-File -FilePath $VbsPath -Encoding ASCII

# Get startup folder path
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "HeartbeatClient.lnk"

Write-Info "Startup folder: $StartupFolder"

# Display option menu
Write-Host "Please select an option:" -ForegroundColor Yellow
Write-Host "1. Add to startup folder" -ForegroundColor White
Write-Host "2. Remove from startup folder" -ForegroundColor White
Write-Host "3. Check autostart status" -ForegroundColor White
Write-Host "4. Add to scheduled task (Recommended)" -ForegroundColor White
Write-Host "5. Remove from scheduled task" -ForegroundColor White
Write-Host "0. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter option number"

switch ($choice) {
    "1" {
        # Add to startup folder
        try {
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
            $Shortcut.TargetPath = $VbsPath
            $Shortcut.WorkingDirectory = $ScriptDir
            $Shortcut.Description = "Heartbeat Client Autostart"
            $Shortcut.Save()
            
            Write-Success "Added to startup folder"
            Write-Info "Shortcut location: $ShortcutPath"
        } catch {
            Write-Error "Failed to add to startup: $_"
        }
    }
    
    "2" {
        # Remove from startup folder
        if (Test-Path $ShortcutPath) {
            Remove-Item $ShortcutPath -Force
            Write-Success "Removed from startup folder"
        } else {
            Write-Warning "Startup item not found"
        }
    }
    
    "3" {
        # Check status
        if (Test-Path $ShortcutPath) {
            Write-Success "Startup folder autostart is enabled"
            Write-Info "Shortcut: $ShortcutPath"
        } else {
            Write-Info "Startup folder autostart is not enabled"
        }
        
        # Check scheduled task
        $TaskName = "HeartbeatClient"
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Success "Scheduled task autostart is enabled"
            Write-Info "Task name: $TaskName"
            Write-Info "Task status: $($task.State)"
        } else {
            Write-Info "Scheduled task autostart is not enabled"
        }
    }
    
    "4" {
        # Add to scheduled task
        $TaskName = "HeartbeatClient"
        $TaskDescription = "Heartbeat Client Automatic Startup Task"
        
        try {
            # Check if task already exists
            $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($existingTask) {
                Write-Warning "Scheduled task already exists"
                $overwrite = Read-Host "Do you want to overwrite the existing task? (y/N)"
                if ($overwrite.ToLower() -ne 'y') {
                    Write-Info "Operation cancelled"
                    break
                }
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            }
            
            # Create task action
            $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$StartupScript`""
            
            # Create task trigger (startup)
            $Trigger = New-ScheduledTaskTrigger -AtLogOn
            
            # Create task settings
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
            
            # Create task principal (run as current user)
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            
            # Register task
            $result = Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -ErrorAction Stop
            
            if ($result) {
                Write-Success "Added to scheduled task"
                Write-Info "Task name: $TaskName"
                Write-Info "You can manage this task in 'Task Scheduler'"
            } else {
                Write-Error "Failed to create scheduled task"
            }
            
        } catch {
            Write-Error "Failed to add scheduled task: $_"
            Write-Host ""
            Write-Info "Alternative solution: Use startup folder method (option 1)"
            Write-Info "This method doesn't require special permissions"
        }
    }
    
    "5" {
        # Remove from scheduled task
        $TaskName = "HeartbeatClient"
        try {
            $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($task) {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Success "Removed from scheduled task"
            } else {
                Write-Warning "Scheduled task not found"
            }
        } catch {
            Write-Error "Failed to remove scheduled task: $_"
        }
    }
    
    "0" {
        Write-Info "Exit"
        exit 0
    }
    
    default {
        Write-Warning "Invalid option"
    }
}

# Clean up temporary files
if (Test-Path $VbsPath) {
    # Delete VBS file if no autostart is set
    if (-not (Test-Path $ShortcutPath)) {
        $TaskName = "HeartbeatClient"
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if (-not $task) {
            Remove-Item $VbsPath -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  Startup folder method: Simple but PowerShell window may briefly appear" -ForegroundColor White
Write-Host "  Scheduled task method: Professional, runs completely in background (Recommended)" -ForegroundColor White
Write-Host "  Windows service method: Most stable, requires admin privileges, run install_service.ps1" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit" 