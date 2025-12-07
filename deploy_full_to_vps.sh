#!/bin/bash
# 部署完整版实盘引擎到VPS
# 用法: bash deploy_full_to_vps.sh

echo "=================================="
echo "🚀 部署完整版实盘引擎到VPS"
echo "=================================="

VPS_HOST="45.76.97.37"
VPS_USER="root"
VPS_DIR="/root/prometheus"

# 1. 停止现有进程
echo ""
echo "⏹️  停止现有进程..."
ssh ${VPS_USER}@${VPS_HOST} "pkill -f vps_main.py"
sleep 2
echo "✅ 完成"

# 2. 备份原文件
echo ""
echo "💾 备份原文件..."
ssh ${VPS_USER}@${VPS_HOST} "cp ${VPS_DIR}/prometheus/trading/live_engine.py ${VPS_DIR}/prometheus/trading/live_engine.py.backup.\$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
echo "✅ 完成"

# 3. 上传完整版
echo ""
echo "📤 上传完整版引擎..."
scp prometheus/trading/live_engine_full.py ${VPS_USER}@${VPS_HOST}:${VPS_DIR}/prometheus/trading/live_engine.py
echo "✅ 完成"

# 4. 清空日志
echo ""
echo "📝 清空旧日志..."
ssh ${VPS_USER}@${VPS_HOST} "echo '' > ${VPS_DIR}/prometheus_vps.log"
echo "✅ 完成"

# 5. 重启系统
echo ""
echo "🚀 重启系统..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${VPS_DIR} && nohup python3 vps_main.py --config config/vps_config.json > /dev/null 2>&1 &"
sleep 5
echo "✅ 完成"

# 6. 检查状态
echo ""
echo "📊 检查进程状态..."
ssh ${VPS_USER}@${VPS_HOST} "ps aux | grep vps_main.py | grep -v grep"

echo ""
echo "=================================="
echo "✅ 部署完成！"
echo "=================================="
echo ""
echo "📝 后续操作:"
echo "   1. 查看日志: ssh root@45.76.97.37 'tail -f /root/prometheus/prometheus_vps.log'"
echo "   2. 停止系统: ssh root@45.76.97.37 'pkill -f vps_main.py'"
echo ""
echo "⚠️  注意: 当前配置 enable_real_trading=False (仅模拟)"
echo "   要启用真实交易，需要修改 live_engine_full.py 中的默认值"
echo ""

