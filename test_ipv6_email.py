import json
import os
import sys
import locale
import platform
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


def test_send_email(config, ipv6_address):
    """测试发送邮件，捕获并显示详细错误信息"""
    print("\n正在发送测试邮件...")
    try:
        if send_email(config, ipv6_address):
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

        # 测试发送邮件
        test_send_email(config, ipv6_address)
    else:
        print("未能获取IPv6地址，请检查网络连接和IPv6支持情况")

    input("\n测试完成，按Enter键退出...")


if __name__ == "__main__":
    main()
