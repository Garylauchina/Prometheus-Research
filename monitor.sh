#!/bin/bash

###############################################################################
# Prometheus v3.0 - 增强监控脚本
# 版本: 2.0
# 日期: 2025-12-01
# 功能: 系统监控、性能指标、Docker支持、告警通知
###############################################################################

set -e
set -u
set -o pipefail

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 全局变量和默认值
MONITOR_MODE="vps"  # 默认监控模式: vps 或 docker
PROJECT_DIR="$HOME/prometheus-v30"
LOG_FILE="$PROJECT_DIR/logs/monitor_$(date +%Y%m%d).log"
LOG_LINES=10
INTERVAL=60  # 持续监控的时间间隔（秒）
ALERT_THRESHOLD_CPU=80  # CPU告警阈值
ALERT_THRESHOLD_MEM=85  # 内存告警阈值
ALERT_THRESHOLD_DISK=90  # 磁盘告警阈值
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
NOTIFICATION_ENABLED=false
EMAIL=""
TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""
DEBUG=false
SERVICE_NAME="prometheus.service"
CONTAINER_NAME="prometheus-v30"
CHECK_NETWORK=true
CHECK_TRADE_STATS=true
GENERATE_REPORT=false

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log_to_file "[INFO] $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_to_file "[SUCCESS] $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_to_file "[WARNING] $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_to_file "[ERROR] $1"
    if [ "$NOTIFICATION_ENABLED" = true ]; then
        send_alert "错误: $1"
    fi
}

log_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
        log_to_file "[DEBUG] $1"
    fi
}

log_to_file() {
    # 确保日志目录存在
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help                显示帮助信息"
    echo "  -m, --mode MODE           监控模式: vps 或 docker (默认: vps)"
    echo "  -d, --dir DIRECTORY       指定项目目录 (默认: $HOME/prometheus-v30)"
    echo "  -l, --log-lines N         显示的日志行数 (默认: 10)"
    echo "  -i, --interval SECONDS    持续监控的时间间隔 (默认: 60秒)"
    echo "  -c, --continuous          启用持续监控模式"
    echo "  -r, --report              生成详细报告"
    echo "  --no-network              禁用网络监控"
    echo "  --no-trade-stats          禁用交易统计监控"
    echo "  --debug                   启用调试模式"
    echo "  --enable-alerts           启用告警通知"
    echo "  --email EMAIL             设置告警邮箱"
    echo "  --telegram TOKEN:CHAT_ID  设置Telegram通知 (格式: bot_token:chat_id)"
    echo ""
    echo "示例:"
    echo "  $0                         # 标准监控"
    echo "  $0 --mode docker           # Docker模式监控"
    echo "  $0 --continuous -i 30      # 每30秒持续监控"
    echo "  $0 --report                # 生成详细报告"
    exit 0
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                ;;
            -m|--mode)
                if [[ "$2" == "vps" || "$2" == "docker" ]]; then
                    MONITOR_MODE="$2"
                else
                    log_error "无效的监控模式: $2. 请使用 'vps' 或 'docker'"
                    exit 1
                fi
                shift 2
                ;;
            -d|--dir)
                PROJECT_DIR="$2"
                LOG_FILE="$PROJECT_DIR/logs/monitor_$(date +%Y%m%d).log"
                DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
                shift 2
                ;;
            -l|--log-lines)
                LOG_LINES="$2"
                shift 2
                ;;
            -i|--interval)
                INTERVAL="$2"
                shift 2
                ;;
            -c|--continuous)
                CONTINUOUS=true
                shift
                ;;
            -r|--report)
                GENERATE_REPORT=true
                shift
                ;;
            --no-network)
                CHECK_NETWORK=false
                shift
                ;;
            --no-trade-stats)
                CHECK_TRADE_STATS=false
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --enable-alerts)
                NOTIFICATION_ENABLED=true
                shift
                ;;
            --email)
                EMAIL="$2"
                NOTIFICATION_ENABLED=true
                shift 2
                ;;
            --telegram)
                IFS=':' read -r TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID <<< "$2"
                NOTIFICATION_ENABLED=true
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                ;;
        esac
    done
    
    log_debug "监控参数设置:"
    log_debug "- 监控模式: $MONITOR_MODE"
    log_debug "- 项目目录: $PROJECT_DIR"
    log_debug "- 日志文件: $LOG_FILE"
    log_debug "- 显示日志行数: $LOG_LINES"
    log_debug "- 告警已启用: $NOTIFICATION_ENABLED"
}

# 显示横幅
show_banner() {
    echo "============================================================"
    echo "  Prometheus v3.0 - 系统监控"
    echo "  模式: $MONITOR_MODE"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""
    log_info "监控会话开始"
}

# 检查服务状态
check_service_status() {
    echo -e "${GREEN}[服务状态]${NC}"
    
    if [ "$MONITOR_MODE" = "vps" ]; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo "✅ Prometheus服务: 运行中"
            
            # 获取运行时间
            uptime=$(systemctl show "$SERVICE_NAME" -p ActiveEnterTimestamp --value)
            echo "   启动时间: $uptime"
            
            # 获取重启次数
            restart_count=$(systemctl show "$SERVICE_NAME" -p NRestarts --value)
            echo "   重启次数: $restart_count"
            
            if [ "$restart_count" -gt 5 ]; then
                log_warning "服务重启次数过多: $restart_count次"
                if [ "$NOTIFICATION_ENABLED" = true ]; then
                    send_alert "警告: Prometheus服务重启次数过多 ($restart_count次)"
                fi
            fi
        else
            echo -e "${RED}❌ Prometheus服务: 已停止${NC}"
            log_error "Prometheus服务未运行"
        fi
    else
        # Docker模式检查
        if docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null; then
            echo "✅ Docker容器: 运行中"
            
            # 获取容器启动时间
            start_time=$(docker inspect -f '{{.State.StartedAt}}' "$CONTAINER_NAME")
            echo "   启动时间: $start_time"
            
            # 获取容器健康状态
            if docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null; then
                health_status=$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME")
                echo "   健康状态: $health_status"
                
                if [ "$health_status" != "healthy" ]; then
                    log_warning "容器健康状态异常: $health_status"
                    if [ "$NOTIFICATION_ENABLED" = true ]; then
                        send_alert "警告: Prometheus容器健康状态异常 ($health_status)"
                    fi
                fi
            else
                echo "   健康检查: 未配置"
            fi
        else
            echo -e "${RED}❌ Docker容器: 未运行或不存在${NC}"
            log_error "Prometheus容器未运行"
        fi
    fi
    echo ""
}

# 检查系统资源
check_system_resources() {
    echo -e "${GREEN}[系统资源]${NC}"
    
    # CPU使用率
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')
    cpu_value=$(echo "$cpu_usage" | tr -d '%')
    echo "CPU使用率: $cpu_usage"
    
    # CPU阈值检查
    if (( $(echo "$cpu_value > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_warning "CPU使用率过高: $cpu_usage"
        if [ "$NOTIFICATION_ENABLED" = true ]; then
            send_alert "警告: CPU使用率过高 ($cpu_usage)"
        fi
    fi
    
    # 内存使用
    mem_info=$(free -h | awk '/^Mem:/ {print $3 "/" $2}')
    mem_percent=$(free | awk '/^Mem:/ {print $3/$2 * 100"%"}')
    mem_value=$(echo "$mem_percent" | tr -d '%')
    echo "内存使用: $mem_info ($mem_percent)"
    
    # 内存阈值检查
    if (( $(echo "$mem_value > $ALERT_THRESHOLD_MEM" | bc -l) )); then
        log_warning "内存使用率过高: $mem_percent"
        if [ "$NOTIFICATION_ENABLED" = true ]; then
            send_alert "警告: 内存使用率过高 ($mem_percent)"
        fi
    fi
    
    # 磁盘使用
    disk_usage=$(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')
    disk_percent=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    echo "磁盘使用: $disk_usage"
    
    # 磁盘阈值检查
    if [ "$disk_percent" -gt "$ALERT_THRESHOLD_DISK" ]; then
        log_warning "磁盘使用率过高: $disk_percent%"
        if [ "$NOTIFICATION_ENABLED" = true ]; then
            send_alert "警告: 磁盘使用率过高 ($disk_percent%)"
        fi
    fi
    
    # 系统负载
    load=$(uptime | awk '{print $10, $11, $12}')
    echo "系统负载: $load"
    
    # 交换空间使用
    swap_info=$(free -h | awk '/^Swap:/ {print $3 "/" $2}')
    echo "交换空间: $swap_info"
    
    # 系统正常运行时间
    uptime_info=$(uptime -p)
    echo "系统运行: $uptime_info"
    
    echo ""
}

# 检查进程信息
check_process_info() {
    echo -e "${GREEN}[进程信息]${NC}"
    
    if [ "$MONITOR_MODE" = "vps" ]; then
        pid=$(pgrep -f "run_virtual_trading.py" | head -1)
        
        if [ -n "$pid" ]; then
            echo "进程ID: $pid"
            
            # 进程内存使用
            mem=$(ps -p $pid -o rss= | awk '{print $1/1024 " MB"}')
            echo "内存使用: $mem"
            
            # 进程CPU使用
            cpu=$(ps -p $pid -o %cpu= | awk '{print $1"%"}')
            echo "CPU使用: $cpu"
            
            # 进程状态
            status=$(ps -p $pid -o stat= | tr -d ' ')
            echo "进程状态: $status"
            
            # 打开文件数
            open_files=$(lsof -p $pid 2>/dev/null | wc -l || echo "N/A")
            echo "打开文件: $open_files"
            
            # 检查进程是否有异常状态
            if [[ "$status" == *'Z'* ]]; then
                log_error "进程处于僵尸状态"
            elif [[ "$status" == *'T'* ]]; then
                log_warning "进程已暂停"
            fi
        else
            echo -e "${RED}未找到运行中的进程${NC}"
            log_error "未找到Prometheus交易进程"
        fi
    else
        # Docker模式的进程信息
        if docker ps | grep -q "$CONTAINER_NAME"; then
            echo "容器ID: $(docker ps | grep "$CONTAINER_NAME" | awk '{print $1}')"
            
            # 容器资源使用
            echo "资源使用:"
            docker stats "$CONTAINER_NAME" --no-stream --format "CPU: {{.CPUPerc}}, 内存: {{.MemPerc}} ({{.MemUsage}})"
            
            # 容器内进程数量
            proc_count=$(docker exec "$CONTAINER_NAME" ps aux 2>/dev/null | wc -l || echo "N/A")
            if [ "$proc_count" != "N/A" ]; then
                proc_count=$((proc_count - 1)) # 减去标题行
            fi
            echo "容器内进程数: $proc_count"
            
            # 查看主要进程
            echo "主要进程:"
            docker exec "$CONTAINER_NAME" ps aux 2>/dev/null | grep -v ps | head -3 || echo "无法获取进程信息"
        else
            echo -e "${RED}容器未运行，无法获取进程信息${NC}"
        fi
    fi
    
    echo ""
}

# 检查网络状态
check_network_status() {
    if [ "$CHECK_NETWORK" = false ]; then
        return
    fi
    
    echo -e "${GREEN}[网络状态]${NC}"
    
    # 网络连接状态
    connections=$(netstat -tuln 2>/dev/null | wc -l || echo "N/A")
    if [ "$connections" != "N/A" ]; then
        connections=$((connections - 2)) # 减去标题行
    fi
    echo "活跃连接数: $connections"
    
    # 检查关键端口（如WebSocket连接）
    echo "关键端口状态:"
    for port in 443 80; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo "✅ 端口 $port: 开放"
        else
            echo -e "${YELLOW}⚠️  端口 $port: 未开放${NC}"
        fi
    done
    
    # ping测试（连接到交易所API）
    echo "交易所API连接测试:"
    if ping -c 2 api.okx.com > /dev/null 2>&1; then
        ping_time=$(ping -c 1 api.okx.com | grep time= | awk '{print $7}' | cut -d= -f2)
        echo "✅ OKX API: 可连接 (延迟: ${ping_time}ms)"
    else
        echo -e "${RED}❌ OKX API: 无法连接${NC}"
        log_error "无法连接到OKX API服务器"
        if [ "$NOTIFICATION_ENABLED" = true ]; then
            send_alert "警告: 无法连接到OKX API服务器"
        fi
    fi
    
    echo ""
}

# 检查最近的日志
check_recent_logs() {
    echo -e "${GREEN}[最近日志]${NC}"
    echo "最近$LOG_LINES行日志:"
    echo "---"
    
    if [ "$MONITOR_MODE" = "vps" ]; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            journalctl -u "$SERVICE_NAME" -n "$LOG_LINES" --no-pager | tail -"$LOG_LINES"
            
            # 检查日志中的错误
            error_count=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" | grep -i "error\|exception\|fail" | wc -l)
            if [ "$error_count" -gt 0 ]; then
                log_warning "最近1小时内发现 $error_count 个错误日志"
                echo "最近的错误日志:"
                journalctl -u "$SERVICE_NAME" --since "1 hour ago" | grep -i "error\|exception\|fail" | tail -3
                
                if [ "$NOTIFICATION_ENABLED" = true ]; then
                    send_alert "警告: 最近1小时内发现 $error_count 个错误日志"
                fi
            fi
        else
            echo -e "${RED}服务未运行，无法获取日志${NC}"
        fi
    else
        # Docker模式的日志查看
        if docker ps | grep -q "$CONTAINER_NAME"; then
            docker logs "$CONTAINER_NAME" --tail "$LOG_LINES"
            
            # 检查Docker日志中的错误
            error_count=$(docker logs "$CONTAINER_NAME" --since "1h" 2>&1 | grep -i "error\|exception\|fail" | wc -l)
            if [ "$error_count" -gt 0 ]; then
                log_warning "最近1小时内发现 $error_count 个错误日志"
                echo "最近的错误日志:"
                docker logs "$CONTAINER_NAME" --since "1h" 2>&1 | grep -i "error\|exception\|fail" | tail -3
                
                if [ "$NOTIFICATION_ENABLED" = true ]; then
                    send_alert "警告: 容器最近1小时内发现 $error_count 个错误日志"
                fi
            fi
        else
            echo -e "${RED}容器未运行，无法获取日志${NC}"
        fi
    fi
    echo ""
    
    # 检查磁盘上的日志文件大小
    if [ -d "$PROJECT_DIR/logs" ]; then
        log_size=$(du -sh "$PROJECT_DIR/logs" 2>/dev/null | cut -f1 || echo "N/A")
        if [ "$log_size" != "N/A" ]; then
            echo "日志目录大小: $log_size"
            
            # 日志清理建议
            log_count=$(find "$PROJECT_DIR/logs" -name "*.log" | wc -l)
            echo "日志文件数量: $log_count"
            
            if [ "$log_count" -gt 10 ]; then
                log_warning "日志文件数量较多，建议清理旧日志"
            fi
        fi
    fi
    echo ""
}

# 检查交易统计
check_trading_stats() {
    if [ "$CHECK_TRADE_STATS" = false ]; then
        return
    fi
    
    echo -e "${GREEN}[交易统计]${NC}"
    
    # 查找最新的报告文件
    latest_report=$(ls -t "$PROJECT_DIR/trading_logs/report_*.json" 2>/dev/null | head -1)
    
    if [ -n "$latest_report" ]; then
        echo "最新报告: $(basename "$latest_report")"
        report_time=$(stat -c '%y' "$latest_report" 2>/dev/null | cut -d' ' -f1,2 || echo "未知")
        echo "生成时间: $report_time"
        
        # 提取关键信息
        if command -v jq &> /dev/null; then
            roi=$(jq -r '.summary.roi_pct' "$latest_report" 2>/dev/null || echo "N/A")
            trades=$(jq -r '.trading.total_trades' "$latest_report" 2>/dev/null || echo "N/A")
            agents=$(jq -r '.agents.active_agents' "$latest_report" 2>/dev/null || echo "N/A")
            win_rate=$(jq -r '.trading.win_rate' "$latest_report" 2>/dev/null || echo "N/A")
            max_drawdown=$(jq -r '.risk.max_drawdown' "$latest_report" 2>/dev/null || echo "N/A")
            
            echo "ROI: ${roi}%"
            echo "总交易: $trades"
            echo "胜率: $win_rate%"
            echo "最大回撤: $max_drawdown%"
            echo "活跃Agent: $agents"
            
            # 检查风险指标
            if [ "$max_drawdown" != "N/A" ] && (( $(echo "$max_drawdown > 10" | bc -l) )); then
                log_warning "最大回撤较高: $max_drawdown%"
                if [ "$NOTIFICATION_ENABLED" = true ]; then
                    send_alert "警告: 最大回撤较高 ($max_drawdown%)"
                fi
            fi
        else
            echo "安装jq以查看详细统计: sudo apt install jq"
            # 尝试使用简单的grep提取信息
            if grep -q '"roi_pct"' "$latest_report"; then
                roi=$(grep '"roi_pct"' "$latest_report" | cut -d':' -f2 | tr -d '", ' | head -1)
                echo "ROI: ${roi}%"
            fi
        fi
        
        # 检查报告时间是否过旧（超过1小时）
        if [ "$report_time" != "未知" ]; then
            report_age=$(echo "$(date +%s) - $(date -d "$report_time" +%s)" | bc)
            if [ "$report_age" -gt 3600 ]; then
                log_warning "交易报告已超过1小时未更新"
                if [ "$NOTIFICATION_ENABLED" = true ]; then
                    send_alert "警告: 交易报告已超过1小时未更新"
                fi
            fi
        fi
    else
        echo "未找到交易报告"
        log_warning "未找到交易报告文件"
    fi
    
    # 检查交易日志目录
    if [ -d "$PROJECT_DIR/trading_logs" ]; then
        trade_log_count=$(find "$PROJECT_DIR/trading_logs" -name "*.json" | wc -l)
        echo "交易日志数量: $trade_log_count"
    fi
    
    echo ""}

# 发送告警通知
send_alert() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local alert_message="[Prometheus监控告警] $timestamp\n$message"
    
    log_info "发送告警: $message"
    
    # 发送邮件告警
    if [ -n "$EMAIL" ]; then
        echo -e "Subject: Prometheus监控告警\n\n$alert_message" | sendmail "$EMAIL" || \
        echo -e "$alert_message" | mail -s "Prometheus监控告警" "$EMAIL" || \
        log_debug "无法发送邮件告警，请检查sendmail或mail命令"
    fi
    
    # 发送Telegram告警
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        local escaped_message=$(echo "$alert_message" | sed 's/\n/%0A/g' | sed 's/ /+/g')
        curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage?chat_id=$TELEGRAM_CHAT_ID&text=$escaped_message" > /dev/null || \
        log_debug "无法发送Telegram告警，请检查令牌和聊天ID"
    fi
}

# 生成详细报告
generate_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return
    fi
    
    local report_file="$PROJECT_DIR/reports/monitor_report_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$(dirname "$report_file")"
    
    log_info "生成详细监控报告: $report_file"
    
    echo "============================================================" > "$report_file"
    echo "Prometheus v3.0 - 详细监控报告" >> "$report_file"
    echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$report_file"
    echo "============================================================" >> "$report_file"
    echo "" >> "$report_file"
    
    # 系统信息
    echo "[系统信息]" >> "$report_file"
    echo "主机名: $(hostname)" >> "$report_file"
    echo "操作系统: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "未知")" >> "$report_file"
    echo "内核版本: $(uname -r)" >> "$report_file"
    echo "CPU信息: $(lscpu 2>/dev/null | grep 'Model name' | cut -d':' -f2 | tr -s ' ' || echo "未知")" >> "$report_file"
    echo "内存总量: $(free -h | awk '/^Mem:/ {print $2}')" >> "$report_file"
    echo "磁盘总量: $(df -h / | awk 'NR==2 {print $2}')" >> "$report_file"
    echo "" >> "$report_file"
    
    # 网络连接详情
    echo "[网络连接详情]" >> "$report_file"
    netstat -tuln 2>/dev/null | grep LISTEN >> "$report_file" || echo "无法获取网络连接信息" >> "$report_file"
    echo "" >> "$report_file"
    
    # 进程详情
    echo "[进程详情]" >> "$report_file"
    if [ "$MONITOR_MODE" = "vps" ]; then
        pid=$(pgrep -f "run_virtual_trading.py" | head -1)
        if [ -n "$pid" ]; then
            ps -p "$pid" -o pid,ppid,user,%cpu,%mem,etime,cmd >> "$report_file"
        else
            echo "Prometheus进程未运行" >> "$report_file"
        fi
    else
        docker stats "$CONTAINER_NAME" --no-stream >> "$report_file" 2>/dev/null || echo "容器未运行" >> "$report_file"
    fi
    echo "" >> "$report_file"
    
    # 最近错误日志
    echo "[最近错误日志]" >> "$report_file"
    if [ "$MONITOR_MODE" = "vps" ]; then
        journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -i "error\|exception\|fail" | tail -20 >> "$report_file" 2>/dev/null || \
        echo "无法获取错误日志" >> "$report_file"
    else
        docker logs "$CONTAINER_NAME" --since "24h" 2>&1 | grep -i "error\|exception\|fail" | tail -20 >> "$report_file" 2>/dev/null || \
        echo "无法获取错误日志" >> "$report_file"
    fi
    
    log_success "详细报告已生成: $report_file"
}

# 主函数
main() {
    # 解析命令行参数
    parse_args "$@"
    
    # 显示横幅
    show_banner
    
    # 检查必要的工具
    if [ "$MONITOR_MODE" = "docker" ] && ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请安装Docker或使用VPS模式"
        exit 1
    fi
    
    # 持续监控模式
    if [ "$CONTINUOUS" = true ]; then
        log_info "进入持续监控模式，间隔: ${INTERVAL}秒"
        log_info "按Ctrl+C停止监控"
        
        while true; do
            clear
            show_banner
            check_service_status
            check_system_resources
            check_process_info
            check_network_status
            check_recent_logs
            check_trading_stats
            
            echo "============================================================"
            echo "下一次监控将在 ${INTERVAL} 秒后进行..."
            echo "============================================================"
            
            sleep "$INTERVAL"
        done
    else
        # 单次监控
        check_service_status
        check_system_resources
        check_process_info
        check_network_status
        check_recent_logs
        check_trading_stats
        
        # 生成详细报告
        generate_report
        
        # 显示管理命令
        echo "============================================================"
        if [ "$MONITOR_MODE" = "vps" ]; then
            echo "服务管理: sudo systemctl [status|start|stop|restart] $SERVICE_NAME"
            echo "实时日志: sudo journalctl -u $SERVICE_NAME -f"
        else
            echo "容器管理: docker-compose [ps|up -d|down|restart]"
            echo "实时日志: docker-compose logs -f"
        fi
        echo "持续监控: $0 --continuous --mode $MONITOR_MODE"
        echo "详细报告: $0 --report --mode $MONITOR_MODE"
        echo "============================================================"
    fi
    
    log_info "监控会话结束"
}

# 初始化CONTINUOUS变量
CONTINUOUS=false

# 运行主函数
main "$@"
