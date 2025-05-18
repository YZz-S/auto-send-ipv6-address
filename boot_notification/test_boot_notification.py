import json
import os
import sys
import locale
import platform
import socket
from datetime import datetime
from boot_notification import send_boot_notification, load_config, CONFIG_FILE

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

def main():
    print("开机通知测试工具")
    print("==============")

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

    # 测试发送开机通知
    print("\n测试发送开机通知:")
    print("---------------")
    
    choice = input("是否发送测试通知邮件？(y/n): ")
    if choice.lower() == 'y':
        print("正在发送测试通知...")
        if send_boot_notification(config):
            print("通知邮件发送成功！")
        else:
            print("通知邮件发送失败，请检查日志获取详细错误信息")
    else:
        print("已取消发送测试通知")

    input("\n测试完成，按Enter键退出...")

if __name__ == "__main__":
    main()