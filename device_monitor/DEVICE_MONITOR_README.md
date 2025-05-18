# 设备监控与离线通知系统

这个工具实现了在第三方服务器上监控多台设备的在线状态，并在设备离线时自动发送通知邮件。

## 工作原理

系统通过定期检查（ping或TCP端口连接）设备的网络连通性来判断设备是否在线。当发现设备离线时，会立即发送通知邮件，并提供详细的设备信息和上次在线时间。

## 优势

1. **不依赖被监控设备**：监控完全由独立服务器完成，不需要在被监控设备上安装任何软件
2. **检测意外关机**：可以检测到设备崩溃、断网或意外关机等情况
3. **支持多设备**：可同时监控多台设备，每台设备可单独配置监控方式
4. **详细状态记录**：记录设备的上/下线时间，方便查看设备历史状态

## 安装说明

### 系统要求

- Windows 7/8/10/11 或 Linux/macOS
- Python 3.6 或更高版本
- 网络连接（用于发送邮件通知）

### 快速安装（Windows）

1. 确保已安装Python
2. 运行`setup_device_monitor.bat`，按提示操作：
   - 创建配置文件
   - 选择安装类型（系统服务/开机启动项/桌面快捷方式）

### 手动安装（所有系统）

1. 确保已安装Python
2. 生成配置文件：`python device_monitor.py --create-example`
3. 编辑配置文件：`monitor_config.json`
4. 启动监控服务：`python device_monitor.py`

## 配置说明

配置文件`monitor_config.json`包含以下设置：

```json
{
  "check_interval": 300,  // 检查间隔（秒）
  "notify_when_back_online": true,  // 设备恢复在线时是否通知
  "include_online_in_report": true,  // 离线报告中是否包含在线设备
  "status_file": "device_status.json",  // 状态保存文件
  
  "email": {
    "smtp_server": "smtp.qq.com",  // 邮箱SMTP服务器
    "smtp_port": 465,  // 端口
    "smtp_encryption": "SSL",  // 加密类型：SSL/TLS/None
    "sender_email": "your_email@qq.com",  // 发件人邮箱
    "sender_password": "your_password",  // 邮箱密码/授权码
    "receiver_email": "recipient@example.com",  // 接收人邮箱
    "subject_prefix": "[设备监控]"  // 邮件主题前缀
  },
  
  "devices": [
    {
      "name": "家庭服务器",  // 设备名称
      "ip": "192.168.1.100",  // IP地址
      "check_method": "ping",  // 检查方法：ping或tcp
      "description": "存储服务器，运行NAS系统"  // 设备描述
    },
    {
      "name": "工作站",
      "ip": "192.168.1.101",
      "check_method": "ping",
      "description": "日常开发使用的工作站"
    },
    {
      "name": "树莓派",
      "ip": "192.168.1.102",
      "check_method": "tcp",  // 使用TCP端口检查
      "port": 22,  // 检查的TCP端口
      "description": "智能家居控制中心"
    }
  ]
}
```

## 使用方法

### 命令行参数

```
python device_monitor.py [选项]

选项:
  --config, -c FILE   指定配置文件路径（默认: monitor_config.json）
  --check-once, -o    只检查一次设备状态不持续监控
  --create-example, -e 创建示例配置文件
```

### 运行方式

有多种方式运行监控服务：

1. **作为系统服务**（推荐，仅Windows）：使用`setup_device_monitor.bat`设置
2. **开机启动项**：使用`setup_device_monitor.bat`设置
3. **命令行手动运行**：`python device_monitor.py`
4. **后台运行**（Linux）：`nohup python device_monitor.py &`

## 日志和状态

- **程序日志**：`device_monitor.log` - 记录程序运行状态和错误
- **设备状态**：`device_status.json` - 记录设备的在线历史
- **服务日志**（如果作为服务运行）：`service_output.log`和`service_error.log`

## 故障排除

1. **设备始终显示离线**
   - 检查设备IP地址是否正确
   - 确认网络连接正常
   - 尝试手动ping设备或连接端口

2. **无法发送邮件通知**
   - 检查邮箱配置是否正确
   - 确认是否使用了正确的授权码（不是邮箱密码）
   - 检查网络连接

3. **服务无法启动**
   - 检查Python安装是否正确
   - 确认配置文件格式正确无误
   - 查看日志文件了解详细错误 