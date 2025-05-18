import os
import sys
import socket
import json
from datetime import datetime

# 导入shutdown_notification模块
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
import shutdown_notification

def print_section(title):
    """打印带有分隔线的章节标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "*"))
    print("=" * 50 + "\n")

def test_config_loading():
    """测试配置文件加载"""
    print_section("测试配置文件加载")
    
    config_path = os.path.join(script_dir, "config.json")
    print(f"配置文件路径: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在于 {config_path}")
        return None
    
    config = shutdown_notification.load_config()
    if not config:
        print("错误: 无法加载配置文件")
        return None
    
    print("配置文件加载成功!")
    print(f"SMTP服务器: {config['smtp_server']}")
    print(f"SMTP端口: {config['smtp_port']}")
    print(f"加密方式: {config.get('smtp_encryption', 'SSL')}")
    print(f"发件人邮箱: {config['sender_email']}")
    print(f"收件人邮箱: {config['receiver_email']}")
    print(f"最后记录的IPv6地址: {config.get('last_sent_ipv6', '未知')}")
    
    return config

def test_email_sending(config):
    """测试邮件发送功能"""
    print_section("测试关机通知邮件发送")
    
    if not config:
        print("错误: 无法进行邮件测试，配置不可用")
        return False
    
    print(f"当前主机名: {socket.gethostname()}")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"收件人: {config['receiver_email']}")
    
    try:
        print("\n正在尝试发送测试邮件...")
        result = shutdown_notification.send_shutdown_notification(config)
        
        if result:
            print("测试邮件发送成功!")
            return True
        else:
            print("测试邮件发送失败!")
            return False
    except Exception as e:
        print(f"发送邮件时发生异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_logging():
    """测试日志记录功能"""
    print_section("测试日志记录功能")
    
    log_message = "这是一条测试日志消息 - 来自关机通知测试程序"
    print(f"正在记录测试日志: {log_message}")
    
    shutdown_notification.log_message(log_message)
    
    print("日志记录已尝试，请检查日志文件")

def main():
    """主函数"""
    print_section("关机通知功能测试程序")
    print("此程序将测试关机通知功能的各个组件")
    print("不会实际触发系统关机")
    
    # 测试配置文件加载
    config = test_config_loading()
    
    # 测试日志记录
    test_logging()
    
    # 测试邮件发送
    if config:
        test_email_sending(config)
    
    print_section("测试完成")
    print("如果所有步骤都成功，则表明关机通知功能可以正常工作")
    print("请检查您的邮箱，查看是否收到测试邮件")
    print("同时请检查日志文件，确认日志记录功能正常")

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...") 