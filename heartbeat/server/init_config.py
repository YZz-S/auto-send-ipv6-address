#!/usr/bin/env python3
"""
配置文件初始化脚本
用于在容器启动时检查和创建配置文件
"""
import os
import sys
import json


def create_default_config():
    """创建默认配置文件"""
    config = {
        "http_port": 8080,
        "heartbeat_timeout": 300,
        "check_interval": 60,
        "email": {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "smtp_encryption": "SSL",
            "sender_email": "your_email@qq.com",
            "sender_password": "your_email_password_or_app_password",
            "receiver_email": "recipient@example.com",
            "subject_prefix": "[心跳监控]",
        },
    }
    return config


def init_config():
    """初始化配置文件"""
    config_path = "/data/heartbeat_config.json"

    print("=== 心跳监控服务器配置初始化 ===")

    # 确保data目录存在
    os.makedirs("/data", exist_ok=True)

    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        print("配置文件不存在，正在创建默认配置...")

        try:
            # 创建默认配置
            config = create_default_config()
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"✓ 已创建配置文件：{config_path}")
            print("⚠️  请根据需要修改配置文件中的邮件设置等参数")

        except Exception as e:
            print(f"❌ 创建配置文件失败：{e}")
            return False
    else:
        print(f"✓ 配置文件已存在：{config_path}")

    return True


if __name__ == "__main__":
    # 初始化配置
    if not init_config():
        sys.exit(1)

    print("=== 启动心跳监控服务器 ===")
    print("配置文件：/data/heartbeat_config.json")
    print("状态文件：/data/heartbeat_status.json")
    print("日志文件：/data/heartbeat_server.log")
    print("=================================")

    # 设置环境变量
    os.environ["LOG_PATH"] = "/data/heartbeat_server.log"

    # 启动主程序
    try:
        os.execv(
            sys.executable,
            [
                sys.executable,
                "heartbeat_server.py",
                "--config",
                "/data/heartbeat_config.json",
            ],
        )
    except Exception as e:
        print(f"❌ 启动服务器失败：{e}")
        sys.exit(1)
