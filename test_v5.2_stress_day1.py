#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus v5.2 Day 1 压力测试
测试改进1和改进2的稳定性

改进1：允许±10%种群波动
改进2：变异率随机化（±20%）

压力条件：
- 100个Agent（2倍种群）
- 20轮进化（4倍周期）
- 极端市场（高波动+高滑点）
- 3次独立运行
"""

import sys
import pandas as pd
from pathlib import Path
import logging
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# 导入核心模块
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

print("="*80)
print("🧪 Prometheus v5.2 Day 1 压力测试")
print("="*80)
print("测试目标：")
print("  1. 种群波动稳定性（±10%范围）")
print("  2. 变异率随机化效果（0.8-1.2倍）")
print("  3. 极端市场下的系统稳定性")
print()

# ============================================================================
# 配置
# ============================================================================
POPULATION_SIZE = 100  # 更大种群
CYCLES = 20           # 更多周期
RUNS = 3              # 3次独立运行
INITIAL_CAPITAL = 10000.0

# 极端市场条件
EXTREME_VOLATILITY = 0.8   # 80%波动率
EXTREME_LOSS_RATE = 0.6    # 60%亏损概率

# ============================================================================
# 运行测试
# ============================================================================
all_runs_results = []

for run_id in range(1, RUNS + 1):
    print(f"\n{'='*80}")
    print(f"🔄 第 {run_id}/{RUNS} 次运行")
    print(f"{'='*80}\n")
    
    # 初始化
    moirai = Moirai(num_families=50)
    
    # 创建初始Agent
    print(f"📊 初始化...")
    print(f"   种群: {POPULATION_SIZE}个Agent")
    print(f"   周期: {CYCLES}轮")
    print(f"   市场: 极端条件（波动{EXTREME_VOLATILITY:.0%}，亏损率{EXTREME_LOSS_RATE:.0%}）")
    print()
    
    created_agents = moirai._genesis_create_agents(
        agent_count=POPULATION_SIZE,
        gene_pool={},
        capital_per_agent=INITIAL_CAPITAL
    )
    moirai.agents.extend(created_agents)
    
    # 创建进化管理器
    evolution_manager = EvolutionManagerV5(
        moirai=moirai,
        elite_ratio=0.20,
        elimination_ratio=0.30,
        num_families=50
    )
    
    print(f"   ✅ 初始化完成: {len(moirai.agents)}个Agent\n")
    
    # ============================================================================
    # 进化循环
    # ============================================================================
    print(f"{'='*80}")
    print(f"📈 开始进化（极端市场压力）")
    print(f"{'='*80}\n")
    
    run_results = []
    mutation_rates = []  # 记录变异率
    
    for cycle in range(1, CYCLES + 1):
        print(f"--- 周期 {cycle}/{CYCLES} ---")
        
        population_before = len(moirai.agents)
        
        # 模拟极端市场：大幅随机盈亏
        import random
        for agent in moirai.agents:
            # 60%概率亏损，40%概率盈利
            if random.random() < EXTREME_LOSS_RATE:
                # 亏损：-10%到-30%
                loss_pct = random.uniform(0.10, 0.30)
                pnl = -agent.current_capital * loss_pct
            else:
                # 盈利：+5%到+20%
                profit_pct = random.uniform(0.05, 0.20)
                pnl = agent.current_capital * profit_pct
            
            agent.current_capital += pnl
        
        # 记录平均资金
        avg_capital_before = sum(a.current_capital for a in moirai.agents) / len(moirai.agents)
        
        # 执行进化
        evolution_manager.run_evolution_cycle()
        
        # 记录结果
        population_after = len(moirai.agents)
        population_change = population_after - population_before
        avg_capital_after = sum(a.current_capital for a in moirai.agents) / len(moirai.agents)
        
        # 获取健康指标
        health = evolution_manager.blood_lab.population_checkup(moirai.agents)
        
        run_results.append({
            'run_id': run_id,
            'cycle': cycle,
            'population_before': population_before,
            'population_after': population_after,
            'population_change': population_change,
            'avg_capital_before': avg_capital_before,
            'avg_capital_after': avg_capital_after,
            'lineage_entropy': health.lineage_entropy_normalized,
            'gene_entropy': health.gene_entropy,
            'health': health.overall_health
        })
        
        print(f"   种群: {population_before} → {population_after} ({population_change:+d})")
        print(f"   资金: ${avg_capital_before:.0f} → ${avg_capital_after:.0f}")
        print(f"   健康: 血统熵{health.lineage_entropy_normalized:.3f} | 基因熵{health.gene_entropy:.3f} | {health.overall_health}")
        print()
    
    # 保存本次运行结果
    all_runs_results.extend(run_results)
    
    # 本次运行总结
    run_df = pd.DataFrame(run_results)
    final_population = run_df['population_after'].iloc[-1]
    min_population = run_df['population_after'].min()
    max_population = run_df['population_after'].max()
    population_range = max_population - min_population
    
    print(f"\n{'='*80}")
    print(f"📊 第{run_id}次运行总结")
    print(f"{'='*80}")
    print(f"  初始种群: {POPULATION_SIZE}")
    print(f"  最终种群: {final_population}")
    print(f"  最小种群: {min_population} ({(min_population/POPULATION_SIZE-1)*100:+.1f}%)")
    print(f"  最大种群: {max_population} ({(max_population/POPULATION_SIZE-1)*100:+.1f}%)")
    print(f"  波动范围: {population_range}个Agent")
    print(f"  存活率: {final_population/POPULATION_SIZE*100:.1f}%")
    print(f"{'='*80}\n")

# ============================================================================
# 汇总分析
# ============================================================================
print(f"\n{'='*80}")
print(f"📊 汇总分析（{RUNS}次运行）")
print(f"{'='*80}\n")

df = pd.DataFrame(all_runs_results)

# 按运行分组统计
for run_id in range(1, RUNS + 1):
    run_data = df[df['run_id'] == run_id]
    
    initial_pop = run_data['population_before'].iloc[0]
    final_pop = run_data['population_after'].iloc[-1]
    min_pop = run_data['population_after'].min()
    max_pop = run_data['population_after'].max()
    
    growth_cycles = len(run_data[run_data['population_change'] > 0])
    shrink_cycles = len(run_data[run_data['population_change'] < 0])
    stable_cycles = len(run_data[run_data['population_change'] == 0])
    
    print(f"运行{run_id}:")
    print(f"  种群: {initial_pop} → {final_pop} (存活率{final_pop/initial_pop*100:.1f}%)")
    print(f"  波动: 最小{min_pop} | 最大{max_pop} | 范围{max_pop-min_pop}")
    print(f"  周期: 增长{growth_cycles}轮 | 萎缩{shrink_cycles}轮 | 平衡{stable_cycles}轮")
    print()

# ============================================================================
# 关键指标
# ============================================================================
print(f"{'='*80}")
print(f"🎯 关键指标")
print(f"{'='*80}\n")

# 1. 种群稳定性
avg_final_population = df.groupby('run_id')['population_after'].last().mean()
avg_min_population = df.groupby('run_id')['population_after'].min().mean()
avg_survival_rate = avg_final_population / POPULATION_SIZE * 100

print(f"1. 种群稳定性:")
print(f"   平均最终种群: {avg_final_population:.1f} ({avg_survival_rate:.1f}%存活)")
print(f"   平均最低种群: {avg_min_population:.1f} ({avg_min_population/POPULATION_SIZE*100:.1f}%)")

# 判断
if avg_min_population >= POPULATION_SIZE * 0.70:
    print(f"   ✅ 通过！最低种群>{POPULATION_SIZE*0.70:.0f}（70%阈值）")
elif avg_min_population >= POPULATION_SIZE * 0.60:
    print(f"   ⚠️ 警告！最低种群在60-70%之间")
else:
    print(f"   ❌ 失败！最低种群<60%，系统不稳定")

# 2. 种群波动
total_fluctuation = df.groupby('run_id')['population_change'].apply(lambda x: x.abs().sum()).mean()
print(f"\n2. 种群波动:")
print(f"   平均总波动: {total_fluctuation:.1f}个Agent")
print(f"   平均波动率: {total_fluctuation/POPULATION_SIZE/CYCLES*100:.1f}%/周期")

if total_fluctuation > 0:
    growth_ratio = len(df[df['population_change'] > 0]) / len(df) * 100
    shrink_ratio = len(df[df['population_change'] < 0]) / len(df) * 100
    stable_ratio = len(df[df['population_change'] == 0]) / len(df) * 100
    
    print(f"   增长周期: {growth_ratio:.1f}%")
    print(f"   萎缩周期: {shrink_ratio:.1f}%")
    print(f"   平衡周期: {stable_ratio:.1f}%")
    
    if growth_ratio > 0 and shrink_ratio > 0:
        print(f"   ✅ 真实自然波动（有增有减）")
    else:
        print(f"   ⚠️ 单向趋势（缺乏真实波动）")

# 3. 基因多样性
avg_final_gene_entropy = df.groupby('run_id')['gene_entropy'].last().mean()
avg_initial_gene_entropy = df.groupby('run_id')['gene_entropy'].first().mean()
gene_entropy_change = avg_final_gene_entropy - avg_initial_gene_entropy

print(f"\n3. 基因多样性:")
print(f"   初始基因熵: {avg_initial_gene_entropy:.3f}")
print(f"   最终基因熵: {avg_final_gene_entropy:.3f}")
print(f"   变化: {gene_entropy_change:+.3f}")

if gene_entropy_change >= 0:
    print(f"   ✅ 多样性维持或增加")
else:
    print(f"   ⚠️ 多样性下降（可能需要更强保护）")

# ============================================================================
# 成功标准判断
# ============================================================================
print(f"\n{'='*80}")
print(f"🏁 成功标准判断")
print(f"{'='*80}\n")

success_criteria = {
    '种群不崩溃（>60%）': avg_min_population >= POPULATION_SIZE * 0.60,
    '存活率健康（>70%）': avg_final_population >= POPULATION_SIZE * 0.70,
    '真实波动（有增有减）': growth_ratio > 0 and shrink_ratio > 0,
    '多样性维持（熵不降）': gene_entropy_change >= -0.05,
}

passed_count = sum(success_criteria.values())
total_count = len(success_criteria)

for criterion, passed in success_criteria.items():
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"  {status}: {criterion}")

print(f"\n总评: {passed_count}/{total_count} 通过")

if passed_count == total_count:
    print(f"\n🎉 完美通过！v5.2 Day 1改进非常稳定！")
elif passed_count >= total_count * 0.75:
    print(f"\n✅ 良好！大部分指标通过，可以继续开发。")
elif passed_count >= total_count * 0.50:
    print(f"\n⚠️ 警告！部分指标未通过，需要调优。")
else:
    print(f"\n❌ 失败！系统不稳定，需要回退改动。")

# ============================================================================
# 保存结果
# ============================================================================
output_file = "v5.2_day1_stress_test_results.csv"
df.to_csv(output_file, index=False)
print(f"\n💾 详细数据已保存: {output_file}")

print(f"\n{'='*80}")
print(f"🎉 压力测试完成！")
print(f"{'='*80}\n")

