#!/usr/bin/env python3
"""
Phase 0 深度分析：Agent决策模式和评分系统诊断

核心问题：
1. Agent为什么交易这么少？（平均0.7笔/50周期）
2. Daimon的决策逻辑是否有问题？
3. Fitness评分是否正确引导了Agent行为？
4. 演化是否在朝正确方向进行？
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

sys.path.insert(0, '.')

# 导入核心模块
from prometheus.facade.v6_facade import build_facade
from prometheus.core.agent_v5 import AgentState

def analyze_phase0_results():
    """分析Phase 0的详细结果"""
    
    print("=" * 80)
    print("🔍 Phase 0 深度分析：Agent决策模式诊断")
    print("=" * 80)
    
    # 1. 加载Phase 0结果
    result_file = "results/phase0_verify_20251208_024327.json"
    
    if not Path(result_file).exists():
        print(f"❌ 结果文件不存在: {result_file}")
        return
    
    with open(result_file, 'r') as f:
        phase0_data = json.load(f)
    
    print(f"\n📊 Phase 0 整体统计:")
    print(f"   成功率: {phase0_data['summary']['success_rate']*100:.1f}%")
    print(f"   平均存活: {phase0_data['summary']['avg_alive_agents']:.1f}")
    print(f"   平均收益: {phase0_data['summary']['avg_system_return']:+.2f}%")
    print(f"   平均交易: {phase0_data['summary']['avg_trades']:.0f}笔")
    print(f"   人均交易: {phase0_data['summary']['avg_trades_per_agent']:.1f}笔")
    
    # 2. 重新运行一个seed，记录详细决策
    print("\n" + "=" * 80)
    print("🔬 详细决策分析：重新运行Seed 8005（记录完整决策）")
    print("=" * 80)
    
    # 加载市场数据
    df_btc = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    prices = df_btc['close'].tolist()
    
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    # 构建facade（50 cycles，记录详细日志）
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    facade = build_facade(
        mode="backtest",
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        evo_interval=10,
        seed=None,
        genesis_seed=8005,
        evolution_seed=None,
        full_genome_unlock=True
    )
    
    # 运行并记录决策
    decisions_log = []
    no_decision_count = 0
    decision_count = 0
    
    market_feed = make_market_feed()
    
    for cycle in range(1, 51):
        market_data, bulletins = market_feed(cycle)
        
        # 运行周期
        facade.run_cycle(
            market_data=market_data,
            bulletins=bulletins,
            cycle_count=cycle,
            scenario="backtest"
        )
        
        # 记录每个Agent的决策
        for agent in facade.moirai.agents:
            if agent.state == AgentState.DEAD:
                continue
            
            # 获取Agent的最新决策（如果有）
            if hasattr(agent, 'account') and agent.account:
                trades = agent.account.private_ledger.trade_history
                if len(trades) > len([d for d in decisions_log if d['agent_id'] == agent.agent_id]):
                    # 新交易
                    last_trade = trades[-1]
                    decisions_log.append({
                        'cycle': cycle,
                        'agent_id': agent.agent_id,
                        'action': last_trade.action,
                        'amount': last_trade.amount,
                        'price': last_trade.price,
                        'confidence': last_trade.confidence,
                        'capital': agent.account.private_ledger.virtual_capital,
                        'genome_params': {
                            'trend_preference': agent.genome.active_params.get('trend_preference', 0),
                            'risk_appetite': agent.genome.active_params.get('risk_appetite', 0),
                            'patience': agent.genome.active_params.get('patience', 0),
                        }
                    })
                    decision_count += 1
        
        # 统计无决策的Agent
        active_agents = len([a for a in facade.moirai.agents if a.state != AgentState.DEAD])
        no_decision_count += (active_agents - decision_count)
    
    # 3. 分析决策模式
    print(f"\n📊 决策统计:")
    print(f"   总周期数: 50")
    print(f"   活跃Agent: ~50")
    print(f"   总决策机会: ~2500 (50 agents × 50 cycles)")
    print(f"   实际决策数: {decision_count}")
    print(f"   决策率: {decision_count/2500*100:.1f}%")
    print(f"   无决策次数: {no_decision_count}")
    print(f"   无决策率: {no_decision_count/2500*100:.1f}%")
    
    if len(decisions_log) == 0:
        print("\n❌ 没有记录到任何决策！这是一个严重问题！")
        print("\n可能原因:")
        print("   1. Daimon决策逻辑过于保守")
        print("   2. Agent基因参数不合理")
        print("   3. 市场数据feed有问题")
        return
    
    # 4. 分析决策类型分布
    print(f"\n📊 决策类型分布:")
    action_counts = Counter([d['action'] for d in decisions_log])
    for action, count in action_counts.most_common():
        print(f"   {action}: {count} ({count/len(decisions_log)*100:.1f}%)")
    
    # 5. 分析决策时机
    print(f"\n📊 决策时机分布:")
    cycle_counts = Counter([d['cycle'] for d in decisions_log])
    early_cycles = sum(count for cycle, count in cycle_counts.items() if cycle <= 10)
    mid_cycles = sum(count for cycle, count in cycle_counts.items() if 10 < cycle <= 40)
    late_cycles = sum(count for cycle, count in cycle_counts.items() if cycle > 40)
    
    print(f"   早期(1-10):  {early_cycles} ({early_cycles/len(decisions_log)*100:.1f}%)")
    print(f"   中期(11-40): {mid_cycles} ({mid_cycles/len(decisions_log)*100:.1f}%)")
    print(f"   后期(41-50): {late_cycles} ({late_cycles/len(decisions_log)*100:.1f}%)")
    
    # 6. 分析决策Agent特征
    print(f"\n📊 决策Agent特征:")
    agent_decision_counts = Counter([d['agent_id'] for d in decisions_log])
    
    trading_agents = len(agent_decision_counts)
    no_trading_agents = 50 - trading_agents
    
    print(f"   有交易Agent: {trading_agents}/50 ({trading_agents/50*100:.1f}%)")
    print(f"   无交易Agent: {no_trading_agents}/50 ({no_trading_agents/50*100:.1f}%)")
    
    if trading_agents > 0:
        most_active = agent_decision_counts.most_common(3)
        print(f"\n   最活跃Agent:")
        for agent_id, count in most_active:
            print(f"      {agent_id}: {count}笔交易")
    
    # 7. 分析基因参数与决策的关系
    print(f"\n📊 基因参数分析（交易Agent）:")
    if len(decisions_log) > 0:
        avg_trend_pref = sum(d['genome_params']['trend_preference'] for d in decisions_log) / len(decisions_log)
        avg_risk_app = sum(d['genome_params']['risk_appetite'] for d in decisions_log) / len(decisions_log)
        avg_patience = sum(d['genome_params']['patience'] for d in decisions_log) / len(decisions_log)
        
        print(f"   平均趋势偏好: {avg_trend_pref:.3f}")
        print(f"   平均风险偏好: {avg_risk_app:.3f}")
        print(f"   平均耐心值: {avg_patience:.3f}")
    
    # 8. 分析Fitness评分
    print(f"\n" + "=" * 80)
    print("📊 Fitness评分系统分析")
    print("=" * 80)
    
    # 获取最终Agent状态
    agent_stats = []
    current_price = prices[min(49, len(prices) - 1)]
    
    for agent in facade.moirai.agents:
        if not hasattr(agent, 'account') or not agent.account:
            continue
        
        capital = agent.account.private_ledger.virtual_capital
        unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
        total_capital = capital + unrealized_pnl
        profit = total_capital - agent.initial_capital
        profit_pct = profit / agent.initial_capital * 100
        
        trades = len(agent.account.private_ledger.trade_history)
        
        agent_stats.append({
            'agent_id': agent.agent_id,
            'profit': profit,
            'profit_pct': profit_pct,
            'trades': trades,
            'capital': total_capital,
            'state': agent.state.value
        })
    
    # 排序
    agent_stats.sort(key=lambda x: x['profit'], reverse=True)
    
    print(f"\n🏆 Top 10 盈利Agent:")
    for i, stats in enumerate(agent_stats[:10], 1):
        print(f"   {i}. {stats['agent_id']}: {stats['profit']:+.2f} ({stats['profit_pct']:+.1f}%) | {stats['trades']}笔交易")
    
    print(f"\n💀 Bottom 10 亏损Agent:")
    for i, stats in enumerate(agent_stats[-10:], 1):
        print(f"   {i}. {stats['agent_id']}: {stats['profit']:+.2f} ({stats['profit_pct']:+.1f}%) | {stats['trades']}笔交易")
    
    # 9. 关键发现总结
    print(f"\n" + "=" * 80)
    print("💡 关键发现和问题诊断")
    print("=" * 80)
    
    # 诊断1: 决策率过低
    if decision_count / 2500 < 0.1:
        print(f"\n🚨 问题1: 决策率过低 ({decision_count/2500*100:.1f}%)")
        print(f"   现象: Agent在99%的时间里都没有做出交易决策")
        print(f"   可能原因:")
        print(f"      - Daimon的决策阈值过高（confidence门槛）")
        print(f"      - Agent基因参数导致过于保守")
        print(f"      - WorldSignature没有正确传递给Agent")
        print(f"   建议:")
        print(f"      - 检查Daimon._make_decision()的vote聚合逻辑")
        print(f"      - 检查Agent基因的active_params是否正确激活")
        print(f"      - 增加日志输出，看Daimon每个周期的vote内容")
    
    # 诊断2: 交易Agent占比低
    if trading_agents / 50 < 0.5:
        print(f"\n🚨 问题2: 交易Agent占比过低 ({trading_agents}/50 = {trading_agents/50*100:.1f}%)")
        print(f"   现象: 大部分Agent从未交易")
        print(f"   可能原因:")
        print(f"      - 基因多样性不足（虽然50个参数，但可能都偏保守）")
        print(f"      - Fitness评分鼓励\"不交易\"（生存奖励过高？）")
        print(f"   建议:")
        print(f"      - 检查genesis时基因参数的初始化分布")
        print(f"      - 调整Fitness v3，降低[生存]权重，提高[盈利]权重")
    
    # 诊断3: Fitness评分是否合理
    avg_profit_trading = sum(s['profit'] for s in agent_stats if s['trades'] > 0) / max(1, trading_agents)
    avg_profit_no_trading = sum(s['profit'] for s in agent_stats if s['trades'] == 0) / max(1, no_trading_agents)
    
    if no_trading_agents > 0:
        print(f"\n🚨 问题3: Fitness评分可能有偏差")
        print(f"   交易Agent平均盈利: {avg_profit_trading:+.2f}")
        print(f"   不交易Agent平均盈利: {avg_profit_no_trading:+.2f}")
        
        if avg_profit_no_trading >= avg_profit_trading:
            print(f"   ⚠️ 警告: 不交易的Agent盈利更好！")
            print(f"   说明: Fitness评分可能在鼓励\"不作为\"")
            print(f"   建议: 调整Fitness v3，增加[探索奖励]")
    
    # 诊断4: 市场适应性
    btc_return = (prices[49] - prices[0]) / prices[0] * 100
    system_return = phase0_data['summary']['avg_system_return']
    
    print(f"\n📊 市场适应性:")
    print(f"   BTC收益: {btc_return:+.2f}%")
    print(f"   系统收益: {system_return:+.2f}%")
    print(f"   相对表现: {system_return/btc_return*100:.1f}% of BTC")
    
    if system_return < btc_return * 0.5:
        print(f"   ⚠️ 警告: 系统收益远低于BTC（<50%）")
        print(f"   说明: Agent没有有效利用市场机会")
    
    # 10. 保存详细分析结果
    analysis_file = f"results/phase0_decision_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'summary': {
                'total_cycles': 50,
                'total_agents': 50,
                'decision_count': decision_count,
                'decision_rate': decision_count / 2500,
                'trading_agents': trading_agents,
                'no_trading_agents': no_trading_agents,
            },
            'decisions': decisions_log,
            'agent_stats': agent_stats,
            'action_distribution': dict(action_counts),
        }, f, indent=2)
    
    print(f"\n💾 详细分析已保存: {analysis_file}")
    
    # 11. 最终建议
    print(f"\n" + "=" * 80)
    print("🎯 最终建议")
    print("=" * 80)
    
    print("""
基于Phase 0的分析，建议在进入Phase 1之前：

优先级1: 检查Daimon决策逻辑 🔥
  → 增加详细日志，查看每个周期Daimon的vote内容
  → 确认confidence阈值是否合理
  → 验证WorldSignature是否正确传递

优先级2: 调整Fitness v3评分 ⚡
  → 降低"生存奖励"权重（当前10%）
  → 增加"探索奖励"（鼓励交易）
  → 或者直接简化为AlphaZero式（纯收益）

优先级3: 检查基因初始化 🧬
  → 验证50个参数的初始分布
  → 确保有足够的"激进型"Agent

建议顺序：
1. 先运行一个详细的Daimon决策日志测试（5-10 cycles）
2. 根据日志分析，调整Daimon或Fitness
3. 重新运行Phase 0验证
4. 通过后再进入Phase 1大规模训练
    """)


if __name__ == "__main__":
    analyze_phase0_results()

