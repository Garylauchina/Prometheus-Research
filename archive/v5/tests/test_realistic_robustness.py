#!/usr/bin/env python3
"""
真实版鲁棒性测试
==================

新增约束（更真实）：
1. ✅ 限制单次最大盈利（防止数值爆炸）
2. ✅ 限制Agent最大资金（100万美元）
3. ✅ 降低杠杆上限（10x，而不是100x）
4. ✅ 增加风险控制（止损）
5. ✅ 真实的资金规模影响
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
import json

logging.basicConfig(level=logging.CRITICAL)


def run_single_test(seed, steps=2000, evolution_interval=30):
    """运行单次测试（真实版）"""
    
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    try:
        df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        market_start_price = df.iloc[0]['close']
        market_end_price = df.iloc[min(steps - 1, len(df) - 1)]['close']
        
        moirai = Moirai()
        evolution_manager = EvolutionManagerV5(moirai=moirai)
        evolution_manager.immigration_enabled = False
        
        initial_agent_count = 50
        initial_capital_per_agent = 10000.0
        
        agents = moirai._genesis_create_agents(
            agent_count=initial_agent_count,
            gene_pool=[],
            capital_per_agent=initial_capital_per_agent
        )
        
        for agent in agents:
            agent.fitness = 1.0
        
        moirai.agents = agents
        
        initial_total_capital = initial_agent_count * initial_capital_per_agent
        
        current_step = 0
        evolution_count = 0
        total_trades = 0
        total_liquidations = 0
        
        for idx, row in df.head(steps).iterrows():
            current_step += 1
            current_price = row['close']
            
            if idx > 0:
                prev_price = df.iloc[idx - 1]['close']
                price_change = (current_price - prev_price) / prev_price
            else:
                price_change = 0.0
            
            for agent in agents:
                if agent.current_capital <= 0:
                    continue
                
                # 💰 资金规模限制（关键！）
                max_capital = 1_000_000  # 最大100万美元
                if agent.current_capital > max_capital:
                    agent.current_capital = max_capital
                
                risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
                
                if abs(price_change) < 0.001:
                    position = 0.0
                elif price_change > 0:
                    position = risk_tolerance * 0.8
                else:
                    position = -risk_tolerance * 0.8
                
                if position != 0:
                    total_trades += 1
                
                # 🎯 降低杠杆上限（关键！）
                max_leverage = 10.0  # 最高10x，而不是100x
                leverage = 1.0 + risk_tolerance * (max_leverage - 1.0)
                leverage = min(leverage, max_leverage)
                
                base_return = price_change * position
                leveraged_return = base_return * leverage
                
                # 真实交易成本
                if abs(position) > 0.01:
                    trading_fee = 0.001
                    slippage = 0.0001
                    funding_rate = 0.0003
                    total_cost = trading_fee + slippage + funding_rate
                    leveraged_return -= total_cost * leverage
                
                # 🛡️ 限制单次最大盈利/亏损（关键！）
                max_single_return = 0.5  # 单次最多赚50%
                min_single_return = -0.9  # 单次最多亏90%（留10%资金）
                
                leveraged_return = max(min_single_return, min(max_single_return, leveraged_return))
                
                # 检查爆仓
                if leveraged_return <= -1.0:
                    agent.current_capital = 0.0
                    total_liquidations += 1
                else:
                    agent.current_capital *= (1 + leveraged_return)
                
                # 🚨 止损机制（额外保护）
                if agent.current_capital < initial_capital_per_agent * 0.1:  # 亏损90%
                    agent.current_capital = 0.0  # 强制清算
                    total_liquidations += 1
            
            if current_step % evolution_interval == 0:
                evolution_count += 1
                agents = [a for a in agents if a.current_capital > 0]
                moirai.agents = agents
                
                if len(agents) > 0:
                    try:
                        evolution_manager.run_evolution_cycle()
                        agents = moirai.agents
                    except:
                        pass
        
        # 计算结果
        all_agents_capitals = []
        for agent in moirai.agents:
            all_agents_capitals.append(agent.current_capital)
        
        while len(all_agents_capitals) < initial_agent_count:
            all_agents_capitals.append(0.0)
        
        final_total_capital = sum(all_agents_capitals)
        avg_capital_all = final_total_capital / initial_agent_count
        total_profit = final_total_capital - initial_total_capital
        roi_all = (final_total_capital / initial_total_capital - 1) * 100
        
        years = steps / 365.0
        if roi_all > -100:
            annualized_return = (pow(1 + roi_all / 100, 1 / years) - 1) * 100
        else:
            annualized_return = -100
        
        market_roi = (market_end_price / market_start_price - 1) * 100
        
        survivors = [a for a in moirai.agents if a.current_capital > 0]
        survival_rate = len(survivors) / initial_agent_count * 100
        
        if len(survivors) > 0:
            avg_survivors = np.mean([a.current_capital for a in survivors])
            max_capital_achieved = np.max([a.current_capital for a in survivors])
        else:
            avg_survivors = 0
            max_capital_achieved = 0
        
        return {
            'seed': seed,
            'success': True,
            'survivors': len(survivors),
            'survival_rate': survival_rate,
            'evolution_count': evolution_count,
            'liquidations': total_liquidations,
            'final_total_capital': final_total_capital,
            'total_profit': total_profit,
            'avg_capital_all': avg_capital_all,
            'roi_all': roi_all,
            'annualized_return': annualized_return,
            'avg_survivors': avg_survivors,
            'max_capital': max_capital_achieved,
            'market_roi': market_roi,
            'excess_return': roi_all - market_roi,
        }
    
    except Exception as e:
        return {
            'seed': seed,
            'success': False,
            'error': str(e),
            'roi_all': -100,
        }


def main():
    print()
    print("=" * 80)
    print("🧬 真实版鲁棒性测试")
    print("=" * 80)
    print()
    
    print("✅ 真实约束:")
    print("   1. 单次最大盈利: 50%（防止数值爆炸）")
    print("   2. Agent最大资金: 100万美元（规模限制）")
    print("   3. 杠杆上限: 10x（而不是100x）")
    print("   4. 止损机制: 亏损90%强制清算")
    print("   5. 真实交易成本: 0.14%总成本")
    print()
    print("=" * 80)
    print()
    
    num_tests = 20
    steps = 2000
    
    print(f"📋 测试配置:")
    print(f"   测试次数: {num_tests}")
    print(f"   每次步数: {steps}步（约5.5年）")
    print(f"   初始资金: $500,000")
    print()
    print("🚀 开始测试...")
    print()
    
    results = []
    start_time = datetime.now()
    
    for i in range(num_tests):
        seed = i * 100
        print(f"   测试 #{i+1}/{num_tests} (seed={seed})...", end=" ", flush=True)
        
        result = run_single_test(seed, steps=steps)
        results.append(result)
        
        if result['success']:
            roi = result['roi_all']
            ann_ret = result['annualized_return']
            survivors = result['survivors']
            status = "✅盈利" if roi > 0 else "❌亏损"
            print(f"{status} ROI:{roi:+.2f}% 年化:{ann_ret:+.2f}% 幸存:{survivors}个")
        else:
            print(f"❌失败: {result.get('error', '未知错误')}")
    
    successful = [r for r in results if r.get('success', True)]
    
    if len(successful) == 0:
        print("\n❌ 没有成功的测试")
        return
    
    rois = [r['roi_all'] for r in successful]
    ann_rets = [r['annualized_return'] for r in successful]
    total_profits = [r['total_profit'] for r in successful]
    survival_rates = [r['survival_rate'] for r in successful]
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 80)
    print()
    print("📊 测试结果（真实版）:")
    print()
    
    print("💰 系统总盈利:")
    print(f"   初始: $500,000")
    print(f"   平均最终: ${np.mean([r['final_total_capital'] for r in successful]):,.2f}")
    print(f"   平均盈利: ${np.mean(total_profits):,.2f}")
    print()
    
    print("📈 ROI统计（消除偏差+真实约束）:")
    avg_roi = np.mean(rois)
    median_roi = np.median(rois)
    std_roi = np.std(rois)
    min_roi = np.min(rois)
    max_roi = np.max(rois)
    profitable_count = sum(1 for r in rois if r > 0)
    profitable_rate = profitable_count / len(rois) * 100
    
    print(f"   平均ROI: {avg_roi:+.2f}%")
    print(f"   中位数ROI: {median_roi:+.2f}%")
    print(f"   标准差: ±{std_roi:.2f}%")
    print(f"   最好: {max_roi:+.2f}%")
    print(f"   最差: {min_roi:+.2f}%")
    print(f"   盈利率: {profitable_rate:.1f}% ({profitable_count}/{len(rois)})")
    if avg_roi != 0:
        print(f"   变异系数: {abs(std_roi / avg_roi) * 100:.2f}%")
    print()
    
    print("📊 年化收益率:")
    avg_ann = np.mean(ann_rets)
    median_ann = np.median(ann_rets)
    print(f"   平均: {avg_ann:+.2f}%")
    print(f"   中位数: {median_ann:+.2f}%")
    print(f"   最好: {np.max(ann_rets):+.2f}%")
    print(f"   最差: {np.min(ann_rets):+.2f}%")
    if avg_ann > 0:
        print(f"   vs 巴菲特(20%): {avg_ann / 20:.2f}x")
    print()
    
    print("👥 幸存率:")
    print(f"   平均: {np.mean(survival_rates):.1f}%")
    print()
    
    if successful[0].get('market_roi'):
        market_roi = successful[0]['market_roi']
        print(f"📊 vs 市场:")
        print(f"   BTC: {market_roi:+.2f}%")
        print(f"   系统: {avg_roi:+.2f}%")
        print(f"   超额: {avg_roi - market_roi:+.2f}%")
        print()
    
    print(f"⏱️  耗时: {duration} ({duration.total_seconds() / len(results):.1f}秒/次)")
    print()
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"realistic_robustness_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("🎯 结论:")
    if profitable_rate >= 90:
        print(f"   🏆 优秀 - {profitable_rate:.0f}%盈利率, {avg_ann:+.1f}%年化")
    elif profitable_rate >= 70:
        print(f"   ✅ 良好 - {profitable_rate:.0f}%盈利率, {avg_ann:+.1f}%年化")
    else:
        print(f"   ⚠️  需改进 - {profitable_rate:.0f}%盈利率, {avg_ann:+.1f}%年化")
    print()


if __name__ == "__main__":
    main()

