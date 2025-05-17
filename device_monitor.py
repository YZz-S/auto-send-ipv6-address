import os
import json
import time
import socket
import smtplib
import logging
import argparse
import ipaddress
import subprocess
import platform
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Tuple, Union


# 配置日志
logging.basicConfig(
    filename="device_monitor.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class DeviceMonitor:
    """设备监控类，用于检测设备是否在线并发送通知"""

    def __init__(self, config_file: str = "monitor_config.json"):
        """初始化监控器"""
        self.config_file = config_file
        self.config = self._load_config()
        self.device_status = {}  # 保存设备状态历史
        self.first_check = True  # 是否为第一次检查

    def _load_config(self) -> dict:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            logging.error(f"配置文件不存在: {self.config_file}")
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                logging.info(f"成功加载配置文件: {self.config_file}")
                return config
        except Exception as e:
            logging.error(f"加载配置文件时出错: {e}")
            raise

    def _save_status(self):
        """保存设备状态到文件"""
        status_file = self.config.get("status_file", "device_status.json")
        try:
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(self.device_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存状态文件失败: {e}")

    def _load_status(self):
        """从文件加载设备状态"""
        status_file = self.config.get("status_file", "device_status.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    self.device_status = json.load(f)
                    self.first_check = False
            except Exception as e:
                logging.error(f"加载状态文件失败: {e}")

    def ping(self, host: str, count: int = 4, timeout: int = 2) -> bool:
        """检查主机是否可以通过ping访问"""
        os_name = platform.system().lower()

        try:
            if os_name == "windows":
                # Windows系统下的ping命令
                args = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
                result = subprocess.run(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout * count + 5,
                )
                return result.returncode == 0
            else:
                # Linux/macOS系统下的ping命令
                args = ["ping", "-c", str(count), "-W", str(timeout), host]
                result = subprocess.run(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout * count + 5,
                )
                return result.returncode == 0
        except Exception as e:
            logging.error(f"ping {host} 时出错: {e}")
            return False

    def check_tcp_port(self, host: str, port: int, timeout: int = 2) -> bool:
        """检查主机的TCP端口是否开放"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((host, port))
                return result == 0
        except Exception as e:
            logging.error(f"检查 {host}:{port} 时出错: {e}")
            return False

    def is_device_online(self, device: dict) -> bool:
        """检查设备是否在线"""
        host = device["ip"]
        check_method = device.get("check_method", "ping")

        if check_method == "ping":
            return self.ping(host)
        elif check_method == "tcp":
            port = device.get("port", 80)
            return self.check_tcp_port(host, port)
        else:
            logging.error(f"不支持的检查方法: {check_method}")
            return False

    def send_notification(
        self, offline_devices: List[dict], online_devices: List[dict] = None
    ) -> bool:
        """发送离线设备通知"""
        if not offline_devices:
            return True

        email_config = self.config.get("email", {})
        if not email_config:
            logging.error("邮件配置不存在")
            return False

        try:
            # 构建邮件内容
            message = MIMEMultipart()
            message["Subject"] = (
                email_config.get("subject_prefix", "[设备监控]")
                + f" {len(offline_devices)}台设备离线"
            )
            message["From"] = email_config["sender_email"]
            message["To"] = email_config["receiver_email"]

            # 邮件正文
            body = f"""设备离线通知

监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

以下设备当前离线:
"""
            for device in offline_devices:
                last_seen = self.device_status.get(device["ip"], {}).get(
                    "last_online", "从未在线"
                )
                if isinstance(last_seen, str):
                    last_online_str = last_seen
                else:
                    last_online_str = datetime.fromtimestamp(last_seen).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                body += f"""
* {device['name']} ({device['ip']})
  备注: {device.get('description', '无')}
  最后在线时间: {last_online_str}
"""

            if online_devices:
                body += "\n\n以下设备当前在线:\n"
                for device in online_devices:
                    body += f"* {device['name']} ({device['ip']})\n"

            body += """
此邮件由设备监控系统自动发送，请勿回复。
"""

            message.attach(MIMEText(body, "plain", "utf-8"))

            # 连接SMTP服务器并发送
            smtp_server = email_config["smtp_server"]
            smtp_port = email_config["smtp_port"]
            smtp_user = email_config["sender_email"]
            smtp_password = email_config["sender_password"]

            encryption = email_config.get("smtp_encryption", "SSL").upper()

            if encryption == "SSL":
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            elif encryption == "TLS":
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)

            server.login(smtp_user, smtp_password)
            server.send_message(message)
            server.quit()

            logging.info(f"已发送离线设备通知：{len(offline_devices)}台设备")
            return True

        except Exception as e:
            logging.error(f"发送邮件通知失败: {e}")
            import traceback

            logging.error(traceback.format_exc())
            return False

    def check_devices(
        self, send_notification: bool = True
    ) -> Tuple[List[dict], List[dict]]:
        """检查所有设备状态"""
        devices = self.config.get("devices", [])
        if not devices:
            logging.warning("没有配置任何设备")
            return [], []

        online_devices = []
        offline_devices = []
        current_time = time.time()

        for device in devices:
            ip = device["ip"]
            device_id = f"{device['name']}({ip})"

            # 如果是第一次检查，加载之前的状态
            if self.first_check and not self.device_status:
                self._load_status()

            # 初始化设备状态记录
            if ip not in self.device_status:
                self.device_status[ip] = {
                    "name": device["name"],
                    "last_status": "unknown",
                    "last_check": current_time,
                    "last_status_change": current_time,
                }

            is_online = self.is_device_online(device)

            # 更新设备状态
            previous_status = self.device_status[ip].get("last_status")
            self.device_status[ip]["last_check"] = current_time

            if is_online:
                self.device_status[ip]["last_status"] = "online"
                self.device_status[ip]["last_online"] = current_time
                online_devices.append(device)

                # 如果设备从离线恢复为在线，记录状态变化
                if previous_status == "offline":
                    self.device_status[ip]["last_status_change"] = current_time
                    logging.info(f"设备 {device_id} 恢复在线")

                    # 如果配置了设备恢复通知，则发送
                    if self.config.get("notify_when_back_online", False):
                        recover_device = device.copy()
                        recover_device["recovery"] = True
                        self.send_notification([recover_device], send_recovery=True)
            else:
                self.device_status[ip]["last_status"] = "offline"
                offline_devices.append(device)

                # 如果设备从在线变为离线，记录状态变化
                if previous_status == "online":
                    self.device_status[ip]["last_status_change"] = current_time
                    logging.warning(f"设备 {device_id} 已离线")

        # 保存状态到文件
        self._save_status()

        # 发送通知
        if offline_devices and send_notification and not self.first_check:
            self.send_notification(
                offline_devices,
                (
                    online_devices
                    if self.config.get("include_online_in_report", True)
                    else None
                ),
            )

        self.first_check = False
        return offline_devices, online_devices

    def start_monitoring(self):
        """开始监控设备"""
        check_interval = self.config.get("check_interval", 300)  # 默认5分钟检查一次

        logging.info(f"设备监控服务启动，检查间隔: {check_interval}秒")

        try:
            while True:
                offline, online = self.check_devices()
                total = len(offline) + len(online)
                logging.info(
                    f"检查完成: 共{total}台设备，{len(online)}台在线，{len(offline)}台离线"
                )

                # 睡眠到下一次检查
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logging.info("接收到中断信号，监控服务已停止")
        except Exception as e:
            logging.error(f"监控过程中发生错误: {e}")
            import traceback

            logging.error(traceback.format_exc())


def create_example_config():
    """创建示例配置文件"""
    config = {
        "check_interval": 300,  # 检查间隔，单位：秒
        "notify_when_back_online": True,  # 设备恢复在线时是否通知
        "include_online_in_report": True,  # 在离线报告中是否包含在线设备信息
        "status_file": "device_status.json",  # 状态保存文件
        "email": {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "smtp_encryption": "SSL",  # SSL, TLS 或者 None
            "sender_email": "your_email@qq.com",
            "sender_password": "your_email_password",
            "receiver_email": "recipient@example.com",
            "subject_prefix": "[设备监控]",
        },
        "devices": [
            {
                "name": "家庭服务器",
                "ip": "192.168.1.100",
                "check_method": "ping",  # ping 或 tcp
                "description": "存储服务器，运行NAS系统",
            },
            {
                "name": "工作站",
                "ip": "192.168.1.101",
                "check_method": "ping",
                "description": "日常开发使用的工作站",
            },
            {
                "name": "树莓派",
                "ip": "192.168.1.102",
                "check_method": "tcp",
                "port": 22,  # 如果check_method是tcp，指定检查端口
                "description": "智能家居控制中心",
            },
        ],
    }

    with open("monitor_config_example.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("已创建示例配置文件：monitor_config_example.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="设备在线状态监控工具")
    parser.add_argument(
        "--config", "-c", default="monitor_config.json", help="配置文件路径"
    )
    parser.add_argument(
        "--check-once", "-o", action="store_true", help="只检查一次不持续监控"
    )
    parser.add_argument(
        "--create-example", "-e", action="store_true", help="创建示例配置文件"
    )

    args = parser.parse_args()

    if args.create_example:
        create_example_config()
        return

    try:
        monitor = DeviceMonitor(args.config)

        if args.check_once:
            offline, online = monitor.check_devices()
            print(
                f"检查完成: 共{len(offline) + len(online)}台设备，{len(online)}台在线，{len(offline)}台离线"
            )
            if offline:
                print("\n离线设备:")
                for device in offline:
                    print(
                        f"  - {device['name']} ({device['ip']}) - {device.get('description', '无描述')}"
                    )
            if online:
                print("\n在线设备:")
                for device in online:
                    print(
                        f"  - {device['name']} ({device['ip']}) - {device.get('description', '无描述')}"
                    )
        else:
            monitor.start_monitoring()

    except FileNotFoundError:
        print(f"配置文件 '{args.config}' 不存在。使用 --create-example 创建示例配置。")
        return

    except Exception as e:
        print(f"发生错误: {e}")
        return


if __name__ == "__main__":
    main()
