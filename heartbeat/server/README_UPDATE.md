# 心跳监控服务器 Docker 一键更新脚本

## 功能特性

✅ **已解决的 Docker 日志问题：**
- 修复了日志只写入文件而不输出到控制台的问题
- 增加了详细的服务器启动信息
- 增强了设备连接/断开的日志记录
- 添加了图标和格式化输出，便于区分不同类型的事件

✅ **更新脚本功能：**
- 自动备份现有配置和数据
- 停止旧容器并清理旧镜像
- 重新构建最新镜像
- 启动新容器并验证服务状态
- 彩色输出和详细日志记录

## 日志改进内容

### 1. 服务器启动日志
现在Docker日志中会显示：
```
🚀 心跳监控服务器启动中...
📋 服务器配置信息
📊 已加载设备状态
🔍 状态监控线程已启动
✅ 心跳监控服务器启动成功！
🌐 监听端口: 8080
📡 心跳接收地址: http://[server-ip]:8080/heartbeat
🖥️ 状态监控页面: http://[server-ip]:8080/
```

### 2. 设备连接日志
```
🔗 新设备连接 - ID: device001, 名称: 测试设备, IP: 192.168.1.100
✅ 设备恢复在线 - ID: device001, 名称: 测试设备, IP: 192.168.1.100 (离线时长: 0:05:30)
```

### 3. 设备离线日志
```
❌ 设备离线 - ID: device001, 名称: 测试设备, IP: 192.168.1.100, 超时时长: 5分30秒
   最后心跳: 2024-01-01 12:00:00
```

## 使用方法

### 在 iStoreOS 中使用

1. **上传脚本到设备**
   ```bash
   # 将 update_docker.sh 上传到服务器目录
   scp update_docker.sh root@your-istoreos-ip:/path/to/heartbeat/server/
   ```

2. **赋予执行权限**
   ```bash
   chmod +x update_docker.sh
   ```

3. **运行更新脚本**
   ```bash
   ./update_docker.sh
   ```

### 手动更新步骤（如果脚本无法运行）

1. **停止现有容器**
   ```bash
   docker-compose down
   # 或者
   docker stop heartbeat-server && docker rm heartbeat-server
   ```

2. **重新构建镜像**
   ```bash
   docker-compose build --no-cache
   # 或者
   docker build --no-cache -t heartbeat-server:latest .
   ```

3. **启动新容器**
   ```bash
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker logs -f heartbeat-server
   ```

## 验证日志输出

更新完成后，使用以下命令查看是否有正确的日志输出：

```bash
# 查看实时日志
docker logs -f heartbeat-server

# 查看最近的日志
docker logs --tail 50 heartbeat-server
```

您应该能看到类似以下的输出：
```
[2024-01-01 12:00:00] INFO: 📋 服务器配置信息:
[2024-01-01 12:00:00] INFO:    心跳超时时间: 300秒
[2024-01-01 12:00:00] INFO:    状态检查间隔: 60秒
[2024-01-01 12:00:00] INFO: 🔍 状态监控线程已启动
[2024-01-01 12:00:00] INFO: ✅ 心跳监控服务器启动成功！
[2024-01-01 12:00:00] INFO: 🌐 监听端口: 8080
```

## 故障排除

### 1. 如果看不到日志输出
- 确认容器是否正在运行：`docker ps`
- 检查容器日志：`docker logs heartbeat-server`
- 查看应用日志文件：`cat data/heartbeat_server.log`

### 2. 如果服务无法启动
- 检查配置文件是否存在：`ls -la data/heartbeat_config.json`
- 查看端口是否被占用：`netstat -tlnp | grep 18080`
- 检查 Docker 镜像是否构建成功：`docker images`

### 3. 如果设备连接后看不到日志
- 确认设备是否正确发送心跳到 `/heartbeat` 端点
- 检查防火墙设置，确保端口 18080 可访问
- 使用 curl 测试：`curl -X POST http://localhost:18080/heartbeat -d '{"device_id":"test","name":"测试设备"}'`

## 文件说明

- `update_docker.sh` - 一键更新脚本
- `heartbeat_server.py` - 已修改的主程序（增强日志功能）
- `docker-compose.yml` - Docker Compose 配置
- `Dockerfile` - Docker 镜像构建文件
- `data/` - 数据目录（配置文件和日志）

## 注意事项

1. **备份重要数据**：脚本会自动备份，但建议手动备份重要配置
2. **网络访问**：确保设备能够访问 Docker Hub 或配置本地镜像仓库
3. **资源需求**：构建过程需要一定的磁盘空间和内存
4. **日志轮转**：建议配置日志轮转避免日志文件过大

更新后，您的心跳监控服务器将提供更详细和用户友好的日志输出！ 