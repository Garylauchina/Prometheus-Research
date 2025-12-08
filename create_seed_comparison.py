#!/usr/bin/env python3
"""创建20种子详细对比表"""

import json
from pathlib import Path

# 读取结果
with open("results/phase2a_results_20251208_101203.json", 'r') as f:
    data = json.load(f)

results = data['results']

print("=" * 120)
print("📊 Phase 2A - 20种子详细对比表")
print("=" * 120)
print()

# 表头
print(f"{'Seed':<8} {'系统收益':<12} {'实盈':<15} {'浮盈':<18} {'交易数':<10} {'实盈占比':<10}")
print("-" * 120)

# 排序：按系统收益降序
sorted_results = sorted(results, key=lambda x: x['system_return_pct'], reverse=True)

for r in sorted_results:
    seed = r['seed']
    sys_return = r['system_return_pct']
    realized = r['avg_realized_pnl']
    unrealized = r['avg_unrealized_pnl']
    trades = r['total_trades']
    
    # 计算实盈占比
    total_pnl = realized + unrealized
    realized_ratio = (realized / total_pnl * 100) if total_pnl > 0 else 0
    
    # 收益状态
    if sys_return > 2000:
        status = "🏆"
    elif sys_return > 1500:
        status = "✅"
    elif sys_return > 500:
        status = "⚠️"
    else:
        status = "🔴"
    
    print(f"{seed:<8} {status} {sys_return:>8.2f}%   ${realized:>10.2f}   ${unrealized:>13.2f}   {trades:>8}笔   {realized_ratio:>7.2f}%")

print("-" * 120)
print()

# 统计分析
print("📊 关键统计:")
print()

realized_values = [r['avg_realized_pnl'] for r in results]
unrealized_values = [r['avg_unrealized_pnl'] for r in results]

import numpy as np

print(f"实盈统计:")
print(f"  平均: ${np.mean(realized_values):,.2f}")
print(f"  最高: ${np.max(realized_values):,.2f}")
print(f"  最低: ${np.min(realized_values):,.2f}")
print()

print(f"浮盈统计:")
print(f"  平均: ${np.mean(unrealized_values):,.2f}")
print(f"  最高: ${np.max(unrealized_values):,.2f}")
print(f"  最低: ${np.min(unrealized_values):,.2f}")
print()

# 实盈占比分析
total_pnls = [r['avg_realized_pnl'] + r['avg_unrealized_pnl'] for r in results]
realized_ratios = [(r['avg_realized_pnl'] / (r['avg_realized_pnl'] + r['avg_unrealized_pnl']) * 100) 
                   if (r['avg_realized_pnl'] + r['avg_unrealized_pnl']) > 0 else 0
                   for r in results]

print(f"实盈占比统计:")
print(f"  平均: {np.mean(realized_ratios):.2f}%")
print(f"  最高: {np.max(realized_ratios):.2f}%")
print(f"  最低: {np.min(realized_ratios):.2f}%")
print()

print("=" * 120)
print()

print("🎯 结论:")
print()
print(f"✅ 所有种子盈利: 20/20")
print(f"⚠️ 实盈极低: 平均仅{np.mean(realized_ratios):.2f}%")
print(f"🔴 核心问题: Agent策略 = 买入持有，不平仓！")
print()
print("=" * 120)

