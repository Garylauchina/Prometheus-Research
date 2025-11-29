#!/bin/bash

###############################################################################
# Prometheus v3.0 - VPS自动化部署脚本
# 版本: 1.0
# 日期: 2025-11-29
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 显示横幅
show_banner() {
    echo "============================================================"
    echo "  Prometheus v3.0 - VPS自动化部署脚本"
    echo "============================================================"
    echo ""
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
}

# 安装依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    sudo apt update
    sudo apt install -y git python3.11 python3.11-venv python3-pip
    
    log_success "系统依赖安装完成"
}

# 克隆或更新代码
setup_code() {
    log_info "设置项目代码..."
    
    PROJECT_DIR="$HOME/prometheus-v30"
    
    if [ -d "$PROJECT_DIR" ]; then
        log_info "项目目录已存在，拉取最新代码..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        log_info "克隆项目代码..."
        
        # 提示输入GitHub凭证
        echo ""
        log_info "请输入GitHub凭证（用于克隆私有仓库）"
        read -p "GitHub用户名: " GITHUB_USER
        read -sp "GitHub Token: " GITHUB_TOKEN
        echo ""
        
        git clone "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/Garylauchina/prometheus-v30.git" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    log_success "代码设置完成"
}

# 设置Python虚拟环境
setup_venv() {
    log_info "设置Python虚拟环境..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
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
}

# 配置API凭证
setup_credentials() {
    log_info "配置API凭证..."
    
    cd "$PROJECT_DIR"
    
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
}

# 测试运行
test_run() {
    log_info "运行测试..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    source .env
    
    log_info "运行60秒测试..."
    timeout 70 python run_virtual_trading.py --duration 60 || true
    
    log_success "测试完成"
}

# 设置systemd服务
setup_service() {
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
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=prometheus-v30

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    log_success "systemd服务配置完成"
}

# 启动服务
start_service() {
    log_info "启动Prometheus服务..."
    
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
}

# 显示管理命令
show_commands() {
    echo ""
    echo "============================================================"
    echo "  常用管理命令"
    echo "============================================================"
    echo ""
    echo "查看服务状态:"
    echo "  sudo systemctl status prometheus.service"
    echo ""
    echo "停止服务:"
    echo "  sudo systemctl stop prometheus.service"
    echo ""
    echo "启动服务:"
    echo "  sudo systemctl start prometheus.service"
    echo ""
    echo "重启服务:"
    echo "  sudo systemctl restart prometheus.service"
    echo ""
    echo "查看实时日志:"
    echo "  sudo journalctl -u prometheus.service -f"
    echo ""
    echo "查看最近100行日志:"
    echo "  sudo journalctl -u prometheus.service -n 100"
    echo ""
    echo "禁用开机自启:"
    echo "  sudo systemctl disable prometheus.service"
    echo ""
    echo "============================================================"
}

# 主函数
main() {
    show_banner
    check_root
    check_system
    
    echo ""
    log_info "开始部署流程..."
    echo ""
    
    # 安装依赖
    install_dependencies
    
    # 设置代码
    setup_code
    
    # 设置虚拟环境
    setup_venv
    
    # 配置凭证
    setup_credentials
    
    # 询问是否测试
    echo ""
    read -p "是否运行测试? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_run
    fi
    
    # 设置服务
    echo ""
    read -p "是否设置为systemd服务? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_service
        
        # 启动服务
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
}

# 运行主函数
main
