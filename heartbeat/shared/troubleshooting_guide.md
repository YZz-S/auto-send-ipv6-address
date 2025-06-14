# 心跳监控系统问题排查指南

## 🚨 服务器启动无日志输出排查流程

### 第一步：检查Docker服务状态

```bash
# 检查Docker是否运行
docker --version
docker info

# 检查容器状态
docker-compose ps

# 如果没有容器，检查是否启动成功
docker-compose up -d

# 查看所有容器（包括停止的）
docker ps -a
```

### 第二步：查看详细日志

```bash
# 查看容器启动日志
docker-compose logs

# 查看实时日志
docker-compose logs -f

# 查看特定容器日志
docker-compose logs heartbeat-server

# 查看最后50行日志
docker-compose logs --tail=50 heartbeat-server
```

### 第三步：检查配置文件

```bash
# 检查配置文件是否存在
ls -la ./data/

# 查看配置文件内容
cat ./data/heartbeat_config.json

# 验证JSON格式是否正确
python3 -m json.tool ./data/heartbeat_config.json
```

### 第四步：检查端口占用

```bash
# 检查端口13141是否被占用
netstat -tlnp | grep 13141

# 或者使用ss命令
ss -tlnp | grep 13141

# 检查容器内部端口8080
docker-compose exec heartbeat-server netstat -tlnp | grep 8080
```

### 第五步：手动测试容器

```bash
# 进入容器内部
docker-compose exec heartbeat-server bash

# 在容器内手动运行程序
cd /app
python heartbeat_server.py --config /data/heartbeat_config.json

# 查看容器内的文件
ls -la /data/
ls -la /app/
```

### 第六步：重建容器

```bash
# 停止并删除容器
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 重新启动
docker-compose up -d

# 查看启动过程
docker-compose up
```

## 🔧 常见问题及解决方案

### 问题1：配置文件格式错误

**现象：** 容器启动失败，日志显示JSON解析错误

**解决方案：**
```bash
# 检查JSON格式
python3 -m json.tool ./data/heartbeat_config.json

# 如果格式错误，删除并重新生成
rm ./data/heartbeat_config.json
docker-compose up -d
```

### 问题2：端口被占用

**现象：** 容器无法绑定到端口

**解决方案：**
```bash
# 修改docker-compose.yml中的端口映射
# 将 "13141:8080" 改为 "8080:8080" 或其他可用端口
```

### 问题3：邮件配置错误

**现象：** 服务启动但邮件发送失败

**解决方案：**
```bash
# 编辑邮件配置
nano ./data/heartbeat_config.json

# 确保以下配置正确：
# - smtp_server: SMTP服务器地址
# - smtp_port: 端口号
# - sender_email: 发送方邮箱
# - sender_password: 邮箱密码或应用专用密码
```

### 问题4：容器内无法创建文件

**现象：** 权限错误

**解决方案：**
```bash
# 检查data目录权限
ls -la ./data/

# 修改权限
chmod 755 ./data/
sudo chown -R $USER:$USER ./data/
```

## 🧪 测试步骤

### 1. 基础连接测试

```bash
# 测试健康检查端点
curl http://localhost:13141/health

# 如果使用其他端口
curl http://localhost:8080/health

# 测试状态查询
curl http://localhost:13141/status
```

### 2. 发送测试心跳

```bash
curl -X POST http://localhost:13141/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device",  
    "name": "测试设备",
    "description": "服务器测试",
    "info": {
      "test": true,
      "timestamp": "'$(date)'"
    }
  }'
```

### 3. 查看系统资源

```bash
# 检查Docker容器资源使用
docker stats heartbeat-server

# 检查系统资源
top
htop
```

## 📋 收集调试信息

如果问题依然存在，请收集以下信息：

```bash
# 系统信息
uname -a
cat /etc/os-release

# Docker信息  
docker --version
docker-compose --version

# 容器状态
docker-compose ps
docker-compose logs > heartbeat-debug.log

# 网络状态
netstat -tlnp | grep -E "(8080|13141)"

# 文件权限
ls -la ./
ls -la ./data/

# 磁盘空间
df -h
```

## 🚀 一键诊断脚本

创建诊断脚本：

```bash
#!/bin/bash
echo "=== 心跳监控系统诊断脚本 ==="
echo "时间: $(date)"
echo "系统: $(uname -a)"
echo ""

echo "=== Docker状态 ==="
docker --version
docker-compose --version
echo ""

echo "=== 容器状态 ==="
docker-compose ps
echo ""

echo "=== 端口检查 ==="
netstat -tlnp | grep -E "(8080|13141)" || echo "端口未被占用"
echo ""

echo "=== 配置文件检查 ==="
if [ -f "./data/heartbeat_config.json" ]; then
    echo "配置文件存在"
    python3 -m json.tool ./data/heartbeat_config.json > /dev/null && echo "JSON格式正确" || echo "JSON格式错误"
else
    echo "配置文件不存在"
fi
echo ""

echo "=== 最近日志 ==="
docker-compose logs --tail=20 2>/dev/null || echo "无法获取日志"
echo ""

echo "=== 健康检查 ==="
curl -s http://localhost:13141/health || curl -s http://localhost:8080/health || echo "服务无响应"
```

保存为 `diagnose.sh` 并运行：
```bash
chmod +x diagnose.sh
./diagnose.sh
``` 