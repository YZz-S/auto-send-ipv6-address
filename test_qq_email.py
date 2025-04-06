import smtplib
import json
import os
from email.mime.text import MIMEText
from auto_send_ipv6 import CONFIG_FILE


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
    print(f"SMTP服务器: {config['smtp_server']}")
    print(f"SMTP端口: {config['smtp_port']}")
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
        message = MIMEText(f"测试邮件内容: IPv6地址 = {test_ipv6}", "plain", "utf-8")
        message["Subject"] = "测试邮件"  # 不使用Header包装
        message["From"] = config["sender_email"]  # 不使用Header包装
        message["To"] = config["receiver_email"]  # 不使用Header包装

        print("\n邮件内容:")
        print(f"From: {message['From']}")
        print(f"To: {message['To']}")
        print(f"Subject: {message['Subject']}")
        print(f"Body: {message.get_payload(decode=True).decode('utf-8')}")

        print("\n连接到SMTP服务器...")
        smtp = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])

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
