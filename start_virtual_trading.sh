#!/bin/bash
# Prometheus v3.0 虚拟交易启动脚本
# 提供简化的部署和运行界面，支持性能测试选项

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Prometheus v3.0 虚拟交易启动脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: python3 未安装${NC}"
    exit 1
fi

# 检查项目目录结构
if [ ! -f "run_virtual_trading.py" ] || [ ! -f "live_trading_system.py" ]; then
    echo -e "${RED}错误: 请在Prometheus项目根目录下运行此脚本${NC}"
    exit 1
fi

# 解析命令行参数
PERFORMANCE_TEST=false
DURATION=3600
LOG_LEVEL="INFO"

while [[ $# -gt 0 ]]; do
    case $1 in
        --performance)
            PERFORMANCE_TEST=true
            shift
            ;;
        --duration)
            DURATION=$2
            shift 2
            ;;
        --log-level)
            LOG_LEVEL=$2
            shift 2
            ;;
        --help)
            echo -e "使用方法: ./start_virtual_trading.sh [选项]"
            echo -e "选项:"
            echo -e "  --performance      运行性能测试模式"
            echo -e "  --duration <秒数>   设置运行时长（默认: 3600秒=1小时）"
            echo -e "  --log-level <级别>  设置日志级别 (DEBUG, INFO, WARNING, ERROR)"
            echo -e "  --help             显示此帮助信息"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}警告: 未知参数 $1${NC}"
            shift
            ;;
    esac
done

# 检查配置文件
if [ ! -f "config_virtual.py" ]; then
    echo -e "${YELLOW}警告: 未找到config_virtual.py文件${NC}"
    echo -e "正在创建默认配置文件..."
    
    cat > config_virtual.py << 'EOF'
"""
Prometheus v3.0 虚拟交易配置文件
"""

CONFIG_VIRTUAL_TRADING = {
    'initial_capital': 10000.0,
    'initial_agents': 10,
    'max_agents': 50,
    'trading_interval_seconds': 5,
    'max_daily_loss_pct': 10.0,  # 每日最大亏损百分比
    'max_drawdown_pct': 20.0,    # 最大回撤百分比
    'performance_test': False,
    'performance_metrics_enabled': True,
    'api_call_limit_per_minute': 600,
    'cache_ttl_seconds': 10,
    'concurrent_agents_threshold': 15,
    
    'logging': {
        'dir': 'logs',
        'file_prefix': 'prometheus_virtual',
        'level': 'INFO',
        'max_size_mb': 100,
        'backup_count': 10
    },
    
    'risk': {
        'max_position_size_pct': 5.0,  # 最大仓位百分比
        'max_leverage': 1.0,          # 最大杠杆倍数
        'stop_loss_pct': 2.0,         # 止损百分比
        'take_profit_pct': 5.0,       # 止盈百分比
        'max_open_trades': 5          # 最大开仓数量
    },
    
    'okx_api': {
        'api_key': 'your_api_key',
        'secret_key': 'your_secret_key',
        'passphrase': 'your_passphrase',
        'use_testnet': True
    }
}
EOF
    
    echo -e "${GREEN}✓ 已创建默认config_virtual.py${NC}"
    echo -e "${YELLOW}请编辑config_virtual.py，添加您的OKX API凭证${NC}"
    exit 0
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}警告: 未找到虚拟环境venv${NC}"
    echo -e "正在创建虚拟环境..."
    
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 已创建虚拟环境${NC}"
        echo -e "正在安装依赖..."
        
        # 激活虚拟环境并安装依赖
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        elif [ -f "venv/Scripts/activate" ]; then
            # Windows环境
            source venv/Scripts/activate
        fi
        
        # 升级pip
        pip install --upgrade pip
        
        # 安装依赖
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            echo -e "${YELLOW}警告: 未找到requirements.txt，安装基本依赖${NC}"
            pip install okx pandas numpy matplotlib seaborn colorlog
        fi
        
        echo -e "${GREEN}✓ 依赖安装完成${NC}"
    else
        echo -e "${RED}错误: 创建虚拟环境失败${NC}"
        exit 1
    fi
fi

# 激活虚拟环境
echo -e "正在激活虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows环境
    source venv/Scripts/activate
else
    echo -e "${YELLOW}警告: 无法找到激活脚本，请手动激活虚拟环境${NC}"
fi

# 检查API凭证（简化检查）
echo -e "正在检查配置..."
grep -q "your_api_key" config_virtual.py
if [ $? -eq 0 ]; then
    echo -e "${RED}错误: config_virtual.py中的API凭证未设置${NC}"
    echo -e "请编辑config_virtual.py，添加您的OKX API凭证"
    exit 1
fi

# 开始运行
echo -e "${GREEN}✓ 所有检查通过${NC}"
echo -e "${BLUE}==========================================${NC}"

if [ "$PERFORMANCE_TEST" = true ]; then
    echo -e "${YELLOW}启动性能测试模式...${NC}"
    echo -e "持续时间: ${DURATION}秒"
    echo -e "日志级别: ${LOG_LEVEL}"
    echo -e "${BLUE}==========================================${NC}"
    
    python test_performance.py --duration $DURATION --log-level $LOG_LEVEL
else
    echo -e "${YELLOW}启动虚拟交易模式...${NC}"
    echo -e "持续时间: ${DURATION}秒 (${DURATION//3600}小时)"
    echo -e "日志级别: ${LOG_LEVEL}"
    echo -e "${BLUE}==========================================${NC}"
    echo -e "按 Ctrl+C 停止交易"
    echo -e "${BLUE}==========================================${NC}"
    
    python run_virtual_trading.py --duration $DURATION --log-level $LOG_LEVEL
fi

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}\n✓ 程序正常退出${NC}"
else
    echo -e "${RED}\n✗ 程序异常退出 (退出码: $exit_code)${NC}"
fi

# 显示运行建议
echo -e "\n${BLUE}运行建议:${NC}"
echo -e "1. 查看logs目录下的交易日志了解详情"
echo -e "2. 对于性能测试，检查performance_charts目录下的性能报告"
echo -e "3. 如需系统级服务，使用systemd服务配置文件"

echo -e "\n${BLUE}==========================================${NC}"
echo -e "${GREEN}谢谢使用Prometheus v3.0${NC}"
echo -e "${BLUE}==========================================${NC}"
