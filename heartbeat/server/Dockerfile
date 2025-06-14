FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和启动脚本
COPY heartbeat_server.py .
COPY start.sh .
COPY entrypoint.sh .
COPY init_config.py .

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

# 启动命令选择 (选择其中一种方式)
# 方式1：使用Python初始化脚本（推荐，包含配置检查）
CMD ["python", "init_config.py"]
# 方式2：使用bash启动脚本
# CMD ["/bin/bash", "/app/start.sh"]  
# 方式3：直接启动Python（简单但无配置检查）
# CMD ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"] 