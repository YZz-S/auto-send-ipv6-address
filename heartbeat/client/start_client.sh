#!/bin/bash

echo "=== 心跳监控客户端启动脚本 ==="

# 检查配置文件是否存在
if [ ! -f "heartbeat_client_config.json" ]; then
    echo "配置文件不存在，正在创建示例配置..."
    python3 heartbeat_client.py --create-example
    echo "请编辑 heartbeat_client_config_example.json 文件，并重命名为 heartbeat_client_config.json"
    echo "配置服务器地址等信息后重新运行此脚本"
    exit 1
fi

echo "正在启动心跳客户端..."
python3 heartbeat_client.py 