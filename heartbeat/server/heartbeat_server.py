import os
import json
import time
import threading
import http.server
import socketserver
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List

# 配置日志
log_file = os.environ.get("LOG_PATH", "heartbeat_server.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 设备状态存储
DEVICE_STATUS = {}
CONFIG_FILE = "heartbeat_config.json"
STATUS_FILE = "heartbeat_status.json"


class HeartbeatRequestHandler(http.server.BaseHTTPRequestHandler):
    """处理心跳请求的HTTP处理器"""

    # 服务器启动时间
    _server_start_time = datetime.now()

    def log_message(self, format, *args):
        """覆盖默认的日志方法，使用我们的日志配置"""
        logging.info(f"{self.client_address[0]} - {format % args}")

    def get_server_uptime(self):
        """获取服务器运行时长"""
        uptime = datetime.now() - self._server_start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟 {seconds}秒"

    def generate_status_page(self):
        """生成设备状态页面"""
        online_devices = [
            d for d in DEVICE_STATUS.values() if d.get("status") == "online"
        ]
        offline_devices = [
            d for d in DEVICE_STATUS.values() if d.get("status") == "offline"
        ]

        # 如果没有设备
        if not DEVICE_STATUS:
            devices_html = """
            <div class="no-devices">
                <div class="icon">🔍</div>
                <h3>暂无设备连接</h3>
                <p>还没有设备连接到监控服务器</p>
                <div class="help-info">
                    <h4>📋 如何连接设备？</h4>
                    <div class="steps">
                        <div class="step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <strong>配置客户端</strong>
                                <p>在需要监控的设备上配置心跳客户端</p>
                            </div>
                        </div>
                        <div class="step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <strong>设置服务器地址</strong>
                                <p>配置服务器地址：<code>http://此服务器IP:端口</code></p>
                            </div>
                        </div>
                        <div class="step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <strong>启动监控</strong>
                                <p>启动客户端程序开始发送心跳信号</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        else:
            devices_html = ""

            # 在线设备
            if online_devices:
                devices_html += '<div class="section-title">🟢 在线设备</div>'
                for device_id, device in DEVICE_STATUS.items():
                    if device.get("status") == "online":
                        info = device.get("info", {})

                        # 提取关键系统信息
                        system_info_brief = ""
                        if info:
                            hostname = info.get("hostname", "")
                            primary_ip = info.get("primary_ip", "")
                            memory = info.get("memory", {})
                            disk_usage = info.get("disk_usage", [])

                            memory_percent = (
                                memory.get("percent", "未知") if memory else "未知"
                            )
                            disk_percent = "未知"
                            if disk_usage and len(disk_usage) > 0:
                                disk_percent = disk_usage[0].get("percent", "未知")

                            system_info_brief = f"""
                            <div class="system-brief">
                                <span class="info-tag">🖥️ {hostname}</span>
                                <span class="info-tag">🌐 {primary_ip}</span>
                                <span class="info-tag">💾 内存 {memory_percent}</span>
                                <span class="info-tag">💿 磁盘 {disk_percent}</span>
                            </div>
                            """

                        devices_html += f"""
                        <div class="device-card online" data-device="{device_id.lower()} {device['name'].lower()}">
                            <div class="device-header">
                                <div class="device-title">
                                    <h4>{device['name']}</h4>
                                    <span class="device-id">{device_id}</span>
                                </div>
                                <div class="status-indicators">
                                    <span class="status-badge online">
                                        <span class="status-dot"></span>
                                        在线
                                    </span>
                                    <div class="signal-strength">
                                        <div class="signal-bar"></div>
                                        <div class="signal-bar"></div>
                                        <div class="signal-bar"></div>
                                        <div class="signal-bar"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="device-info">
                                <div class="basic-info">
                                    <div class="info-row">
                                        <span class="info-label">📝 描述</span>
                                        <span class="info-value">{device.get('description', '无')}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">🌐 IP地址</span>
                                        <span class="info-value">{device.get('ip', '未知')}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">💓 最后心跳</span>
                                        <span class="info-value">{device.get('last_heartbeat', '未知')}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">🚀 首次连接</span>
                                        <span class="info-value">{device.get('first_seen', '未知')}</span>
                                    </div>
                                </div>
                                {system_info_brief}
                        """

                        if info:
                            devices_html += """
                                <div class="system-details" style="display: none;">
                                    <h5>📊 详细系统信息</h5>
                                    <div class="system-grid">
                            """
                            for key, value in info.items():
                                if isinstance(value, dict):
                                    if key == "memory" and value:
                                        devices_html += f"""
                                        <div class="system-item">
                                            <span class="system-label">💾 内存</span>
                                            <span class="system-value">已用 {value.get('used', '未知')} / 总计 {value.get('total', '未知')} ({value.get('percent', '未知')})</span>
                                        </div>
                                        """
                                    elif key == "disk_usage" and value:
                                        for disk in value[:2]:  # 只显示前2个磁盘
                                            drive_name = disk.get(
                                                "drive", disk.get("filesystem", "未知")
                                            )
                                            devices_html += f"""
                                            <div class="system-item">
                                                <span class="system-label">💿 {drive_name}</span>
                                                <span class="system-value">{disk.get('used', '未知')} / {disk.get('total', disk.get('size', '未知'))} ({disk.get('percent', '未知')})</span>
                                            </div>
                                            """
                                    else:
                                        devices_html += f"""
                                        <div class="system-item">
                                            <span class="system-label">{key}</span>
                                            <span class="system-value">{json.dumps(value, ensure_ascii=False)}</span>
                                        </div>
                                        """
                                else:
                                    icon = (
                                        "🖥️"
                                        if key == "hostname"
                                        else "🔧" if key == "platform" else "📈"
                                    )
                                    devices_html += f"""
                                    <div class="system-item">
                                        <span class="system-label">{icon} {key}</span>
                                        <span class="system-value">{value}</span>
                                    </div>
                                    """
                            devices_html += """
                                    </div>
                                    <button class="toggle-details" onclick="hideDetails(this)">收起详情 ▲</button>
                                </div>
                                <button class="toggle-details" onclick="showDetails(this)">查看详情 ▼</button>
                            """

                        devices_html += "</div></div>"

            # 离线设备
            if offline_devices:
                devices_html += '<div class="section-title">🔴 离线设备</div>'
                for device_id, device in DEVICE_STATUS.items():
                    if device.get("status") == "offline":
                        devices_html += f"""
                        <div class="device-card offline" data-device="{device_id.lower()} {device['name'].lower()}">
                            <div class="device-header">
                                <div class="device-title">
                                    <h4>{device['name']}</h4>
                                    <span class="device-id">{device_id}</span>
                                </div>
                                <div class="status-indicators">
                                    <span class="status-badge offline">
                                        <span class="status-dot"></span>
                                        离线
                                    </span>
                                </div>
                            </div>
                            <div class="device-info">
                                <div class="basic-info">
                                    <div class="info-row">
                                        <span class="info-label">📝 描述</span>
                                        <span class="info-value">{device.get('description', '无')}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">💓 最后心跳</span>
                                        <span class="info-value">{device.get('last_heartbeat', '未知')}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">🔴 离线时间</span>
                                        <span class="info-value">{device.get('offline_since', '未知')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """

        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>设备监控状态 - 心跳监控系统</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }}
        
        .container {{ 
            max-width: 1400px; margin: 0 auto; padding: 20px;
            background: rgba(255,255,255,0.95); 
            min-height: 100vh; box-shadow: 0 0 50px rgba(0,0,0,0.1);
        }}
        
        .header {{ 
            text-align: center; margin-bottom: 30px; 
            padding: 30px 20px; background: white;
            border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{ 
            font-size: 2.5em; color: #667eea; margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        
        .controls {{ 
            display: flex; justify-content: center; gap: 15px; 
            margin: 20px 0; flex-wrap: wrap;
        }}
        
        .search-box {{ 
            padding: 12px 20px; border: 2px solid #eee; 
            border-radius: 25px; font-size: 16px; width: 300px;
            outline: none; transition: all 0.3s;
        }}
        
        .search-box:focus {{ border-color: #667eea; }}
        
        .refresh-btn, .filter-btn {{ 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; padding: 12px 25px; border: none; 
            border-radius: 25px; cursor: pointer; font-size: 16px;
            transition: transform 0.2s; text-decoration: none; display: inline-block;
        }}
        
        .refresh-btn:hover, .filter-btn:hover {{ transform: translateY(-2px); }}
        
        .stats {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; margin-bottom: 30px;
        }}
        
        .stat-card {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 25px; border-radius: 15px; text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{ transform: translateY(-5px); }}
        
        .stat-number {{ font-size: 36px; font-weight: bold; margin-bottom: 8px; }}
        .stat-label {{ opacity: 0.9; font-size: 14px; }}
        
        .section-title {{ 
            font-size: 1.5em; font-weight: bold; margin: 30px 0 15px 0;
            color: #333; display: flex; align-items: center; gap: 10px;
        }}
        
        .device-card {{ 
            background: white; border-radius: 15px; padding: 25px; 
            margin: 20px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 5px solid #ddd; transition: all 0.3s;
        }}
        
        .device-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
        .device-card.online {{ border-left-color: #00C851; }}
        .device-card.offline {{ border-left-color: #ff4444; }}
        
        .device-header {{ 
            display: flex; justify-content: space-between; 
            align-items: center; margin-bottom: 20px;
        }}
        
        .device-title h4 {{ font-size: 1.4em; margin-bottom: 5px; }}
        .device-id {{ color: #666; font-size: 0.9em; }}
        
        .status-indicators {{ display: flex; align-items: center; gap: 15px; }}
        
        .status-badge {{ 
            padding: 8px 15px; border-radius: 20px; 
            font-size: 14px; font-weight: bold; display: flex;
            align-items: center; gap: 8px;
        }}
        
        .status-badge.online {{ background: #00C851; color: white; }}
        .status-badge.offline {{ background: #ff4444; color: white; }}
        
        .status-dot {{ 
            width: 8px; height: 8px; border-radius: 50%;
            background: currentColor; animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        
        .signal-strength {{ display: flex; gap: 2px; }}
        .signal-bar {{ 
            width: 3px; height: 12px; background: #00C851; 
            border-radius: 2px; animation: signal 1.5s infinite;
        }}
        .signal-bar:nth-child(2) {{ animation-delay: 0.1s; }}
        .signal-bar:nth-child(3) {{ animation-delay: 0.2s; }}
        .signal-bar:nth-child(4) {{ animation-delay: 0.3s; }}
        
        @keyframes signal {{ 0%, 100% {{ opacity: 0.3; transform: scaleY(0.5); }} 50% {{ opacity: 1; transform: scaleY(1); }} }}
        
        .device-info {{ }}
        
        .basic-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        
        .info-row {{ display: flex; justify-content: space-between; align-items: center; }}
        .info-label {{ font-weight: 600; color: #555; }}
        .info-value {{ color: #333; }}
        
        .system-brief {{ 
            margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px;
        }}
        
        .info-tag {{ 
            background: #f8f9fa; padding: 5px 12px; border-radius: 15px;
            font-size: 0.9em; color: #555; border: 1px solid #eee;
        }}
        
        .system-details {{ 
            margin-top: 20px; padding: 20px; 
            background: #f8f9fa; border-radius: 10px;
        }}
        
        .system-details h5 {{ margin-bottom: 15px; color: #333; }}
        
        .system-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        
        .system-item {{ 
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px; background: white; border-radius: 8px;
        }}
        
        .system-label {{ font-weight: 600; color: #555; }}
        .system-value {{ color: #333; font-family: monospace; }}
        
        .toggle-details {{ 
            background: #667eea; color: white; border: none; 
            padding: 8px 15px; border-radius: 20px; cursor: pointer;
            margin-top: 15px; transition: all 0.3s;
        }}
        
        .toggle-details:hover {{ background: #5a67d8; }}
        
        .no-devices {{ 
            text-align: center; padding: 60px 20px; 
            background: white; border-radius: 15px; margin: 20px 0;
        }}
        
        .no-devices .icon {{ font-size: 64px; margin-bottom: 20px; }}
        
        .help-info {{ 
            background: #f8f9fa; padding: 30px; border-radius: 15px; 
            margin-top: 30px; text-align: left; max-width: 600px; 
            margin-left: auto; margin-right: auto;
        }}
        
        .help-info h4 {{ margin-bottom: 20px; color: #333; }}
        
        .steps {{ display: flex; flex-direction: column; gap: 20px; }}
        
        .step {{ display: flex; align-items: flex-start; gap: 15px; }}
        
        .step-number {{ 
            width: 30px; height: 30px; background: #667eea; 
            color: white; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; font-weight: bold;
            flex-shrink: 0;
        }}
        
        .step-content strong {{ display: block; margin-bottom: 5px; color: #333; }}
        
        .help-info code {{ 
            background: #e9ecef; padding: 3px 8px; 
            border-radius: 4px; font-family: monospace; color: #e83e8c;
        }}
        
        .footer {{ 
            text-align: center; margin-top: 40px; padding: 20px;
            background: white; border-radius: 15px;
        }}
        
        .footer a {{ 
            text-decoration: none; color: #667eea; margin: 0 15px;
            font-weight: 600; transition: color 0.3s;
        }}
        
        .footer a:hover {{ color: #764ba2; }}
        
        .auto-refresh {{ 
            color: #666; font-size: 0.9em; margin-top: 10px;
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .header {{ padding: 20px 15px; }}
            .header h1 {{ font-size: 2em; }}
            .controls {{ flex-direction: column; align-items: center; }}
            .search-box {{ width: 100%; max-width: 300px; }}
            .stats {{ grid-template-columns: 1fr; }}
            .basic-info {{ grid-template-columns: 1fr; }}
            .system-grid {{ grid-template-columns: 1fr; }}
            .device-header {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
        }}
    </style>
    <script>
        let autoRefresh = true;
        let refreshInterval;
        
        function toggleAutoRefresh() {{
            autoRefresh = !autoRefresh;
            const btn = document.querySelector('.auto-refresh-btn');
            if (autoRefresh) {{
                btn.textContent = '⏸️ 暂停自动刷新';
                startAutoRefresh();
            }} else {{
                btn.textContent = '▶️ 开启自动刷新';
                clearInterval(refreshInterval);
            }}
        }}
        
        function startAutoRefresh() {{
            refreshInterval = setInterval(() => {{
                if (autoRefresh) {{
                    window.location.reload();
                }}
            }}, 30000);
        }}
        
        function refreshPage() {{ 
            window.location.reload(); 
        }}
        
        function showDetails(btn) {{
            const details = btn.parentElement.querySelector('.system-details');
            details.style.display = 'block';
            btn.style.display = 'none';
        }}
        
        function hideDetails(btn) {{
            const details = btn.parentElement;
            const showBtn = details.parentElement.querySelector('.toggle-details:not(.hide)');
            details.style.display = 'none';
            showBtn.style.display = 'inline-block';
        }}
        
        function searchDevices() {{
            const query = document.querySelector('.search-box').value.toLowerCase();
            const devices = document.querySelectorAll('.device-card');
            
            devices.forEach(device => {{
                const deviceText = device.getAttribute('data-device') || '';
                if (deviceText.includes(query)) {{
                    device.style.display = 'block';
                }} else {{
                    device.style.display = 'none';
                }}
            }});
        }}
        
        function filterDevices(status) {{
            const devices = document.querySelectorAll('.device-card');
            devices.forEach(device => {{
                if (status === 'all' || device.classList.contains(status)) {{
                    device.style.display = 'block';
                }} else {{
                    device.style.display = 'none';
                }}
            }});
        }}
        
        // 页面加载完成后启动自动刷新
        document.addEventListener('DOMContentLoaded', function() {{
            startAutoRefresh();
            
            // 搜索框实时搜索
            const searchBox = document.querySelector('.search-box');
            if (searchBox) {{
                searchBox.addEventListener('input', searchDevices);
            }}
        }});
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 设备监控状态</h1>
            <p>服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="controls">
                <input type="text" class="search-box" placeholder="🔍 搜索设备名称或ID..." />
                <button class="refresh-btn" onclick="refreshPage()">🔄 立即刷新</button>
                <button class="filter-btn" onclick="filterDevices('online')">🟢 仅在线</button>
                <button class="filter-btn" onclick="filterDevices('offline')">🔴 仅离线</button>
                <button class="filter-btn" onclick="filterDevices('all')">📋 全部设备</button>
                <button class="refresh-btn auto-refresh-btn" onclick="toggleAutoRefresh()">⏸️ 暂停自动刷新</button>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(DEVICE_STATUS)}</div>
                <div class="stat-label">📱 总设备数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(online_devices)}</div>
                <div class="stat-label">🟢 在线设备</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(offline_devices)}</div>
                <div class="stat-label">🔴 离线设备</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{round(len(online_devices) / len(DEVICE_STATUS) * 100) if DEVICE_STATUS else 0}%</div>
                <div class="stat-label">📈 在线率</div>
            </div>
        </div>
        
        {devices_html}
        
        <div class="footer">
            <p>
                <a href="/health">🏠 服务器状态</a> | 
                <a href="/api/status">📊 JSON API</a> | 
                <a href="javascript:refreshPage()">🔄 手动刷新</a>
            </p>
            <div class="auto-refresh">
                <small>⏰ 页面每30秒自动刷新 | 💡 支持实时搜索和筛选</small>
            </div>
        </div>
    </div>
</body>
</html>
        """

    def do_GET(self):
        """处理GET请求"""
        # 根路径重定向到健康检查页面
        if self.path == "/" or self.path == "/index" or self.path == "/home":
            self.send_response(302)
            self.send_header("Location", "/health")
            self.end_headers()
            return

        # 健康检查页面
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            uptime = self.get_server_uptime()
            online_count = len(
                [d for d in DEVICE_STATUS.values() if d.get("status") == "online"]
            )
            offline_count = len(
                [d for d in DEVICE_STATUS.values() if d.get("status") == "offline"]
            )
            total_count = len(DEVICE_STATUS)

            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>心跳监控服务器 - 健康状态</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; overflow-x: hidden;
        }}
        
        .container {{ 
            max-width: 1200px; margin: 0 auto; padding: 20px;
            min-height: 100vh; display: flex; flex-direction: column;
        }}
        
        .header {{ text-align: center; margin-bottom: 40px; }}
        
        .header h1 {{ 
            font-size: 3em; margin-bottom: 15px; 
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .subtitle {{ 
            font-size: 1.2em; opacity: 0.9; margin-bottom: 30px;
        }}
        
        .status-hero {{ 
            background: rgba(255,255,255,0.15); 
            padding: 40px; border-radius: 20px; 
            backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.2);
            text-align: center; margin-bottom: 40px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }}
        
        .status-icon {{ 
            font-size: 80px; margin-bottom: 20px; 
            animation: heartbeat 2s infinite;
        }}
        
        @keyframes heartbeat {{
            0%, 100% {{ transform: scale(1); }}
            25% {{ transform: scale(1.1); }}
            50% {{ transform: scale(1); }}
            75% {{ transform: scale(1.05); }}
        }}
        
        .status-text {{ 
            font-size: 2em; font-weight: bold; margin-bottom: 10px;
        }}
        
        .status-description {{ 
            font-size: 1.1em; opacity: 0.9;
        }}
        
        .stats-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 25px; margin-bottom: 40px;
        }}
        
        .stat-card {{ 
            background: rgba(255,255,255,0.15); 
            padding: 30px; border-radius: 15px; text-align: center;
            backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{ 
            transform: translateY(-5px); 
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }}
        
        .stat-icon {{ font-size: 48px; margin-bottom: 15px; }}
        
        .stat-value {{ 
            font-size: 2.5em; font-weight: bold; 
            margin-bottom: 10px; text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .stat-label {{ 
            font-size: 1.1em; opacity: 0.9; font-weight: 500;
        }}
        
        .info-section {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; border-radius: 15px; 
            backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 30px;
        }}
        
        .info-title {{ 
            font-size: 1.5em; font-weight: bold; 
            margin-bottom: 20px; text-align: center;
        }}
        
        .info-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px;
        }}
        
        .info-item {{ 
            background: rgba(255,255,255,0.1); 
            padding: 20px; border-radius: 10px; text-align: center;
        }}
        
        .info-item-label {{ 
            font-size: 0.9em; opacity: 0.8; margin-bottom: 8px; 
            text-transform: uppercase; letter-spacing: 1px;
        }}
        
        .info-item-value {{ 
            font-size: 1.3em; font-weight: bold;
        }}
        
        .actions {{ 
            display: flex; justify-content: center; gap: 20px; 
            margin: 30px 0; flex-wrap: wrap;
        }}
        
        .action-btn {{ 
            background: rgba(255,255,255,0.2); 
            color: white; padding: 15px 30px; border: none; 
            border-radius: 25px; cursor: pointer; font-size: 16px;
            text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
            transition: all 0.3s; font-weight: 600;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        
        .action-btn:hover {{ 
            background: rgba(255,255,255,0.3); 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
        
        .action-btn.primary {{ 
            background: rgba(255,255,255,0.9); 
            color: #667eea; font-weight: bold;
        }}
        
        .action-btn.primary:hover {{ 
            background: white; 
        }}
        
        .footer {{ 
            text-align: center; margin-top: auto; padding: 20px 0;
            opacity: 0.8; font-size: 0.9em;
        }}
        
        .live-indicator {{ 
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(0,200,81,0.2); padding: 8px 15px; 
            border-radius: 20px; margin: 10px 0;
        }}
        
        .live-dot {{ 
            width: 8px; height: 8px; border-radius: 50%;
            background: #00C851; animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{ 
            0%, 100% {{ opacity: 1; transform: scale(1); }} 
            50% {{ opacity: 0.5; transform: scale(1.1); }} 
        }}
        
        .system-health {{ 
            display: grid; grid-template-columns: repeat(3, 1fr); 
            gap: 15px; margin-top: 20px;
        }}
        
        .health-indicator {{ 
            display: flex; flex-direction: column; align-items: center;
            padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;
        }}
        
        .health-icon {{ font-size: 24px; margin-bottom: 8px; }}
        .health-status {{ font-size: 0.9em; font-weight: 600; }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .header h1 {{ font-size: 2.5em; }}
            .status-hero {{ padding: 30px 20px; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .actions {{ flex-direction: column; align-items: center; }}
            .system-health {{ grid-template-columns: 1fr; }}
        }}
        
        /* 背景动画 */
        .background-shapes {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; z-index: -1; overflow: hidden;
        }}
        
        .shape {{
            position: absolute; opacity: 0.1;
            animation: float 20s infinite linear;
        }}
        
        @keyframes float {{
            0% {{ transform: translateY(100vh) rotate(0deg); }}
            100% {{ transform: translateY(-100px) rotate(360deg); }}
        }}
    </style>
    <script>
        function refreshPage() {{ 
            window.location.reload(); 
        }}
        
        function updateTime() {{
            const now = new Date();
            const timeString = now.toLocaleString('zh-CN');
            const timeElement = document.querySelector('.current-time');
            if (timeElement) {{
                timeElement.textContent = timeString;
            }}
        }}
        
        // 创建浮动背景形状
        function createBackgroundShapes() {{
            const container = document.querySelector('.background-shapes');
            const shapes = ['💓', '🔄', '📊', '⚡', '🌐', '💻', '📱'];
            
            setInterval(() => {{
                const shape = document.createElement('div');
                shape.className = 'shape';
                shape.textContent = shapes[Math.floor(Math.random() * shapes.length)];
                shape.style.left = Math.random() * 100 + '%';
                shape.style.fontSize = (Math.random() * 30 + 20) + 'px';
                shape.style.animationDuration = (Math.random() * 10 + 15) + 's';
                container.appendChild(shape);
                
                // 5秒后删除元素
                setTimeout(() => {{
                    shape.remove();
                }}, 25000);
            }}, 3000);
        }}
        
        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {{
            updateTime();
            setInterval(updateTime, 1000);
            createBackgroundShapes();
        }});
    </script>
</head>
<body>
    <div class="background-shapes"></div>
    
    <div class="container">
        <div class="header">
            <h1>💓 心跳监控服务器</h1>
            <div class="subtitle">实时设备监控与健康检查系统</div>
            <div class="live-indicator">
                <div class="live-dot"></div>
                <span>服务正在运行</span>
            </div>
        </div>
        
        <div class="status-hero">
            <div class="status-icon">✅</div>
            <div class="status-text">系统运行正常</div>
            <div class="status-description">所有核心服务运行良好，监控系统工作正常</div>
            
            <div class="system-health">
                <div class="health-indicator">
                    <div class="health-icon">🌐</div>
                    <div class="health-status">网络正常</div>
                </div>
                <div class="health-indicator">
                    <div class="health-icon">💾</div>
                    <div class="health-status">存储正常</div>
                </div>
                <div class="health-indicator">
                    <div class="health-icon">📊</div>
                    <div class="health-status">监控正常</div>
                </div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">⏰</div>
                <div class="stat-value">{uptime}</div>
                <div class="stat-label">服务器运行时长</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📱</div>
                <div class="stat-value">{total_count}</div>
                <div class="stat-label">注册设备总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🟢</div>
                <div class="stat-value">{online_count}</div>
                <div class="stat-label">在线设备数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔴</div>
                <div class="stat-value">{offline_count}</div>
                <div class="stat-label">离线设备数量</div>
            </div>
        </div>
        
        <div class="info-section">
            <div class="info-title">📊 服务器信息</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-item-label">当前时间</div>
                    <div class="info-item-value current-time">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="info-item">
                    <div class="info-item-label">启动时间</div>
                    <div class="info-item-value">{self._server_start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="info-item">
                    <div class="info-item-label">在线率</div>
                    <div class="info-item-value">{round(online_count / total_count * 100) if total_count else 100}%</div>
                </div>
                <div class="info-item">
                    <div class="info-item-label">监控状态</div>
                    <div class="info-item-value">🟢 正常</div>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/status" class="action-btn primary">
                📊 查看设备状态
            </a>
            <a href="/api/status" class="action-btn">
                📄 JSON API
            </a>
            <button class="action-btn" onclick="refreshPage()">
                🔄 刷新页面
            </button>
        </div>
        
        <div class="footer">
            <p>心跳监控系统 | 实时监控设备状态变化并自动发送通知</p>
            <p><small>💡 访问 /status 查看详细设备信息 | 访问 /api/status 获取JSON数据</small></p>
        </div>
    </div>
</body>
</html>
            """
            self.wfile.write(html_content.encode("utf-8"))
            return

        # 设备状态页面
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html_content = self.generate_status_page()
            self.wfile.write(html_content.encode("utf-8"))
            return

        # JSON API接口
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            status_data = {
                "devices": DEVICE_STATUS,
                "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_devices": len(DEVICE_STATUS),
                "online_devices": len(
                    [d for d in DEVICE_STATUS.values() if d.get("status") == "online"]
                ),
                "offline_devices": len(
                    [d for d in DEVICE_STATUS.values() if d.get("status") == "offline"]
                ),
            }
            self.wfile.write(
                json.dumps(status_data, indent=2, ensure_ascii=False).encode("utf-8")
            )
            return

        # 处理根路径重定向
        if self.path == "/" or self.path == "/index" or self.path == "/home":
            self.send_response(302)
            self.send_header("Location", "/health")
            self.end_headers()
            return

        # 404页面
        self.send_response(404)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        not_found_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面未找到 - 心跳监控系统</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; 
            display: flex; align-items: center; justify-content: center;
        }}
        
        .container {{ 
            text-align: center; padding: 40px; 
            background: rgba(255,255,255,0.1); 
            border-radius: 20px; backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }}
        
        .error-icon {{ font-size: 120px; margin-bottom: 30px; }}
        
        .error-title {{ 
            font-size: 3em; margin-bottom: 20px; font-weight: bold;
        }}
        
        .error-message {{ 
            font-size: 1.2em; margin-bottom: 40px; opacity: 0.9;
        }}
        
        .nav-links {{ 
            display: flex; justify-content: center; gap: 20px; 
            flex-wrap: wrap; margin-bottom: 30px;
        }}
        
        .nav-btn {{ 
            background: rgba(255,255,255,0.2); 
            color: white; padding: 15px 25px; border: none; 
            border-radius: 25px; cursor: pointer; font-size: 16px;
            text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
            transition: all 0.3s; font-weight: 600;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        
        .nav-btn:hover {{ 
            background: rgba(255,255,255,0.3); 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
        
        .nav-btn.primary {{ 
            background: rgba(255,255,255,0.9); 
            color: #667eea; font-weight: bold;
        }}
        
        .nav-btn.primary:hover {{ background: white; }}
        
        .suggestion {{ 
            opacity: 0.8; font-size: 0.9em; margin-top: 20px;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 30px 20px; margin: 20px; }}
            .error-title {{ font-size: 2.5em; }}
            .nav-links {{ flex-direction: column; align-items: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">🔍</div>
        <h1 class="error-title">404</h1>
        <p class="error-message">哎呀！您访问的页面不存在</p>
        
        <div class="nav-links">
            <a href="/health" class="nav-btn primary">
                🏠 服务器状态
            </a>
            <a href="/status" class="nav-btn">
                📊 设备监控
            </a>
            <a href="/api/status" class="nav-btn">
                📄 API接口
            </a>
        </div>
        
        <div class="suggestion">
            <p>💡 提示：您可以访问上述页面查看监控信息</p>
        </div>
    </div>
</body>
</html>
        """

        self.wfile.write(not_found_html.encode("utf-8"))

    def do_POST(self):
        """处理POST请求 - 接收心跳信号"""
        if self.path == "/heartbeat":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length).decode("utf-8")
                try:
                    heartbeat_data = json.loads(post_data)
                    device_id = heartbeat_data.get("device_id")

                    if not device_id:
                        self.send_response(400)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"Missing device_id")
                        return

                    # 更新设备状态
                    now = datetime.now()

                    # 如果是第一次收到此设备的心跳
                    is_new_device = False
                    if device_id not in DEVICE_STATUS:
                        is_new_device = True
                        DEVICE_STATUS[device_id] = {
                            "name": heartbeat_data.get("name", device_id),
                            "description": heartbeat_data.get("description", ""),
                            "first_seen": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "online",
                        }
                        logging.info(f"新设备首次心跳: {device_id}")

                    # 如果设备之前是离线状态
                    was_offline = DEVICE_STATUS[device_id].get("status") == "offline"

                    # 更新心跳信息
                    DEVICE_STATUS[device_id].update(
                        {
                            "last_heartbeat": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "online",
                            "ip": self.client_address[0],
                            "info": heartbeat_data.get("info", {}),
                        }
                    )

                    # 如果不是新设备，且之前是离线状态，则发送恢复通知
                    if not is_new_device and was_offline:
                        device_info = DEVICE_STATUS[device_id].copy()
                        threading.Thread(
                            target=send_status_notification,
                            args=([device_info], [], "recovery"),
                        ).start()
                        logging.info(f"设备已恢复在线: {device_id}")

                    # 保存状态
                    save_status()

                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Heartbeat received")

                except json.JSONDecodeError:
                    self.send_response(400)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Invalid JSON data")
                except Exception as e:
                    logging.error(f"处理心跳请求时出错: {e}")
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Internal server error")
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Empty request body")
        else:
            self.send_response(404)
            self.end_headers()


def load_config() -> dict:
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


def save_status():
    """保存设备状态到文件"""
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEVICE_STATUS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存状态文件失败: {e}")


def load_status():
    """从文件加载设备状态"""
    global DEVICE_STATUS
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                DEVICE_STATUS = json.load(f)
                logging.info(f"成功加载状态文件: {STATUS_FILE}")
        except Exception as e:
            logging.error(f"加载状态文件失败: {e}")


def send_status_notification(
    offline_devices: List[Dict],
    online_devices: List[Dict] = None,
    notification_type: str = "offline",
) -> bool:
    """发送设备状态变化通知"""
    config = load_config()
    email_config = config.get("email", {})

    if not email_config:
        logging.error("邮件配置不存在")
        return False

    if not offline_devices and notification_type == "offline":
        return True

    try:
        # 构建邮件内容
        message = MIMEMultipart()

        if notification_type == "offline":
            subject = f"{email_config.get('subject_prefix', '[心跳监控]')} {len(offline_devices)}台设备离线"
            body_title = "设备离线通知"
        else:  # recovery
            subject = f"{email_config.get('subject_prefix', '[心跳监控]')} 设备恢复在线"
            body_title = "设备恢复在线通知"

        message["Subject"] = subject
        message["From"] = email_config["sender_email"]
        message["To"] = email_config["receiver_email"]

        # 邮件正文
        body = f"""{body_title}

监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        if notification_type == "offline":
            body += """
以下设备当前离线:
"""
            for device in offline_devices:
                last_seen = device.get("last_heartbeat", "未知")

                body += f"""
* {device['name']} (ID: {device.get('device_id', '未知')})
  描述: {device.get('description', '无')}
  最后心跳时间: {last_seen}
  IP地址: {device.get('ip', '未知')}
"""
                # 添加额外信息
                info = device.get("info", {})
                if info:
                    body += "  额外信息:\n"
                    for key, value in info.items():
                        body += f"    - {key}: {value}\n"
        else:  # recovery
            body += """
以下设备已恢复在线:
"""
            for (
                device
            ) in offline_devices:  # 这里参数名称保持一致，实际上是恢复在线的设备
                body += f"""
* {device['name']} (ID: {device.get('device_id', '未知')})
  描述: {device.get('description', '无')}
  恢复时间: {device.get('last_heartbeat', '未知')}
  IP地址: {device.get('ip', '未知')}
"""

        if online_devices and notification_type == "offline":
            body += "\n\n当前在线的设备:\n"
            for device in online_devices:
                body += f"* {device['name']} (ID: {device.get('device_id', '未知')})\n"

        body += """
此邮件由心跳监控系统自动发送，请勿回复。
"""

        message.attach(MIMEText(body, "plain", "utf-8"))

        # 连接SMTP服务器并发送
        smtp_server = email_config["smtp_server"]
        smtp_port = email_config["smtp_port"]
        smtp_user = email_config["sender_email"]
        smtp_password = email_config["sender_password"]

        encryption = email_config.get("smtp_encryption", "SSL").upper()

        if encryption == "SSL":
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        elif encryption == "TLS":
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)

        server.login(smtp_user, smtp_password)
        server.send_message(message)
        server.quit()

        logging.info(f"已发送{body_title}")
        return True

    except Exception as e:
        logging.error(f"发送通知邮件失败: {e}")
        import traceback

        logging.error(traceback.format_exc())
        return False


def check_device_status():
    """检查设备状态，标记离线设备"""
    config = load_config()
    timeout = config.get("heartbeat_timeout", 300)  # 默认5分钟超时

    offline_devices = []
    online_devices = []
    current_time = datetime.now()

    for device_id, device_info in list(DEVICE_STATUS.items()):
        # 如果设备没有last_heartbeat字段，跳过
        if "last_heartbeat" not in device_info:
            continue

        # 计算上次心跳到现在的时间差
        last_heartbeat = datetime.strptime(
            device_info["last_heartbeat"], "%Y-%m-%d %H:%M:%S"
        )
        time_diff = (current_time - last_heartbeat).total_seconds()

        # 如果超时，标记为离线
        if time_diff > timeout:
            # 仅对状态变化的设备进行处理
            if device_info.get("status") == "online":
                device_info["status"] = "offline"
                device_info["offline_since"] = current_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                offline_devices.append(device_info)
                logging.warning(
                    f"设备已离线: {device_id}, 最后心跳: {device_info['last_heartbeat']}"
                )
        else:
            device_info["status"] = "online"
            online_devices.append(device_info)

    # 保存状态
    save_status()

    # 发送离线通知
    if offline_devices:
        send_status_notification(offline_devices, online_devices)


def status_monitor():
    """监控线程，定期检查设备状态"""
    config = load_config()
    check_interval = config.get("check_interval", 60)  # 默认每分钟检查一次

    logging.info(f"状态监控线程启动，检查间隔: {check_interval}秒")

    while True:
        try:
            check_device_status()
            time.sleep(check_interval)
        except Exception as e:
            logging.error(f"状态监控过程中发生错误: {e}")
            import traceback

            logging.error(traceback.format_exc())
            time.sleep(check_interval)


def create_example_config():
    """创建示例配置文件"""
    config = {
        "http_port": 8080,  # 心跳服务器HTTP端口
        "heartbeat_timeout": 300,  # 心跳超时时间（秒）
        "check_interval": 60,  # 状态检查间隔（秒）
        "email": {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "smtp_encryption": "SSL",  # SSL, TLS 或者 None
            "sender_email": "your_email@qq.com",
            "sender_password": "your_email_password",
            "receiver_email": "recipient@example.com",
            "subject_prefix": "[心跳监控]",
        },
    }

    with open("heartbeat_config_example.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("已创建示例配置文件：heartbeat_config_example.json")
    print("请将其重命名为heartbeat_config.json并编辑相关配置后使用。")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="设备心跳监控服务器")
    parser.add_argument(
        "--create-example", "-e", action="store_true", help="创建示例配置文件"
    )
    parser.add_argument(
        "--config", "-c", default="heartbeat_config.json", help="配置文件路径"
    )

    args = parser.parse_args()

    global CONFIG_FILE
    CONFIG_FILE = args.config

    if args.create_example:
        create_example_config()
        return

    try:
        # 加载配置
        config = load_config()

        # 加载之前的状态
        load_status()

        # 设置端口
        port = config.get("http_port", 8080)

        # 启动状态监控线程
        threading.Thread(target=status_monitor, daemon=True).start()

        # 启动HTTP服务器
        with socketserver.TCPServer(("", port), HeartbeatRequestHandler) as httpd:
            logging.info(f"心跳监控服务器启动，监听端口: {port}")
            print(f"心跳监控服务器启动，监听端口: {port}")
            print(f"设备可通过 http://[server-ip]:{port}/heartbeat 发送心跳")
            httpd.serve_forever()

    except FileNotFoundError:
        print(f"配置文件 '{CONFIG_FILE}' 不存在。使用 --create-example 创建示例配置。")
    except Exception as e:
        logging.error(f"服务器启动失败: {e}")
        import traceback

        logging.error(traceback.format_exc())
        print(f"服务器启动失败: {e}")


if __name__ == "__main__":
    main()
