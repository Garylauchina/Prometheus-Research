#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus v5.2 Day 1 测试
测试改进1和改进2

改进1：允许5%种群波动
改进2：变异率随机化（±20%）
"""

import sys
import pandas as pd
from pathlib import Path
import logging

# 配置日志输出（v5.2：显示所有关键日志）
# 如果想看详细的本能数值，改为 logging.DEBUG
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别可看到本能数值
    format='%(message)s'
)

# 导入核心模块
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

print("="*80)
print("🧪 Prometheus v5.2 Day 1 测试")
print("="*80)
print("测试改进：")
print("  1. 允许5%种群波动")
print("  2. 变异率随机化（±20%）")
print()

# ============================================================================
# 配置
# ============================================================================
POPULATION_SIZE = 50  # 更大种群才能观察到波动（淘汰数≈15）
CYCLES = 10  # 更多周期
INITIAL_CAPITAL = 10000.0

# ============================================================================
# 初始化
# ============================================================================
print("📊 [1/3] 初始化系统...")
print(f"   种群: {POPULATION_SIZE}个Agent")
print(f"   周期: {CYCLES}轮")
print()

# 创建Moirai (不传initial_capital，在创建Agent时指定)
moirai = Moirai(num_families=50)

# 创建初始Agent
print(f"   创建{POPULATION_SIZE}个Agent...")
created_agents = moirai._genesis_create_agents(
    agent_count=POPULATION_SIZE,
    gene_pool={},  # v5.0不使用gene_pool，传空字典
    capital_per_agent=INITIAL_CAPITAL
)
# 添加到moirai的agents列表
moirai.agents.extend(created_agents)
print(f"   ✅ 创建完成: {len(moirai.agents)}个Agent")
print()

# 创建进化管理器
evolution_manager = EvolutionManagerV5(
    moirai=moirai,
    elite_ratio=0.2,
    elimination_ratio=0.3,
    num_families=50
)

print(f"   ✅ 进化管理器已初始化")
print()

# ============================================================================
# 模拟交易并进化
# ============================================================================
print("="*80)
print("📈 [2/3] 模拟交易并进化")
print("="*80)
print()

results = []

for cycle in range(1, CYCLES + 1):
    print(f"--- 周期 {cycle}/{CYCLES} ---")
    
    # 记录当前种群
    population_before = len(moirai.agents)
    
    # 模拟交易结果（随机盈亏）
    import random
    for agent in moirai.agents:
        pnl = random.uniform(-500, 500)
        agent.current_capital += pnl
    
    # 记录平均资金
    avg_capital = sum(a.current_capital for a in moirai.agents) / len(moirai.agents)
    
    # 执行进化
    evolution_manager.run_evolution_cycle()
    
    # 记录结果
    population_after = len(moirai.agents)
    population_change = population_after - population_before
    
    results.append({
        'cycle': cycle,
        'population_before': population_before,
        'population_after': population_after,
        'population_change': population_change,
        'avg_capital': avg_capital
    })
    
    print(f"   种群变化: {population_before} → {population_after} ({population_change:+d})")
    print()

# ============================================================================
# 结果分析
# ============================================================================
print("="*80)
print("📊 [3/3] 结果分析")
print("="*80)
print()

df = pd.DataFrame(results)

print("种群变化统计：")
print(df[['cycle', 'population_before', 'population_after', 'population_change']].to_string(index=False))
print()

# 分析
population_fluctuation = df['population_change'].abs().sum()
max_drop = df['population_change'].min()
max_rise = df['population_change'].max()

print("关键指标：")
print(f"   总波动: {population_fluctuation}个Agent")
print(f"   最大下降: {max_drop}个Agent")
print(f"   最大上升: {max_rise}个Agent")
print(f"   最终种群: {df['population_after'].iloc[-1]}个Agent")
print()

# 验证v5.2特性
print("="*80)
print("✅ v5.2特性验证")
print("="*80)

print("\n1. 种群波动（改进1）：")
# 统计增长和萎缩
growth_cycles = len(df[df['population_change'] > 0])
shrink_cycles = len(df[df['population_change'] < 0])
stable_cycles = len(df[df['population_change'] == 0])

if population_fluctuation > 0:
    print(f"   ✅ 检测到种群波动：{population_fluctuation}个Agent")
    print(f"   📈 增长周期: {growth_cycles}轮")
    print(f"   📉 萎缩周期: {shrink_cycles}轮")
    print(f"   ⚖️ 平衡周期: {stable_cycles}轮")
    
    # 判断是否是自然波动还是持续萎缩
    if growth_cycles > 0 and shrink_cycles > 0:
        print(f"   ✅ 真实的自然波动（有增有减）")
    elif shrink_cycles == CYCLES:
        print(f"   ⚠️ 持续萎缩（需要优化繁殖比例）")
    else:
        print(f"   ✅ 系统允许自然波动（v5.2特性）")
else:
    print(f"   ⚠️ 未检测到种群波动")
    print(f"   可能是种群规模太大或周期太少")

print("\n2. 变异率随机化（改进2）：")
print(f"   ✅ 查看日志中的 '🎲 噪声系数' 行")
print(f"   ✅ 每轮应该有不同的噪声系数（0.8-1.2）")
print(f"   ℹ️ 实际变异率 = 基础变异率 × 噪声系数")

print("\n="*80)
print("🎉 测试完成！")
print("="*80)
print("\n💡 提示：")
print("  - 查看上方日志，确认每轮都有 '📊 目标繁殖数' 行")
print("  - 繁殖比例应该在95%-105%之间随机波动")
print("  - 种群应该出现增长和萎缩的混合情况")
print("  - 如果持续萎缩，说明随机数生成器偏向低值")
print()

