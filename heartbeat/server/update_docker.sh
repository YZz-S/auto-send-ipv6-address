#!/bin/bash

# ==============================================
# iStoreOS 心跳监控服务器 Docker 一键更新脚本
# 支持代码更新、重新构建和重启服务
# ==============================================

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="heartbeat-server"
IMAGE_NAME="heartbeat-server:latest"
CONTAINER_NAME="heartbeat-server"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
BACKUP_DIR="$SCRIPT_DIR/backup"
LOG_FILE="$SCRIPT_DIR/update.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

# 显示标题
show_banner() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "🚀 心跳监控服务器 Docker 一键更新脚本"
    echo "=============================================="
    echo -e "${NC}"
}

# 检查Docker是否运行
check_docker() {
    log_info "检查 Docker 服务状态..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未找到"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装或未找到"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 备份当前配置和数据
backup_data() {
    log_info "备份当前配置和数据..."
    
    BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    CURRENT_BACKUP_DIR="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    mkdir -p "$CURRENT_BACKUP_DIR"
    
    # 备份数据目录
    if [ -d "$SCRIPT_DIR/data" ]; then
        cp -r "$SCRIPT_DIR/data" "$CURRENT_BACKUP_DIR/"
        log_success "数据目录已备份到: $CURRENT_BACKUP_DIR/data"
    fi
    
    # 备份当前运行的容器配置
    if docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        docker inspect "$CONTAINER_NAME" > "$CURRENT_BACKUP_DIR/container_config.json" 2>/dev/null
        log_success "容器配置已备份"
    fi
    
    # 保持最近5个备份
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
        if [ $BACKUP_COUNT -gt 5 ]; then
            cd "$BACKUP_DIR"
            ls -1t | tail -n +6 | xargs -d '\n' rm -rf --
            log_info "已清理旧备份，保留最近5个备份"
        fi
    fi
}

# 停止和清理现有容器
stop_container() {
    log_info "停止现有容器..."
    
    if docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log_info "停止运行中的容器: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME"
        log_success "容器已停止"
    fi
    
    if docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log_info "删除现有容器: $CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
        log_success "容器已删除"
    fi
}

# 清理旧镜像
clean_old_images() {
    log_info "清理旧镜像..."
    
    # 删除标记为 <none> 的镜像
    DANGLING_IMAGES=$(docker images -f "dangling=true" -q)
    if [ ! -z "$DANGLING_IMAGES" ]; then
        docker rmi $DANGLING_IMAGES
        log_success "已清理悬空镜像"
    fi
    
    # 清理旧版本的项目镜像（可选）
    OLD_IMAGES=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "^$PROJECT_NAME:" | grep -v "latest" | head -n -2)
    if [ ! -z "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs -r docker rmi
        log_info "已清理旧版本镜像"
    fi
}

# 重新构建镜像
build_image() {
    log_info "重新构建 Docker 镜像..."
    
    cd "$SCRIPT_DIR"
    
    # 使用 docker-compose 构建
    if [ -f "$COMPOSE_FILE" ]; then
        if command -v docker-compose &> /dev/null; then
            docker-compose build --no-cache
        else
            docker compose build --no-cache
        fi
    else
        # 直接使用 Dockerfile 构建
        docker build --no-cache -t "$IMAGE_NAME" .
    fi
    
    if [ $? -eq 0 ]; then
        log_success "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 启动新容器
start_container() {
    log_info "启动新容器..."
    
    cd "$SCRIPT_DIR"
    
    # 确保数据目录存在
    mkdir -p "$SCRIPT_DIR/data"
    
    if [ -f "$COMPOSE_FILE" ]; then
        # 使用 docker-compose 启动
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d
        else
            docker compose up -d
        fi
    else
        # 直接使用 docker run 启动
        docker run -d \
            --name "$CONTAINER_NAME" \
            --restart unless-stopped \
            -p 18080:8080 \
            -v "$SCRIPT_DIR/data:/data" \
            -e TZ=Asia/Shanghai \
            -e CONFIG_PATH=/data/heartbeat_config.json \
            -e STATUS_PATH=/data/heartbeat_status.json \
            -e LOG_PATH=/data/heartbeat_server.log \
            "$IMAGE_NAME"
    fi
    
    if [ $? -eq 0 ]; then
        log_success "容器启动成功"
    else
        log_error "容器启动失败"
        exit 1
    fi
}

# 检查服务状态
check_service() {
    log_info "检查服务状态..."
    
    # 等待服务启动
    sleep 10
    
    # 检查容器是否运行
    if docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log_success "✅ 容器运行正常"
        
        # 检查日志中是否有启动成功信息
        CONTAINER_LOGS=$(docker logs "$CONTAINER_NAME" --tail 20 2>&1)
        if echo "$CONTAINER_LOGS" | grep -q "心跳监控服务器启动成功"; then
            log_success "✅ 服务启动成功"
            
            # 显示服务信息
            log_info "服务信息:"
            echo -e "${WHITE}  📡 心跳接收地址: http://localhost:18080/heartbeat${NC}"
            echo -e "${WHITE}  🖥️  监控页面: http://localhost:18080/${NC}"
            echo -e "${WHITE}  📊 Docker 日志: docker logs -f $CONTAINER_NAME${NC}"
        else
            log_warn "⚠️  服务可能未完全启动，请检查日志"
            echo -e "${YELLOW}最近的容器日志:${NC}"
            echo "$CONTAINER_LOGS"
        fi
    else
        log_error "❌ 容器未运行"
        echo -e "${RED}最近的容器日志:${NC}"
        docker logs "$CONTAINER_NAME" --tail 20
        exit 1
    fi
}

# 显示更新后的状态
show_status() {
    echo -e "\n${CYAN}=============================================="
    echo "📊 更新完成状态"
    echo -e "===============================================${NC}"
    
    echo -e "${WHITE}容器状态:${NC}"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${WHITE}镜像信息:${NC}"
    docker images --filter "reference=$PROJECT_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo -e "\n${WHITE}日志位置:${NC}"
    echo "  - 容器日志: docker logs -f $CONTAINER_NAME"
    echo "  - 应用日志: $SCRIPT_DIR/data/heartbeat_server.log"
    echo "  - 更新日志: $LOG_FILE"
    
    echo -e "\n${WHITE}访问地址:${NC}"
    echo "  - 心跳接收: http://localhost:18080/heartbeat"
    echo "  - 监控页面: http://localhost:18080/"
    
    echo -e "\n${GREEN}✅ 更新完成！${NC}"
}

# 主函数
main() {
    show_banner
    
    # 创建日志文件
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=============================================" > "$LOG_FILE"
    echo "Docker 更新日志 - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
    
    log_info "开始执行 Docker 更新流程..."
    
    # 执行更新步骤
    check_docker
    backup_data
    stop_container
    clean_old_images
    build_image
    start_container
    check_service
    show_status
    
    log_success "🎉 Docker 更新流程完成！"
}

# 错误处理
trap 'log_error "脚本执行过程中发生错误，退出代码: $?"' ERR

# 执行主函数
main "$@" 