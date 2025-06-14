#!/bin/bash
set -e

echo "=== 心跳监控服务器启动 ==="

# 检查配置文件
if [ ! -f "/data/heartbeat_config.json" ]; then
    echo "创建默认配置文件..."
    python heartbeat_server.py --create-example
    mv heartbeat_config_example.json /data/heartbeat_config.json
    echo "✓ 配置文件已创建：/data/heartbeat_config.json"
fi

# 设置环境变量
export LOG_PATH=/data/heartbeat_server.log

echo "启动心跳监控服务器..."
exec python heartbeat_server.py --config /data/heartbeat_config.json 