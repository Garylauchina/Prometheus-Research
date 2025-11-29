#!/bin/bash

###############################################################################
# Prometheus v3.0 - 监控脚本
# 用于监控系统运行状态和性能
###############################################################################

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 显示横幅
echo "============================================================"
echo "  Prometheus v3.0 - 系统监控"
echo "============================================================"
echo ""

# 检查服务状态
check_service_status() {
    echo -e "${GREEN}[服务状态]${NC}"
    if systemctl is-active --quiet prometheus.service; then
        echo "✅ Prometheus服务: 运行中"
        
        # 获取运行时间
        uptime=$(systemctl show prometheus.service -p ActiveEnterTimestamp --value)
        echo "   启动时间: $uptime"
    else
        echo -e "${RED}❌ Prometheus服务: 已停止${NC}"
    fi
    echo ""
}

# 检查系统资源
check_system_resources() {
    echo -e "${GREEN}[系统资源]${NC}"
    
    # CPU使用率
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')
    echo "CPU使用率: $cpu_usage"
    
    # 内存使用
    mem_info=$(free -h | awk '/^Mem:/ {print $3 "/" $2}')
    echo "内存使用: $mem_info"
    
    # 磁盘使用
    disk_usage=$(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')
    echo "磁盘使用: $disk_usage"
    
    echo ""
}

# 检查进程信息
check_process_info() {
    echo -e "${GREEN}[进程信息]${NC}"
    
    pid=$(pgrep -f "run_virtual_trading.py" | head -1)
    
    if [ -n "$pid" ]; then
        echo "进程ID: $pid"
        
        # 进程内存使用
        mem=$(ps -p $pid -o rss= | awk '{print $1/1024 " MB"}')
        echo "内存使用: $mem"
        
        # 进程CPU使用
        cpu=$(ps -p $pid -o %cpu= | awk '{print $1 "%"}')
        echo "CPU使用: $cpu"
    else
        echo -e "${RED}未找到运行中的进程${NC}"
    fi
    
    echo ""
}

# 检查最近的日志
check_recent_logs() {
    echo -e "${GREEN}[最近日志]${NC}"
    echo "最近10行日志:"
    echo "---"
    journalctl -u prometheus.service -n 10 --no-pager | tail -10
    echo ""
}

# 检查交易统计
check_trading_stats() {
    echo -e "${GREEN}[交易统计]${NC}"
    
    # 查找最新的报告文件
    latest_report=$(ls -t ~/prometheus-v30/trading_logs/report_*.json 2>/dev/null | head -1)
    
    if [ -n "$latest_report" ]; then
        echo "最新报告: $(basename $latest_report)"
        
        # 提取关键信息
        if command -v jq &> /dev/null; then
            roi=$(jq -r '.summary.roi_pct' "$latest_report" 2>/dev/null)
            trades=$(jq -r '.trading.total_trades' "$latest_report" 2>/dev/null)
            agents=$(jq -r '.agents.active_agents' "$latest_report" 2>/dev/null)
            
            echo "ROI: ${roi}%"
            echo "总交易: $trades"
            echo "活跃Agent: $agents"
        else
            echo "安装jq以查看详细统计: sudo apt install jq"
        fi
    else
        echo "未找到交易报告"
    fi
    
    echo ""
}

# 主函数
main() {
    check_service_status
    check_system_resources
    check_process_info
    check_recent_logs
    check_trading_stats
    
    echo "============================================================"
    echo "实时监控: sudo journalctl -u prometheus.service -f"
    echo "完整日志: sudo journalctl -u prometheus.service"
    echo "============================================================"
}

main
