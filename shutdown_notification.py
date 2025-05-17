import smtplib
import json
import os
import ssl
import socket
from email.mime.text import MIMEText
from datetime import datetime

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_message(f"加载配置文件失败: {e}")
            return None
    else:
        log_message(f"配置文件不存在: {CONFIG_FILE}")
        return None


def log_message(message):
    """记录日志"""
    config = load_config()
    if not config:
        log_file = "shutdown_notification.log"
    else:
        log_file = config["paths"].get("log_file", "shutdown_notification.log")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"写入日志失败: {e}")


def send_shutdown_notification(config):
    """发送关机通知邮件"""
    try:
        # 获取主机名
        hostname = socket.gethostname()

        # 获取最后一次发送的IPv6地址
        last_ipv6 = config.get("last_sent_ipv6", "未知")

        # 创建邮件主题和正文
        subject = f"[{hostname}] 系统关机通知"
        body = f"""设备 {hostname} 正在关机

关机时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
最后记录的IPv6地址: {last_ipv6}

此邮件由关机通知程序自动发送，请勿回复。
"""
        # 创建邮件对象
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = config["sender_email"]
        message["To"] = config["receiver_email"]

        # 设置超时时间较短，以确保在关机过程中能够完成
        timeout = 10  # 秒

        # 连接到SMTP服务器
        encryption = config.get("smtp_encryption", "SSL").upper()

        if encryption == "SSL":
            context = ssl.create_default_context()
            smtp = smtplib.SMTP_SSL(
                config["smtp_server"],
                config["smtp_port"],
                timeout=timeout,
                context=context,
            )
        elif encryption == "TLS":
            smtp = smtplib.SMTP(
                config["smtp_server"], config["smtp_port"], timeout=timeout
            )
            smtp.starttls(context=ssl.create_default_context())
        else:
            smtp = smtplib.SMTP(
                config["smtp_server"], config["smtp_port"], timeout=timeout
            )

        # 登录
        smtp.login(config["sender_email"], config["sender_password"])

        # 发送邮件
        smtp.sendmail(
            config["sender_email"], config["receiver_email"], message.as_string()
        )

        # 关闭连接
        smtp.quit()

        log_message(f"关机通知邮件已成功发送至 {config['receiver_email']}")
        return True
    except Exception as e:
        log_message(f"发送关机通知邮件失败: {e}")
        import traceback

        log_message(traceback.format_exc())
        return False


def main():
    """主函数"""
    log_message("关机通知程序启动")

    # 加载配置
    config = load_config()
    if not config:
        log_message("未能加载配置文件，程序退出")
        return

    # 发送关机通知
    send_shutdown_notification(config)


if __name__ == "__main__":
    main()
