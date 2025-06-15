# 心跳监控服务器 Docker 部署指南

## 问题解决

之前的 Docker 容器启动时会出现 "配置文件 '/data/heartbeat_config.json' 不存在" 的错误，现已修复。

## 修复内容

1. **自动配置文件创建**：容器启动时会自动检查配置文件是否存在，如果不存在会自动创建示例配置
2. **改进的启动脚本**：添加了详细的启动日志和错误处理
3. **环境变量支持**：日志文件路径现在支持环境变量配置

## 快速开始

### 1. 构建和启动容器

```bash
# 进入 heartbeat 目录
cd heartbeat

# 使用 docker-compose 启动（推荐）
docker-compose up -d

# 或者直接使用 docker
docker build -t heartbeat-server .
docker run -d -p 13141:8080 -v ./data:/data --name heartbeat-server heartbeat-server
```

### 2. 配置邮件通知

容器首次启动时会在 `./data/` 目录下创建 `heartbeat_config.json` 配置文件。

**编辑配置文件：**

```bash
# 停止容器
docker-compose down

# 编辑配置文件
nano ./data/heartbeat_config.json
```

**配置说明：**

```json
{
  "http_port": 8080,           # 服务器端口
  "heartbeat_timeout": 300,    # 心跳超时时间（秒）
  "check_interval": 60,        # 状态检查间隔（秒）
  "email": {
    "smtp_server": "smtp.qq.com",              # SMTP服务器
    "smtp_port": 465,                          # SMTP端口
    "smtp_encryption": "SSL",                  # 加密方式：SSL/TLS/None
    "sender_email": "your_email@qq.com",       # 发送邮箱
    "sender_password": "your_app_password",    # 邮箱密码或应用专用密码
    "receiver_email": "recipient@example.com", # 接收邮箱
    "subject_prefix": "[心跳监控]"              # 邮件主题前缀
  }
}
```

### 3. 重新启动容器

```bash
docker-compose up -d
```

## 验证服务

### 检查服务状态

```bash
# 查看容器日志
docker-compose logs -f

# 检查服务器健康状态
curl http://localhost:13141/health

# 查看设备状态
curl http://localhost:13141/status
```

### 发送测试心跳

```bash
curl -X POST http://localhost:13141/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device",
    "name": "测试设备",
    "description": "Docker部署测试",
    "info": {
      "version": "1.0",
      "location": "服务器机房"
    }
  }'
```

## 目录结构

```
heartbeat/
├── Dockerfile                    # Docker 构建文件
├── docker-compose.yml           # Docker Compose 配置
├── start.sh                     # 容器启动脚本
├── heartbeat_server.py          # 主程序
├── requirements.txt             # Python 依赖
├── heartbeat_config_example.json # 配置文件示例
└── data/                        # 数据目录（挂载点）
    ├── heartbeat_config.json    # 配置文件（自动生成）
    ├── heartbeat_status.json    # 状态文件
    └── heartbeat_server.log     # 日志文件
```

## 常见问题

### 1. 邮件发送失败

- 检查 SMTP 配置是否正确
- 确认邮箱密码或应用专用密码
- 验证网络连接和防火墙设置

### 2. 容器无法启动

```bash
# 查看详细错误日志
docker-compose logs heartbeat-server

# 检查配置文件格式
cat ./data/heartbeat_config.json | python -m json.tool
```

### 3. 端口冲突

如果端口 13141 被占用，可以在 `docker-compose.yml` 中修改：

```yaml
ports:
  - "其他端口:8080"  # 例如 "8080:8080"
```

## 监控和维护

### 查看运行状态

```bash
# 容器状态
docker-compose ps

# 资源使用
docker stats heartbeat-server

# 实时日志
docker-compose logs -f --tail=50
```

### 备份数据

```bash
# 备份配置和状态文件
tar -czf heartbeat-backup-$(date +%Y%m%d).tar.gz ./data/
```

### 更新服务

```bash
# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build

# 启动新版本
docker-compose up -d
```

现在您的心跳监控服务应该可以正常运行了！ 