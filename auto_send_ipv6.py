import socket
import smtplib
import time
import logging
from email.mime.text import MIMEText
import sys
import os
import json
import subprocess
import re

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "smtp_server": "smtp.example.com",
    "smtp_port": 465,
    "sender_email": "your_email@example.com",
    "sender_password": "your_password",
    "receiver_email": "receiver@example.com",
    "check_interval": 3600,  # 检查间隔，默认为1小时
    "last_sent_ipv6": "",
    "paths": {
        "log_file": "ipv6_sender.log",
        "config_file": "config.json",
        "vbs_script": "start_ipv6_sender.vbs",
        "python_script": "auto_send_ipv6.py",
        "startup_folder": "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
        "shortcut_name": "IPv6AddressSender.lnk",
    },
}


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return DEFAULT_CONFIG
    else:
        # 创建默认配置文件
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        print(f"已创建默认配置文件: {CONFIG_FILE}")
        return DEFAULT_CONFIG


# 先加载配置
config = load_config()

# 配置日志
log_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    config.get("paths", {}).get("log_file", "ipv6_sender.log"),
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file_path,
    filemode="a",
    encoding="utf-8",  # 明确指定UTF-8编码
)
logger = logging.getLogger("auto_send_ipv6")


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("配置已保存")
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")


def get_ipv6_address():
    """获取本机IPv6地址"""
    try:
        # 方法1：通过socket连接获取
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.connect(("2001:4860:4860::8888", 80))  # Google的公共DNS服务器
            ipv6 = s.getsockname()[0]
            s.close()
            logger.info(f"通过socket方法获取到IPv6地址: {ipv6}")
            return ipv6
        except Exception as e:
            logger.warning(f"通过socket获取IPv6地址失败: {e}")

        # 方法2：通过ipconfig命令获取（Windows系统）
        try:
            result = subprocess.check_output("ipconfig", shell=True).decode("gbk")
            # 查找IPv6地址
            ipv6_pattern = r"IPv6.*?: (([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
            matches = re.findall(ipv6_pattern, result)
            if matches:
                # 过滤掉本地链路地址和临时地址
                for match in matches:
                    ipv6 = match[0]
                    if not ipv6.startswith("fe80") and "temporary" not in ipv6.lower():
                        logger.info(f"通过ipconfig命令获取到IPv6地址: {ipv6}")
                        return ipv6
            logger.warning("通过ipconfig命令未找到有效的IPv6地址")
        except Exception as e:
            logger.warning(f"通过ipconfig获取IPv6地址失败: {e}")

        # 如果以上方法都失败了，尝试使用第三方服务获取公网IP
        try:
            import requests

            response = requests.get("https://api6.ipify.org", timeout=5)
            if response.status_code == 200:
                ipv6 = response.text.strip()
                logger.info(f"通过ipify.org获取到IPv6地址: {ipv6}")
                return ipv6
        except Exception as e:
            logger.warning(f"通过ipify.org获取IPv6地址失败: {e}")

        return None
    except Exception as e:
        logger.error(f"获取IPv6地址失败: {e}")
        return None


def send_email(config, ipv6_address):
    """发送邮件"""
    # 邮件内容
    message = MIMEText(f"当前IPv6地址: {ipv6_address}", "plain", "utf-8")

    # 按照RFC标准设置邮件头
    message["From"] = config["sender_email"]  # 直接使用邮箱地址
    message["To"] = config["receiver_email"]  # 直接使用邮箱地址
    message["Subject"] = "IPv6地址通知"  # 直接使用纯文本主题

    try:
        # 使用SSL连接SMTP服务器
        smtp = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        # 登录
        smtp.login(config["sender_email"], config["sender_password"])
        # 发送邮件
        smtp.sendmail(
            config["sender_email"], config["receiver_email"], message.as_string()
        )
        # 关闭连接
        smtp.quit()
        logger.info(f"邮件发送成功，IPv6: {ipv6_address}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def main():
    logger.info("IPv6地址自动发送程序启动")

    # 使用全局配置变量
    global config

    # 重新加载配置，确保使用最新的配置
    config = load_config()

    # 检查配置是否为默认值
    if config["smtp_server"] == DEFAULT_CONFIG["smtp_server"]:
        logger.warning("请先修改配置文件中的默认值")
        print("请先修改配置文件中的默认值，配置文件路径:", CONFIG_FILE)
        input("按Enter键退出...")
        sys.exit(1)

    while True:
        try:
            # 获取IPv6地址
            ipv6_address = get_ipv6_address()

            if ipv6_address:
                logger.info(f"获取到IPv6地址: {ipv6_address}")

                # 如果IPv6地址发生变化，则发送邮件
                if ipv6_address != config["last_sent_ipv6"]:
                    if send_email(config, ipv6_address):
                        # 更新最后发送的IPv6地址
                        config["last_sent_ipv6"] = ipv6_address
                        save_config(config)
            else:
                logger.warning("未获取到IPv6地址")

            # 等待下一次检查
            time.sleep(config["check_interval"])
        except KeyboardInterrupt:
            logger.info("程序被手动终止")
            break
        except Exception as e:
            logger.error(f"运行时发生错误: {e}")
            time.sleep(60)  # 出错后等待一分钟再重试


if __name__ == "__main__":
    main()
