#!/usr/bin/env python3
"""
🎯 收敛性验证测试 - 实现"殊途同归"
============================================================================
目标：验证在相同seed下，系统能否收敛到相似结果

当前问题：
- 相同seed，差异30%（太大！）

解决方案：
1. 增加周期数：200 → 1000
2. 增加Agent数：20 → 50
3. 观察收敛性

成功标准：
- 相同seed下，3次运行差异 < 10%
- 平均收益标准差 < 5%
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

def run_convergence_test(test_name: str, total_cycles: int, agent_count: int, num_runs: int = 5):
    """
    运行收敛性测试
    
    Args:
        test_name: 测试名称
        total_cycles: 总周期数
        agent_count: Agent数量
        num_runs: 运行次数
    """
    print(f"\n{'='*80}")
    print(f"🧪 {test_name}")
    print(f"{'='*80}")
    print(f"   周期数: {total_cycles}")
    print(f"   Agent数: {agent_count}")
    print(f"   运行次数: {num_runs}")
    print(f"   固定seed: 7001")
    print(f"   Evolution: 随机\n")
    
    prices = load_prices(limit=total_cycles)
    market_feed = make_market_feed(prices)
    
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"   🔄 Run {run_id}/{num_runs}...", end=' ', flush=True)
        
        start_time = datetime.now()
        
        facade = run_scenario(
            mode="backtest",
            total_cycles=total_cycles,
            market_feed=market_feed,
            num_families=50,
            agent_count=agent_count,
            capital_per_agent=10000.0,
            scenario=f"convergence_{test_name}_run{run_id}",
            evo_interval=30,
            seed=7001,            # 固定创世seed
            evolution_seed=None   # 演化真随机
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 收集结果
        current_price = prices[-1]
        agent_returns = []
        
        for agent in facade.moirai.agents:
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
            effective_capital = agent.current_capital + unrealized_pnl
            total_return = (effective_capital - agent.initial_capital) / agent.initial_capital * 100
            agent_returns.append(total_return)
        
        system_return = np.mean(agent_returns)
        best_return = max(agent_returns)
        
        results.append({
            'run_id': run_id,
            'system_return': system_return,
            'best_return': best_return,
            'elapsed': elapsed
        })
        
        print(f"系统{system_return:+.2f}%, 最佳{best_return:+.2f}%, 用时{elapsed:.1f}s")
    
    # 分析收敛性
    system_returns = [r['system_return'] for r in results]
    avg_return = np.mean(system_returns)
    std_return = np.std(system_returns)
    diff_return = max(system_returns) - min(system_returns)
    
    print(f"\n{'='*80}")
    print(f"📊 收敛性分析")
    print(f"{'='*80}")
    
    for i, result in enumerate(results, 1):
        print(f"   Run{i}: {result['system_return']:+7.2f}%")
    
    print(f"\n   平均收益:   {avg_return:+.2f}%")
    print(f"   标准差:     {std_return:.2f}%")
    print(f"   最大差异:   {diff_return:.2f}%")
    print(f"   变异系数:   {std_return/abs(avg_return)*100:.1f}%")
    
    # 评价
    print(f"\n{'='*80}")
    print(f"💡 评价")
    print(f"{'='*80}")
    
    if diff_return < 5.0:
        status = "✅ 优秀"
        comment = "差异<5%，已实现殊途同归！"
    elif diff_return < 10.0:
        status = "✅ 良好"
        comment = "差异5-10%，基本收敛，可接受"
    elif diff_return < 20.0:
        status = "⚠️ 一般"
        comment = "差异10-20%，收敛性不足"
    else:
        status = "❌ 较差"
        comment = f"差异{diff_return:.1f}%，收敛性差"
    
    print(f"   状态: {status}")
    print(f"   评价: {comment}")
    
    return {
        'test_name': test_name,
        'avg_return': avg_return,
        'std_return': std_return,
        'diff_return': diff_return,
        'status': status
    }

def main():
    print("=" * 80)
    print("🎯 Prometheus收敛性验证 - 实现'殊途同归'")
    print("=" * 80)
    print()
    print("目标：相同seed下，系统收敛到相似结果（差异<10%）")
    print()
    
    # 记录所有测试结果
    all_results = []
    
    # 测试1：基线（当前配置）
    print("\n" + "="*80)
    print("📌 测试1：基线（200周期，50 Agent）")
    print("="*80)
    result1 = run_convergence_test(
        test_name="baseline_200c_50a",
        total_cycles=200,
        agent_count=50,
        num_runs=5
    )
    all_results.append(result1)
    
    # 测试2：增加周期
    print("\n" + "="*80)
    print("📌 测试2：增加周期（500周期，50 Agent）")
    print("="*80)
    result2 = run_convergence_test(
        test_name="long_500c_50a",
        total_cycles=500,
        agent_count=50,
        num_runs=5
    )
    all_results.append(result2)
    
    # 测试3：超长周期
    print("\n" + "="*80)
    print("📌 测试3：超长周期（1000周期，50 Agent）")
    print("="*80)
    result3 = run_convergence_test(
        test_name="ultra_1000c_50a",
        total_cycles=1000,
        agent_count=50,
        num_runs=3  # 减少运行次数以节省时间
    )
    all_results.append(result3)
    
    # 汇总对比
    print("\n" + "="*80)
    print("📊 汇总对比")
    print("="*80)
    
    print(f"\n{'测试':<25} {'平均收益':<12} {'标准差':<10} {'最大差异':<10} {'状态':<10}")
    print("-"*80)
    for r in all_results:
        print(f"{r['test_name']:<25} {r['avg_return']:+10.2f}% {r['std_return']:>8.2f}% {r['diff_return']:>8.2f}% {r['status']:<10}")
    
    # 结论
    print("\n" + "="*80)
    print("🎓 结论")
    print("="*80)
    
    # 找出最佳配置
    best_result = min(all_results, key=lambda x: x['diff_return'])
    
    print(f"\n最佳配置: {best_result['test_name']}")
    print(f"   最大差异: {best_result['diff_return']:.2f}%")
    print(f"   {best_result['status']}")
    
    if best_result['diff_return'] < 10.0:
        print("\n✅ 成功！已实现'殊途同归'")
        print(f"   相同seed下，系统收敛良好（差异{best_result['diff_return']:.1f}%）")
        print("   可以进入下一阶段：大规模多seed训练")
    else:
        print("\n⚠️ 尚未达标")
        print(f"   当前最佳差异{best_result['diff_return']:.1f}%，目标<10%")
        print("   建议：")
        print("   1. 进一步增加周期数")
        print("   2. 调整演化参数（降低变异率？）")
        print("   3. 增加Immigration稳定性")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

