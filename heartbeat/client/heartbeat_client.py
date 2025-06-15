import os
import json
import time
import socket
import platform
import logging
import requests
import uuid
import subprocess
from datetime import datetime

# 配置日志 - 同时输出到文件和控制台
log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件处理器
file_handler = logging.FileHandler("heartbeat_client.log", encoding="utf-8")
file_handler.setFormatter(log_formatter)

# 控制台处理器（美化输出）
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter(
    "\033[36m[%(asctime)s]\033[0m \033[1m%(levelname)s\033[0m: %(message)s",
    datefmt="%H:%M:%S",
)
console_handler.setFormatter(console_formatter)

# 配置根日志器
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 为了向后兼容，保留原有的 logging 使用方式

# 配置文件路径
CONFIG_FILE = "heartbeat_client_config.json"


def load_config():
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


def get_machine_info():
    """获取机器信息"""
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "boot_time": get_boot_time(),
    }

    # 获取IP地址信息
    ip_info = get_ip_addresses()
    if ip_info:
        info.update(ip_info)

    # 获取磁盘使用情况
    disk_info = get_disk_usage()
    if disk_info:
        info["disk_usage"] = disk_info

    # 获取内存使用情况
    mem_info = get_memory_info()
    if mem_info:
        info["memory"] = mem_info

    # 获取负载信息
    load_info = get_load_info()
    if load_info:
        info["load"] = load_info

    return info


def get_ip_addresses():
    """获取所有网络接口的IP地址"""
    ip_info = {}

    try:
        # 尝试获取主机名对应的IP地址
        primary_ip = socket.gethostbyname(socket.gethostname())
        ip_info["primary_ip"] = primary_ip

        # 获取所有接口的IP地址（仅限于支持的平台）
        if hasattr(socket, "getaddrinfo"):
            try:
                ip_list = []
                # 获取所有网络接口
                for interface in get_network_interfaces():
                    ip_list.append(interface)

                if ip_list:
                    ip_info["interfaces"] = ip_list
            except Exception as e:
                logging.warning(f"获取网络接口信息失败: {e}")
    except Exception as e:
        logging.warning(f"获取IP地址信息失败: {e}")

    return ip_info


def get_network_interfaces():
    """获取网络接口信息，返回格式因操作系统而异"""
    interfaces = []

    try:
        if platform.system() == "Windows":
            # Windows下使用ipconfig命令
            output = subprocess.check_output("ipconfig /all", shell=True).decode("gbk")
            # 简单解析，实际生产环境可能需要更复杂的解析
            interfaces = [
                line.strip()
                for line in output.split("\n")
                if "IPv4" in line or "IPv6" in line
            ]
        else:
            # Linux/MacOS下使用ifconfig命令
            try:
                output = subprocess.check_output("ifconfig", shell=True).decode("utf-8")
            except subprocess.SubprocessError:
                # 某些系统可能使用ip命令
                output = subprocess.check_output("ip addr show", shell=True).decode(
                    "utf-8"
                )

            # 简单解析，实际生产环境可能需要更复杂的解析
            interfaces = [line.strip() for line in output.split("\n") if "inet" in line]
    except Exception as e:
        logging.warning(f"获取网络接口信息失败: {e}")

    return interfaces


def get_boot_time():
    """获取系统启动时间"""
    try:
        if platform.system() == "Windows":
            # Windows下使用wmic命令
            output = subprocess.check_output(
                "wmic os get lastbootuptime", shell=True
            ).decode()
            lines = output.strip().split("\n")
            if len(lines) >= 2:
                # 解析WMIC的时间格式
                boot_time_str = lines[1].strip()
                # 转换格式，仅保留日期和时间部分
                boot_time = f"{boot_time_str[0:4]}-{boot_time_str[4:6]}-{boot_time_str[6:8]} {boot_time_str[8:10]}:{boot_time_str[10:12]}:{boot_time_str[12:14]}"
                return boot_time
        else:
            # Linux/MacOS下使用uptime命令
            output = subprocess.check_output("uptime -s", shell=True).decode().strip()
            return output
    except Exception as e:
        logging.warning(f"获取系统启动时间失败: {e}")

    return "未知"


def get_disk_usage():
    """获取磁盘使用情况"""
    disk_info = []

    try:
        if platform.system() == "Windows":
            # Windows下使用wmic命令
            output = subprocess.check_output(
                "wmic logicaldisk get deviceid,freespace,size", shell=True
            ).decode()
            lines = output.strip().split("\n")
            for line in lines[1:]:  # 跳过标题行
                parts = line.split()
                if len(parts) >= 3:
                    drive = parts[0]
                    try:
                        free = int(parts[1])
                        size = int(parts[2])
                        used = size - free
                        percent = round(used / size * 100, 2) if size > 0 else 0

                        disk_info.append(
                            {
                                "drive": drive,
                                "total": f"{size / (1024**3):.2f}GB",
                                "used": f"{used / (1024**3):.2f}GB",
                                "free": f"{free / (1024**3):.2f}GB",
                                "percent": f"{percent}%",
                            }
                        )
                    except ValueError:
                        pass
        else:
            # Linux/MacOS下使用df命令
            output = subprocess.check_output("df -h", shell=True).decode()
            lines = output.strip().split("\n")
            for line in lines[1:]:  # 跳过标题行
                parts = line.split()
                if len(parts) >= 6:
                    disk_info.append(
                        {
                            "filesystem": parts[0],
                            "size": parts[1],
                            "used": parts[2],
                            "available": parts[3],
                            "percent": parts[4],
                            "mounted": parts[5],
                        }
                    )
    except Exception as e:
        logging.warning(f"获取磁盘使用情况失败: {e}")

    return disk_info


def get_memory_info():
    """获取内存使用情况"""
    try:
        if platform.system() == "Windows":
            # Windows下使用wmic命令
            total_output = subprocess.check_output(
                "wmic OS get TotalVisibleMemorySize /Value", shell=True
            ).decode()
            free_output = subprocess.check_output(
                "wmic OS get FreePhysicalMemory /Value", shell=True
            ).decode()

            total = (
                int(total_output.strip().split("=")[1]) if "=" in total_output else 0
            )
            free = int(free_output.strip().split("=")[1]) if "=" in free_output else 0
            used = total - free
            percent = round(used / total * 100, 2) if total > 0 else 0

            return {
                "total": f"{total / (1024**1):.2f}MB",
                "used": f"{used / (1024**1):.2f}MB",
                "free": f"{free / (1024**1):.2f}MB",
                "percent": f"{percent}%",
            }
        else:
            # Linux下使用free命令
            output = subprocess.check_output("free -m", shell=True).decode()
            lines = output.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 7:
                    total = int(parts[1])
                    used = int(parts[2])
                    free = int(parts[3])
                    percent = round(used / total * 100, 2) if total > 0 else 0

                    return {
                        "total": f"{total}MB",
                        "used": f"{used}MB",
                        "free": f"{free}MB",
                        "percent": f"{percent}%",
                    }
    except Exception as e:
        logging.warning(f"获取内存使用情况失败: {e}")

    return None


def get_load_info():
    """获取系统负载信息"""
    try:
        if platform.system() != "Windows":
            # Linux/MacOS下获取负载信息
            output = subprocess.check_output("uptime", shell=True).decode()
            if "load average" in output:
                load_part = output.split("load average:")[1].strip()
                loads = load_part.split(", ")
                return {"1min": loads[0], "5min": loads[1], "15min": loads[2]}
        else:
            # Windows下获取CPU使用率
            output = subprocess.check_output(
                "wmic cpu get loadpercentage", shell=True
            ).decode()
            lines = output.strip().split("\n")
            if len(lines) >= 2:
                try:
                    cpu_load = int(lines[1].strip())
                    return {"cpu_percent": f"{cpu_load}%"}
                except ValueError:
                    pass
    except Exception as e:
        logging.warning(f"获取系统负载信息失败: {e}")

    return None


def generate_device_id():
    """生成设备ID，优先使用配置中的ID，否则基于主机信息生成"""
    config = load_config()

    # 如果配置中已有设备ID，直接使用
    if "device_id" in config:
        return config["device_id"]

    # 否则，尝试基于主机名和MAC地址生成
    try:
        # 获取主机名
        hostname = socket.gethostname()

        # 尝试获取网卡MAC地址
        mac = uuid.getnode()
        mac_str = ":".join(
            [
                "{:02x}".format((mac >> elements) & 0xFF)
                for elements in range(0, 8 * 6, 8)
            ][::-1]
        )

        # 组合成唯一ID
        device_id = f"{hostname}-{mac_str}"

        # 将生成的ID保存到配置文件
        config["device_id"] = device_id
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return device_id
    except Exception as e:
        logging.error(f"生成设备ID时出错: {e}")
        # 生成随机UUID作为备选
        return str(uuid.uuid4())


def send_heartbeat():
    """发送心跳请求"""
    start_time = time.time()

    try:
        config = load_config()

        # 服务器URL
        server_url = config.get("server_url", "")
        if not server_url:
            logging.error("❌ 配置文件中未指定服务器URL")
            return False

        # 组装心跳URL
        heartbeat_url = f"{server_url.rstrip('/')}/heartbeat"

        # 设备信息
        device_id = generate_device_id()
        device_name = config.get("device_name", socket.gethostname())
        device_description = config.get("description", "")

        logging.info("📡 正在发送心跳信号...")
        logging.info(f"   设备名称: {device_name}")
        logging.info(f"   设备ID: {device_id}")
        logging.info(f"   服务器地址: {server_url}")

        # 附加信息
        logging.info("🔍 收集系统信息...")
        additional_info = get_machine_info()

        # 显示关键系统信息
        if additional_info:
            hostname = additional_info.get("hostname", "未知")
            platform_info = additional_info.get("platform", "未知")
            primary_ip = additional_info.get("primary_ip", "未知")

            logging.info(f"   主机名: {hostname}")
            logging.info(f"   系统: {platform_info}")
            logging.info(f"   IP地址: {primary_ip}")

            # 显示内存和磁盘信息
            memory = additional_info.get("memory")
            if memory:
                logging.info(f"   内存使用: {memory.get('percent', '未知')}")

            disk_usage = additional_info.get("disk_usage")
            if disk_usage and len(disk_usage) > 0:
                main_disk = disk_usage[0]
                disk_percent = main_disk.get("percent", "未知")
                logging.info(f"   磁盘使用: {disk_percent}")

        # 心跳数据
        heartbeat_data = {
            "device_id": device_id,
            "name": device_name,
            "description": device_description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "info": additional_info,
        }

        # 发送请求
        headers = {"Content-Type": "application/json"}
        logging.info(f"🚀 发送心跳数据到 {heartbeat_url}")

        response = requests.post(
            heartbeat_url, data=json.dumps(heartbeat_data), headers=headers, timeout=10
        )

        elapsed_time = round((time.time() - start_time) * 1000, 2)

        # 检查响应
        if response.status_code == 200:
            logging.info(f"✅ 心跳发送成功! 响应时间: {elapsed_time}ms")
            logging.info(f"   服务器响应: {response.text.strip()}")
            return True
        else:
            logging.error("❌ 心跳发送失败!")
            logging.error(f"   状态码: {response.status_code}")
            logging.error(f"   响应内容: {response.text}")
            return False

    except requests.ConnectionError:
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        logging.error(f"🔌 网络连接失败 ({elapsed_time}ms): 无法连接到服务器")
        logging.error("   请检查: 1) 服务器是否运行 2) 网络连接 3) 服务器地址配置")
        return False
    except requests.Timeout:
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        logging.error(f"⏰ 请求超时 ({elapsed_time}ms): 服务器响应过慢")
        return False
    except requests.RequestException as e:
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        logging.error(f"🌐 网络请求出错 ({elapsed_time}ms): {e}")
        return False
    except Exception as e:
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        logging.error(f"💥 发送心跳时出现未知错误 ({elapsed_time}ms): {e}")
        import traceback

        logging.error("%s", traceback.format_exc())
        return False


def create_example_config():
    """创建示例配置文件"""
    config = {
        "server_url": "http://monitor-server-ip:8080",  # 监控服务器URL
        "device_name": socket.gethostname(),  # 设备名称
        "description": "NAT模式下的NAS虚拟机",  # 设备描述
        "heartbeat_interval": 60,  # 心跳间隔（秒）
    }

    with open("heartbeat_client_config_example.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("已创建示例配置文件：heartbeat_client_config_example.json")
    print("请将其重命名为heartbeat_client_config.json并编辑相关配置后使用。")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="设备心跳客户端")
    parser.add_argument(
        "--create-example", "-e", action="store_true", help="创建示例配置文件"
    )
    parser.add_argument(
        "--config", "-c", default="heartbeat_client_config.json", help="配置文件路径"
    )
    parser.add_argument("--once", "-o", action="store_true", help="只发送一次心跳信号")

    args = parser.parse_args()

    global CONFIG_FILE
    CONFIG_FILE = args.config

    if args.create_example:
        create_example_config()
        return

    try:
        if args.once:
            # 只发送一次心跳
            send_heartbeat()
            return

        # 加载配置
        config = load_config()
        heartbeat_interval = config.get("heartbeat_interval", 60)  # 默认60秒
        server_url = config.get("server_url", "未配置")
        device_name = config.get("device_name", socket.gethostname())

        # 启动banner
        print("\n" + "=" * 60)
        print("💓 心跳监控客户端 - Heartbeat Client")
        print("=" * 60)
        print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏷️  设备名称: {device_name}")
        print(f"🌐 服务器地址: {server_url}")
        print(f"⏰ 心跳间隔: {heartbeat_interval}秒")
        print(f"📁 配置文件: {CONFIG_FILE}")
        print(f"📝 日志文件: heartbeat_client.log")
        print("=" * 60)

        logging.info("🚀 心跳监控客户端启动")
        logging.info(f"   配置文件: {CONFIG_FILE}")
        logging.info(f"   设备名称: {device_name}")
        logging.info(f"   服务器地址: {server_url}")
        logging.info(f"   心跳间隔: {heartbeat_interval}秒")

        # 立即发送第一次心跳
        print("\n🔄 开始心跳监控...\n")
        send_heartbeat()

        # 循环发送心跳
        heartbeat_count = 1
        while True:
            time.sleep(heartbeat_interval)
            heartbeat_count += 1
            logging.info(f"📊 第 {heartbeat_count} 次心跳")
            send_heartbeat()

    except FileNotFoundError:
        print(f"配置文件 '{CONFIG_FILE}' 不存在。使用 --create-example 创建示例配置。")
    except KeyboardInterrupt:
        logging.info("收到中断信号，客户端停止")
        print("客户端已停止")
    except Exception as e:
        logging.error(f"客户端运行出错: {e}")
        import traceback

        logging.error("%s", traceback.format_exc())
        print(f"客户端运行出错: {e}")


if __name__ == "__main__":
    main()
