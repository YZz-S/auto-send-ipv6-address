# 心跳监控系统 (Heartbeat Monitoring System)

这是一个分布式设备心跳监控系统，用于监控NAT网络环境下的设备在线状态，并在设备离线或恢复时自动发送邮件通知。

## 📁 项目结构

项目现已重新组织为以下目录结构：

```
heartbeat/
├── client/                          # 客户端相关文件
│   ├── heartbeat_client.py         # 客户端主程序
│   ├── heartbeat_client_config.json # 客户端配置文件示例
│   ├── requirements.txt            # Python依赖
│   └── start_client.sh            # 客户端启动脚本
├── server/                          # 服务器端相关文件
│   ├── heartbeat_server.py         # 服务器主程序
│   ├── heartbeat_server_config.json # 服务器配置文件示例
│   ├── requirements.txt            # Python依赖
│   ├── Dockerfile                  # Docker构建文件
│   ├── docker-compose.yml         # Docker Compose配置
│   ├── start.sh                   # Docker容器启动脚本
│   ├── run_heartbeat_server.sh    # Linux服务器启动脚本
│   └── data/                      # 数据目录（持久化存储）
│       ├── heartbeat_config.json  # 实际配置文件
│       ├── heartbeat_status.json  # 设备状态文件
│       └── heartbeat_server.log   # 日志文件
└── shared/                          # 共享文档
    ├── README.md                   # 主要说明文档
    ├── troubleshooting_guide.md    # 问题排查指南
    ├── DOCKER_SETUP_README.md     # Docker部署指南
    ├── docker_heartbeat_readme.md # Docker相关文档
    └── heartbeat_readme.md        # 原始说明文档
```

## 🚀 快速开始

### 方式一：Docker部署服务器（推荐）

1. **进入服务器目录**
```bash
cd server
```

2. **启动服务器**
```bash
docker-compose up -d
```

3. **配置邮件通知**
```bash
# 编辑配置文件
nano ./data/heartbeat_config.json

# 重启服务
docker-compose restart
```

### 方式二：手动部署

#### 部署服务器

1. **进入服务器目录**
```bash
cd server
```

2. **安装依赖并启动**
```bash
# 安装依赖
pip install -r requirements.txt

# 创建配置文件（如果不存在）
python heartbeat_server.py --create-example

# 编辑配置文件
cp heartbeat_config_example.json heartbeat_config.json
nano heartbeat_config.json

# 启动服务器
python heartbeat_server.py
```

#### 部署客户端

1. **进入客户端目录**
```bash
cd client
```

2. **安装依赖并配置**
```bash
# 安装依赖
pip install -r requirements.txt

# 创建配置文件
python heartbeat_client.py --create-example

# 编辑配置文件
cp heartbeat_client_config_example.json heartbeat_client_config.json
nano heartbeat_client_config.json
```

3. **配置服务器地址**

编辑 `heartbeat_client_config.json`：
```json
{
  "server_url": "http://your-server-ip:18080",
  "device_name": "My-NAS",
  "description": "家庭NAS服务器",
  "heartbeat_interval": 60
}
```

4. **启动客户端**
```bash
# 使用启动脚本
chmod +x start_client.sh
./start_client.sh

# 或直接运行
python heartbeat_client.py
```

## 📋 文件说明

### 客户端文件 (client/)

| 文件名 | 必需 | 说明 |
|--------|------|------|
| `heartbeat_client.py` | ✅ | 客户端主程序 |
| `requirements.txt` | ✅ | Python依赖包 |
| `heartbeat_client_config.json` | ✅ | 配置文件（需要手动创建或从示例复制） |
| `start_client.sh` | ❌ | 启动脚本（可选，方便使用） |

### 服务器文件 (server/)

#### Docker部署需要的文件
| 文件名 | 必需 | 说明 |
|--------|------|------|
| `heartbeat_server.py` | ✅ | 服务器主程序 |
| `Dockerfile` | ✅ | Docker镜像构建文件 |
| `docker-compose.yml` | ✅ | Docker Compose配置 |
| `start.sh` | ✅ | 容器启动脚本 |
| `requirements.txt` | ✅ | Python依赖包 |
| `data/` | ✅ | 数据目录（自动创建） |

#### 手动部署需要的文件
| 文件名 | 必需 | 说明 |
|--------|------|------|
| `heartbeat_server.py` | ✅ | 服务器主程序 |
| `requirements.txt` | ✅ | Python依赖包 |
| `heartbeat_server_config.json` | ✅ | 配置文件示例 |
| `run_heartbeat_server.sh` | ❌ | Linux启动脚本（可选） |

### 共享文档 (shared/)

| 文件名 | 说明 |
|--------|------|
| `README.md` | 主要说明文档 |
| `troubleshooting_guide.md` | 问题排查指南 |
| `DOCKER_SETUP_README.md` | Docker部署详细指南 |

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

### 1. 设备离线通知
- **触发条件**：设备超过300秒（可配置）未发送心跳
- **邮件内容**：离线设备信息、最后心跳时间、在线设备列表

### 2. 设备恢复通知
- **触发条件**：离线设备重新发送心跳
- **邮件内容**：恢复设备信息、恢复时间

### 3. 邮件发送逻辑
- 检查周期：每60秒（可配置）
- 只在状态变化时发送邮件（避免重复通知）

## 🖥️ 启动时控制台输出

### 服务器启动（Docker）

#### 正常启动输出
```bash
=== 心跳监控服务器启动脚本 ===
✓ 配置文件已存在：/data/heartbeat_config.json
=== 启动心跳监控服务器 ===
心跳监控服务器启动，监听端口: 8081
设备可通过 http://[server-ip]:18080/heartbeat 发送心跳
```

#### 首次启动（无配置文件）
```bash
=== 心跳监控服务器启动脚本 ===
配置文件不存在，正在创建示例配置...
✓ 已创建配置文件：/data/heartbeat_config.json
⚠️  请根据需要修改配置文件中的邮件设置等参数
```

### 客户端启动

```bash
=== 心跳监控客户端启动脚本 ===
心跳客户端启动，间隔: 60秒
```

## ⚙️ 配置说明

### 服务器配置 (server/data/heartbeat_config.json)
```json
{
  "http_port": 8081,                    # HTTP服务端口
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

### 客户端配置 (client/heartbeat_client_config.json)
```json
{
  "server_url": "http://server-ip:18080", # 监控服务器地址
  "device_name": "NAS-Server",           # 设备名称
  "description": "家庭NAS服务器",        # 设备描述
  "heartbeat_interval": 60,              # 心跳发送间隔（秒）
  "device_id": "auto-generated"          # 设备唯一ID（自动生成）
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
    "platform": "Linux"
  }
}
```

### 查看设备状态
```http
GET /status
# 返回所有设备的当前状态
```

### 健康检查
```http
GET /health
# 返回服务器运行状态
```

## 🔍 故障排查

### 常见问题

1. **端口冲突**
   - 修改服务器配置中的 `http_port`
   - 修改 `docker-compose.yml` 中的端口映射

2. **邮件发送失败**
   - 检查SMTP配置
   - 确认邮箱密码或应用专用密码

3. **客户端连接失败**
   - 确认服务器地址和端口
   - 检查防火墙设置

### 快速诊断

**服务器端**：
```bash
cd server
docker-compose logs -f
curl http://localhost:18080/health
```

**客户端端**：
```bash
cd client
tail -f heartbeat_client.log
```

详细的排查指南请参考 `shared/troubleshooting_guide.md`

## 🐳 Docker 部署详情

- **容器内端口**: 8081 (避免8080冲突)
- **外部访问端口**: 18080
- **数据持久化**: 通过 `./data` 目录挂载
- **配置文件**: 自动创建或手动配置

详细的Docker部署指南请参考 `shared/DOCKER_SETUP_README.md`

## 🤝 贡献

欢迎提交Issues和Pull Requests来改进这个项目！

## 📄 许可证

本项目采用MIT许可证。 