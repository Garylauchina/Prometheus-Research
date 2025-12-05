#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析 v5.2 Day 1 压力测试结果
"""

import pandas as pd
import numpy as np

print("="*80)
print("📊 v5.2 Day 1 压力测试结果分析")
print("="*80)
print()

# 读取结果
df = pd.read_csv("v5.2_day1_stress_test_results.csv")

INITIAL_POPULATION = 100
CYCLES = 20
RUNS = 3

# ============================================================================
# 1. 种群稳定性分析
# ============================================================================
print("1️⃣ 种群稳定性分析")
print("-" * 80)

for run_id in range(1, RUNS + 1):
    run_data = df[df['run_id'] == run_id]
    
    initial = run_data['population_before'].iloc[0]
    final = run_data['population_after'].iloc[-1]
    min_pop = run_data['population_after'].min()
    max_pop = run_data['population_after'].max()
    
    print(f"\n运行{run_id}:")
    print(f"  初始 → 最终: {initial} → {final} ({final-initial:+d}, {final/initial*100:.1f}%)")
    print(f"  最低种群: {min_pop} ({min_pop/INITIAL_POPULATION*100:.1f}%)")
    print(f"  最高种群: {max_pop} ({max_pop/INITIAL_POPULATION*100:.1f}%)")
    print(f"  波动范围: {max_pop - min_pop}个Agent")

# 汇总统计
final_populations = df.groupby('run_id')['population_after'].last()
min_populations = df.groupby('run_id')['population_after'].min()

avg_final = final_populations.mean()
avg_min = min_populations.mean()

print(f"\n{'='*80}")
print(f"📈 汇总:")
print(f"  平均最终种群: {avg_final:.1f} ({avg_final/INITIAL_POPULATION*100:.1f}%)")
print(f"  平均最低种群: {avg_min:.1f} ({avg_min/INITIAL_POPULATION*100:.1f}%)")

# 判断
if avg_min >= INITIAL_POPULATION * 0.70:
    print(f"  ✅ 通过！最低种群 > 70%阈值")
elif avg_min >= INITIAL_POPULATION * 0.60:
    print(f"  ⚠️ 警告！最低种群在60-70%之间")
else:
    print(f"  ❌ 失败！最低种群 < 60%")

# ============================================================================
# 2. 种群波动分析
# ============================================================================
print(f"\n{'='*80}")
print("2️⃣ 种群波动分析")
print("-" * 80)

for run_id in range(1, RUNS + 1):
    run_data = df[df['run_id'] == run_id]
    
    growth = len(run_data[run_data['population_change'] > 0])
    shrink = len(run_data[run_data['population_change'] < 0])
    stable = len(run_data[run_data['population_change'] == 0])
    
    total_fluctuation = run_data['population_change'].abs().sum()
    
    print(f"\n运行{run_id}:")
    print(f"  增长周期: {growth}/{CYCLES} ({growth/CYCLES*100:.0f}%)")
    print(f"  萎缩周期: {shrink}/{CYCLES} ({shrink/CYCLES*100:.0f}%)")
    print(f"  平衡周期: {stable}/{CYCLES} ({stable/CYCLES*100:.0f}%)")
    print(f"  总波动量: {total_fluctuation}个Agent")

# 全局统计
total_growth = len(df[df['population_change'] > 0])
total_shrink = len(df[df['population_change'] < 0])
total_stable = len(df[df['population_change'] == 0])
total_cycles = len(df)

print(f"\n{'='*80}")
print(f"📊 全局统计:")
print(f"  增长周期: {total_growth}/{total_cycles} ({total_growth/total_cycles*100:.1f}%)")
print(f"  萎缩周期: {total_shrink}/{total_cycles} ({total_shrink/total_cycles*100:.1f}%)")
print(f"  平衡周期: {total_stable}/{total_cycles} ({total_stable/total_cycles*100:.1f}%)")

if total_growth > 0 and total_shrink > 0:
    print(f"  ✅ 真实自然波动（有增有减）")
else:
    print(f"  ⚠️ 单向趋势")

# ============================================================================
# 3. 基因多样性分析
# ============================================================================
print(f"\n{'='*80}")
print("3️⃣ 基因多样性分析")
print("-" * 80)

for run_id in range(1, RUNS + 1):
    run_data = df[df['run_id'] == run_id]
    
    initial_entropy = run_data['gene_entropy'].iloc[0]
    final_entropy = run_data['gene_entropy'].iloc[-1]
    change = final_entropy - initial_entropy
    
    print(f"\n运行{run_id}:")
    print(f"  初始基因熵: {initial_entropy:.3f}")
    print(f"  最终基因熵: {final_entropy:.3f}")
    print(f"  变化: {change:+.3f} ({change/initial_entropy*100:+.1f}%)")

# 汇总
avg_initial_entropy = df.groupby('run_id')['gene_entropy'].first().mean()
avg_final_entropy = df.groupby('run_id')['gene_entropy'].last().mean()
avg_change = avg_final_entropy - avg_initial_entropy

print(f"\n{'='*80}")
print(f"📊 汇总:")
print(f"  平均初始基因熵: {avg_initial_entropy:.3f}")
print(f"  平均最终基因熵: {avg_final_entropy:.3f}")
print(f"  平均变化: {avg_change:+.3f}")

if avg_change >= 0:
    print(f"  ✅ 多样性维持或增加")
elif avg_change >= -0.05:
    print(f"  ⚠️ 轻微下降（可接受）")
else:
    print(f"  ❌ 多样性显著下降")

# ============================================================================
# 4. 资金变化分析
# ============================================================================
print(f"\n{'='*80}")
print("4️⃣ 资金变化分析（极端市场压力）")
print("-" * 80)

for run_id in range(1, RUNS + 1):
    run_data = df[df['run_id'] == run_id]
    
    initial_capital = run_data['avg_capital_before'].iloc[0]
    final_capital = run_data['avg_capital_after'].iloc[-1]
    loss_rate = (final_capital - initial_capital) / initial_capital * 100
    
    print(f"\n运行{run_id}:")
    print(f"  初始平均资金: ${initial_capital:.0f}")
    print(f"  最终平均资金: ${final_capital:.0f}")
    print(f"  损失率: {loss_rate:.1f}%")

# ============================================================================
# 5. 成功标准判断
# ============================================================================
print(f"\n{'='*80}")
print("🏁 成功标准判断")
print("="*80)
print()

criteria = {
    '种群不崩溃（>60%）': avg_min >= INITIAL_POPULATION * 0.60,
    '存活率健康（>70%）': avg_final >= INITIAL_POPULATION * 0.70,
    '真实波动（有增有减）': total_growth > 0 and total_shrink > 0,
    '多样性维持（下降<5%）': avg_change >= -0.05,
}

passed = sum(criteria.values())
total = len(criteria)

for name, result in criteria.items():
    status = "✅ 通过" if result else "❌ 失败"
    print(f"  {status}: {name}")

print(f"\n{'='*80}")
print(f"总评: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
print("="*80)

if passed == total:
    print(f"\n🎉 完美通过！v5.2 Day 1改进非常稳定！")
    print(f"✅ 可以安全地继续Day 2开发（添加市场噪声层）")
elif passed >= total * 0.75:
    print(f"\n✅ 良好！大部分指标通过。")
    print(f"💡 建议：继续开发，但保持观察")
elif passed >= total * 0.50:
    print(f"\n⚠️ 警告！部分指标未通过。")
    print(f"💡 建议：调优参数后再继续")
else:
    print(f"\n❌ 失败！系统不稳定。")
    print(f"💡 建议：回退改动，重新设计")

print()

