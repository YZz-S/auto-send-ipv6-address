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

## 🔌 端口配置说明

系统中涉及三个重要的端口配置，请确保它们的配置一致性：

### 端口配置文件对照表

| 文件 | 端口配置项 | 默认值 | 说明 |
|-----|-----------|-------|------|
| `docker-compose.yml` | `ports: "18080:8080"` | 主机端口18080，容器端口8080 | **主机端口18080**：外部访问服务器的端口<br/>**容器端口8080**：容器内应用监听的端口 |
| `Dockerfile` | `EXPOSE 8080` | 8080 | 声明容器暴露的端口，必须与应用监听端口一致 |
| `heartbeat_config_example.json` | `"http_port": 8080` | 8080 | 应用程序实际监听的端口 |

### 🚨 重要提醒

1. **容器端口一致性**：`Dockerfile`中的`EXPOSE`端口、`docker-compose.yml`中的容器端口、以及配置文件中的`http_port`必须保持一致
2. **主机端口**：`docker-compose.yml`中的主机端口（18080）可以根据需要修改，但要确保防火墙允许该端口
3. **访问地址**：客户端连接服务器时使用主机端口，例如：`http://your-server-ip:18080`

### 📝 端口修改示例

如果要修改服务端口为9090：

```bash
# 1. 修改 docker-compose.yml
ports:
  - "19090:9090"  # 主机端口19090，容器端口9090

# 2. 修改 Dockerfile  
EXPOSE 9090

# 3. 修改配置文件 data/heartbeat_config.json
{
  "http_port": 9090,
  ...
}
```

## 🔧 快速开始

### ⚡ 快速更新指南（针对已有用户）

如果你已经部署了心跳监控系统，想要更新到最新版本：

#### Docker用户（30秒更新）
```bash
# 停止服务 → 更新代码 → 重建启动
docker-compose down
git pull  # 或下载新代码覆盖
docker-compose build --no-cache
docker-compose up -d

# 验证更新：访问 http://your-server:port/health
```

#### 手动部署用户（1分钟更新）
```bash
# 停止服务 → 备份 → 替换文件 → 重启
pkill -f heartbeat_server.py
cp heartbeat_server.py heartbeat_server.py.backup
# 下载新的 heartbeat_server.py 文件覆盖旧文件
python heartbeat_server.py

# 验证更新：访问 http://your-server:port/health
```

> 📖 **详细更新说明请看下方"🔄 更新已有的服务器端代码"章节**

### Docker 部署（推荐）

1. **启动服务器**
```bash
cd heartbeat/server
docker-compose up -d
```

2. **配置邮件通知**
```bash
# 编辑配置文件
nano ./data/heartbeat_config.json

# 重启服务
docker-compose restart
```

### 🔧 常见问题排查

#### 问题1：`exec /app/start.sh: no such file or directory`

**原因**：Docker容器中缺少bash或启动脚本权限问题

**解决方案**：
```bash
# 1. 重新构建镜像（清除缓存）
docker-compose down
docker-compose build --no-cache

# 2. 或者手动修复权限
docker-compose exec heartbeat-server chmod +x /app/start.sh

# 3. 重新启动
docker-compose up -d
```

#### 问题2：端口配置不一致导致无法访问

**检查清单**：
- ✅ `docker-compose.yml` 中的端口映射：`"18080:8080"`
- ✅ `Dockerfile` 中的暴露端口：`EXPOSE 8080`  
- ✅ 配置文件中的监听端口：`"http_port": 8080`
- ✅ 防火墙允许18080端口访问

**验证端口**：
```bash
# 检查容器端口状态
docker-compose ps

# 检查端口监听
docker-compose exec heartbeat-server netstat -tlnp | grep 8080

# 测试外部访问
curl http://your-server-ip:18080/health
```

## 🔄 更新已有的服务器端代码

### 📋 更新前准备

#### 1. 停止现有服务
```bash
# Docker部署的用户
docker-compose down

# 手动部署的用户（如果使用systemd）
sudo systemctl stop heartbeat-server

# 或直接终止Python进程
pkill -f heartbeat_server.py
```

#### 2. 备份重要数据
```bash
# 备份配置文件
cp heartbeat_config.json heartbeat_config.json.backup
cp -r data/ data_backup/  # Docker用户

# 备份设备状态文件
cp heartbeat_status.json heartbeat_status.json.backup
```

### 🚀 更新步骤

#### 方式一：Docker用户（推荐）

1. **拉取最新代码**
```bash
cd /path/to/your/heartbeat/project
git pull origin main  # 或下载最新的源码包
```

2. **重新构建并启动**
```bash
cd server/
docker-compose down
docker-compose build --no-cache  # 强制重新构建镜像
docker-compose up -d
```

3. **验证更新**
```bash
# 检查容器状态
docker-compose ps

# 查看启动日志
docker-compose logs -f

# 验证Web界面
curl http://localhost:13141/health
```

#### 方式二：手动部署用户

1. **下载最新代码**
```bash
# 备份当前代码
cp heartbeat_server.py heartbeat_server.py.backup

# 下载或复制新的服务器文件
wget https://raw.githubusercontent.com/your-repo/heartbeat_server.py
# 或直接替换 heartbeat_server.py 文件
```

2. **检查依赖**
```bash
# 比较requirements.txt是否有更新
diff requirements.txt requirements.txt.new

# 如有新依赖，进行安装
pip install -r requirements.txt --upgrade
```

3. **启动服务**
```bash
# 直接启动
python heartbeat_server.py

# 或使用systemd（如果已配置）
sudo systemctl start heartbeat-server
```

### ✅ 更新验证

#### 1. 检查服务状态
```bash
# 验证HTTP服务
curl http://localhost:8080/health
curl http://localhost:8080/status

# 检查日志
tail -f heartbeat_server.log  # 手动部署
docker-compose logs -f        # Docker部署
```

#### 2. 验证新功能
访问以下链接确认Web界面已更新：

- **首页（自动重定向）**: `http://your-server:port/`
- **健康状态页面**: `http://your-server:port/health`
- **设备监控页面**: `http://your-server:port/status`
- **JSON API**: `http://your-server:port/api/status`

#### 3. 确认新功能特性
- ✅ **美化的Web界面**：渐变背景、现代化设计
- ✅ **实时搜索功能**：设备名称和ID搜索
- ✅ **状态筛选**：在线/离线设备筛选
- ✅ **自动刷新控制**：可开启/暂停自动刷新
- ✅ **响应式设计**：移动端适配
- ✅ **根路径重定向**：访问根路径自动跳转到健康页面
- ✅ **404页面美化**：统一设计风格的错误页面

### 🔧 配置文件兼容性

新版本完全兼容现有配置文件，无需修改配置文件格式。

#### 配置文件检查
```bash
# 验证配置文件格式
python -c "import json; print('配置文件格式正确') if json.load(open('heartbeat_config.json')) else print('配置文件格式错误')"
```

### 🚨 回滚方案

如果更新后出现问题，可以快速回滚：

#### Docker用户回滚
```bash
# 停止新版本
docker-compose down

# 恢复备份的配置
cp data_backup/* data/

# 使用旧版本镜像（如果需要）
docker-compose up -d
```

#### 手动部署回滚
```bash
# 停止服务
pkill -f heartbeat_server.py

# 恢复代码文件
cp heartbeat_server.py.backup heartbeat_server.py

# 恢复配置和状态文件
cp heartbeat_config.json.backup heartbeat_config.json
cp heartbeat_status.json.backup heartbeat_status.json

# 重新启动
python heartbeat_server.py
```

### 📝 更新日志记录

建议在每次更新时记录以下信息：
```bash
# 创建更新日志
echo "$(date): 更新到版本X.X.X - 新增Web界面美化功能" >> update_history.log
```

### ⚠️ 注意事项

1. **数据持久性**：设备状态数据会在更新过程中保留
2. **服务中断**：更新过程中服务会短暂中断（通常1-2分钟）
3. **客户端兼容**：新版服务器完全兼容旧版客户端
4. **端口配置**：确认防火墙设置允许访问Web界面端口

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

## 🌐 Web监控界面

### 页面访问

| 路径 | 说明 | 功能特色 |
|------|------|----------|
| `/` 或 `/index` 或 `/home` | 首页（自动重定向到健康页面） | 便捷访问 |
| `/health` | 服务器健康状态页面 | 服务器运行时长、设备统计、在线率 |
| `/status` | 设备监控状态页面 | 设备列表、搜索筛选、详细信息 |
| `/api/status` | JSON API接口 | 程序化访问设备数据 |

### 🎨 界面特色

#### 健康状态页面 (`/health`)
- **💫 动效设计**：心跳动画、浮动背景、脉冲指示器
- **📊 实时统计**：服务器运行时长、设备统计、在线率
- **🔄 自动更新**：实时时间显示、动态背景效果
- **📱 响应式设计**：完美适配桌面端和移动端

#### 设备监控页面 (`/status`)
- **🔍 实时搜索**：支持设备名称和ID的即时搜索
- **🎛️ 状态筛选**：快速筛选在线/离线设备
- **📋 设备详情**：
  - 基础信息：IP地址、心跳时间、连接时长
  - 系统概要：主机名、内存使用、磁盘使用
  - 详细信息：可展开查看完整系统信息
- **⚡ 自动刷新**：支持30秒自动刷新，可手动控制
- **📶 在线指示**：信号强度动画、状态脉冲指示

#### 404错误页面
- **🎯 友好提示**：清晰的错误说明和导航建议
- **🔗 快速导航**：直接链接到主要功能页面
- **🎨 统一设计**：与主界面保持一致的设计风格

### 💡 使用技巧

1. **搜索功能**：在设备监控页面可实时搜索设备名称或ID
2. **筛选功能**：使用顶部按钮快速筛选在线/离线设备
3. **详情展开**：点击"查看详情"按钮展开设备完整系统信息
4. **自动刷新**：可通过"暂停自动刷新"按钮控制页面更新
5. **移动访问**：支持手机和平板设备访问，布局自动适配

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

### To-do

1. [ ] 我希望在服务端代码看到有机器连接或者断开。

2. [ ] 增强项目安全性。

3. [ ] 增加发送测试邮件的功能。

4. [ ] 增加被监控设备某项指标异常的报警通知功能

5. [ ] 增加客户端找不到服务端的报警通知功能

6. [ ] 适配更多客户端，如安卓，Mac，IOS，Linux等


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

## 📈 版本更新历史

### 最新版本特性
- ✅ **美化Web界面**：全新的现代化设计，支持响应式布局
- ✅ **实时搜索筛选**：设备名称/ID搜索，在线/离线状态筛选
- ✅ **动态效果**：心跳动画、信号强度指示、浮动背景
- ✅ **自动刷新控制**：可控制的30秒自动刷新功能
- ✅ **根路径重定向**：访问根目录自动跳转到健康页面
- ✅ **美化404页面**：统一设计风格的错误页面
- ✅ **增强系统信息**：更详细的设备系统信息展示
- ✅ **移动端优化**：完美的移动设备访问体验

### 兼容性说明
- 🔄 **向后兼容**：新版本完全兼容旧版配置文件和客户端
- 📊 **数据保持**：更新过程中设备状态数据完全保留
- 🔧 **配置不变**：无需修改现有配置文件格式

## 🤝 贡献

欢迎提交Issues和Pull Requests来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。 