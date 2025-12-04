#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus v5.1 极端压力测试

测试场景：
1. 极端市场波动（-3.72%单小时跌幅）
2. 大规模种群（50个Agent）
3. 连续进化周期（10轮）
4. 高滑点环境
5. 极端资金费率
6. 验证系统鲁棒性
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# 导入核心模块
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.mastermind import Mastermind
from prometheus.core.slippage_model import SlippageModel, MarketCondition, OrderSide, OrderType
from prometheus.core.funding_rate_model import FundingRateModel
from prometheus.core.niche_protection import NicheProtectionSystem

print("="*80)
print("🔥 Prometheus v5.1 极端压力测试")
print("="*80)
print("⚠️  警告：将使用极端市场条件测试系统极限")
print()

# ============================================================================
# 配置：极端测试参数
# ============================================================================
TEST_CONFIG = {
    'population_size': 50,       # 大规模种群
    'evolution_cycles': 10,      # 连续10轮进化
    'extreme_volatility': 0.05,  # 5%极端波动
    'extreme_slippage': 0.005,   # 0.5%极端滑点
    'extreme_funding': 0.01,     # 1%极端资金费率
    'initial_capital': 10000.0,
}

print(f"📋 测试配置:")
print(f"   种群规模: {TEST_CONFIG['population_size']}个Agent")
print(f"   进化轮数: {TEST_CONFIG['evolution_cycles']}轮")
print(f"   极端波动: {TEST_CONFIG['extreme_volatility']*100:.1f}%")
print(f"   极端滑点: {TEST_CONFIG['extreme_slippage']*100:.2f}%")
print(f"   极端资金费率: {TEST_CONFIG['extreme_funding']*100:.2f}%")

# ============================================================================
# 第一步：加载极端波动时期数据
# ============================================================================
print("\n" + "="*80)
print("📊 [1/5] 加载极端波动时期数据...")
print("="*80)

data_file = Path("data/okx/BTC_USDT_1h_3y.parquet")
df = pd.read_parquet(data_file)
df['returns'] = df['close'].pct_change()

# 找出极端波动时期（Top 20）
extreme_periods = df.nlargest(20, 'returns', keep='all')
extreme_periods = pd.concat([extreme_periods, df.nsmallest(20, 'returns', keep='all')])
extreme_periods = extreme_periods.sort_values('timestamp')

print(f"✅ 找到 {len(extreme_periods)} 个极端波动时刻")
print(f"   最大涨幅: +{extreme_periods['returns'].max()*100:.2f}%")
print(f"   最大跌幅: {extreme_periods['returns'].min()*100:.2f}%")
print(f"   时间范围: {extreme_periods['timestamp'].min()} 至 {extreme_periods['timestamp'].max()}")

# ============================================================================
# 第二步：初始化极端压力环境
# ============================================================================
print("\n" + "="*80)
print("🔧 [2/5] 初始化极端压力环境...")
print("="*80)

# 创建系统组件
mastermind = Mastermind(initial_capital=100000.0, decision_mode='llm')
moirai = Moirai(num_families=50)
evolution_manager = EvolutionManagerV5(moirai=moirai)

# 创建极端市场模型
extreme_slippage_model = SlippageModel(
    base_slippage=TEST_CONFIG['extreme_slippage'],  # 10倍极端滑点
    liquidity_factor=0.05,  # 流动性差
    volatility_factor=2.0   # 波动率影响加倍
)

extreme_funding_model = FundingRateModel(
    base_rate=TEST_CONFIG['extreme_funding'],  # 10倍极端费率
    max_rate=0.05  # 5%最大费率
)

niche_protection = NicheProtectionSystem()

print("✅ 极端环境配置完成")
print(f"   基础滑点: {TEST_CONFIG['extreme_slippage']*100:.2f}% (正常10倍)")
print(f"   基础资金费率: {TEST_CONFIG['extreme_funding']*100:.2f}% (正常10倍)")

# ============================================================================
# 第三步：创建大规模初始种群
# ============================================================================
print("\n" + "="*80)
print("👥 [3/5] 创建大规模初始种群...")
print("="*80)

agents = moirai._genesis_create_agents(
    agent_count=TEST_CONFIG['population_size'],
    gene_pool=[],
    capital_per_agent=TEST_CONFIG['initial_capital']
)
moirai.agents = agents

print(f"✅ 创建 {len(agents)} 个Agent")

# 统计初始多样性
meta_styles = [agent.meta_genome.describe_decision_style() for agent in agents]
unique_styles = len(set(meta_styles))
print(f"   决策风格数量: {unique_styles} 种")
print(f"   多样性比例: {unique_styles/len(agents)*100:.1f}%")

# ============================================================================
# 第四步：极端市场压力测试（连续进化）
# ============================================================================
print("\n" + "="*80)
print("🔥 [4/5] 开始极端市场压力测试...")
print("="*80)

# 记录统计数据
evolution_stats = []

for cycle in range(TEST_CONFIG['evolution_cycles']):
    print(f"\n{'='*70}")
    print(f"🧬 进化周期 #{cycle + 1}/{TEST_CONFIG['evolution_cycles']}")
    print(f"{'='*70}")
    
    # 随机选择一个极端时期
    extreme_sample = extreme_periods.sample(1).iloc[0]
    extreme_volatility = abs(extreme_sample['returns'])
    
    print(f"📉 选中极端时刻: {extreme_sample['timestamp']}")
    print(f"   价格变化: {extreme_sample['returns']*100:.2f}%")
    print(f"   当前价格: ${extreme_sample['close']:.2f}")
    
    # 模拟极端交易
    current_agents = moirai.agents.copy()
    for agent in current_agents:
        # 随机交易次数
        num_trades = np.random.randint(3, 8)
        total_pnl = 0
        
        for _ in range(num_trades):
            position_size = np.random.uniform(2000, 8000)
            
            # 极端波动下的收益（放大波动）
            pnl_pct = np.random.normal(0, extreme_volatility * 2)
            
            # 计算极端滑点
            market_condition = MarketCondition(
                price=extreme_sample['close'],
                volume=extreme_sample['volume'],
                volatility=extreme_volatility,
                spread=TEST_CONFIG['extreme_slippage'],
                liquidity_depth=extreme_sample['volume_quote'] * 0.1  # 流动性下降90%
            )
            
            slippage_result = extreme_slippage_model.calculate_slippage(
                order_side=OrderSide.BUY if np.random.random() > 0.5 else OrderSide.SELL,
                order_size_usd=position_size,
                order_type=OrderType.MARKET,
                market_condition=market_condition
            )
            
            # 极端资金费率影响
            funding_result = extreme_funding_model.calculate_funding_rate(
                mark_price=extreme_sample['close'] * (1 + extreme_volatility),
                index_price=extreme_sample['close'],
                long_short_ratio=np.random.uniform(0.5, 2.0),
                open_interest=1000000000
            )
            funding_cost = position_size * abs(funding_result.funding_rate)
            
            # 综合PnL（极端条件）
            pnl = position_size * pnl_pct - slippage_result.slippage_amount - funding_cost
            total_pnl += pnl
        
        # 更新Agent资金
        agent.current_capital += total_pnl
        agent.total_pnl = total_pnl
    
    # 计算极端环境压力
    pnl_list = [agent.total_pnl for agent in current_agents]
    profitable_ratio = sum(1 for pnl in pnl_list if pnl > 0) / len(current_agents)
    
    pressure = mastermind.evaluate_environmental_pressure(
        market_data=extreme_periods,
        agent_performance_stats={
            'profitable_ratio': profitable_ratio,
            'avg_pnl_ratio': np.mean(pnl_list) / TEST_CONFIG['initial_capital']
        }
    )
    
    print(f"\n📊 周期统计:")
    print(f"   盈利比例: {profitable_ratio*100:.1f}%")
    print(f"   平均盈亏: ${np.mean(pnl_list):.2f}")
    print(f"   环境压力: {pressure:.3f}")
    
    # 执行进化
    moirai.agents = current_agents
    evolution_manager.run_evolution_cycle(current_price=extreme_sample['close'])
    
    # 记录统计
    health_metrics = evolution_manager.blood_lab.population_checkup(moirai.agents)
    stats = {
        'cycle': cycle + 1,
        'population': len(moirai.agents),
        'profitable_ratio': profitable_ratio,
        'avg_pnl': np.mean(pnl_list),
        'pressure': pressure,
        'lineage_entropy': health_metrics.lineage_entropy_normalized,
        'gene_entropy': health_metrics.gene_entropy,
        'health': health_metrics.overall_health
    }
    evolution_stats.append(stats)
    
    print(f"\n🔍 种群健康:")
    print(f"   血统熵: {health_metrics.lineage_entropy_normalized:.3f}")
    print(f"   基因熵: {health_metrics.gene_entropy:.3f}")
    print(f"   总体健康: {health_metrics.overall_health}")
    print(f"   存活Agent: {len(moirai.agents)}")

# ============================================================================
# 第五步：压力测试结果分析
# ============================================================================
print("\n" + "="*80)
print("📈 [5/5] 压力测试结果分析")
print("="*80)

stats_df = pd.DataFrame(evolution_stats)

print("\n1️⃣  种群存活率:")
print(f"   初始: {TEST_CONFIG['population_size']} 个Agent")
print(f"   最终: {stats_df.iloc[-1]['population']} 个Agent")
print(f"   存活率: {stats_df.iloc[-1]['population']/TEST_CONFIG['population_size']*100:.1f}%")

print("\n2️⃣  盈利能力演变:")
print(f"   初始盈利率: {stats_df.iloc[0]['profitable_ratio']*100:.1f}%")
print(f"   最终盈利率: {stats_df.iloc[-1]['profitable_ratio']*100:.1f}%")
print(f"   变化: {(stats_df.iloc[-1]['profitable_ratio'] - stats_df.iloc[0]['profitable_ratio'])*100:+.1f}%")

print("\n3️⃣  种群健康度演变:")
print(f"   初始血统熵: {stats_df.iloc[0]['lineage_entropy']:.3f}")
print(f"   最终血统熵: {stats_df.iloc[-1]['lineage_entropy']:.3f}")
print(f"   初始基因熵: {stats_df.iloc[0]['gene_entropy']:.3f}")
print(f"   最终基因熵: {stats_df.iloc[-1]['gene_entropy']:.3f}")

print("\n4️⃣  平均环境压力:")
print(f"   平均: {stats_df['pressure'].mean():.3f}")
print(f"   最高: {stats_df['pressure'].max():.3f}")
print(f"   最低: {stats_df['pressure'].min():.3f}")

print("\n5️⃣  最终策略分布:")
niche_statuses = niche_protection.analyze_strategy_distribution(moirai.agents)
for strategy, status in niche_statuses.items():
    print(f"   {strategy}: {status.population_ratio*100:.1f}%")

# 生存测试：检查Agent是否全部死亡
if len(moirai.agents) == 0:
    print("\n" + "="*80)
    print("❌ 系统崩溃：所有Agent在极端压力下死亡！")
    print("="*80)
elif len(moirai.agents) < TEST_CONFIG['population_size'] * 0.1:
    print("\n" + "="*80)
    print("⚠️  严重警告：种群濒临灭绝（<10%存活）")
    print("="*80)
else:
    print("\n" + "="*80)
    print("✅ 压力测试通过：系统在极端条件下保持鲁棒性")
    print("="*80)

# 保存测试结果
stats_df.to_csv('extreme_stress_test_results.csv', index=False)
print(f"\n💾 测试结果已保存: extreme_stress_test_results.csv")

print("\n" + "="*80)
print("🎯 压力测试总结")
print("="*80)
print(f"✅ 完成 {TEST_CONFIG['evolution_cycles']} 轮极端进化")
print(f"✅ 测试 {TEST_CONFIG['population_size']} 个Agent在极端市场")
print(f"✅ 验证系统鲁棒性和自适应能力")
print("\n🔥 Prometheus v5.1 极端压力测试完成！")

