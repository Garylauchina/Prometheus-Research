#!/bin/bash
# 实时监控训练进度

LOG_FILE="results/gene_collection_training_v2.log"

echo "🔍 训练进度实时监控"
echo "===================="
echo ""

while true; do
    clear
    echo "🔍 训练进度实时监控 - $(date '+%H:%M:%S')"
    echo "================================================"
    echo ""
    
    # 总行数
    LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
    echo "📊 日志行数: $LINES"
    echo ""
    
    # 最近的进度信息
    echo "📈 最近进展:"
    tail -n 100 "$LOG_FILE" 2>/dev/null | grep -E "(Round|完成|ROI|经验记录|基因积累)" | tail -n 10
    echo ""
    
    # 最新日志
    echo "📝 最新日志:"
    tail -n 5 "$LOG_FILE" 2>/dev/null
    echo ""
    echo "================================================"
    echo "按 Ctrl+C 退出监控"
    
    sleep 3
done

