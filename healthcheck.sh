#!/bin/bash

# Prometheus-V30 健康检查脚本
# 该脚本用于监控交易系统的运行状态，确保系统正常运行

set -e

# 配置变量
APP_DIR="/app"
LOG_FILE="${APP_DIR}/logs/healthcheck.log"
MAX_MEMORY_USAGE=90  # 最大内存使用率百分比
MAX_CPU_USAGE=90    # 最大CPU使用率百分比
NETWORK_TEST_TIMEOUT=5  # 网络测试超时时间（秒）
EXPECTED_PROCESS="python -m prometheus_v30"  # 期望运行的进程

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查进程是否运行
check_process() {
    log "检查交易系统进程状态..."
    if pgrep -f "$EXPECTED_PROCESS" > /dev/null; then
        log "交易系统进程正常运行"
        return 0
    else
        log "错误: 交易系统进程未运行"
        return 1
    fi
}

# 检查内存使用情况
check_memory() {
    log "检查内存使用情况..."
    MEMORY_USAGE=$(free | awk '/Mem/{printf("%.0f", $3/$2*100)}')
    log "当前内存使用率: ${MEMORY_USAGE}%"
    if [ "$MEMORY_USAGE" -lt "$MAX_MEMORY_USAGE" ]; then
        log "内存使用正常"
        return 0
    else
        log "警告: 内存使用率过高 (${MEMORY_USAGE}%)"
        # 内存过高不直接失败，仅记录警告
        return 0
    fi
}

# 检查CPU使用情况
check_cpu() {
    log "检查CPU使用情况..."
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    CPU_USAGE_INT=$(printf "%.0f" "$CPU_USAGE")
    log "当前CPU使用率: ${CPU_USAGE_INT}%"
    if [ "$CPU_USAGE_INT" -lt "$MAX_CPU_USAGE" ]; then
        log "CPU使用正常"
        return 0
    else
        log "警告: CPU使用率过高 (${CPU_USAGE_INT}%)"
        # CPU过高不直接失败，仅记录警告
        return 0
    fi
}

# 检查网络连接
check_network() {
    log "检查网络连接..."
    # 测试到OKX API的连接
    if curl -s --max-time "$NETWORK_TEST_TIMEOUT" "https://www.okx.com" > /dev/null; then
        log "网络连接正常"
        return 0
    else
        log "错误: 无法连接到外部网络"
        return 1
    fi
}

# 检查日志是否有严重错误
check_logs() {
    log "检查日志错误..."
    if [ -f "${APP_DIR}/logs/trading.log" ]; then
        # 查找最近5分钟内的错误日志
        ERROR_COUNT=$(grep -i "error\|exception\|fail\|critical" "${APP_DIR}/logs/trading.log" | wc -l)
        if [ "$ERROR_COUNT" -eq 0 ]; then
            log "日志中未发现错误"
            return 0
        else
            log "警告: 日志中发现 ${ERROR_COUNT} 个错误记录"
            # 错误日志不直接导致容器不健康，仅记录警告
            return 0
        fi
    else
        log "警告: 交易日志文件不存在"
        return 0
    fi
}

# 检查磁盘空间
check_disk() {
    log "检查磁盘空间..."
    DISK_USAGE=$(df -h "/" | awk 'NR==2 {print $5}' | sed 's/%//')
    log "当前磁盘使用率: ${DISK_USAGE}%"
    if [ "$DISK_USAGE" -lt 95 ]; then  # 磁盘空间低于95%认为正常
        log "磁盘空间正常"
        return 0
    else
        log "警告: 磁盘空间不足 (${DISK_USAGE}%)"
        # 磁盘空间不足不直接失败，仅记录警告
        return 0
    fi
}

# 主健康检查函数
main() {
    log "开始执行健康检查"
    
    # 收集所有检查结果
    local FAILED_CHECKS=0
    
    check_process || FAILED_CHECKS=$((FAILED_CHECKS + 1))
    check_memory
    check_cpu
    check_network || FAILED_CHECKS=$((FAILED_CHECKS + 1))
    check_logs
    check_disk
    
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        log "所有关键检查通过，容器健康状态正常"
        exit 0
    else
        log "错误: ${FAILED_CHECKS} 个关键检查失败，容器不健康"
        exit 1
    fi
}

# 执行主函数
main