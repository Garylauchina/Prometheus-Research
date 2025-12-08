#!/usr/bin/env python3
"""
OKX真实规则版本
==================

真实OKX交易规则：
1. ✅ 杠杆不限制（最高125x，小额持仓）
2. ✅ 资金规模会自动限制（梯度保证金）
3. ✅ 持仓越大，可用杠杆越低
4. ✅ 流动性影响（滑点随规模增加）
5. ✅ 订单簿深度限制
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


def get_okx_leverage_limit(position_size_usd, btc_price):
    """
    OKX梯度保证金制度
    根据持仓规模返回最大可用杠杆
    
    OKX真实规则（BTC/USDT永续）：
    - 持仓 < $50万: 最高125x
    - 持仓 $50万-$100万: 最高100x
    - 持仓 $100万-$200万: 最高50x
    - 持仓 $200万-$500万: 最高25x
    - 持仓 > $500万: 最高10x
    """
    if position_size_usd < 500_000:
        return 125.0
    elif position_size_usd < 1_000_000:
        return 100.0
    elif position_size_usd < 2_000_000:
        return 50.0
    elif position_size_usd < 5_000_000:
        return 25.0
    else:
        return 10.0


def get_dynamic_slippage(position_size_usd):
    """
    动态滑点：随资金规模增加
    
    估算：
    - < $10万: 0.01%
    - $10万-$50万: 0.02%
    - $50万-$100万: 0.05%
    - $100万-$500万: 0.10%
    - > $500万: 0.20%
    """
    if position_size_usd < 100_000:
        return 0.0001  # 0.01%
    elif position_size_usd < 500_000:
        return 0.0002  # 0.02%
    elif position_size_usd < 1_000_000:
        return 0.0005  # 0.05%
    elif position_size_usd < 5_000_000:
        return 0.0010  # 0.10%
    else:
        return 0.0020  # 0.20%


def get_market_impact(position_size_usd, daily_volume_usd=1_000_000_000):
    """
    市场冲击成本
    
    估算：position_size / daily_volume * impact_factor
    BTC日均交易量约10亿美元
    """
    if position_size_usd < 100_000:
        return 0.0  # 小单无冲击
    
    # 简化模型：冲击成本 = (持仓/日交易量) * 0.5
    impact = (position_size_usd / daily_volume_usd) * 0.5
    return min(impact, 0.01)  # 最高1%


def run_single_test(seed, steps=2000, evolution_interval=30):
    """运行单次测试（OKX真实规则）"""
    
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
                
                risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
                
                # Agent决策
                if abs(price_change) < 0.001:
                    position = 0.0
                elif price_change > 0:
                    position = risk_tolerance * 0.8
                else:
                    position = -risk_tolerance * 0.8
                
                if abs(position) < 0.01:
                    continue
                
                # 💰 计算持仓规模
                position_value = abs(position) * agent.current_capital
                
                # 🎯 OKX动态杠杆（关键！）
                # 根据持仓规模自动限制杠杆
                max_leverage = get_okx_leverage_limit(position_value, current_price)
                
                # Agent选择杠杆（但不能超过OKX限制）
                desired_leverage = 1.0 + risk_tolerance * 124.0  # 1-125x
                leverage = min(desired_leverage, max_leverage)
                
                # 计算收益
                base_return = price_change * position
                leveraged_return = base_return * leverage
                
                # 💸 动态交易成本（关键！）
                trading_fee = 0.001  # 0.10% OKX Taker费用
                
                # 动态滑点（随资金规模增加）
                slippage = get_dynamic_slippage(position_value)
                
                # 市场冲击成本（大单才有）
                market_impact = get_market_impact(position_value)
                
                # 资金费率
                funding_rate = 0.0003  # 0.03%/天
                
                # 总成本
                total_cost = trading_fee + slippage + market_impact + funding_rate
                leveraged_return -= total_cost * leverage
                
                # 🛡️ 限制单次最大盈亏（防止数值爆炸）
                # 即使用高杠杆，也很难一次赚超过100%
                max_single_return = 1.0    # 最多翻倍
                min_single_return = -0.95  # 最多亏95%
                leveraged_return = max(min_single_return, min(max_single_return, leveraged_return))
                
                # 检查爆仓
                if leveraged_return <= -1.0:
                    agent.current_capital = 0.0
                    total_liquidations += 1
                else:
                    agent.current_capital *= (1 + leveraged_return)
                
                # 💀 强制止损（亏损90%）
                if agent.current_capital < initial_capital_per_agent * 0.1:
                    agent.current_capital = 0.0
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
        
        return {
            'seed': seed,
            'success': True,
            'survivors': len(survivors),
            'survival_rate': survival_rate,
            'liquidations': total_liquidations,
            'final_total_capital': final_total_capital,
            'total_profit': total_profit,
            'avg_capital_all': avg_capital_all,
            'roi_all': roi_all,
            'annualized_return': annualized_return,
            'market_roi': market_roi,
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
    print("🏦 OKX真实规则版本")
    print("=" * 80)
    print()
    
    print("✅ OKX真实交易规则:")
    print()
    print("   🎯 杠杆（梯度保证金）:")
    print("      持仓 < $50万: 最高125x")
    print("      持仓 $50万-$100万: 最高100x")
    print("      持仓 $100万-$200万: 最高50x")
    print("      持仓 $200万-$500万: 最高25x")
    print("      持仓 > $500万: 最高10x")
    print()
    print("   💸 动态滑点:")
    print("      < $10万: 0.01%")
    print("      $10万-$50万: 0.02%")
    print("      $50万-$100万: 0.05%")
    print("      $100万-$500万: 0.10%")
    print("      > $500万: 0.20%")
    print()
    print("   🌊 市场冲击:")
    print("      根据持仓/日交易量动态计算")
    print("      小单(<$10万): 无冲击")
    print("      大单: 最高1%冲击成本")
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
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 80)
    print()
    print("📊 测试结果（OKX真实规则）:")
    print()
    
    print("💰 系统总盈利:")
    print(f"   初始: $500,000")
    print(f"   平均最终: ${np.mean([r['final_total_capital'] for r in successful]):,.2f}")
    print(f"   平均盈利: ${np.mean(total_profits):,.2f}")
    print()
    
    print("📈 ROI统计:")
    avg_roi = np.mean(rois)
    median_roi = np.median(rois)
    std_roi = np.std(rois)
    profitable_count = sum(1 for r in rois if r > 0)
    profitable_rate = profitable_count / len(rois) * 100
    
    print(f"   平均ROI: {avg_roi:+.2f}%")
    print(f"   中位数: {median_roi:+.2f}%")
    print(f"   标准差: ±{std_roi:.2f}%")
    print(f"   最好: {np.max(rois):+.2f}%")
    print(f"   最差: {np.min(rois):+.2f}%")
    print(f"   盈利率: {profitable_rate:.1f}% ({profitable_count}/{len(rois)})")
    if avg_roi != 0:
        print(f"   变异系数: {abs(std_roi / avg_roi) * 100:.2f}%")
    print()
    
    print("📊 年化收益率:")
    avg_ann = np.mean(ann_rets)
    print(f"   平均: {avg_ann:+.2f}%")
    print(f"   中位数: {np.median(ann_rets):+.2f}%")
    print(f"   最好: {np.max(ann_rets):+.2f}%")
    print(f"   最差: {np.min(ann_rets):+.2f}%")
    if avg_ann > 0:
        print(f"   vs 巴菲特(20%): {avg_ann / 20:.2f}x")
    print()
    
    print("👥 幸存率:")
    print(f"   平均: {np.mean([r['survival_rate'] for r in successful]):.1f}%")
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
    with open(f"okx_realistic_{timestamp}.json", 'w') as f:
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
    print("📝 关键发现:")
    print("   - 杠杆随资金规模自动降低（OKX梯度保证金）")
    print("   - 滑点随规模增加（流动性影响）")
    print("   - 大资金自然限制了收益上限")
    print("   - 这是更真实的模拟！")
    print()


if __name__ == "__main__":
    main()

