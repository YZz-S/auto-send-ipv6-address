import os
import json
import time
import threading
import http.server
import socketserver
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List

# 配置日志
log_file = os.environ.get("LOG_PATH", "heartbeat_server.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 设备状态存储
DEVICE_STATUS = {}
CONFIG_FILE = "heartbeat_config.json"
STATUS_FILE = "heartbeat_status.json"


class HeartbeatRequestHandler(http.server.BaseHTTPRequestHandler):
    """处理心跳请求的HTTP处理器"""

    def log_message(self, format, *args):
        """覆盖默认的日志方法，使用我们的日志配置"""
        logging.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        """处理GET请求"""
        # 简单的健康检查
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Heartbeat server is running")
            return

        # 获取所有设备状态
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            status_data = {
                "devices": DEVICE_STATUS,
                "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.wfile.write(json.dumps(status_data, indent=2).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 接收心跳信号"""
        if self.path == "/heartbeat":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length).decode("utf-8")
                try:
                    heartbeat_data = json.loads(post_data)
                    device_id = heartbeat_data.get("device_id")

                    if not device_id:
                        self.send_response(400)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"Missing device_id")
                        return

                    # 更新设备状态
                    now = datetime.now()

                    # 如果是第一次收到此设备的心跳
                    is_new_device = False
                    if device_id not in DEVICE_STATUS:
                        is_new_device = True
                        DEVICE_STATUS[device_id] = {
                            "name": heartbeat_data.get("name", device_id),
                            "description": heartbeat_data.get("description", ""),
                            "first_seen": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "online",
                        }
                        logging.info(f"新设备首次心跳: {device_id}")

                    # 如果设备之前是离线状态
                    was_offline = DEVICE_STATUS[device_id].get("status") == "offline"

                    # 更新心跳信息
                    DEVICE_STATUS[device_id].update(
                        {
                            "last_heartbeat": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "online",
                            "ip": self.client_address[0],
                            "info": heartbeat_data.get("info", {}),
                        }
                    )

                    # 如果不是新设备，且之前是离线状态，则发送恢复通知
                    if not is_new_device and was_offline:
                        device_info = DEVICE_STATUS[device_id].copy()
                        threading.Thread(
                            target=send_status_notification,
                            args=([device_info], [], "recovery"),
                        ).start()
                        logging.info(f"设备已恢复在线: {device_id}")

                    # 保存状态
                    save_status()

                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Heartbeat received")

                except json.JSONDecodeError:
                    self.send_response(400)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Invalid JSON data")
                except Exception as e:
                    logging.error(f"处理心跳请求时出错: {e}")
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Internal server error")
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Empty request body")
        else:
            self.send_response(404)
            self.end_headers()


def load_config() -> dict:
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"配置文件不存在: {CONFIG_FILE}")
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            logging.info(f"成功加载配置文件: {CONFIG_FILE}")
            return config
    except Exception as e:
        logging.error(f"加载配置文件时出错: {e}")
        raise


def save_status():
    """保存设备状态到文件"""
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEVICE_STATUS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存状态文件失败: {e}")


def load_status():
    """从文件加载设备状态"""
    global DEVICE_STATUS
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                DEVICE_STATUS = json.load(f)
                logging.info(f"成功加载状态文件: {STATUS_FILE}")
        except Exception as e:
            logging.error(f"加载状态文件失败: {e}")


def send_status_notification(
    offline_devices: List[Dict],
    online_devices: List[Dict] = None,
    notification_type: str = "offline",
) -> bool:
    """发送设备状态变化通知"""
    config = load_config()
    email_config = config.get("email", {})

    if not email_config:
        logging.error("邮件配置不存在")
        return False

    if not offline_devices and notification_type == "offline":
        return True

    try:
        # 构建邮件内容
        message = MIMEMultipart()

        if notification_type == "offline":
            subject = f"{email_config.get('subject_prefix', '[心跳监控]')} {len(offline_devices)}台设备离线"
            body_title = "设备离线通知"
        else:  # recovery
            subject = f"{email_config.get('subject_prefix', '[心跳监控]')} 设备恢复在线"
            body_title = "设备恢复在线通知"

        message["Subject"] = subject
        message["From"] = email_config["sender_email"]
        message["To"] = email_config["receiver_email"]

        # 邮件正文
        body = f"""{body_title}

监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        if notification_type == "offline":
            body += """
以下设备当前离线:
"""
            for device in offline_devices:
                last_seen = device.get("last_heartbeat", "未知")

                body += f"""
* {device['name']} (ID: {device.get('device_id', '未知')})
  描述: {device.get('description', '无')}
  最后心跳时间: {last_seen}
  IP地址: {device.get('ip', '未知')}
"""
                # 添加额外信息
                info = device.get("info", {})
                if info:
                    body += "  额外信息:\n"
                    for key, value in info.items():
                        body += f"    - {key}: {value}\n"
        else:  # recovery
            body += """
以下设备已恢复在线:
"""
            for (
                device
            ) in offline_devices:  # 这里参数名称保持一致，实际上是恢复在线的设备
                body += f"""
* {device['name']} (ID: {device.get('device_id', '未知')})
  描述: {device.get('description', '无')}
  恢复时间: {device.get('last_heartbeat', '未知')}
  IP地址: {device.get('ip', '未知')}
"""

        if online_devices and notification_type == "offline":
            body += "\n\n当前在线的设备:\n"
            for device in online_devices:
                body += f"* {device['name']} (ID: {device.get('device_id', '未知')})\n"

        body += """
此邮件由心跳监控系统自动发送，请勿回复。
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

        logging.info(f"已发送{body_title}")
        return True

    except Exception as e:
        logging.error(f"发送通知邮件失败: {e}")
        import traceback

        logging.error(traceback.format_exc())
        return False


def check_device_status():
    """检查设备状态，标记离线设备"""
    config = load_config()
    timeout = config.get("heartbeat_timeout", 300)  # 默认5分钟超时

    offline_devices = []
    online_devices = []
    current_time = datetime.now()

    for device_id, device_info in list(DEVICE_STATUS.items()):
        # 如果设备没有last_heartbeat字段，跳过
        if "last_heartbeat" not in device_info:
            continue

        # 计算上次心跳到现在的时间差
        last_heartbeat = datetime.strptime(
            device_info["last_heartbeat"], "%Y-%m-%d %H:%M:%S"
        )
        time_diff = (current_time - last_heartbeat).total_seconds()

        # 如果超时，标记为离线
        if time_diff > timeout:
            # 仅对状态变化的设备进行处理
            if device_info.get("status") == "online":
                device_info["status"] = "offline"
                device_info["offline_since"] = current_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                offline_devices.append(device_info)
                logging.warning(
                    f"设备已离线: {device_id}, 最后心跳: {device_info['last_heartbeat']}"
                )
        else:
            device_info["status"] = "online"
            online_devices.append(device_info)

    # 保存状态
    save_status()

    # 发送离线通知
    if offline_devices:
        send_status_notification(offline_devices, online_devices)


def status_monitor():
    """监控线程，定期检查设备状态"""
    config = load_config()
    check_interval = config.get("check_interval", 60)  # 默认每分钟检查一次

    logging.info(f"状态监控线程启动，检查间隔: {check_interval}秒")

    while True:
        try:
            check_device_status()
            time.sleep(check_interval)
        except Exception as e:
            logging.error(f"状态监控过程中发生错误: {e}")
            import traceback

            logging.error(traceback.format_exc())
            time.sleep(check_interval)


def create_example_config():
    """创建示例配置文件"""
    config = {
        "http_port": 8080,  # 心跳服务器HTTP端口
        "heartbeat_timeout": 300,  # 心跳超时时间（秒）
        "check_interval": 60,  # 状态检查间隔（秒）
        "email": {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "smtp_encryption": "SSL",  # SSL, TLS 或者 None
            "sender_email": "your_email@qq.com",
            "sender_password": "your_email_password",
            "receiver_email": "recipient@example.com",
            "subject_prefix": "[心跳监控]",
        },
    }

    with open("heartbeat_config_example.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("已创建示例配置文件：heartbeat_config_example.json")
    print("请将其重命名为heartbeat_config.json并编辑相关配置后使用。")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="设备心跳监控服务器")
    parser.add_argument(
        "--create-example", "-e", action="store_true", help="创建示例配置文件"
    )
    parser.add_argument(
        "--config", "-c", default="heartbeat_config.json", help="配置文件路径"
    )

    args = parser.parse_args()

    global CONFIG_FILE
    CONFIG_FILE = args.config

    if args.create_example:
        create_example_config()
        return

    try:
        # 加载配置
        config = load_config()

        # 加载之前的状态
        load_status()

        # 设置端口
        port = config.get("http_port", 8080)

        # 启动状态监控线程
        threading.Thread(target=status_monitor, daemon=True).start()

        # 启动HTTP服务器
        with socketserver.TCPServer(("", port), HeartbeatRequestHandler) as httpd:
            logging.info(f"心跳监控服务器启动，监听端口: {port}")
            print(f"心跳监控服务器启动，监听端口: {port}")
            print(f"设备可通过 http://[server-ip]:{port}/heartbeat 发送心跳")
            httpd.serve_forever()

    except FileNotFoundError:
        print(f"配置文件 '{CONFIG_FILE}' 不存在。使用 --create-example 创建示例配置。")
    except Exception as e:
        logging.error(f"服务器启动失败: {e}")
        import traceback

        logging.error(traceback.format_exc())
        print(f"服务器启动失败: {e}")


if __name__ == "__main__":
    main()
