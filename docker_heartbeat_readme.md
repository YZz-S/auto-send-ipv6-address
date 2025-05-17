# 心跳监控服务端 Docker 部署指南

本指南将帮助您在 istoreOS 上通过 Docker 部署心跳监控服务器。

## 部署步骤

### 1. 前期准备

确保您的 istoreOS 系统已安装 Docker 和 Docker Compose。istoreOS 通常预装了 Docker，您可以通过以下命令验证：

```bash
docker --version
docker-compose --version
```

### 2. 下载部署文件

将以下文件下载到您的 istoreOS 系统上的同一目录中：
- `Dockerfile` - 用于构建Docker镜像
- `docker-compose.yml` - Docker Compose配置文件
- `heartbeat_server.py` - 心跳监控服务器代码
- `requirements.txt` - Python依赖项列表
- `run_heartbeat_server.sh` - 部署脚本

您可以使用 istoreOS 的文件管理器上传这些文件，或者通过命令行下载：

```bash
# 在istoreOS上创建一个目录
mkdir -p /volume1/docker/heartbeat-server
cd /volume1/docker/heartbeat-server

# 下载文件（示例，具体URL根据您的情况修改）
curl -O https://your-domain.com/files/Dockerfile
curl -O https://your-domain.com/files/docker-compose.yml
curl -O https://your-domain.com/files/heartbeat_server.py
curl -O https://your-domain.com/files/requirements.txt
curl -O https://your-domain.com/files/run_heartbeat_server.sh

# 为脚本添加执行权限
chmod +x run_heartbeat_server.sh
```

### 3. 运行部署脚本

运行部署脚本开始安装：

```bash
./run_heartbeat_server.sh
```

脚本会自动执行以下操作：
1. 创建数据目录
2. 生成初始配置文件（如果不存在）
3. 构建并启动Docker容器

部署过程中，脚本会提示您编辑配置文件，设置正确的邮箱信息。

### 4. 修改配置文件

编辑 `data/heartbeat_config.json` 文件，设置您的邮箱信息：

```json
{
  "http_port": 8080,
  "heartbeat_timeout": 300,
  "check_interval": 60,
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_encryption": "SSL",
    "sender_email": "your_email@qq.com",
    "sender_password": "your_email_password",  // QQ邮箱需要使用授权码
    "receiver_email": "recipient@example.com",
    "subject_prefix": "[心跳监控]"
  }
}
```

### 5. 验证服务状态

查看容器是否正常运行：

```bash
docker-compose ps
```

查看服务日志：

```bash
docker-compose logs -f heartbeat-server
```

### 6. 设置客户端

在您需要监控的NAT后设备上安装心跳客户端：

1. 在设备上安装Python：`apt-get install python3 python3-pip` 或对应平台的安装命令
2. 安装依赖：`pip install requests`
3. 下载客户端：`curl -O https://your-domain.com/files/heartbeat_client.py`
4. 生成配置文件：`python heartbeat_client.py --create-example`
5. 编辑配置，设置服务器地址：
   ```json
   {
     "server_url": "http://your-istoreos-ip:8080",
     "device_name": "NAS虚拟机",
     "description": "NAT模式下的设备",
     "heartbeat_interval": 60
   }
   ```
6. 运行客户端：`python heartbeat_client.py`

## Docker常用命令

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 查看日志
```bash
docker-compose logs -f heartbeat-server
```

### 重启服务
```bash
docker-compose restart heartbeat-server
```

## 数据持久化

所有配置和状态数据存储在 `./data` 目录中：
- `heartbeat_config.json` - 配置文件
- `heartbeat_status.json` - 设备状态文件
- `heartbeat_server.log` - 服务器日志

您可以备份此目录以保存服务器配置和状态。

## 端口配置

默认情况下，服务使用8080端口。如需修改，请同时更改以下文件：
1. `docker-compose.yml` 中的端口映射
2. `data/heartbeat_config.json` 中的 `http_port` 设置

## 升级指南

要升级到新版本，只需替换原有的源代码文件并重新构建：

```bash
# 更新源代码文件
# ...

# 重新构建并启动
docker-compose down
docker-compose build --no-cache
docker-compose up -d
``` 