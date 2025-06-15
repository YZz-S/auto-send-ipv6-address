#!/bin/bash

# 创建数据目录
mkdir -p ./data

# 检查配置文件是否存在
if [ ! -f "./data/heartbeat_config.json" ]; then
  echo "配置文件不存在，正在创建示例配置..."
  cat > ./data/heartbeat_config.json << EOF
{
  "http_port": 8080,
  "heartbeat_timeout": 300,
  "check_interval": 60,
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_encryption": "SSL",
    "sender_email": "your_email@qq.com",
    "sender_password": "your_email_password",
    "receiver_email": "recipient@example.com",
    "subject_prefix": "[心跳监控]"
  }
}
EOF
  echo "请编辑 ./data/heartbeat_config.json 文件，配置正确的邮箱信息。"
  echo "按任意键继续..."
  read -n 1
fi

# 启动Docker容器
echo "正在启动心跳监控服务器..."
docker-compose up -d

echo "心跳监控服务器已启动！"
echo "您可以通过以下命令查看日志："
echo "docker-compose logs -f heartbeat-server"
echo ""
echo "服务器地址: http://$(hostname -I | awk '{print $1}'):8080"
echo "请在NAT后的设备上配置心跳客户端，使用上述地址作为服务器URL。" 