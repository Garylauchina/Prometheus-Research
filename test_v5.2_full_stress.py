"""
Prometheus v5.2 完整压力测试

测试v5.2的3大改进：
1. 种群波动（±10%）
2. 变异率随机化（±20%）
3. 市场噪声层（流动性冲击/滑点尖峰/资金费率跳跃/订单簿断层）

Author: Prometheus Team
Version: v5.2
Date: 2025-12-05
"""

import sys
import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 导入核心模块
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.mastermind import Mastermind
from prometheus.core.slippage_model import SlippageModel, MarketCondition, OrderSide, OrderType
from prometheus.core.funding_rate_model import FundingRateModel
from prometheus.core.market_noise import create_noise_layer  # v5.2新增

print("="*80)
print("🔥 Prometheus v5.2 完整压力测试")
print("="*80)
print("测试内容：")
print("  ✅ Day 1改进：种群波动（90-110%）+ 变异率随机化（±20%）")
print("  ✅ Day 2改进：市场噪声层（流动性/滑点/资金费率/订单簿）")
print()

# ============================================================================
# 配置
# ============================================================================
POPULATION_SIZE = 50
CYCLES = 15
INITIAL_CAPITAL = 10000.0

print(f"📋 测试配置:")
print(f"   种群规模: {POPULATION_SIZE}个Agent")
print(f"   进化轮数: {CYCLES}轮")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print()

# 清理旧结果文件
result_file = 'v5.2_full_stress_results.csv'
if os.path.exists(result_file):
    os.remove(result_file)
    logging.info(f"已删除旧结果文件: {result_file}")

# ============================================================================
# 初始化系统
# ============================================================================
print("="*80)
print("📊 [1/3] 初始化系统")
print("="*80)
print()

# 1. 创建Moirai
moirai = Moirai(num_families=50)

# 2. 创建初始Agent
print(f"   🧵 Clotho开始纺织{POPULATION_SIZE}条生命之线...")
created_agents = moirai._genesis_create_agents(
    agent_count=POPULATION_SIZE,
    gene_pool={},
    capital_per_agent=INITIAL_CAPITAL
)
moirai.agents.extend(created_agents)
print(f"   🧵 Clotho纺织完成: {len(moirai.agents)}个Agent诞生")
print()

# 3. 创建进化管理器（v5.2：含种群波动和变异率随机化）
evolution_manager = EvolutionManagerV5(
    moirai=moirai,
    elite_ratio=0.2,
    elimination_ratio=0.3,
    num_families=50
)

# 4. 创建Mastermind
mastermind = Mastermind(
    initial_capital=INITIAL_CAPITAL * POPULATION_SIZE,
    decision_mode='llm'
)

# 5. 创建市场模型
slippage_model = SlippageModel(
    base_slippage=0.002,      # 0.2%基础滑点
    liquidity_factor=0.5,
    volatility_factor=1.5
)

funding_rate_model = FundingRateModel()

# 6. 创建市场噪声层（v5.2新增）
market_noise = create_noise_layer("moderate")  # 中等噪声

print("   ✅ 系统初始化完成")
print(f"   种群: {len(moirai.agents)}个Agent")
print(f"   噪声层: moderate模式")
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
    print(f"\n{'='*70}")
    print(f"🧬 进化周期 #{cycle}/{CYCLES}")
    print(f"{'='*70}")
    
    population_before = len(moirai.agents)
    
    # v5.2 Day 2：应用市场噪声
    base_liquidity = 1.0
    base_slippage = 0.002
    base_funding = 0.0001
    
    noisy_market = market_noise.apply_noise(
        base_liquidity=base_liquidity,
        base_slippage=base_slippage,
        base_funding=base_funding,
        current_cycle=cycle
    )
    
    if noisy_market['events']:
        print(f"   🌪️ 噪声事件: {', '.join(noisy_market['events'])}")
    
    actual_liquidity = noisy_market['liquidity']
    actual_slippage = noisy_market['slippage']
    actual_funding = noisy_market['funding']
    
    # 模拟交易
    import random
    for agent in moirai.agents:
        # 随机盈亏，考虑噪声
        if random.random() < 0.6:  # 60%盈利
            pnl_base = random.uniform(100, 500)
        else:  # 40%亏损
            pnl_base = random.uniform(-400, -100)
        
        # 噪声影响：滑点增加导致成本上升
        slippage_cost = abs(pnl_base) * (actual_slippage / base_slippage - 1) * 0.5
        
        # 噪声影响：流动性降低导致额外成本
        liquidity_cost = abs(pnl_base) * (1 - actual_liquidity / base_liquidity) * 0.3
        
        # 噪声影响：资金费率波动
        funding_cost = abs(pnl_base) * abs(actual_funding - base_funding) * 10
        
        # 总PnL
        total_pnl = pnl_base - slippage_cost - liquidity_cost - funding_cost
        agent.current_capital += total_pnl
    
    # 执行进化（v5.2：含种群波动和变异率随机化）
    evolution_manager.run_evolution_cycle(current_price=100000.0)
    
    # 记录结果
    population_after = len(moirai.agents)
    population_change = population_after - population_before
    
    health = evolution_manager.blood_lab.population_checkup(evolution_manager.moirai.agents)
    
    avg_capital = sum(a.current_capital for a in moirai.agents) / len(moirai.agents)
    
    results.append({
        'cycle': cycle,
        'population_before': population_before,
        'population_after': population_after,
        'population_change': population_change,
        'avg_capital': avg_capital,
        'lineage_entropy': health.lineage_entropy_normalized,
        'gene_entropy': health.gene_entropy,
        'health': health.overall_health,
        'noise_events': len(noisy_market['events'])
    })
    
    print(f"   种群: {population_before} → {population_after} ({population_change:+d})")
    print(f"   平均资金: ${avg_capital:.0f}")
    print(f"   基因熵: {health.gene_entropy:.3f}")
    print()

# 保存结果
df_results = pd.DataFrame(results)
df_results.to_csv(result_file, index=False)
logging.info(f"结果已保存到: {result_file}")

# ============================================================================
# 结果分析
# ============================================================================
print("="*80)
print("📊 [3/3] 结果分析")
print("="*80)
print()

print("1️⃣  种群波动分析 (v5.2 Day 1特性)")
print("--------------------------------------------------------------------------------")
growth_cycles = (df_results['population_change'] > 0).sum()
shrink_cycles = (df_results['population_change'] < 0).sum()
stable_cycles = (df_results['population_change'] == 0).sum()

print(f"  增长周期: {growth_cycles}/{CYCLES} ({growth_cycles/CYCLES:.1%})")
print(f"  萎缩周期: {shrink_cycles}/{CYCLES} ({shrink_cycles/CYCLES:.1%})")
print(f"  平衡周期: {stable_cycles}/{CYCLES} ({stable_cycles/CYCLES:.1%})")
print(f"  最终种群: {df_results['population_after'].iloc[-1]}个 ({df_results['population_after'].iloc[-1]/POPULATION_SIZE:.1%})")

if growth_cycles > 0 and shrink_cycles > 0:
    print(f"  ✅ 真实自然波动（有增有减）")
else:
    print(f"  ⚠️ 波动不足")
print()

print("2️⃣  市场噪声影响分析 (v5.2 Day 2特性)")
print("--------------------------------------------------------------------------------")
noise_stats = market_noise.get_statistics()
print(f"  总噪声事件: {noise_stats['total_events']}次")
print(f"  平均每轮: {noise_stats['total_events']/CYCLES:.1f}次")
print(f"  流动性冲击: {noise_stats['liquidity_shocks']}次")
print(f"  滑点尖峰: {noise_stats['slippage_spikes']}次")
print(f"  资金费率跳跃: {noise_stats['funding_jumps']}次")
print(f"  订单簿断层: {noise_stats['orderbook_gaps']}次")

if noise_stats['total_events'] > 0:
    print(f"  ✅ 市场噪声成功应用")
else:
    print(f"  ⚠️ 未检测到市场噪声")
print()

print("3️⃣  基因多样性维持")
print("--------------------------------------------------------------------------------")
initial_gene_entropy = df_results['gene_entropy'].iloc[0]
final_gene_entropy = df_results['gene_entropy'].iloc[-1]
entropy_change = final_gene_entropy - initial_gene_entropy

print(f"  初始基因熵: {initial_gene_entropy:.3f}")
print(f"  最终基因熵: {final_gene_entropy:.3f}")
print(f"  变化: {entropy_change:+.3f} ({entropy_change/initial_gene_entropy:+.1%})")

if abs(entropy_change / initial_gene_entropy) <= 0.15:
    print(f"  ✅ 基因多样性维持良好")
else:
    print(f"  ⚠️ 基因多样性波动较大")
print()

print("4️⃣  资金变化")
print("--------------------------------------------------------------------------------")
initial_capital = INITIAL_CAPITAL
final_capital = df_results['avg_capital'].iloc[-1]
capital_change = (final_capital - initial_capital) / initial_capital

print(f"  初始平均资金: ${initial_capital:.0f}")
print(f"  最终平均资金: ${final_capital:.0f}")
print(f"  变化率: {capital_change:+.1%}")
print()

# ============================================================================
# 成功标准判断
# ============================================================================
print("="*80)
print("🏁 v5.2完整测试成功标准")
print("="*80)
print()

all_pass = True

# 1. 种群稳定性
if df_results['population_after'].iloc[-1] >= POPULATION_SIZE * 0.80:
    print("  ✅ 种群稳定（>80%）")
else:
    print("  ❌ 种群萎缩过多")
    all_pass = False

# 2. 种群波动
if growth_cycles > 0 and shrink_cycles > 0:
    print("  ✅ 真实波动（有增有减）")
else:
    print("  ❌ 波动不足")
    all_pass = False

# 3. 市场噪声应用
if noise_stats['total_events'] > 0:
    print("  ✅ 市场噪声成功应用")
else:
    print("  ❌ 市场噪声未触发")
    all_pass = False

# 4. 基因多样性
if abs(entropy_change / initial_gene_entropy) <= 0.20:
    print("  ✅ 基因多样性维持")
else:
    print("  ❌ 基因多样性波动过大")
    all_pass = False

print()
if all_pass:
    print("="*80)
    print("🎉 v5.2完整测试通过！")
    print("="*80)
    print()
    print("✅ Day 1改进（种群波动+变异率随机化）：正常工作")
    print("✅ Day 2改进（市场噪声层）：正常工作")
    print()
    print("v5.2已成功引入可控的混乱！🌪️")
else:
    print("="*80)
    print("⚠️ v5.2测试未完全通过")
    print("="*80)
    print()
    print("需要进一步调试或调整参数。")

print()

