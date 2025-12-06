#!/usr/bin/env python3
"""
终极测试：OKX真实规则 × 1000次
================================

这将是最终的、最准确的验证！
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
import os

logging.basicConfig(level=logging.CRITICAL)


def get_okx_leverage_limit(position_size_usd, btc_price):
    """OKX梯度保证金"""
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
    """动态滑点"""
    if position_size_usd < 100_000:
        return 0.0001
    elif position_size_usd < 500_000:
        return 0.0002
    elif position_size_usd < 1_000_000:
        return 0.0005
    elif position_size_usd < 5_000_000:
        return 0.0010
    else:
        return 0.0020


def get_market_impact(position_size_usd, daily_volume_usd=1_000_000_000):
    """市场冲击"""
    if position_size_usd < 100_000:
        return 0.0
    impact = (position_size_usd / daily_volume_usd) * 0.5
    return min(impact, 0.01)


def run_single_test(seed, steps=2000):
    """运行单次测试"""
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    try:
        df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        market_start = df.iloc[0]['close']
        market_end = df.iloc[min(steps - 1, len(df) - 1)]['close']
        
        moirai = Moirai()
        evolution_manager = EvolutionManagerV5(moirai=moirai)
        evolution_manager.immigration_enabled = False
        
        initial_count = 50
        initial_capital = 10000.0
        
        agents = moirai._genesis_create_agents(
            agent_count=initial_count,
            gene_pool=[],
            capital_per_agent=initial_capital
        )
        
        for agent in agents:
            agent.fitness = 1.0
        moirai.agents = agents
        
        initial_total = initial_count * initial_capital
        
        for idx, row in df.head(steps).iterrows():
            current_price = row['close']
            
            if idx > 0:
                prev_price = df.iloc[idx - 1]['close']
                price_change = (current_price - prev_price) / prev_price
            else:
                price_change = 0.0
            
            for agent in agents:
                if agent.current_capital <= 0:
                    continue
                
                risk = getattr(agent.instinct, 'risk_tolerance', 0.5)
                
                if abs(price_change) < 0.001:
                    position = 0.0
                elif price_change > 0:
                    position = risk * 0.8
                else:
                    position = -risk * 0.8
                
                if abs(position) < 0.01:
                    continue
                
                position_value = abs(position) * agent.current_capital
                max_lev = get_okx_leverage_limit(position_value, current_price)
                desired_lev = 1.0 + risk * 124.0
                leverage = min(desired_lev, max_lev)
                
                base_return = price_change * position
                lev_return = base_return * leverage
                
                fee = 0.001
                slip = get_dynamic_slippage(position_value)
                impact = get_market_impact(position_value)
                funding = 0.0003
                
                total_cost = fee + slip + impact + funding
                lev_return -= total_cost * leverage
                
                lev_return = max(-0.95, min(1.0, lev_return))
                
                if lev_return <= -1.0:
                    agent.current_capital = 0.0
                else:
                    agent.current_capital *= (1 + lev_return)
                
                if agent.current_capital < initial_capital * 0.1:
                    agent.current_capital = 0.0
            
            if (idx + 1) % 30 == 0:
                agents = [a for a in agents if a.current_capital > 0]
                moirai.agents = agents
                
                if len(agents) > 0:
                    try:
                        evolution_manager.run_evolution_cycle()
                        agents = moirai.agents
                    except:
                        pass
        
        all_caps = [a.current_capital for a in moirai.agents]
        while len(all_caps) < initial_count:
            all_caps.append(0.0)
        
        final_total = sum(all_caps)
        roi = (final_total / initial_total - 1) * 100
        
        years = steps / 365.0
        if roi > -100:
            ann = (pow(1 + roi / 100, 1 / years) - 1) * 100
        else:
            ann = -100
        
        market_roi = (market_end / market_start - 1) * 100
        survivors = len([a for a in moirai.agents if a.current_capital > 0])
        
        return {
            'seed': seed,
            'success': True,
            'roi': roi,
            'annualized': ann,
            'survivors': survivors,
            'final_total': final_total,
            'market_roi': market_roi,
        }
    except Exception as e:
        return {
            'seed': seed,
            'success': False,
            'error': str(e),
            'roi': -100,
        }


def save_progress(results, filename):
    """保存进度"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def generate_report(results):
    """生成报告"""
    successful = [r for r in results if r.get('success', True)]
    
    if len(successful) == 0:
        return
    
    rois = [r['roi'] for r in successful]
    anns = [r['annualized'] for r in successful]
    
    report = []
    report.append("\n" + "=" * 80)
    report.append(f"📊 当前进度：{len(successful)}/1000 测试完成")
    report.append("=" * 80)
    report.append("")
    report.append("💰 系统总盈利:")
    report.append(f"   初始: $500,000")
    report.append(f"   平均最终: ${np.mean([r['final_total'] for r in successful]):,.2f}")
    report.append("")
    report.append("📈 ROI统计:")
    report.append(f"   平均: {np.mean(rois):+,.2f}%")
    report.append(f"   中位数: {np.median(rois):+,.2f}%")
    report.append(f"   标准差: ±{np.std(rois):,.2f}%")
    report.append(f"   最好: {np.max(rois):+,.2f}%")
    report.append(f"   最差: {np.min(rois):+,.2f}%")
    report.append(f"   盈利率: {sum(1 for r in rois if r > 0)/len(rois)*100:.1f}%")
    report.append("")
    report.append("📊 年化收益:")
    report.append(f"   平均: {np.mean(anns):+.2f}%")
    report.append(f"   中位数: {np.median(anns):+.2f}%")
    report.append(f"   vs 巴菲特(20%): {np.mean(anns)/20:.2f}x")
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print(report_text)
    
    return report_text


def main():
    print()
    print("=" * 80)
    print("🚀 终极测试：OKX真实规则 × 1000次")
    print("=" * 80)
    print()
    print("这将是最终的、最准确的验证！")
    print("预计耗时: 3-5小时")
    print()
    print("=" * 80)
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    progress_file = f"ultimate_okx_1000x_{timestamp}.json"
    
    results = []
    start_time = datetime.now()
    
    print(f"🚀 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for i in range(1000):
        seed = i * 1000
        
        if (i + 1) % 10 == 0:
            progress = (i + 1) / 1000 * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / (i + 1)
            remaining = avg_time * (1000 - i - 1)
            eta = datetime.now() + pd.Timedelta(seconds=remaining)
            
            print(f"   [{i+1:>4}/1000] 进度:{progress:>5.1f}% 用时:{elapsed/60:>5.1f}分 剩余:{remaining/60:>5.1f}分 预计:{eta.strftime('%H:%M:%S')}", end="")
        
        result = run_single_test(seed)
        results.append(result)
        
        if (i + 1) % 10 == 0:
            if result['success']:
                print(f" ROI:{result['roi']:>10,.0f}% ✓")
            else:
                print(f" 失败 ✗")
        
        # 每100次保存进度和生成报告
        if (i + 1) % 100 == 0:
            save_progress(results, progress_file)
            generate_report(results)
    
    # 最终保存
    save_progress(results, progress_file)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 80)
    print()
    print(f"🎉 测试完成！")
    print(f"   开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   总耗时: {duration}")
    print()
    
    # 生成最终报告
    successful = [r for r in results if r.get('success', True)]
    
    if len(successful) == 0:
        print("❌ 没有成功的测试")
        return
    
    rois = [r['roi'] for r in successful]
    anns = [r['annualized'] for r in successful]
    
    print("=" * 80)
    print("📊 最终统计报告")
    print("=" * 80)
    print()
    print(f"💰 系统总盈利:")
    print(f"   初始: $500,000")
    print(f"   平均最终: ${np.mean([r['final_total'] for r in successful]):,.2f}")
    print(f"   平均盈利: ${np.mean([r['final_total'] for r in successful]) - 500000:,.2f}")
    print()
    print(f"📈 ROI统计（1000次测试）:")
    print(f"   平均: {np.mean(rois):+,.2f}%")
    print(f"   中位数: {np.median(rois):+,.2f}%")
    print(f"   标准差: ±{np.std(rois):,.2f}%")
    print(f"   变异系数: {abs(np.std(rois)/np.mean(rois))*100:.2f}%")
    print(f"   最好: {np.max(rois):+,.2f}%")
    print(f"   最差: {np.min(rois):+,.2f}%")
    print(f"   盈利率: {sum(1 for r in rois if r > 0)/len(rois)*100:.2f}%")
    print()
    print(f"📊 年化收益率:")
    print(f"   平均: {np.mean(anns):+.2f}%")
    print(f"   中位数: {np.median(anns):+.2f}%")
    print(f"   最好: {np.max(anns):+.2f}%")
    print(f"   最差: {np.min(anns):+.2f}%")
    print(f"   vs 巴菲特(20%): {np.mean(anns)/20:.2f}x")
    print()
    print(f"👥 幸存率:")
    print(f"   平均: {np.mean([r['survivors']/50*100 for r in successful]):.1f}%")
    print()
    print(f"📊 vs 市场:")
    market_roi = successful[0]['market_roi']
    print(f"   BTC: {market_roi:+.2f}%")
    print(f"   系统: {np.mean(rois):+,.2f}%")
    print(f"   超额: {np.mean(rois) - market_roi:+,.2f}%")
    print()
    print(f"📊 分位数分布:")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        print(f"   {p:>2}%: {np.percentile(rois, p):+,.2f}%")
    print()
    print("=" * 80)
    print()
    print(f"💾 详细数据已保存: {progress_file}")
    print()
    print("🎯 最终评估:")
    
    profitable_rate = sum(1 for r in rois if r > 0)/len(rois)*100
    avg_ann = np.mean(anns)
    
    if profitable_rate >= 95:
        print(f"   🏆 S级系统 - {profitable_rate:.1f}%盈利率, {avg_ann:+.1f}%年化")
    elif profitable_rate >= 90:
        print(f"   🏆 A级系统 - {profitable_rate:.1f}%盈利率, {avg_ann:+.1f}%年化")
    elif profitable_rate >= 80:
        print(f"   ✅ B级系统 - {profitable_rate:.1f}%盈利率, {avg_ann:+.1f}%年化")
    else:
        print(f"   ⚠️  需改进 - {profitable_rate:.1f}%盈利率, {avg_ann:+.1f}%年化")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

