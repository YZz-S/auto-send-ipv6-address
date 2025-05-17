FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY heartbeat_server.py .

# 创建配置目录和数据目录
RUN mkdir -p /data

# 设置环境变量
ENV CONFIG_PATH=/data/heartbeat_config.json
ENV STATUS_PATH=/data/heartbeat_status.json
ENV LOG_PATH=/data/heartbeat_server.log

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "heartbeat_server.py", "--config", "/data/heartbeat_config.json"] 