import os
import sys
import time
import subprocess
import platform
import logging
from datetime import datetime


# 设置日志记录
logging.basicConfig(
    filename="shutdown_helper.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def send_notification_and_shutdown(shutdown_type="shutdown", delay=60):
    """
    发送通知并执行关机操作

    参数:
        shutdown_type: 关机类型 (shutdown, restart, logoff)
        delay: 延迟关机时间(秒)
    """
    try:
        # 记录操作开始
        logging.info(f"启动 {shutdown_type} 操作")

        # 执行通知脚本
        script_dir = os.path.dirname(os.path.abspath(__file__))
        notification_script = os.path.join(script_dir, "shutdown_notification.py")

        logging.info(f"运行通知脚本: {notification_script}")

        # 运行通知脚本并给它足够的时间完成
        subprocess.run([sys.executable, notification_script], timeout=30)

        # 等待一小段时间确保通知已发送
        time.sleep(5)

        # 根据操作系统执行相应的关机命令
        os_name = platform.system().lower()
        logging.info(f"在 {os_name} 系统上执行{shutdown_type}命令")

        if os_name == "windows":
            if shutdown_type == "shutdown":
                cmd = f'shutdown /s /t {delay} /c "系统将在{delay}秒后关机"'
            elif shutdown_type == "restart":
                cmd = f'shutdown /r /t {delay} /c "系统将在{delay}秒后重启"'
            elif shutdown_type == "logoff":
                cmd = f"shutdown /l /t {delay}"
            else:
                logging.error(f"不支持的关机类型: {shutdown_type}")
                return False
        elif os_name in ["linux", "darwin"]:  # Linux 或 macOS
            if shutdown_type == "shutdown":
                cmd = f"shutdown -h +{int(delay/60)}"
            elif shutdown_type == "restart":
                cmd = f"shutdown -r +{int(delay/60)}"
            elif shutdown_type == "logoff":
                logging.error("Linux/macOS不直接支持登出操作")
                return False
            else:
                logging.error(f"不支持的关机类型: {shutdown_type}")
                return False
        else:
            logging.error(f"不支持的操作系统: {os_name}")
            return False

        # 执行命令
        logging.info(f"执行命令: {cmd}")
        os.system(cmd)

        return True

    except Exception as e:
        logging.error(f"执行过程中发生错误: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return False


def main():
    """主函数: 处理命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description="发送通知并执行关机/重启/注销操作")
    parser.add_argument(
        "--type",
        choices=["shutdown", "restart", "logoff"],
        default="shutdown",
        help="操作类型",
    )
    parser.add_argument("--delay", type=int, default=60, help="延迟时间(秒)")

    args = parser.parse_args()

    success = send_notification_and_shutdown(args.type, args.delay)
    if not success:
        print("操作未能成功完成，请查看日志了解详情")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
