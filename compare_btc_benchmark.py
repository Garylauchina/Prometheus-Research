#!/usr/bin/env python3
"""
BTC基准对比分析
==================

对比系统收益 vs BTC买入持有策略
验证系统是否真的跑赢大盘
"""

import pandas as pd
import json
from pathlib import Path


def calculate_btc_benchmark(cycles=500):
    """计算BTC买入持有基准收益"""
    print("=" * 80)
    print("📊 BTC基准计算")
    print("=" * 80)
    print()
    
    # 加载数据
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    prices = df['close'].tolist()
    
    # Phase 1使用的价格范围
    start_price = prices[0]
    end_price = prices[min(cycles - 1, len(prices) - 1)]
    
    btc_return = (end_price - start_price) / start_price * 100
    
    print(f"📈 BTC价格变化:")
    print(f"   起始价格: ${start_price:,.2f}")
    print(f"   结束价格: ${end_price:,.2f}")
    print(f"   价格变化: {end_price - start_price:+,.2f}")
    print(f"   BTC收益率: {btc_return:+.2f}%")
    print()
    
    return btc_return, start_price, end_price


def compare_with_system():
    """对比系统收益与BTC基准"""
    print("=" * 80)
    print("🎯 系统 vs BTC 对比")
    print("=" * 80)
    print()
    
    # 读取Phase 1结果
    result_file = Path("results/phase1_training_20251208_041431.json")
    if not result_file.exists():
        print("❌ 找不到Phase 1结果文件")
        return
    
    with open(result_file, 'r') as f:
        phase1_result = json.load(f)
    
    system_return = phase1_result['result']['system_return']
    
    # 计算BTC基准
    btc_return, start_price, end_price = calculate_btc_benchmark(
        cycles=phase1_result['config']['cycles']
    )
    
    # 对比
    print("=" * 80)
    print("📊 收益对比")
    print("=" * 80)
    print()
    print(f"{'策略':<20} {'收益率':<15} {'初始资金':<15} {'最终资金':<15}")
    print("-" * 80)
    
    # BTC买入持有
    initial_capital = 500000  # 50个Agent × $10,000
    btc_final = initial_capital * (1 + btc_return / 100)
    print(f"{'BTC买入持有':<20} {btc_return:>+13.2f}%  ${initial_capital:>13,.0f}  ${btc_final:>13,.0f}")
    
    # Prometheus系统
    system_final = initial_capital * (1 + system_return / 100)
    print(f"{'Prometheus系统':<20} {system_return:>+13.2f}%  ${initial_capital:>13,.0f}  ${system_final:>13,.0f}")
    
    # 差异
    alpha = system_return - btc_return
    alpha_value = system_final - btc_final
    
    print("-" * 80)
    print(f"{'Alpha超额收益':<20} {alpha:>+13.2f}%  {'':>13}  ${alpha_value:>+13,.0f}")
    print()
    
    # 判定
    print("=" * 80)
    print("🎯 结论")
    print("=" * 80)
    print()
    
    if alpha > 10:
        print(f"🎉 系统显著跑赢BTC！超额收益 {alpha:+.2f}%")
        print(f"   相当于在BTC基础上额外赚了 ${alpha_value:,.0f}")
        print()
        print("✅ 评级: 优秀")
        print("💡 建议: 立即开始Phase 2大规模验证")
    elif alpha > 0:
        print(f"✅ 系统小幅跑赢BTC，超额收益 {alpha:+.2f}%")
        print(f"   相当于在BTC基础上额外赚了 ${alpha_value:,.0f}")
        print()
        print("⚠️ 评级: 良好")
        print("💡 建议: 需要Phase 2验证稳定性")
    elif alpha > -5:
        print(f"⚠️ 系统略微跑输BTC，差距 {alpha:.2f}%")
        print(f"   相当于比BTC少赚了 ${-alpha_value:,.0f}")
        print()
        print("⚠️ 评级: 一般")
        print("💡 建议: 需要优化参数或增加训练周期")
    else:
        print(f"❌ 系统显著跑输BTC，差距 {alpha:.2f}%")
        print(f"   相当于比BTC少赚了 ${-alpha_value:,.0f}")
        print()
        print("❌ 评级: 不及格")
        print("💡 建议: 需要重新审视策略设计")
    
    print()
    
    # 保存对比结果
    comparison_result = {
        "btc_benchmark": {
            "return_pct": btc_return,
            "start_price": start_price,
            "end_price": end_price,
            "initial_capital": initial_capital,
            "final_capital": btc_final
        },
        "prometheus_system": {
            "return_pct": system_return,
            "initial_capital": initial_capital,
            "final_capital": system_final
        },
        "alpha": {
            "return_pct": alpha,
            "value": alpha_value
        },
        "conclusion": "outperform" if alpha > 0 else "underperform"
    }
    
    output_file = Path("results/btc_benchmark_comparison.json")
    with open(output_file, 'w') as f:
        json.dump(comparison_result, f, indent=2)
    
    print(f"💾 对比结果已保存: {output_file}")
    print()
    
    return comparison_result


def analyze_trading_behavior():
    """分析系统的交易行为"""
    print("=" * 80)
    print("🔍 交易行为分析")
    print("=" * 80)
    print()
    
    # 读取Phase 1结果
    result_file = Path("results/phase1_training_20251208_041431.json")
    with open(result_file, 'r') as f:
        phase1_result = json.load(f)
    
    total_trades = phase1_result['result']['total_trades']
    avg_trades = phase1_result['result']['avg_trades_per_agent']
    cycles = phase1_result['config']['cycles']
    
    print(f"总交易数: {total_trades}笔")
    print(f"人均交易: {avg_trades:.1f}笔")
    print(f"总周期数: {cycles}个")
    print(f"交易频率: {total_trades/cycles:.3f}笔/周期")
    print()
    
    if avg_trades < 1:
        print("📊 交易模式: **超低频交易**")
        print("   系统学会了'买入并长期持有'策略")
        print("   这与BTC买入持有策略非常相似")
        print()
        print("💡 洞察:")
        print("   - 系统发现在牛市中，最优策略就是持有")
        print("   - 极低的交易频率降低了交易成本")
        print("   - 如果系统跑赢BTC，说明有更好的择时能力")
    elif avg_trades < 5:
        print("📊 交易模式: **低频交易**")
        print("   系统采用了波段操作策略")
    else:
        print("📊 交易模式: **高频交易**")
        print("   系统采用了频繁进出场策略")
    
    print()


if __name__ == "__main__":
    print()
    print("🔬 Prometheus vs BTC 基准对比分析")
    print("=" * 80)
    print()
    
    # 分析交易行为
    analyze_trading_behavior()
    
    # 对比收益
    comparison_result = compare_with_system()
    
    print()
    print("=" * 80)
    print("分析完成！")
    print("=" * 80)

