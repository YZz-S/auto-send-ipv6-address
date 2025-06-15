import json
import os
import sys
import locale
import platform
import socket
from datetime import datetime  # 添加datetime模块导入
from auto_send_ipv6 import send_email, get_ipv6_address, CONFIG_FILE


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


def show_system_info(config):
    """显示系统信息"""
    print(f"系统平台: {platform.system()} {platform.version()}")
    print(f"Python版本: {sys.version}")
    print(f"系统默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print(f"本地设置: {locale.getdefaultlocale()}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"配置文件路径: {os.path.abspath(CONFIG_FILE)}")

    # 显示路径配置
    if "paths" in config:
        print("\n路径配置:")
        print("---------")
        for key, value in config["paths"].items():
            print(f"{key}: {value}")


def test_send_email(ipv6_address, config):
    """测试发送邮件，捕获并显示详细错误信息"""
    # 获取主机名
    hostname = socket.gethostname()
    
    print(f"正在测试邮件发送功能...")
    print(f"发送者: {config['sender_email']}")
    print(f"接收者: {config['receiver_email']}")
    print(f"SMTP服务器: {config['smtp_server']}:{config['smtp_port']}")
    print(f"加密方式: {config.get('smtp_encryption', 'SSL')}")
    
    # 在主题中添加主机名
    subject = f"[{hostname}] IPv6地址测试邮件"
    # 在正文中也添加主机名信息
    body = f"""来自设备 {hostname} 的IPv6地址测试邮件：

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
IPv6地址: {ipv6_address}

此邮件由IPv6地址自动发送程序测试脚本生成，请勿回复。
"""
    print("\n正在发送测试邮件...")
    try:
        # 修正参数顺序，应该是(ipv6_address, config)而不是(config, ipv6_address)
        if send_email(ipv6_address, config):
            print("邮件发送成功！")
            return True
        else:
            print("邮件发送失败，请检查日志获取详细错误信息")
            return False
    except Exception as e:
        print(f"邮件发送过程中发生异常: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("IPv6地址测试工具")
    print("================")

    # 加载配置
    print("\n加载配置...")
    config = load_config()
    if not config:
        print("未能加载配置文件，请检查config.json是否存在并格式正确")
        input("按Enter键退出...")
        return

    # 显示系统信息
    print("\n系统信息:")
    print("---------")
    show_system_info(config)

    # 显示配置信息
    print("\n配置信息:")
    print("---------")
    print(f"SMTP服务器: {config['smtp_server']}")
    print(f"SMTP端口: {config['smtp_port']}")
    print(f"加密方式: {config.get('smtp_encryption', 'SSL')}")
    print(f"发件人邮箱: {config['sender_email']}")
    print(f"接收人邮箱: {config['receiver_email']}")
    print(f"检查间隔: {config['check_interval']}秒")

    # 获取IPv6地址
    print("\n获取IPv6地址:")
    print("------------")
    print("正在获取IPv6地址...")
    ipv6_address = get_ipv6_address()

    if ipv6_address:
        print(f"成功获取IPv6地址: {ipv6_address}")
        # 修正这里的参数顺序
        test_send_email(ipv6_address, config)
    else:
        print("获取IPv6地址失败")

    input("\n测试完成，按Enter键退出...")


if __name__ == "__main__":
    main()
