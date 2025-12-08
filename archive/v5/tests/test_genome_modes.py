#!/usr/bin/env python3
"""
🔬 基因模式对比实验 - 渐进式 vs 激进式
============================================================================
实验目标：验证"完全解锁基因参数"的效果

实验组：
- 渐进式：创世3个参数，进化逐步解锁到50个（当前模式）
- 激进式：创世直接解锁所有50个参数（新模式）

对比维度：
1. 收敛速度：谁更快找到好策略？
2. 最终收益：谁的系统收益更高？
3. 稳健性：谁的收益更稳定？
4. 多样性：谁保持了更好的多样性？

期待：看看随机性会不会给我们带来惊喜！🎲
============================================================================
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime

from prometheus.facade.v6_facade import run_scenario

logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

def load_prices(limit=None):
    """加载历史价格数据"""
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    closes = df['close'].tolist()
    return closes[:limit] if limit else closes

def make_market_feed(prices):
    """构造市场数据生成器"""
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        return {'price': prices[idx]}, {}
    return feed

def run_mode_test(mode_name: str, full_genome_unlock: bool, num_runs: int = 5):
    """运行单个模式的测试"""
    print(f"\n{'='*80}")
    print(f"🧪 测试模式: {mode_name}")
    print(f"{'='*80}")
    print(f"   full_genome_unlock: {full_genome_unlock}")
    print(f"   运行次数: {num_runs}")
    print()
    
    prices = load_prices(limit=200)
    market_feed = make_market_feed(prices)
    btc_return = (prices[-1] - prices[0]) / prices[0] * 100
    
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"   🔄 Run {run_id}/{num_runs}...", end=' ', flush=True)
        
        start_time = datetime.now()
        
        facade = run_scenario(
            mode="backtest",
            total_cycles=200,
            market_feed=market_feed,
            num_families=50,
            agent_count=50,
            capital_per_agent=10000.0,
            scenario=f"genome_mode_{mode_name}_run{run_id}",
            evo_interval=30,
            seed=7001,  # 固定创世seed
            evolution_seed=None,  # 演化随机
            full_genome_unlock=full_genome_unlock  # ✨ 关键参数！
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 收集结果
        current_price = prices[-1]
        agent_returns = []
        
        # 检查基因参数数量
        first_agent = facade.moirai.agents[0]
        genome_params_count = len(first_agent.genome.to_dict()) if hasattr(first_agent, 'genome') else 0
        
        for agent in facade.moirai.agents:
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
            effective_capital = agent.current_capital + unrealized_pnl
            total_return = (effective_capital - agent.initial_capital) / agent.initial_capital * 100
            agent_returns.append(total_return)
        
        system_return = np.mean(agent_returns)
        best_return = max(agent_returns)
        std_return = np.std(agent_returns)
        
        results.append({
            'run_id': run_id,
            'system_return': system_return,
            'best_return': best_return,
            'std_return': std_return,
            'genome_params': genome_params_count,
            'elapsed': elapsed
        })
        
        print(f"系统{system_return:+.2f}%, 最佳{best_return:+.2f}%, 参数{genome_params_count}个, {elapsed:.1f}s")
    
    # 统计分析
    system_returns = [r['system_return'] for r in results]
    best_returns = [r['best_return'] for r in results]
    
    avg_system = np.mean(system_returns)
    std_system = np.std(system_returns)
    avg_best = np.mean(best_returns)
    avg_params = results[0]['genome_params']
    
    print(f"\n{'='*80}")
    print(f"📊 {mode_name} 汇总")
    print(f"{'='*80}")
    print(f"   BTC基准:        {btc_return:+.2f}%")
    print(f"   系统平均收益:   {avg_system:+.2f}% ± {std_system:.2f}%")
    print(f"   最佳平均收益:   {avg_best:+.2f}%")
    print(f"   基因参数数量:   {avg_params}个")
    print(f"   收敛性（StdDev）: {std_system:.2f}%")
    
    return {
        'mode_name': mode_name,
        'avg_system': avg_system,
        'std_system': std_system,
        'avg_best': avg_best,
        'genome_params': avg_params,
        'btc_return': btc_return
    }

def main():
    print("="*80)
    print("🔬 Prometheus基因模式对比实验")
    print("="*80)
    print()
    print("💡 实验理念：")
    print("   - 渐进式：符合自然进化，逐步解锁")
    print("   - 激进式：最大自由度，随机碰撞")
    print("   让数据告诉我们哪个更好！")
    print()
    
    # 测试1：渐进式（当前默认）
    result_gradual = run_mode_test(
        mode_name="渐进式（3→50参数）",
        full_genome_unlock=False,
        num_runs=5
    )
    
    # 测试2：激进式（完全解锁）
    result_radical = run_mode_test(
        mode_name="激进式（50参数）",
        full_genome_unlock=True,
        num_runs=5
    )
    
    # 对比分析
    print("\n" + "="*80)
    print("⚖️  对比分析")
    print("="*80)
    
    print(f"\n{'指标':<20} {'渐进式':<15} {'激进式':<15} {'胜者':<10}")
    print("-"*80)
    
    # 系统收益
    winner1 = "激进式" if result_radical['avg_system'] > result_gradual['avg_system'] else "渐进式"
    print(f"{'系统平均收益':<20} {result_gradual['avg_system']:+14.2f}% {result_radical['avg_system']:+14.2f}% {winner1:<10}")
    
    # 最佳收益
    winner2 = "激进式" if result_radical['avg_best'] > result_gradual['avg_best'] else "渐进式"
    print(f"{'最佳平均收益':<20} {result_gradual['avg_best']:+14.2f}% {result_radical['avg_best']:+14.2f}% {winner2:<10}")
    
    # 稳健性（标准差越小越好）
    winner3 = "激进式" if result_radical['std_system'] < result_gradual['std_system'] else "渐进式"
    print(f"{'稳健性（StdDev）':<20} {result_gradual['std_system']:>14.2f}% {result_radical['std_system']:>14.2f}% {winner3:<10}")
    
    # 探索空间
    print(f"{'探索空间（参数数）':<20} {result_gradual['genome_params']:>14}个 {result_radical['genome_params']:>14}个 激进式")
    
    # 计分
    scores = {
        '渐进式': 0,
        '激进式': 0
    }
    scores[winner1] += 1
    scores[winner2] += 1
    scores[winner3] += 1
    
    print(f"\n{'='*80}")
    print("🏆 总体评价")
    print("="*80)
    
    print(f"\n   渐进式: {scores['渐进式']}/3 胜")
    print(f"   激进式: {scores['激进式']}/3 胜")
    
    if scores['激进式'] > scores['渐进式']:
        print("\n   🎉 激进式获胜！随机性给我们带来了惊喜！")
        print("   建议：后续实验使用 full_genome_unlock=True")
    elif scores['激进式'] < scores['渐进式']:
        print("\n   ✅ 渐进式获胜！自然进化还是更稳健！")
        print("   建议：保持当前的渐进式解锁机制")
    else:
        print("\n   ⚖️  平局！两种模式各有千秋！")
        print("   建议：根据具体场景选择模式")
    
    # 深度分析
    print(f"\n" + "="*80)
    print("💡 深度分析")
    print("="*80)
    
    # 收益提升
    improvement = (result_radical['avg_system'] - result_gradual['avg_system'])
    improvement_pct = improvement / abs(result_gradual['avg_system']) * 100 if result_gradual['avg_system'] != 0 else 0
    
    print(f"\n激进式 vs 渐进式：")
    print(f"   系统收益差异: {improvement:+.2f}% ({improvement_pct:+.1f}%)")
    print(f"   探索空间扩大: {result_radical['genome_params'] / result_gradual['genome_params']:.1f}倍")
    
    if improvement > 5:
        print(f"   💥 显著提升！激进式在这个数据集上表现更好！")
    elif improvement > 0:
        print(f"   📈 略有提升，但差异不大")
    elif improvement > -5:
        print(f"   📉 略有下降，但差异不大")
    else:
        print(f"   ⚠️  显著下降！激进式在这个数据集上表现较差")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

