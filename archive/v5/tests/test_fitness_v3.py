#!/usr/bin/env python3
"""
⚔️ Fitness V3 验证测试
============================================================================
目标：验证新的适应度函数能否让Agent学会"买入持有"策略

测试配置：
- 10次独立运行
- 每次200周期
- 每次50个Agent
- 使用BTC历史数据

成功标准：
1. Agent平均收益 > BTC收益的50%
2. 最佳Agent收益 > BTC收益的80%
3. Agent平均持仓时间 > 50%
4. Agent平均交易频率 < 20%
============================================================================
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

from prometheus.facade.v6_facade import run_scenario

# 简洁日志
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

def calculate_btc_return(prices):
    """计算BTC基准收益率"""
    if not prices or len(prices) < 2:
        return 0.0
    return (prices[-1] - prices[0]) / prices[0] * 100

def analyze_agent_behaviors(facade, current_price):
    """分析Agent行为（✨ 添加系统盈利统计）"""
    results = {
        'returns': [],
        'holding_ratios': [],
        'trade_frequencies': [],
        'total_trades': 0,
        'system_total_capital': 0.0,  # ✨ 系统总资金（含未实现盈亏）
        'system_initial_capital': 0.0  # ✨ 系统初始总资金
    }
    
    for agent in facade.moirai.agents:
        # ✨ 系统盈利统计：累加所有Agent的资金（含未实现盈亏）
        results['system_initial_capital'] += agent.initial_capital
        
        # 计算未实现盈亏
        unrealized_pnl = 0.0
        if current_price > 0:
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
        
        # 有效资金 = 已实现资金 + 未实现盈亏
        effective_capital = agent.current_capital + unrealized_pnl
        results['system_total_capital'] += effective_capital
        
        # 收益率（含未实现盈亏）
        capital_ratio = effective_capital / agent.initial_capital
        agent_return = (capital_ratio - 1) * 100
        results['returns'].append(agent_return)
        
        # 持仓比例
        if hasattr(agent, 'cycles_with_position') and hasattr(agent, 'cycles_survived'):
            if agent.cycles_survived > 0:
                holding_ratio = agent.cycles_with_position / agent.cycles_survived
                results['holding_ratios'].append(holding_ratio)
        
        # 交易频率
        if hasattr(agent, 'account') and hasattr(agent, 'cycles_survived'):
            trade_count = agent.account.private_ledger.trade_count
            if agent.cycles_survived > 0:
                trade_freq = trade_count / agent.cycles_survived
                results['trade_frequencies'].append(trade_freq)
                results['total_trades'] += trade_count
    
    return results

def main():
    print("=" * 80)
    print("⚔️ Fitness V3 验证测试 - 小批次实验")
    print("=" * 80)
    print()
    print("🎯 测试配置：")
    print("   - 运行次数: 10次")
    print("   - 测试周期: 200周期/次")
    print("   - Agent数量: 50个")
    print("   - 初始资金: $10,000/Agent")
    print("   - 进化周期: 每30步")
    print()
    
    # 加载数据
    total_cycles = 200
    prices = load_prices(limit=total_cycles)
    market_feed = make_market_feed(prices)
    btc_return = calculate_btc_return(prices)
    
    print(f"📊 BTC基准收益率: +{btc_return:.2f}%")
    print("=" * 80)
    print()
    
    # 运行10次实验
    all_run_results = []
    
    for run_id in range(1, 11):
        print(f"🚀 运行 {run_id}/10...", end=" ", flush=True)
        
        try:
            # 运行场景
            facade = run_scenario(
                mode="backtest",
                total_cycles=total_cycles,
                market_feed=market_feed,
                num_families=50,
                agent_count=50,
                capital_per_agent=10000.0,
                scenario=f"fitness_v3_test_run{run_id}",
                evo_interval=30,
                seed=7000 + run_id  # 不同的seed
            )
            
            # 分析结果（✨ 传入当前价格）
            current_price = prices[-1]  # 最后一天的价格
            behaviors = analyze_agent_behaviors(facade, current_price)
            
            avg_return = np.mean(behaviors['returns']) if behaviors['returns'] else 0
            max_return = np.max(behaviors['returns']) if behaviors['returns'] else 0
            avg_holding = np.mean(behaviors['holding_ratios']) if behaviors['holding_ratios'] else 0
            avg_trade_freq = np.mean(behaviors['trade_frequencies']) if behaviors['trade_frequencies'] else 0
            
            # ✨ 计算系统盈利
            system_return = 0.0
            if behaviors['system_initial_capital'] > 0:
                system_return = (behaviors['system_total_capital'] - behaviors['system_initial_capital']) / behaviors['system_initial_capital'] * 100
            
            all_run_results.append({
                'run_id': run_id,
                'avg_return': avg_return,
                'max_return': max_return,
                'avg_holding_ratio': avg_holding,
                'avg_trade_frequency': avg_trade_freq,
                'total_trades': behaviors['total_trades'],
                'system_return': system_return,  # ✨ 系统盈利
                'system_total_capital': behaviors['system_total_capital'],
                'system_initial_capital': behaviors['system_initial_capital']
            })
            
            print(f"✅ Agent平均: {avg_return:+.2f}%, 最佳: {max_return:+.2f}%, 🏦系统盈利: {system_return:+.2f}%, 持仓: {avg_holding*100:.1f}%")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            continue
    
    # 统计分析
    print()
    print("=" * 80)
    print("📊 实验结果汇总")
    print("=" * 80)
    
    if all_run_results:
        all_avg_returns = [r['avg_return'] for r in all_run_results]
        all_max_returns = [r['max_return'] for r in all_run_results]
        all_holdings = [r['avg_holding_ratio'] for r in all_run_results]
        all_freqs = [r['avg_trade_frequency'] for r in all_run_results]
        
        # ✨ 系统盈利统计
        all_system_returns = [r['system_return'] for r in all_run_results]
        
        print(f"\n🎯 收益率对比:")
        print(f"   BTC基准:        +{btc_return:.2f}%")
        print(f"   🏦 系统盈利:     {np.mean(all_system_returns):+.2f}% ✨ (vs BTC: {np.mean(all_system_returns)/btc_return*100:.1f}%)")
        print(f"   Agent平均:      {np.mean(all_avg_returns):+.2f}% (目标: >{btc_return*0.5:.2f}%)")
        print(f"   Agent最佳(平均): {np.mean(all_max_returns):+.2f}% (目标: >{btc_return*0.8:.2f}%)")
        print(f"   Agent最佳(最高): {np.max(all_max_returns):+.2f}%")
        
        print(f"\n📈 行为特征:")
        print(f"   平均持仓比例:   {np.mean(all_holdings)*100:.1f}% (目标: >50%)")
        print(f"   平均交易频率:   {np.mean(all_freqs)*100:.1f}% (目标: <20%)")
        print(f"   总交易笔数(avg): {np.mean([r['total_trades'] for r in all_run_results]):.0f}笔")
        
        # 成功判断
        print(f"\n🏆 成功标准评估:")
        success_count = 0
        
        # 标准1: Agent平均收益 > BTC收益的50%
        criterion_1 = np.mean(all_avg_returns) > btc_return * 0.5
        print(f"   1. Agent平均收益 > BTC×50%:    {'✅' if criterion_1 else '❌'}")
        if criterion_1:
            success_count += 1
        
        # 标准2: 最佳Agent收益 > BTC收益的80%
        criterion_2 = np.mean(all_max_returns) > btc_return * 0.8
        print(f"   2. Agent最佳收益 > BTC×80%:    {'✅' if criterion_2 else '❌'}")
        if criterion_2:
            success_count += 1
        
        # 标准3: 平均持仓时间 > 50%
        criterion_3 = np.mean(all_holdings) > 0.5
        print(f"   3. 平均持仓比例 > 50%:         {'✅' if criterion_3 else '❌'}")
        if criterion_3:
            success_count += 1
        
        # 标准4: 平均交易频率 < 20%
        criterion_4 = np.mean(all_freqs) < 0.2
        print(f"   4. 平均交易频率 < 20%:         {'✅' if criterion_4 else '❌'}")
        if criterion_4:
            success_count += 1
        
        print(f"\n📈 通过标准: {success_count}/4")
        
        if success_count >= 3:
            print("\n🎉 实验成功！Fitness V3有效！")
            print("   → Agent已学会长期持有策略！")
            print("   → 可以进入Phase 3：实施Memory Layer")
        elif success_count >= 2:
            print("\n⚠️ 部分成功，需要调整参数")
            print("   → 考虑进一步加强持仓奖励")
            print("   → 或加强交易频率惩罚")
        else:
            print("\n❌ 实验失败，需要重新设计")
            print("   → Fitness V3可能仍不足以激励长期持有")
            print("   → 需要更激进的奖励/惩罚机制")
    
    print("=" * 80)

if __name__ == '__main__':
    main()

