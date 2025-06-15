# Windows 心跳监控客户端启动脚本说明

本目录包含了多种Windows下启动心跳监控客户端的方式，请根据您的需求选择合适的方案。

## 🚀 快速开始

### 方法一：手动启动（推荐新手）

1. **双击 `start_client.bat`** - 使用批处理脚本启动
2. **右键 `start_client.ps1` -> 使用PowerShell运行** - 使用PowerShell脚本启动

### 方法二：自启动设置（推荐日常使用）

**运行 `setup_autostart.ps1`** 设置开机自启动：
- 方式1：添加到启动文件夹（简单）
- 方式2：添加到计划任务（推荐）

### 方法三：Windows系统服务（推荐服务器使用）

**以管理员身份运行 `install_service.ps1`** 安装为系统服务。

---

## 📝 详细说明

### 🟢 启动脚本

#### `start_client.bat` - Windows批处理脚本
- ✅ 双击即可运行
- ✅ 自动检查Python环境
- ✅ 自动安装依赖包
- ✅ 异常自动重启
- ❌ 会显示命令行窗口

**使用方法：**
```batch
# 直接双击运行，或在命令行中执行：
start_client.bat
```

#### `start_client.ps1` - PowerShell脚本
- ✅ 彩色日志输出
- ✅ 完整的错误处理
- ✅ 智能重启机制
- ✅ 更好的用户体验
- ❌ 可能需要设置执行策略

**使用方法：**
```powershell
# 如果遇到执行策略问题，先运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后启动：
.\start_client.ps1
```

### 🟡 自启动设置

#### `setup_autostart.ps1` - 用户级自启动设置
**无需管理员权限，提供多种自启动方式：**

1. **启动文件夹方式**
   - ✅ 设置简单
   - ❌ PowerShell窗口可能短暂显示

2. **计划任务方式（推荐）**
   - ✅ 完全后台运行
   - ✅ 专业稳定
   - ✅ 支持条件启动
   - ✅ 自动重启

**使用方法：**
```powershell
# 运行自启动设置脚本
.\setup_autostart.ps1

# 按提示选择：
# 1. 添加到开机自启动
# 4. 添加到计划任务（推荐）
```

### 🔴 Windows系统服务

#### `install_service.ps1` - 服务安装脚本
**需要管理员权限，提供最稳定的运行方式：**

- ✅ 开机自动启动
- ✅ 用户注销后仍运行
- ✅ 系统级权限
- ✅ 自动故障恢复
- ❌ 需要管理员权限
- ❌ 需要NSSM工具

**使用方法：**
```powershell
# 1. 下载NSSM工具
# 访问 https://nssm.cc/download 下载nssm.exe
# 将nssm.exe放到客户端目录

# 2. 以管理员身份运行PowerShell
# 右键PowerShell -> 以管理员身份运行

# 3. 安装服务
.\install_service.ps1

# 4. 管理服务
Start-Service -Name HeartbeatClient    # 启动
Stop-Service -Name HeartbeatClient     # 停止
Restart-Service -Name HeartbeatClient  # 重启
Get-Service -Name HeartbeatClient      # 查看状态
```

#### `uninstall_service.ps1` - 服务卸载脚本
```powershell
# 以管理员身份运行
.\uninstall_service.ps1
```

---

## 🛠️ 环境要求

### 基本要求
- Windows 7/10/11
- Python 3.6+
- 网络连接

### PowerShell脚本要求
```powershell
# 如果遇到执行策略问题：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 系统服务要求
- 管理员权限
- NSSM工具 (https://nssm.cc/download)

---

## 🎯 推荐方案

### 👤 个人用户
1. **新手**：使用 `start_client.bat` 手动启动
2. **日常使用**：使用 `setup_autostart.ps1` 设置计划任务自启动

### 🏢 企业/服务器
1. **生产环境**：使用 `install_service.ps1` 安装系统服务
2. **开发环境**：使用 `start_client.ps1` 手动启动

---

## 🐛 故障排除

### 常见问题

#### 1. 中文编码问题
**症状**: 批处理脚本显示 `'查Python依赖...' is not recognized as an internal or external command`

**解决方案**:
- 使用 `start_client.bat` (英文版) 或 `start_client_cn.bat` (中文版)
- 运行 `test_environment.bat` 测试基础环境
- 运行 `test_powershell.ps1` 测试PowerShell环境

#### 2. PowerShell执行策略错误
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. PowerShell中文乱码
**所有PowerShell脚本已优化，包含以下编码设置**:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

#### 4. Python未找到
- 确保Python已安装
- 确保Python已添加到PATH环境变量
- 运行 `test_environment.bat` 检查

#### 5. 依赖包安装失败
```bash
pip install -r requirements.txt
```

#### 6. 配置文件不存在
- 首次运行会自动创建示例配置
- 编辑配置文件设置服务器地址

#### 7. 服务安装失败
- 确保以管理员身份运行
- 确保NSSM工具已下载到客户端目录

### 日志文件
- `heartbeat_client.log` - 客户端运行日志
- `service.log` - 服务运行日志（服务模式）
- `logs/` - 服务日志目录（服务模式）

---

## 📞 技术支持

如果遇到问题，请检查：
1. Python环境是否正确安装
2. 网络连接是否正常
3. 配置文件是否正确设置
4. 防火墙是否阻止连接

更多技术支持请查看主项目文档。 