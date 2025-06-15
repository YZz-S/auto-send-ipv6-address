#!/bin/bash

# 设置错误时退出
set -e

echo "=== 心跳监控服务器启动脚本 ==="

# 检查配置文件是否存在
if [ ! -f "/data/heartbeat_config.json" ]; then
    echo "配置文件不存在，正在创建示例配置..."
    
    # 创建示例配置
    python heartbeat_server.py --create-example
    
    # 将示例配置文件移动到正确位置
    if [ -f "heartbeat_config_example.json" ]; then
        mv heartbeat_config_example.json /data/heartbeat_config.json
        echo "✓ 已创建配置文件：/data/heartbeat_config.json"
        echo "⚠️  请根据需要修改配置文件中的邮件设置等参数"
    else
        echo "❌ 创建示例配置文件失败"
        exit 1
    fi
else
    echo "✓ 配置文件已存在：/data/heartbeat_config.json"
fi

# 设置日志文件位置
export LOG_PATH=/data/heartbeat_server.log

echo "=== 启动心跳监控服务器 ==="
echo "配置文件：/data/heartbeat_config.json"
echo "状态文件：/data/heartbeat_status.json"
echo "日志文件：/data/heartbeat_server.log"
echo "================================="

# 启动服务器
exec python heartbeat_server.py --config /data/heartbeat_config.json 