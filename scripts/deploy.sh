#!/bin/bash

###############################################################################
# Prometheus v3.0 - 自动化部署脚本
# 版本: 2.0
# 日期: 2025-12-01
# 功能: 支持VPS和Docker部署，提供参数化配置选项
###############################################################################

set -e  # 遇到错误立即退出
set -u  # 未定义变量时退出
set -o pipefail  # 管道命令失败时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$DEBUG_MODE" = true ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}
}

# 全局变量和默认值
PROJECT_DIR="$HOME/prometheus-v30"
GITHUB_REPO="Garylauchina/prometheus-v30"
PYTHON_VERSION="3.11"
DEPLOY_MODE="vps"  # 默认部署模式: vps 或 docker
SKIP_TESTS=false
SKIP_SERVICE=false
DEBUG_MODE=false
CONFIG_FILE=""

# 显示横幅
show_banner() {
    echo "============================================================"
    echo "  Prometheus v3.0 - 自动化部署脚本"
    echo "  支持 VPS 和 Docker 部署"
    echo "============================================================"
    echo ""
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help                显示帮助信息"
    echo "  -d, --dir DIRECTORY       指定项目目录路径 (默认: $HOME/prometheus-v30)"
    echo "  -m, --mode MODE           部署模式: vps 或 docker (默认: vps)"
    echo "  -p, --python VERSION      Python版本 (默认: 3.11)"
    echo "  -r, --repo REPO           GitHub仓库 (默认: Garylauchina/prometheus-v30)"
    echo "  --skip-tests              跳过测试运行"
    echo "  --skip-service            跳过服务设置"
    echo "  --debug                   启用调试模式"
    echo "  -c, --config FILE         使用配置文件"
    echo ""
    echo "示例:"
    echo "  $0 --mode docker                 # 使用Docker部署"
    echo "  $0 --dir /opt/prometheus         # 指定自定义目录"
    echo "  $0 --skip-tests --skip-service   # 快速部署，跳过测试和服务设置"
    exit 0
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                ;;
            -d|--dir)
                PROJECT_DIR="$2"
                shift 2
                ;;
            -m|--mode)
                if [[ "$2" == "vps" || "$2" == "docker" ]]; then
                    DEPLOY_MODE="$2"
                else
                    log_error "无效的部署模式: $2. 请使用 'vps' 或 'docker'"
                    exit 1
                fi
                shift 2
                ;;
            -p|--python)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            -r|--repo)
                GITHUB_REPO="$2"
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-service)
                SKIP_SERVICE=true
                shift
                ;;
            --debug)
                DEBUG_MODE=true
                shift
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                ;;
        esac
    done
    
    log_debug "部署参数设置:"
    log_debug "- 项目目录: $PROJECT_DIR"
    log_debug "- 部署模式: $DEPLOY_MODE"
    log_debug "- Python版本: $PYTHON_VERSION"
    log_debug "- GitHub仓库: $GITHUB_REPO"
    log_debug "- 跳过测试: $SKIP_TESTS"
    log_debug "- 跳过服务: $SKIP_SERVICE"
}

# 从配置文件加载设置
load_config_file() {
    if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ]; then
        log_info "从配置文件加载设置: $CONFIG_FILE"
        # 安全地加载配置文件
        set -a
        source "$CONFIG_FILE"
        set +a
        log_success "配置文件加载完成"
    elif [ -n "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "检测到root用户，建议使用普通用户运行"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        log_info "操作系统: $OS $VER"
    else
        log_error "无法识别操作系统"
        exit 1
    fi
    
    # 检查是否为Ubuntu
    if [[ ! "$OS" =~ "Ubuntu" ]]; then
        log_warning "本脚本针对Ubuntu优化，其他系统可能需要调整"
    fi
    
    # 检查Docker (如果选择Docker模式)
    if [ "$DEPLOY_MODE" = "docker" ]; then
        if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
            log_warning "Docker或Docker Compose未安装，将进行安装"
            install_docker
        else
            log_info "Docker和Docker Compose已安装"
        fi
    fi
}

# 安装Docker
install_docker() {
    log_info "安装Docker和Docker Compose..."
    
    # 移除旧版本
    sudo apt-get remove -y docker docker-engine docker.io containerd runc
    
    # 安装依赖
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # 添加Docker GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 设置稳定仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 安装docker-compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    log_success "Docker和Docker Compose安装完成"
    log_info "注意: 您可能需要注销并重新登录以应用Docker组权限"
}

# 安装系统依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    sudo apt update
    sudo apt install -y git python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip
    
    log_success "系统依赖安装完成"
}

# 克隆或更新代码
setup_code() {
    log_info "设置项目代码..."
    
    if [ -d "$PROJECT_DIR" ]; then
        log_info "项目目录已存在，拉取最新代码..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        log_info "克隆项目代码..."
        
        # 创建项目目录的父目录
        mkdir -p "$(dirname "$PROJECT_DIR")"
        
        # 提示输入GitHub凭证
        echo ""
        log_info "请输入GitHub凭证（用于克隆私有仓库）"
        read -p "GitHub用户名: " GITHUB_USER
        read -sp "GitHub Token: " GITHUB_TOKEN
        echo ""
        
        git clone "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    log_success "代码设置完成"
}

# 设置Python虚拟环境
setup_venv() {
    # 仅在VPS模式下设置虚拟环境
    if [ "$DEPLOY_MODE" = "vps" ]; then
        log_info "设置Python虚拟环境..."
        
        cd "$PROJECT_DIR"
        
        if [ ! -d "venv" ]; then
            python${PYTHON_VERSION} -m venv venv
            log_success "虚拟环境创建完成"
        else
            log_info "虚拟环境已存在"
        fi
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 安装依赖
        log_info "安装Python依赖..."
        pip install --upgrade pip
        pip install -r requirements.txt
        
        log_success "Python依赖安装完成"
    else
        log_info "Docker模式下跳过虚拟环境设置"
    fi
}

# 配置API凭证
setup_credentials() {
    log_info "配置API凭证..."
    
    cd "$PROJECT_DIR"
    
    # 检查是否存在.env.example
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        log_info "发现.env.example，将复制为.env"
        cp .env.example .env
    fi
    
    if [ -f ".env" ]; then
        log_warning ".env文件已存在"
        read -p "是否重新配置? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    echo ""
    log_info "请输入OKX API凭证"
    read -p "API Key: " API_KEY
    read -sp "Secret Key: " SECRET_KEY
    echo ""
    read -p "Passphrase: " PASSPHRASE
    
    # 创建.env文件
    cat > .env << EOF
# OKX API Credentials
OKX_API_KEY="$API_KEY"
OKX_SECRET_KEY="$SECRET_KEY"
OKX_PASSPHRASE="$PASSPHRASE"
EOF
    
    chmod 600 .env
    log_success "API凭证配置完成"
    
    # 如果是Docker模式，确保docker-compose.yml正确设置
    if [ "$DEPLOY_MODE" = "docker" ] && [ ! -f "docker-compose.yml" ]; then
        log_warning "Docker模式下未找到docker-compose.yml文件"
        log_info "创建基础的docker-compose.yml文件..."
        create_docker_compose
    fi
}

# 创建Docker Compose配置
create_docker_compose() {
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  prometheus:
    build: .
    image: prometheus-v30:latest
    container_name: prometheus-v30
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./system_state:/app/system_state
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    network_mode: "host"

  monitor:
    build: .
    image: prometheus-v30:latest
    container_name: prometheus-monitor
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    command: bash -c "source venv/bin/activate && python -m monitoring.system_monitor"
    restart: unless-stopped
    depends_on:
      - prometheus
EOF
    log_success "docker-compose.yml文件创建完成"
}

# 测试运行
test_run() {
    if [ "$SKIP_TESTS" = true ]; then
        log_info "跳过测试运行"
        return
    fi
    
    log_info "运行测试..."
    
    cd "$PROJECT_DIR"
    
    if [ "$DEPLOY_MODE" = "vps" ]; then
        source venv/bin/activate
        source .env
        
        log_info "运行60秒测试..."
        timeout 70 python run_virtual_trading.py --duration 60 || true
    else
        # Docker模式下的测试
        log_info "Docker模式下运行测试..."
        docker-compose run --rm prometheus bash -c "python run_virtual_trading.py --duration 60"
    fi
    
    log_success "测试完成"
}

# 设置systemd服务
setup_service() {
    if [ "$SKIP_SERVICE" = true ]; then
        log_info "跳过服务设置"
        return
    fi
    
    if [ "$DEPLOY_MODE" = "vps" ]; then
        log_info "设置systemd服务..."
        
        SERVICE_FILE="/etc/systemd/system/prometheus.service"
        CURRENT_USER=$(whoami)
        
        # 创建服务文件
        sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Prometheus v3.0 Trading Bot
After=network.target

[Service]
User=$CURRENT_USER
Group=$CURRENT_USER

WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python run_virtual_trading.py --duration 2592000

# Environment File for API Keys
EnvironmentFile=$PROJECT_DIR/.env

# Auto-restart configuration
Restart=on-failure
RestartSec=10
StartLimitInterval=30
StartLimitBurst=5

# Resource Limits
LimitNOFILE=4096
LimitNPROC=2048

# Logging
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=prometheus-v30

[Install]
WantedBy=multi-user.target
EOF
        
        # 重新加载systemd
        sudo systemctl daemon-reload
        
        log_success "systemd服务配置完成"
    else
        log_info "Docker模式下使用容器编排，跳过systemd服务设置"
    fi
}

# 启动服务
start_service() {
    if [ "$SKIP_SERVICE" = true ]; then
        log_info "跳过服务启动"
        return
    fi
    
    log_info "启动Prometheus服务..."
    
    if [ "$DEPLOY_MODE" = "vps" ]; then
        # 停止旧服务（如果存在）
        sudo systemctl stop prometheus.service 2>/dev/null || true
        
        # 启动服务
        sudo systemctl start prometheus.service
        
        # 设置开机自启
        sudo systemctl enable prometheus.service
        
        # 等待2秒
        sleep 2
        
        # 检查状态
        if sudo systemctl is-active --quiet prometheus.service; then
            log_success "Prometheus服务启动成功！"
            echo ""
            log_info "查看服务状态: sudo systemctl status prometheus.service"
            log_info "查看实时日志: sudo journalctl -u prometheus.service -f"
        else
            log_error "服务启动失败，请检查日志"
            sudo systemctl status prometheus.service
            exit 1
        fi
    else
        # Docker模式下的启动
        # 停止旧容器（如果存在）
        docker-compose down -v 2>/dev/null || true
        
        # 构建并启动容器
        log_info "构建Docker镜像并启动容器..."
        docker-compose up -d --build
        
        # 等待几秒
        sleep 5
        
        # 检查容器状态
        if docker-compose ps | grep -q "Up"; then
            log_success "Docker容器启动成功！"
            echo ""
            log_info "查看容器状态: docker-compose ps"
            log_info "查看实时日志: docker-compose logs -f"
        else
            log_error "容器启动失败，请检查日志"
            docker-compose logs
            exit 1
        fi
    fi
}

# 显示管理命令
show_commands() {
    echo ""
    echo "============================================================"
    echo "  常用管理命令"
    echo "============================================================"
    echo ""
    
    if [ "$DEPLOY_MODE" = "vps" ]; then
        echo "服务管理:"
        echo "  sudo systemctl status prometheus.service   # 查看服务状态"
        echo "  sudo systemctl stop prometheus.service    # 停止服务"
        echo "  sudo systemctl start prometheus.service   # 启动服务"
        echo "  sudo systemctl restart prometheus.service # 重启服务"
        echo ""
        echo "日志查看:"
        echo "  sudo journalctl -u prometheus.service -f      # 查看实时日志"
        echo "  sudo journalctl -u prometheus.service -n 100  # 查看最近100行日志"
        echo ""
        echo "自启动管理:"
        echo "  sudo systemctl enable prometheus.service  # 启用开机自启"
        echo "  sudo systemctl disable prometheus.service # 禁用开机自启"
    else
        echo "容器管理:"
        echo "  docker-compose ps             # 查看容器状态"
        echo "  docker-compose down           # 停止并移除容器"
        echo "  docker-compose up -d          # 启动容器"
        echo "  docker-compose restart        # 重启容器"
        echo ""
        echo "日志查看:"
        echo "  docker-compose logs -f        # 查看实时日志"
        echo "  docker-compose logs --tail=100 # 查看最近100行日志"
        echo ""
        echo "更新容器:"
        echo "  docker-compose pull           # 拉取最新镜像"
        echo "  docker-compose up -d --build  # 重新构建并启动"
    fi
    echo ""
    echo "============================================================"
}

# 主函数
main() {
    show_banner
    
    # 解析命令行参数
    parse_args "$@"
    
    # 加载配置文件
    load_config_file
    
    # 检查root权限
    check_root
    
    # 检查系统环境
    check_system
    
    echo ""
    log_info "开始部署流程 (模式: $DEPLOY_MODE)..."
    echo ""
    
    # 安装依赖（根据部署模式）
    if [ "$DEPLOY_MODE" = "vps" ]; then
        install_dependencies
    fi
    
    # 设置代码
    setup_code
    
    # 设置虚拟环境（仅VPS模式）
    setup_venv
    
    # 配置凭证
    setup_credentials
    
    # 测试运行
    if [ "$SKIP_TESTS" = false ]; then
        echo ""
        read -p "是否运行测试? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            test_run
        else
            log_warning "跳过测试运行"
            SKIP_TESTS=true
        fi
    fi
    
    # 设置并启动服务
    if [ "$SKIP_SERVICE" = false ]; then
        setup_service
        
        echo ""
        read -p "是否立即启动服务? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            start_service
        fi
    fi
    
    # 显示管理命令
    show_commands
    
    echo ""
    log_success "部署完成！"
    echo ""
    log_info "部署信息摘要:"
    log_info "- 部署模式: $DEPLOY_MODE"
    log_info "- 项目路径: $PROJECT_DIR"
    log_info "- Python版本: $PYTHON_VERSION"
    if [ "$SKIP_TESTS" = true ]; then
        log_info "- 测试状态: 跳过"
    else
        log_info "- 测试状态: 已运行"
    fi
    if [ "$SKIP_SERVICE" = true ]; then
        log_info "- 服务状态: 未配置"
    else
        log_info "- 服务状态: 已配置"
    fi
    echo ""
}

# 运行主函数
main "$@"
