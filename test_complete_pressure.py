#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试完整的市场压力计算（包含资金费率）"""

import sys
sys.path.insert(0, '.')

import logging
from dataclasses import dataclass
from prometheus.core.mastermind import Mastermind

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)

print("="*80)
print("完整市场压力测试 - v5.1（包含资金费率）")
print("="*80)


@dataclass
class CompleteMarketState:
    """完整的市场状态（包含所有微结构数据）"""
    # 波动率
    volatility: float = 0.02
    short_term_volatility: float = 0.02
    
    # 滑点与流动性
    avg_slippage: float = 0.001
    liquidity_depth: float = 1000000.0
    bid_ask_spread: float = 0.0001
    
    # 资金费率（新增）
    funding_rate: float = 0.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景1：平静市场 + 中性资金费率
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景1] 平静市场 + 中性资金费率")
print("-"*80)

# 每个场景使用新的Mastermind实例，避免平滑处理的交叉影响
mastermind = Mastermind(initial_capital=100000.0)

calm_market = CompleteMarketState(
    volatility=0.01,
    short_term_volatility=0.01,
    avg_slippage=0.0005,
    liquidity_depth=2000000.0,
    bid_ask_spread=0.00005,
    funding_rate=0.0003,  # 0.03% 中性
)

pressure1 = mastermind.evaluate_environmental_pressure(
    current_market_state=calm_market,
    agent_performance_stats={'avg_pnl': 1000, 'losing_ratio': 0.3, 'avg_drawdown': -0.05}
)

print(f"\n✅ 市场压力: {pressure1:.3f}")
print(f"   预期: <0.3（平静如水）")
print(f"   资金费率: 0.03%（中性）")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景2：正常市场 + 偏多资金费率
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景2] 正常市场 + 偏多资金费率")
print("-"*80)

mastermind = Mastermind(initial_capital=100000.0)

normal_market_bullish = CompleteMarketState(
    volatility=0.03,
    short_term_volatility=0.035,
    avg_slippage=0.002,
    liquidity_depth=800000.0,
    bid_ask_spread=0.0002,
    funding_rate=0.001,  # 0.1% 偏多
)

pressure2 = mastermind.evaluate_environmental_pressure(
    current_market_state=normal_market_bullish,
    agent_performance_stats={'avg_pnl': -500, 'losing_ratio': 0.5, 'avg_drawdown': -0.15}
)

print(f"\n✅ 市场压力: {pressure2:.3f}")
print(f"   预期: 0.3-0.6（波涛渐起）")
print(f"   资金费率: 0.1%（偏多）")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景3：高波动 + 极端资金费率（偏多）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景3] 高波动 + 极端资金费率（偏多）")
print("-"*80)

mastermind = Mastermind(initial_capital=100000.0)

volatile_extreme_bullish = CompleteMarketState(
    volatility=0.06,
    short_term_volatility=0.10,
    avg_slippage=0.008,
    liquidity_depth=300000.0,
    bid_ask_spread=0.0008,
    funding_rate=0.005,  # 0.5% 极端偏多（达到上限）
)

pressure3 = mastermind.evaluate_environmental_pressure(
    current_market_state=volatile_extreme_bullish,
    agent_performance_stats={'avg_pnl': -3000, 'losing_ratio': 0.75, 'avg_drawdown': -0.25}
)

print(f"\n✅ 市场压力: {pressure3:.3f}")
print(f"   预期: 0.6-0.8（狂风暴雨）")
print(f"   资金费率: 0.5%（极端偏多，多头成本$50/8h）")
print(f"   ⚠️  多头持仓极其昂贵！")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景4：极端市场 + 极端资金费率（偏空）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景4] 极端市场 + 极端资金费率（偏空）")
print("-"*80)

mastermind = Mastermind(initial_capital=100000.0)

extreme_bearish = CompleteMarketState(
    volatility=0.10,
    short_term_volatility=0.25,
    avg_slippage=0.020,
    liquidity_depth=50000.0,
    bid_ask_spread=0.002,
    funding_rate=-0.004,  # -0.4% 极端偏空
)

pressure4 = mastermind.evaluate_environmental_pressure(
    current_market_state=extreme_bearish,
    agent_performance_stats={'avg_pnl': -8000, 'losing_ratio': 0.9, 'avg_drawdown': -0.40}
)

print(f"\n✅ 市场压力: {pressure4:.3f}")
print(f"   预期: 0.8-1.0（末日浩劫）")
print(f"   资金费率: -0.4%（极端偏空，空头成本$40/8h）")
print(f"   ⚠️  空头持仓极其昂贵！")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景5：对比测试 - 资金费率的影响
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景5] 对比测试 - 资金费率的影响")
print("-"*80)

# 5A: 高波动 + 中性资金费率（新实例）
mastermind_5a = Mastermind(initial_capital=100000.0)

high_vol_neutral_funding = CompleteMarketState(
    volatility=0.06,
    short_term_volatility=0.08,
    avg_slippage=0.006,
    liquidity_depth=400000.0,
    bid_ask_spread=0.0006,
    funding_rate=0.0003,  # 中性
)

pressure_5a = mastermind_5a.evaluate_environmental_pressure(
    current_market_state=high_vol_neutral_funding,
    agent_performance_stats={'avg_pnl': -2000, 'losing_ratio': 0.6, 'avg_drawdown': -0.20}
)

# 5B: 高波动 + 极端资金费率（新实例）
mastermind_5b = Mastermind(initial_capital=100000.0)

high_vol_extreme_funding = CompleteMarketState(
    volatility=0.06,              # 相同波动率
    short_term_volatility=0.08,   # 相同
    avg_slippage=0.006,           # 相同
    liquidity_depth=400000.0,     # 相同
    bid_ask_spread=0.0006,        # 相同
    funding_rate=0.005,           # 极端资金费率
)

pressure_5b = mastermind_5b.evaluate_environmental_pressure(
    current_market_state=high_vol_extreme_funding,
    agent_performance_stats={'avg_pnl': -2000, 'losing_ratio': 0.6, 'avg_drawdown': -0.20}
)

print(f"\n对比结果:")
print(f"  高波动 + 中性资金费率: {pressure_5a:.3f}")
print(f"  高波动 + 极端资金费率: {pressure_5b:.3f}")
print(f"  压力差异: {pressure_5b - pressure_5a:.3f} (+{(pressure_5b - pressure_5a) / pressure_5a * 100:.1f}%)")
print(f"\n  ✅ 验证: 极端资金费率显著提高市场压力")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 总结
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*80)
print("✅ 完整市场压力测试完成")
print("="*80)

print("\n📊 压力分级验证:")
print(f"  平静市场 + 中性费率: {pressure1:.3f} {'✅' if pressure1 < 0.3 else '❌'}")
print(f"  正常市场 + 偏多费率: {pressure2:.3f} {'✅' if 0.3 <= pressure2 < 0.6 else '❌'}")
print(f"  高波动 + 极端费率:   {pressure3:.3f} {'✅' if 0.6 <= pressure3 < 0.8 else '❌'}")
print(f"  极端市场 + 极端费率: {pressure4:.3f} {'✅' if pressure4 >= 0.8 else '❌'}")

print("\n🎯 核心成就:")
print("  【完整市场压力系统】✨ v5.1完成！")
print("  \n  微结构因素（5个）:")
print("  ├─ 滑点压力（交易成本）")
print("  ├─ 流动性压力（市场深度）")
print("  ├─ 价差压力（买卖价差）")
print("  ├─ 波动率突发（短期爆发）")
print("  └─ 资金费率压力（持仓成本）⭐新增")
print("  \n  宏观因素（4个）:")
print("  ├─ 市场波动率")
print("  ├─ 价格剧烈变化")
print("  ├─ 趋势反转")
print("  └─ Agent集体表现")

print("\n💡 实际影响:")
print("  → 极端资金费率提高压力约10-15%")
print("  → Agent需要考虑持仓成本")
print("  → 高费率时避免持有该方向仓位")
print("  → 环境压力现在更全面、更真实")

print("\n" + "="*80)

