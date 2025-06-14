# 心跳监控系统 (Heartbeat Monitoring System)

这是一个分布式设备心跳监控系统，用于监控NAT网络环境下的设备在线状态，并在设备离线或恢复时自动发送邮件通知。

## 📋 项目简介

该系统由两部分组成：
- **心跳服务器** (`heartbeat_server.py`)：运行在公网可访问的服务器上，接收并处理心跳信号
- **心跳客户端** (`heartbeat_client.py`)：运行在需要监控的设备上，定期发送心跳信号

### 设计目标
- 监控NAT网络后的设备状态
- 自动检测设备离线和恢复
- 邮件通知状态变化
- 轻量级，资源占用少
- 支持Docker容器化部署

## 🚀 功能特性

### 服务器功能
- **HTTP API接口**：接收心跳信号和查询设备状态
- **状态监控**：定期检查设备是否超时离线
- **邮件通知**：自动发送设备状态变化通知
- **数据持久化**：保存设备状态到本地文件
- **Web监控界面**：通过HTTP接口查看所有设备状态

### 客户端功能
- **系统信息收集**：自动收集设备的详细系统信息
- **自动重连**：网络异常时自动重试
- **可配置间隔**：支持自定义心跳发送间隔
- **跨平台支持**：支持Windows、Linux、macOS

## ⚡ 邮件发送时机

系统会在以下情况自动发送邮件通知：

### 1. 设备离线通知 (offline)
**触发条件：**
- 设备超过配置的`heartbeat_timeout`时间（默认300秒）未发送心跳
- 且设备之前的状态为"在线"

**邮件内容包含：**
- 离线设备列表（设备名、ID、描述、最后心跳时间、IP地址）
- 设备的详细系统信息（如果有）
- 当前仍在线的设备列表
- 通知发送时间

**示例邮件标题：**
```
[心跳监控] 1台设备离线
```

### 2. 设备恢复在线通知 (recovery)
**触发条件：**
- 之前标记为离线的设备重新发送心跳信号

**邮件内容包含：**
- 恢复在线的设备信息
- 恢复时间
- 设备当前IP地址

**示例邮件标题：**
```
[心跳监控] 设备恢复在线
```

### 3. 邮件发送逻辑
```
检查周期：每60秒（可配置）
超时判断：300秒内无心跳则标记离线（可配置）
只在状态变化时发送邮件（避免重复通知）
```

## 🖥️ 启动时控制台输出

### 服务器启动

#### 正常启动输出
```bash
=== 心跳监控服务器启动脚本 ===
✓ 配置文件已存在：/data/heartbeat_config.json
=== 启动心跳监控服务器 ===
配置文件：/data/heartbeat_config.json
状态文件：/data/heartbeat_status.json
日志文件：/data/heartbeat_server.log
=================================
心跳监控服务器启动，监听端口: 8080
设备可通过 http://[server-ip]:8080/heartbeat 发送心跳
```

#### 首次启动（无配置文件）
```bash
=== 心跳监控服务器启动脚本 ===
配置文件不存在，正在创建示例配置...
已创建示例配置文件：heartbeat_config_example.json
✓ 已创建配置文件：/data/heartbeat_config.json
⚠️  请根据需要修改配置文件中的邮件设置等参数
=== 启动心跳监控服务器 ===
配置文件：/data/heartbeat_config.json
状态文件：/data/heartbeat_status.json
日志文件：/data/heartbeat_server.log
=================================
心跳监控服务器启动，监听端口: 8080
设备可通过 http://[server-ip]:8080/heartbeat 发送心跳
```

#### 配置文件错误时
```bash
配置文件 '/data/heartbeat_config.json' 不存在。使用 --create-example 创建示例配置。
```

### 客户端启动

#### 正常启动输出
```bash
心跳客户端启动，间隔: 60秒
```

#### 配置文件不存在时
```bash
配置文件 'heartbeat_client_config.json' 不存在。使用 --create-example 创建示例配置。
```

#### 网络连接失败时
客户端会继续运行，但在日志中记录错误信息，不会在控制台显示错误。

## 🔧 快速开始

### Docker 部署（推荐）

1. **启动服务器**
```bash
cd heartbeat
docker-compose up -d
```

2. **配置邮件通知**
```bash
# 编辑配置文件
nano ./data/heartbeat_config.json

# 重启服务
docker-compose restart
```

### 手动部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **启动服务器**
```bash
# 创建配置文件
python heartbeat_server.py --create-example

# 编辑配置文件
nano heartbeat_config_example.json
mv heartbeat_config_example.json heartbeat_config.json

# 启动服务器
python heartbeat_server.py
```

3. **配置客户端**
```bash
# 在需要监控的设备上
python heartbeat_client.py --create-example

# 编辑配置文件
nano heartbeat_client_config_example.json
mv heartbeat_client_config_example.json heartbeat_client_config.json

# 启动客户端
python heartbeat_client.py
```

## ⚙️ 配置说明

### 服务器配置 (`heartbeat_config.json`)
```json
{
  "http_port": 8080,                    # HTTP服务端口
  "heartbeat_timeout": 300,             # 心跳超时时间（秒）
  "check_interval": 60,                 # 状态检查间隔（秒）
  "email": {
    "smtp_server": "smtp.qq.com",       # SMTP服务器地址
    "smtp_port": 465,                   # SMTP端口
    "smtp_encryption": "SSL",           # 加密方式：SSL/TLS/None
    "sender_email": "your@qq.com",      # 发送方邮箱
    "sender_password": "password",      # 邮箱密码或应用专用密码
    "receiver_email": "admin@example.com", # 接收方邮箱
    "subject_prefix": "[心跳监控]"      # 邮件主题前缀
  }
}
```

### 客户端配置 (`heartbeat_client_config.json`)
```json
{
  "server_url": "http://server-ip:8080", # 监控服务器地址
  "device_name": "NAS-Server",           # 设备名称
  "description": "家庭NAS服务器",        # 设备描述
  "heartbeat_interval": 60,              # 心跳发送间隔（秒）
  "device_id": "nas-001"                 # 设备唯一ID（可选，自动生成）
}
```

## 📡 API接口

### 发送心跳
```http
POST /heartbeat
Content-Type: application/json

{
  "device_id": "device-001",
  "name": "设备名称",
  "description": "设备描述",
  "info": {
    "hostname": "mynas",
    "platform": "Linux",
    "ip": "192.168.1.100"
  }
}
```

### 查看设备状态
```http
GET /status

# 返回所有设备的当前状态
{
  "devices": {
    "device-001": {
      "name": "设备名称",
      "status": "online",
      "last_heartbeat": "2024-01-01 12:00:00",
      "ip": "192.168.1.100"
    }
  },
  "server_time": "2024-01-01 12:00:00"
}
```

### 健康检查
```http
GET /health

# 返回服务器运行状态
Heartbeat server is running
```

## 📊 系统信息收集

客户端会自动收集以下系统信息：

### 基础信息
- 主机名
- 操作系统平台
- 处理器架构
- Python版本
- 系统启动时间

### 网络信息
- 主IP地址
- 所有网络接口信息

### 系统资源
- **磁盘使用情况**：各分区使用率
- **内存使用情况**：总内存、已用内存、使用率
- **系统负载**：CPU使用率（Windows）或负载平均值（Linux/macOS）

## 📝 日志记录

### 服务器日志 (`heartbeat_server.log`)
- 服务器启动/停止
- 设备心跳接收
- 设备状态变化
- 邮件发送结果
- 错误信息

### 客户端日志 (`heartbeat_client.log`)
- 客户端启动/停止
- 心跳发送结果
- 网络连接错误
- 配置加载情况

## 🐳 Docker 部署详情

### 文件结构
```
heartbeat/
├── Dockerfile                    # Docker构建文件
├── docker-compose.yml           # Docker Compose配置
├── start.sh                     # 容器启动脚本
├── heartbeat_server.py          # 服务器主程序
├── requirements.txt             # Python依赖
└── data/                        # 数据目录（持久化）
    ├── heartbeat_config.json    # 配置文件
    ├── heartbeat_status.json    # 设备状态
    └── heartbeat_server.log     # 日志文件
```

### 端口映射
- 容器内端口：8080
- 主机端口：13141（可在docker-compose.yml中修改）

### 数据持久化
通过Volume挂载`./data`目录，确保配置和数据不会因容器重启而丢失。

## 🔍 故障排查

### 常见问题

1. **邮件发送失败**
   - 检查SMTP配置是否正确
   - 确认邮箱密码或应用专用密码
   - 验证网络连接

2. **设备显示离线但实际在线**
   - 检查心跳超时时间设置
   - 确认客户端配置的服务器地址
   - 查看客户端日志

3. **Docker容器无法启动**
   - 检查端口是否被占用
   - 查看容器日志：`docker-compose logs -f`

### 监控命令
```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 检查服务健康状态
curl http://localhost:13141/health

# 查看所有设备状态
curl http://localhost:13141/status
```

## 📋 项目文件说明

| 文件名 | 说明 |
|--------|------|
| `heartbeat_server.py` | 服务器主程序 |
| `heartbeat_client.py` | 客户端主程序 |
| `Dockerfile` | Docker镜像构建文件 |
| `docker-compose.yml` | Docker Compose配置 |
| `start.sh` | 容器启动脚本 |
| `requirements.txt` | Python依赖包 |
| `run_heartbeat_server.sh` | Linux启动脚本 |
| `DOCKER_SETUP_README.md` | Docker部署详细指南 |

## 🤝 贡献

欢迎提交Issues和Pull Requests来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。 