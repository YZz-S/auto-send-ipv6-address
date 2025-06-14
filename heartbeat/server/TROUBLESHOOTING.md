# 故障排除指南

## 🚨 问题：`exec /app/start.sh: no such file or directory`

### 问题原因
这个错误通常由以下原因引起：
1. **文件格式问题**：Windows换行符(\r\n)与Unix换行符(\n)不兼容
2. **文件权限问题**：脚本没有执行权限
3. **文件路径问题**：文件未正确复制到容器中

### 解决方案

#### 方案1：使用修复后的Dockerfile（推荐）
已经修复了Windows换行符问题：
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 方案2：使用备用启动脚本
如果start.sh仍有问题，可以使用entrypoint.sh：
```dockerfile
# 在Dockerfile中改为：
CMD ["/bin/bash", "/app/entrypoint.sh"]
```

#### 方案3：直接启动Python（最可靠）
```dockerfile
# 在Dockerfile中改为：
CMD ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"]
```

### 调试步骤

#### 1. 检查容器内文件
```bash
# 进入容器检查文件
docker run --rm -it heartbeat-server:latest bash
ls -la /app/
cat /app/start.sh
```

#### 2. 手动修复权限
```bash
# 如果容器已启动但脚本无法执行
docker exec -it heartbeat-server bash
chmod +x /app/start.sh
/app/start.sh
```

#### 3. 检查文件格式
```bash
# 在容器内检查文件格式
file /app/start.sh
# 如果显示 "with CRLF line terminators"，则需要转换
sed -i 's/\r$//' /app/start.sh
```

### 验证启动成功
```bash
# 检查容器状态
docker-compose ps

# 查看启动日志
docker-compose logs -f heartbeat-server

# 测试服务接口
curl http://localhost:18080/health
```

## ✅ 推荐的Dockerfile配置

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和启动脚本
COPY heartbeat_server.py .
COPY start.sh .
COPY entrypoint.sh .

# 创建配置目录和数据目录
RUN mkdir -p /data

# 修复文件格式并设置权限
RUN sed -i 's/\r$//' /app/start.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/start.sh && \
    chmod +x /app/entrypoint.sh

# 设置环境变量
ENV CONFIG_PATH=/data/heartbeat_config.json
ENV STATUS_PATH=/data/heartbeat_status.json
ENV LOG_PATH=/data/heartbeat_server.log

# 暴露端口
EXPOSE 8080

# 启动命令（多种方式，选择一种）
# 方式1：使用bash明确调用脚本（推荐）
CMD ["/bin/bash", "/app/start.sh"]

# 方式2：使用备用脚本
# CMD ["/bin/bash", "/app/entrypoint.sh"]

# 方式3：直接启动Python（最可靠）
# CMD ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"]
```

## 🔧 针对iStoreOS的特殊说明

如果你在iStoreOS上仍然遇到问题，建议：

1. **使用直接启动方式**：
   ```dockerfile
   CMD ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"]
   ```

2. **检查Docker版本兼容性**：
   ```bash
   docker --version
   docker-compose --version
   ```

3. **使用简化的启动方式**：
   ```yaml
   # 在docker-compose.yml中直接指定命令
   services:
     heartbeat-server:
       # ... 其他配置
       command: ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"]
   ``` 