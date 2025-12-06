#!/bin/bash
# VPS监控快捷命令
# ================

VPS="root@45.76.97.37"

# 查看最新状态（最后10个周期）
alias vps-status='ssh $VPS "tail -200 ~/prometheus/prometheus_vps.log | grep -E \"交易周期|当前价格|账户总价值|存活Agent|平均资金\" | tail -50"'

# 查看实时日志
alias vps-log='ssh $VPS "tail -f ~/prometheus/prometheus_vps.log"'

# 查看进程
alias vps-ps='ssh $VPS "ps aux | grep vps_main"'

# 查看错误
alias vps-error='ssh $VPS "grep ERROR ~/prometheus/prometheus_vps.log | tail -20"'

# 查看进化记录
alias vps-evolution='ssh $VPS "grep 进化 ~/prometheus/prometheus_vps.log"'

# 重新连接screen
alias vps-screen='ssh $VPS -t "screen -r prometheus"'

# 查看运行时长
alias vps-uptime='ssh $VPS "head -1 ~/prometheus/prometheus_vps.log && tail -1 ~/prometheus/prometheus_vps.log"'

# 快速摘要
vps-summary() {
    echo ""
    echo "========================================"
    echo "🚀 VPS运行摘要"
    echo "========================================"
    echo ""
    
    echo "📊 进程状态:"
    ssh $VPS "ps aux | grep 'vps_main.py' | grep -v grep | wc -l | xargs -I {} echo '   运行中的进程: {} 个'"
    
    echo ""
    echo "📈 最新状态（最后3个周期）:"
    ssh $VPS "tail -100 ~/prometheus/prometheus_vps.log | grep -E '交易周期 #' | tail -3"
    ssh $VPS "tail -100 ~/prometheus/prometheus_vps.log | grep '当前价格' | tail -3"
    ssh $VPS "tail -100 ~/prometheus/prometheus_vps.log | grep '账户总价值' | tail -3"
    ssh $VPS "tail -100 ~/prometheus/prometheus_vps.log | grep '存活Agent' | tail -3"
    
    echo ""
    echo "⚠️  错误统计:"
    ssh $VPS "grep ERROR ~/prometheus/prometheus_vps.log | wc -l | xargs -I {} echo '   总错误数: {} 条'"
    
    echo ""
    echo "🧬 进化状态:"
    EVOL=$(ssh $VPS "grep '进化' ~/prometheus/prometheus_vps.log | wc -l")
    echo "   进化次数: $EVOL 次"
    
    echo ""
    echo "========================================"
    echo ""
}

# 使用说明
vps-help() {
    echo ""
    echo "📋 VPS监控命令:"
    echo ""
    echo "   vps-summary      - 快速摘要（推荐）"
    echo "   vps-status       - 查看最新状态"
    echo "   vps-log          - 实时日志"
    echo "   vps-ps           - 查看进程"
    echo "   vps-error        - 查看错误"
    echo "   vps-evolution    - 查看进化"
    echo "   vps-screen       - 重新连接screen"
    echo "   vps-uptime       - 运行时长"
    echo ""
    echo "💡 使用方法:"
    echo "   source monitor_commands.sh"
    echo "   vps-summary"
    echo ""
}

echo "✅ VPS监控命令已加载！"
echo "   输入 'vps-help' 查看所有命令"
echo "   输入 'vps-summary' 查看快速摘要"

