# NAT环境下的设备心跳监控系统

这个系统专为NAT环境下的设备（如虚拟机）设计，解决了外部无法直接连接到NAT设备的问题。它通过"主动心跳"机制，让NAT后的设备定期向监控服务器报告自己的状态。

## 工作原理

### 心跳机制
1. **设备主动汇报**：NAT后的设备定期向监控服务器发送"我还活着"的心跳信号
2. **状态监控**：监控服务器检测心跳间隔，当一段时间未收到信号时判定设备离线
3. **离线通知**：检测到设备离线时，监控服务器发送邮件通知管理员

![心跳机制示意图](https://mermaid.ink/img/pako:eNp1kc9qwzAMxl_F6JRCk5e40A4K7WGMwQ7bpYeQyE3FYjv4T9aW0HefnSYZHexkWZ_0-74DvBoDiYI9WM-8BaeD0B1u7HRzXdZl1Yyhk5rGn5P6NCn7Aqmgh1pXJr7VJv9d56wUMXwT8mKzqh6_FV7GI67rvJU9edGn4DjCKkfGHo0FzjBUyRXJ3XCGVFhB6oXRtCNfXQe9lrYnrjw9M1BU2Gu1-pJkwbdJZ_UGM8lQYXcQJzkYf-tEzwrY5YRjx87HMqhimnexeU3Bng1_uOdvZV3Lr7LIy8MlSbfLx5e7vYHfzWmOXDqbGXiOIbDoLfkj-0Gg_wMB0lrI?type=png)

### 优势对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| 关机通知 | 简单直接 | 依赖于设备自身发送通知<br>无法检测异常关机<br>关机过程中网络服务可能先关闭 |
| 外部监控 | 可检测多设备<br>不依赖被监控设备<br>可以检测异常关闭 | 无法穿透NAT<br>无法监控无公网IP的设备 |
| 心跳监控 | 可穿透NAT<br>可监控无公网IP的设备<br>可以检测异常关闭<br>可搜集设备信息 | 需要在被监控设备上安装心跳客户端 |

## 系统组件

### 1. 心跳服务器 (heartbeat_server.py)
- 运行在有固定IP的服务器上
- 接收设备发送的心跳信号
- 判断设备状态并发送通知

### 2. 心跳客户端 (heartbeat_client.py)
- 运行在NAT后的虚拟机/设备上
- 定期向服务器发送心跳信号
- 附带设备状态信息

## 安装指南

### 服务器端安装

1. 安装Python 3.6+
2. 安装依赖：`pip install requests`
3. 创建配置文件：`python heartbeat_server.py --create-example`
4. 编辑配置文件：`heartbeat_config.json`
5. 启动服务器：`python heartbeat_server.py`

### 客户端安装（在NAT后的设备上）

1. 安装Python 3.6+
2. 安装依赖：`pip install requests`
3. 创建配置文件：`python heartbeat_client.py --create-example`
4. 编辑配置文件：`heartbeat_client_config.json`，设置服务器地址
5. 启动客户端：`python heartbeat_client.py`

## 配置说明

### 服务器配置 (heartbeat_config.json)

```json
{
  "http_port": 8080,                 // 心跳服务器HTTP端口
  "heartbeat_timeout": 300,          // 心跳超时时间（秒）
  "check_interval": 60,              // 状态检查间隔（秒）
  "email": {
    "smtp_server": "smtp.qq.com",    // 邮箱SMTP服务器
    "smtp_port": 465,                // 端口
    "smtp_encryption": "SSL",        // 加密类型：SSL/TLS/None
    "sender_email": "your_email@qq.com",
    "sender_password": "your_email_password",
    "receiver_email": "recipient@example.com",
    "subject_prefix": "[心跳监控]"
  }
}
```

### 客户端配置 (heartbeat_client_config.json)

```json
{
  "server_url": "http://monitor-server-ip:8080",  // 监控服务器URL
  "device_name": "NAS虚拟机",                     // 设备名称
  "description": "NAT模式下的NAS虚拟机",          // 设备描述
  "heartbeat_interval": 60                        // 心跳间隔（秒）
}
```

## 启动为服务

### Linux (systemd)

创建服务文件 `/etc/systemd/system/heartbeat-client.service`:

```
[Unit]
Description=Device Heartbeat Client
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/heartbeat_client.py
WorkingDirectory=/path/to
Restart=always
User=username

[Install]
WantedBy=multi-user.target
```

启动服务：
```
sudo systemctl enable heartbeat-client
sudo systemctl start heartbeat-client
```

### Windows

设置为开机启动项:

1. 创建批处理文件 `start_heartbeat.bat`:
```
@echo off
cd /d "C:\path\to"
python heartbeat_client.py
```

2. 将批处理文件快捷方式放入启动文件夹:
`C:\Users\用户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

## 故障排除

1. **客户端无法连接服务器**
   - 检查服务器URL配置
   - 确认服务器防火墙允许指定端口
   - 确认网络连接正常

2. **服务器未收到心跳信号**
   - 检查客户端日志
   - 确认心跳间隔配置
   - 排查网络问题

3. **未收到离线通知**
   - 检查邮箱配置
   - 查看服务器日志
   - 确认心跳超时设置 