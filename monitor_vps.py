#!/usr/bin/env python3
"""
VPS监控脚本
===========

从本地Mac监控VPS上Prometheus的运行状态

用法：
    python monitor_vps.py
"""

import subprocess
import re
from datetime import datetime

VPS_IP = "45.76.97.37"
VPS_USER = "root"
LOG_PATH = "~/prometheus/prometheus_vps.log"


def run_ssh_command(command):
    """执行SSH命令"""
    full_command = f'ssh {VPS_USER}@{VPS_IP} "{command}"'
    try:
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        return f"错误: {e}"


def get_latest_status():
    """获取最新状态"""
    output = run_ssh_command(f"tail -100 {LOG_PATH}")
    
    # 解析最新的交易周期信息
    cycles = re.findall(r'🔄 交易周期 #(\d+)', output)
    prices = re.findall(r'当前价格: \$([0-9,\.]+)', output)
    price_changes = re.findall(r'价格变化: ([+-]?[0-9\.]+%)', output)
    account_values = re.findall(r'账户总价值: \$([0-9,\.]+)', output)
    agents = re.findall(r'存活Agent: (\d+)/(\d+)', output)
    avg_capitals = re.findall(r'平均资金: \$([0-9,\.]+)', output)
    
    if cycles:
        latest_cycle = cycles[-1]
        latest_price = prices[-1] if prices else "N/A"
        latest_change = price_changes[-1] if price_changes else "N/A"
        latest_value = account_values[-1] if account_values else "N/A"
        latest_agents = f"{agents[-1][0]}/{agents[-1][1]}" if agents else "N/A"
        latest_avg = avg_capitals[-1] if avg_capitals else "N/A"
        
        return {
            'cycle': latest_cycle,
            'price': latest_price,
            'change': latest_change,
            'value': latest_value,
            'agents': latest_agents,
            'avg_capital': latest_avg
        }
    
    return None


def get_evolution_status():
    """检查是否有进化记录"""
    output = run_ssh_command(f"grep '进化' {LOG_PATH} | tail -5")
    return output.strip() if output.strip() else "暂无进化记录"


def get_error_count():
    """统计错误数量"""
    output = run_ssh_command(f"grep ERROR {LOG_PATH} | wc -l")
    return output.strip()


def check_process_running():
    """检查进程是否运行"""
    output = run_ssh_command("ps aux | grep vps_main.py | grep -v grep")
    return bool(output.strip())


def get_uptime():
    """获取运行时长"""
    output = run_ssh_command(f"head -1 {LOG_PATH}")
    if output:
        # 提取第一条日志的时间
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', output)
        if match:
            start_time = match.group(1)
            return start_time
    return "未知"


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("🚀 Prometheus VPS 实时监控")
    print("=" * 80)
    print()
    
    # 检查进程
    print("📊 系统状态:")
    is_running = check_process_running()
    if is_running:
        print("   ✅ 进程状态: 运行中")
    else:
        print("   ❌ 进程状态: 未运行")
        return
    
    # 运行时长
    start_time = get_uptime()
    print(f"   ⏰ 启动时间: {start_time}")
    
    # 错误统计
    error_count = get_error_count()
    print(f"   ⚠️  错误数量: {error_count}条")
    
    print()
    
    # 最新状态
    print("📈 最新交易状态:")
    status = get_latest_status()
    
    if status:
        print(f"   🔄 交易周期: #{status['cycle']}")
        print(f"   💰 BTC价格: ${status['price']}")
        print(f"   📊 价格变化: {status['change']}")
        print(f"   💼 账户总价值: ${status['value']}")
        print(f"   👥 存活Agent: {status['agents']}")
        print(f"   📊 平均资金: ${status['avg_capital']}")
    else:
        print("   ⚠️  无法获取最新状态")
    
    print()
    
    # 进化状态
    print("🧬 进化记录:")
    evolution = get_evolution_status()
    if evolution:
        for line in evolution.split('\n'):
            if line.strip():
                print(f"   {line}")
    
    print()
    print("=" * 80)
    print()
    
    # 提示
    print("💡 更多命令:")
    print(f"   查看实时日志: ssh {VPS_USER}@{VPS_IP} 'tail -f {LOG_PATH}'")
    print(f"   重新连接screen: ssh {VPS_USER}@{VPS_IP} -t 'screen -r prometheus'")
    print()


if __name__ == "__main__":
    main()

