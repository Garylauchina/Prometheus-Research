#!/usr/bin/env python3
"""
🏆 最佳Agent深度分析
============================================================================
目标：找出为什么最佳Agent能获得21%收益，而其他只有10%

分析内容：
1. 基因（Genome）参数对比
2. 本能（Instinct）参数对比
3. 交易历史详细分析
4. 开仓时机和价格
5. 仓位大小
6. 持有时长
============================================================================
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
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

def analyze_agent_detailed(agent, prices, agent_rank):
    """详细分析单个Agent"""
    print(f"\n{'='*80}")
    print(f"🔍 Agent #{agent_rank}: {agent.agent_id}")
    print(f"{'='*80}")
    
    # 基础信息
    initial_capital = agent.initial_capital
    current_capital = agent.current_capital
    current_price = prices[-1]
    unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
    effective_capital = current_capital + unrealized_pnl
    total_return = (effective_capital - initial_capital) / initial_capital * 100
    
    print(f"\n💰 资金情况:")
    print(f"   初始资金:     ${initial_capital:,.2f}")
    print(f"   当前资金:     ${current_capital:,.2f}")
    print(f"   未实现盈亏:   ${unrealized_pnl:+,.2f}")
    print(f"   有效资金:     ${effective_capital:,.2f}")
    print(f"   总收益率:     {total_return:+.2f}%")
    
    # 基因参数
    if hasattr(agent, 'genome') and agent.genome:
        print(f"\n🧬 基因参数:")
        genome = agent.genome
        if hasattr(genome, 'active_params'):
            for key, value in sorted(genome.active_params.items()):
                print(f"   {key:20s}: {value:.3f}")
    
    # 本能参数
    if hasattr(agent, 'instinct') and agent.instinct:
        print(f"\n🎭 本能参数:")
        instinct = agent.instinct
        print(f"   risk_appetite:      {instinct.risk_appetite:.3f}")
        print(f"   fear_of_death:      {instinct.fear_of_death:.3f}")
        print(f"   loss_aversion:      {instinct.loss_aversion:.3f}")
        print(f"   性格类型:           {instinct.describe_personality()}")
    
    # 交易历史
    if hasattr(agent, 'account') and agent.account:
        ledger = agent.account.private_ledger
        print(f"\n📊 交易统计:")
        print(f"   总交易次数:   {ledger.trade_count}")
        print(f"   总盈亏:       ${ledger.total_pnl:+,.2f}")
        print(f"   胜率:         {ledger.get_win_rate()*100:.1f}%")
        
        # 持仓情况
        print(f"\n📈 持仓情况:")
        if ledger.long_position and ledger.long_position.amount > 0:
            long_pos = ledger.long_position
            print(f"   多头:")
            print(f"     数量:       {long_pos.amount:.6f} BTC")
            print(f"     开仓价:     ${long_pos.entry_price:,.2f}")
            print(f"     当前价:     ${current_price:,.2f}")
            print(f"     未实现盈亏: ${(current_price - long_pos.entry_price) * long_pos.amount:+,.2f}")
            print(f"     仓位占比:   {long_pos.amount * long_pos.entry_price / initial_capital * 100:.1f}%")
        
        if ledger.short_position and ledger.short_position.amount > 0:
            short_pos = ledger.short_position
            print(f"   空头:")
            print(f"     数量:       {short_pos.amount:.6f} BTC")
            print(f"     开仓价:     ${short_pos.entry_price:,.2f}")
            print(f"     当前价:     ${current_price:,.2f}")
            print(f"     未实现盈亏: ${(short_pos.entry_price - current_price) * short_pos.amount:+,.2f}")
            print(f"     仓位占比:   {short_pos.amount * short_pos.entry_price / initial_capital * 100:.1f}%")
        
        # 详细交易历史
        if ledger.trade_history:
            print(f"\n📝 交易历史（前10笔）:")
            print(f"{'序号':<6} {'时间':<20} {'类型':<8} {'数量':<12} {'价格':<12} {'盈亏':<12}")
            print("-" * 80)
            for i, trade in enumerate(ledger.trade_history[:10], 1):
                pnl_str = f"${trade.pnl:+,.2f}" if trade.pnl else "-"
                timestamp_str = trade.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(trade.timestamp, 'strftime') else str(trade.timestamp)[:16]
                print(f"{i:<6} {timestamp_str:<20} {trade.trade_type:<8} {trade.amount:<12.6f} ${trade.price:<11,.2f} {pnl_str:<12}")
    
    # 生命周期统计
    if hasattr(agent, 'cycles_survived'):
        print(f"\n⏱️  生命周期:")
        print(f"   存活周期:     {agent.cycles_survived}")
        print(f"   持仓周期:     {agent.cycles_with_position if hasattr(agent, 'cycles_with_position') else 'N/A'}")
        if hasattr(agent, 'cycles_with_position') and agent.cycles_survived > 0:
            holding_ratio = agent.cycles_with_position / agent.cycles_survived * 100
            print(f"   持仓比例:     {holding_ratio:.1f}%")
    
    return {
        'agent_id': agent.agent_id,
        'total_return': total_return,
        'unrealized_pnl': unrealized_pnl,
        'trade_count': ledger.trade_count if hasattr(agent, 'account') else 0,
        'genome': agent.genome.active_params if hasattr(agent, 'genome') else {},
        'instinct': {
            'risk_appetite': agent.instinct.risk_appetite,
            'fear_of_death': agent.instinct.fear_of_death,
            'loss_aversion': agent.instinct.loss_aversion
        } if hasattr(agent, 'instinct') else {}
    }

def main():
    print("=" * 80)
    print("🏆 最佳Agent深度分析")
    print("=" * 80)
    print()
    
    # 运行一次测试
    total_cycles = 200
    prices = load_prices(limit=total_cycles)
    market_feed = make_market_feed(prices)
    
    print("🚀 运行测试以生成Agent...")
    print()
    
    facade = run_scenario(
        mode="backtest",
        total_cycles=total_cycles,
        market_feed=market_feed,
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        scenario="best_agent_analysis",
        evo_interval=30,
        seed=7001  # 固定seed确保可重复
    )
    
    print("\n" + "=" * 80)
    print("📊 开始分析...")
    print("=" * 80)
    
    # 计算所有Agent的收益率
    current_price = prices[-1]
    agent_returns = []
    
    for agent in facade.moirai.agents:
        unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
        effective_capital = agent.current_capital + unrealized_pnl
        total_return = (effective_capital - agent.initial_capital) / agent.initial_capital * 100
        agent_returns.append((agent, total_return))
    
    # 排序
    agent_returns.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n📈 收益率排名（Top 10）:")
    print(f"{'排名':<6} {'Agent ID':<20} {'收益率':<12} {'交易次数':<10}")
    print("-" * 80)
    for i, (agent, ret) in enumerate(agent_returns[:10], 1):
        trade_count = agent.account.private_ledger.trade_count if hasattr(agent, 'account') else 0
        print(f"{i:<6} {agent.agent_id:<20} {ret:+11.2f}% {trade_count:<10}")
    
    # 详细分析Top 3
    print("\n" + "=" * 80)
    print("🔬 Top 3 深度分析")
    print("=" * 80)
    
    top3_data = []
    for i in range(min(3, len(agent_returns))):
        agent, ret = agent_returns[i]
        data = analyze_agent_detailed(agent, prices, i+1)
        top3_data.append(data)
    
    # 对比分析
    print("\n" + "=" * 80)
    print("⚖️  Top 3 对比分析")
    print("=" * 80)
    
    if len(top3_data) >= 2:
        print("\n🧬 基因参数对比:")
        if top3_data[0]['genome']:
            print(f"{'参数':<20} {'#1':<12} {'#2':<12} {'#3':<12} {'差异':<12}")
            print("-" * 80)
            for key in sorted(top3_data[0]['genome'].keys()):
                val1 = top3_data[0]['genome'].get(key, 0)
                val2 = top3_data[1]['genome'].get(key, 0) if len(top3_data) > 1 else 0
                val3 = top3_data[2]['genome'].get(key, 0) if len(top3_data) > 2 else 0
                diff = max(val1, val2, val3) - min(val1, val2, val3)
                print(f"{key:<20} {val1:<12.3f} {val2:<12.3f} {val3:<12.3f} {diff:<12.3f}")
        
        print("\n🎭 本能参数对比:")
        print(f"{'参数':<20} {'#1':<12} {'#2':<12} {'#3':<12} {'差异':<12}")
        print("-" * 80)
        for key in ['risk_appetite', 'fear_of_death', 'loss_aversion']:
            val1 = top3_data[0]['instinct'].get(key, 0)
            val2 = top3_data[1]['instinct'].get(key, 0) if len(top3_data) > 1 else 0
            val3 = top3_data[2]['instinct'].get(key, 0) if len(top3_data) > 2 else 0
            diff = max(val1, val2, val3) - min(val1, val2, val3)
            print(f"{key:<20} {val1:<12.3f} {val2:<12.3f} {val3:<12.3f} {diff:<12.3f}")
    
    # BTC基准对比
    btc_return = (prices[-1] - prices[0]) / prices[0] * 100
    best_return = agent_returns[0][1]
    
    print("\n" + "=" * 80)
    print("💡 关键发现")
    print("=" * 80)
    print(f"\n📊 收益对比:")
    print(f"   BTC基准:       {btc_return:+.2f}%")
    print(f"   最佳Agent:     {best_return:+.2f}% (达到BTC的 {best_return/btc_return*100:.1f}%)")
    print(f"   Top 3平均:     {np.mean([d['total_return'] for d in top3_data]):+.2f}%")
    
    print(f"\n🎯 成功要素（初步判断）:")
    if top3_data[0]['genome']:
        # 找出最突出的基因特征
        genome_avg = {key: np.mean([d['genome'].get(key, 0) for d in top3_data]) for key in top3_data[0]['genome'].keys()}
        sorted_genome = sorted(genome_avg.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)
        print(f"   关键基因特征:")
        for key, val in sorted_genome[:3]:
            tendency = "高" if val > 0.5 else "低"
            print(f"   - {key}: {val:.3f} ({tendency})")
    
    instinct_avg = {
        'risk_appetite': np.mean([d['instinct'].get('risk_appetite', 0) for d in top3_data]),
        'fear_of_death': np.mean([d['instinct'].get('fear_of_death', 0) for d in top3_data]),
        'loss_aversion': np.mean([d['instinct'].get('loss_aversion', 0) for d in top3_data])
    }
    print(f"   关键本能特征:")
    for key, val in sorted(instinct_avg.items(), key=lambda x: abs(x[1] - 0.5), reverse=True):
        tendency = "高" if val > 0.5 else "低"
        print(f"   - {key}: {val:.3f} ({tendency})")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()

