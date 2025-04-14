import smtplib
import json
import os
import ssl
from email.mime.text import MIMEText
from auto_send_ipv6 import CONFIG_FILE
import socket
from datetime import datetime  # 修改导入方式，直接导入datetime类而不是整个模块


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return None
    else:
        print(f"配置文件不存在: {CONFIG_FILE}")
        return None


def test_qq_email(config):
    """专门测试QQ邮箱的SMTP发送功能"""
    # 获取主机名
    hostname = socket.gethostname()
    
    print(f"正在测试QQ邮箱SMTP功能...")
    print(f"发送者: {config['sender_email']}")
    print(f"接收者: {config['receiver_email']}")
    print(f"SMTP服务器: {config['smtp_server']}:{config['smtp_port']}")
    print(f"加密方式: {config.get('smtp_encryption', 'SSL')}")
    
    # 在主题中添加主机名
    subject = f"[{hostname}] QQ邮箱SMTP测试邮件"
    # 在正文中也添加主机名信息
    body = f"""来自设备 {hostname} 的QQ邮箱SMTP测试邮件：

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试IPv6地址: 2001:db8::1234

此邮件由IPv6地址自动发送程序的QQ邮箱测试脚本生成，请勿回复。
"""
    print(f"发件人邮箱: {config['sender_email']}")
    print(f"收件人邮箱: {config['receiver_email']}")

    # 显示路径配置
    if "paths" in config:
        print("\n路径配置:")
        for key, value in config["paths"].items():
            print(f"{key}: {value}")

    test_ipv6 = "2001:db8::1234"  # 测试用的IPv6地址

    # 创建邮件对象
    print("\n创建邮件对象...")
    try:
        # 使用正确的主题和正文
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = config["sender_email"]
        message["To"] = config["receiver_email"]

        print("\n邮件内容:")
        print(f"From: {message['From']}")
        print(f"To: {message['To']}")
        print(f"Subject: {message['Subject']}")
        print(f"Body: {message.get_payload(decode=True).decode('utf-8')}")

        print("\n连接到SMTP服务器...")
        encryption = config.get("smtp_encryption", "SSL").upper()

        if encryption == "SSL":
            print("使用SSL加密连接")
            smtp = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        elif encryption == "TLS":
            print("使用TLS加密连接")
            smtp = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            smtp.starttls(context=ssl.create_default_context())
        else:
            print("警告: 使用非加密连接（不推荐）")
            smtp = smtplib.SMTP(config["smtp_server"], config["smtp_port"])

        print("登录...")
        smtp.login(config["sender_email"], config["sender_password"])

        print("发送邮件...")
        smtp.sendmail(
            config["sender_email"], config["receiver_email"], message.as_string()
        )

        print("关闭连接...")
        smtp.quit()

        print("\n邮件发送成功！")
        return True
    except Exception as e:
        print(f"\n发送邮件时出错: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("QQ邮箱SMTP测试工具")
    print("==================")

    # 加载配置
    print("\n加载配置...")
    config = load_config()
    if not config:
        print("未能加载配置文件")
        input("按Enter键退出...")
        return

    # 检查是否是QQ邮箱
    if "qq.com" not in config["smtp_server"].lower():
        print(f"警告: 当前SMTP服务器不是QQ邮箱 ({config['smtp_server']})")
        print("这个测试脚本专为QQ邮箱设计，但仍将继续测试...")

    # 测试发送
    test_qq_email(config)

    input("\n按Enter键退出...")


if __name__ == "__main__":
    main()
