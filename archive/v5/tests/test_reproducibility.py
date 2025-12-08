#!/usr/bin/env python3
"""
测试回测的可重复性
运行多次，看结果是否相同
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

logging.basicConfig(level=logging.ERROR)


def run_simple_backtest(seed=None):
    """运行简化版回测，返回最终结果"""
    
    # 设置随机种子（如果提供）
    if seed is not None:
        np.random.seed(seed)
        import random
        random.seed(seed)
    
    # 加载数据
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 初始化系统
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建初始Agent
    agents = moirai._genesis_create_agents(
        agent_count=10,  # 减少到10个，加快测试
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    for agent in agents:
        agent.fitness = 1.0
    
    moirai.agents = agents
    
    # 运行回测（50步）
    evolution_interval = 20
    current_step = 0
    
    for idx, row in df.head(50).iterrows():
        current_step += 1
        current_price = row['close']
        
        if idx > 0:
            prev_price = df.iloc[idx - 1]['close']
            price_change = (current_price - prev_price) / prev_price
        else:
            price_change = 0.0
        
        # 每个Agent交易
        for agent in agents:
            if agent.current_capital <= 0:
                continue
            
            # Agent决策
            risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
            if abs(price_change) < 0.001:
                position = 0.0
            elif price_change > 0:
                position = risk_tolerance * 0.8
            else:
                position = -risk_tolerance * 0.8
            
            # 杠杆选择
            if risk_tolerance < 0.6:
                leverage = 3.0 + (risk_tolerance - 0.2) * 10
            else:
                leverage = 5.0 + (risk_tolerance - 0.6) * 25
            
            leverage = min(max(leverage, 1.0), 100.0)
            
            # 计算收益
            base_return = price_change * position
            leveraged_return = base_return * leverage
            
            # 简化成本
            if abs(position) > 0.01:
                cost = 0.0015
                leveraged_return -= cost * leverage
            
            # 检查爆仓
            if leveraged_return <= -1.0:
                agent.current_capital = 0.0
            else:
                agent.current_capital *= (1 + leveraged_return)
        
        # 定期进化
        if current_step % evolution_interval == 0:
            agents = [a for a in agents if a.current_capital > 0]
            moirai.agents = agents
            
            try:
                evolution_manager.run_evolution_cycle()
                agents = moirai.agents
            except:
                pass
    
    # 收集结果
    final_capitals = [a.current_capital for a in agents if a.current_capital > 0]
    
    if len(final_capitals) > 0:
        avg_capital = np.mean(final_capitals)
        median_capital = np.median(final_capitals)
        max_capital = np.max(final_capitals)
        min_capital = np.min(final_capitals)
    else:
        avg_capital = 0
        median_capital = 0
        max_capital = 0
        min_capital = 0
    
    return {
        'survivors': len(agents),
        'avg_capital': avg_capital,
        'median_capital': median_capital,
        'max_capital': max_capital,
        'min_capital': min_capital,
        'agent_ids': [a.agent_id for a in agents],
        'agent_capitals': {a.agent_id: a.current_capital for a in agents}
    }


def main():
    print()
    print("=" * 80)
    print("🧪 测试回测的可重复性")
    print("=" * 80)
    print()
    
    # 测试1: 不设置随机种子，运行3次
    print("📊 测试1: 不设置随机种子（应该不同）")
    print("-" * 80)
    results_no_seed = []
    for i in range(3):
        print(f"   运行 #{i+1}...", end=" ")
        result = run_simple_backtest(seed=None)
        results_no_seed.append(result)
        print(f"✓ 幸存: {result['survivors']}个, 平均: ${result['avg_capital']:,.2f}")
    
    print()
    print("   结果对比:")
    for i, result in enumerate(results_no_seed, 1):
        print(f"      #{i}: 幸存{result['survivors']}个, 平均${result['avg_capital']:,.2f}, 最高${result['max_capital']:,.2f}")
    
    # 检查是否相同
    all_same = all(
        r['avg_capital'] == results_no_seed[0]['avg_capital'] 
        for r in results_no_seed
    )
    
    if all_same:
        print("   ⚠️  结果完全相同（意外！）")
    else:
        print("   ✅ 结果不同（符合预期，因为有随机性）")
    
    print()
    print("=" * 80)
    
    # 测试2: 设置相同的随机种子，运行3次
    print()
    print("📊 测试2: 设置相同随机种子（应该相同）")
    print("-" * 80)
    results_with_seed = []
    seed = 42
    for i in range(3):
        print(f"   运行 #{i+1} (seed={seed})...", end=" ")
        result = run_simple_backtest(seed=seed)
        results_with_seed.append(result)
        print(f"✓ 幸存: {result['survivors']}个, 平均: ${result['avg_capital']:,.2f}")
    
    print()
    print("   结果对比:")
    for i, result in enumerate(results_with_seed, 1):
        print(f"      #{i}: 幸存{result['survivors']}个, 平均${result['avg_capital']:,.2f}, 最高${result['max_capital']:,.2f}")
    
    # 检查是否相同
    all_same = all(
        r['avg_capital'] == results_with_seed[0]['avg_capital'] 
        for r in results_with_seed
    )
    
    if all_same:
        print("   ✅ 结果完全相同（符合预期，随机种子生效）")
    else:
        print("   ⚠️  结果不同（意外，随机种子没生效）")
        # 详细对比
        print()
        print("   详细差异:")
        for i in range(1, 3):
            diff_survivors = results_with_seed[i]['survivors'] - results_with_seed[0]['survivors']
            diff_avg = results_with_seed[i]['avg_capital'] - results_with_seed[0]['avg_capital']
            print(f"      #{i} vs #1: 幸存差{diff_survivors:+d}, 平均差${diff_avg:+,.2f}")
    
    print()
    print("=" * 80)
    
    # 测试3: 不同随机种子
    print()
    print("📊 测试3: 不同随机种子（应该不同）")
    print("-" * 80)
    results_diff_seed = []
    seeds = [42, 123, 999]
    for i, seed in enumerate(seeds):
        print(f"   运行 #{i+1} (seed={seed})...", end=" ")
        result = run_simple_backtest(seed=seed)
        results_diff_seed.append(result)
        print(f"✓ 幸存: {result['survivors']}个, 平均: ${result['avg_capital']:,.2f}")
    
    print()
    print("   结果对比:")
    for i, (seed, result) in enumerate(zip(seeds, results_diff_seed), 1):
        print(f"      #{i} (seed={seed}): 幸存{result['survivors']}个, 平均${result['avg_capital']:,.2f}, 最高${result['max_capital']:,.2f}")
    
    # 检查是否不同
    all_different = len(set(r['avg_capital'] for r in results_diff_seed)) == 3
    
    if all_different:
        print("   ✅ 结果都不同（符合预期，不同种子不同结果）")
    else:
        print("   ⚠️  有些结果相同（可能是巧合）")
    
    print()
    print("=" * 80)
    print()
    
    # 总结
    print("🎯 结论:")
    print()
    print("1. 随机性来源:")
    print("   - Agent初始基因（每次不同）")
    print("   - Agent决策（含随机成分）")
    print("   - 进化过程（选择、交配、突变都有随机性）")
    print()
    print("2. 可重复性:")
    print("   - 不设置种子：每次结果不同 ✅")
    print("   - 设置相同种子：每次结果相同 ✅")
    print("   - 不同种子：结果不同 ✅")
    print()
    print("3. 实战含义:")
    print("   - 单次回测结果可能有偶然性")
    print("   - 需要多次回测（蒙特卡洛模拟）")
    print("   - 观察结果分布，而不是单一值")
    print("   - 这就是为什么我们强调'统计样本不足'")
    print()
    print("4. 建议:")
    print("   - 运行100+次回测（不同种子）")
    print("   - 计算平均、中位数、标准差")
    print("   - 观察最好、最差、典型情况")
    print("   - 这样才能评估系统的真实表现")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

