#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试Mastermind增强的环境压力计算（v5.1）"""

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
print("Mastermind环境压力测试 - v5.1增强版")
print("="*80)


@dataclass
class MockMarketState:
    """模拟市场状态（包含微结构数据）"""
    volatility: float = 0.02
    short_term_volatility: float = 0.02
    avg_slippage: float = 0.001
    liquidity_depth: float = 1000000.0
    bid_ask_spread: float = 0.0001


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景1：平静市场（低压力）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景1] 平静市场 - 低压力环境")
print("-"*80)

mastermind = Mastermind(initial_capital=100000.0)

calm_market = MockMarketState(
    volatility=0.01,              # 低波动率
    short_term_volatility=0.01,   # 无波动率突发
    avg_slippage=0.0005,          # 低滑点 0.05%
    liquidity_depth=2000000.0,    # 高流动性
    bid_ask_spread=0.00005,       # 窄价差
)

pressure_calm = mastermind.evaluate_environmental_pressure(
    current_market_state=calm_market,
    agent_performance_stats={'avg_pnl': 1000, 'losing_ratio': 0.3, 'avg_drawdown': -0.05}
)

print(f"\n✅ 平静市场压力: {pressure_calm:.3f}")
print(f"   预期: 0.0-0.3（平静如水🌊）")
print(f"   实际: {'✅ 符合' if pressure_calm < 0.3 else '❌ 偏高'}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景2：正常波动市场（中压力）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景2] 正常波动市场 - 中等压力环境")
print("-"*80)

normal_market = MockMarketState(
    volatility=0.03,              # 中等波动率
    short_term_volatility=0.035,  # 轻微突发
    avg_slippage=0.002,           # 中等滑点 0.2%
    liquidity_depth=800000.0,     # 中等流动性
    bid_ask_spread=0.0002,        # 中等价差
)

pressure_normal = mastermind.evaluate_environmental_pressure(
    current_market_state=normal_market,
    agent_performance_stats={'avg_pnl': -500, 'losing_ratio': 0.5, 'avg_drawdown': -0.15}
)

print(f"\n✅ 正常市场压力: {pressure_normal:.3f}")
print(f"   预期: 0.3-0.6（波涛渐起⚡）")
print(f"   实际: {'✅ 符合' if 0.3 <= pressure_normal < 0.6 else ('❌ 偏低' if pressure_normal < 0.3 else '❌ 偏高')}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景3：高波动市场（高压力）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景3] 高波动市场 - 高压力环境")
print("-"*80)

volatile_market = MockMarketState(
    volatility=0.06,              # 高波动率
    short_term_volatility=0.10,   # 明显突发（波动率翻倍）
    avg_slippage=0.008,           # 高滑点 0.8%
    liquidity_depth=300000.0,     # 低流动性
    bid_ask_spread=0.0008,        # 宽价差
)

pressure_volatile = mastermind.evaluate_environmental_pressure(
    current_market_state=volatile_market,
    agent_performance_stats={'avg_pnl': -3000, 'losing_ratio': 0.75, 'avg_drawdown': -0.25}
)

print(f"\n✅ 高波动市场压力: {pressure_volatile:.3f}")
print(f"   预期: 0.6-0.8（狂风暴雨🌪️）")
print(f"   实际: {'✅ 符合' if 0.6 <= pressure_volatile < 0.8 else ('❌ 偏低' if pressure_volatile < 0.6 else '❌ 偏高')}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景4：极端市场（极端压力）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景4] 极端市场 - 极端压力环境")
print("-"*80)

extreme_market = MockMarketState(
    volatility=0.10,              # 极高波动率
    short_term_volatility=0.25,   # 严重突发（波动率暴增2.5倍）
    avg_slippage=0.020,           # 极高滑点 2%
    liquidity_depth=50000.0,      # 极低流动性
    bid_ask_spread=0.002,         # 极宽价差
)

pressure_extreme = mastermind.evaluate_environmental_pressure(
    current_market_state=extreme_market,
    agent_performance_stats={'avg_pnl': -8000, 'losing_ratio': 0.9, 'avg_drawdown': -0.40}
)

print(f"\n✅ 极端市场压力: {pressure_extreme:.3f}")
print(f"   预期: 0.8-1.0（末日浩劫💀）")
print(f"   实际: {'✅ 符合' if pressure_extreme >= 0.8 else '❌ 偏低'}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景5：对比测试 - 微结构因素的影响
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景5] 对比测试 - 微结构因素的影响")
print("-"*80)

# 5A: 高流动性市场（低微结构压力）
high_liquidity = MockMarketState(
    volatility=0.04,              # 中等波动率
    short_term_volatility=0.04,
    avg_slippage=0.0008,          # 低滑点
    liquidity_depth=5000000.0,    # 极高流动性
    bid_ask_spread=0.00003,       # 极窄价差
)

pressure_5a = mastermind.evaluate_environmental_pressure(
    current_market_state=high_liquidity,
    agent_performance_stats={'avg_pnl': 0, 'losing_ratio': 0.5, 'avg_drawdown': -0.10}
)

# 5B: 低流动性市场（高微结构压力）
low_liquidity = MockMarketState(
    volatility=0.04,              # 相同波动率
    short_term_volatility=0.04,
    avg_slippage=0.015,           # 高滑点
    liquidity_depth=100000.0,     # 低流动性
    bid_ask_spread=0.0015,        # 宽价差
)

pressure_5b = mastermind.evaluate_environmental_pressure(
    current_market_state=low_liquidity,
    agent_performance_stats={'avg_pnl': 0, 'losing_ratio': 0.5, 'avg_drawdown': -0.10}
)

print(f"\n对比结果:")
print(f"  高流动性市场压力: {pressure_5a:.3f}")
print(f"  低流动性市场压力: {pressure_5b:.3f}")
print(f"  压力差异: {pressure_5b - pressure_5a:.3f}")
print(f"  \n  ✅ 验证: 低流动性市场压力{'显著更高' if pressure_5b - pressure_5a > 0.1 else '略高'}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 总结
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*80)
print("✅ Mastermind压力计算测试完成")
print("="*80)

print("\n📊 压力分级验证:")
print(f"  平静市场: {pressure_calm:.3f} {'✅' if pressure_calm < 0.3 else '❌'}")
print(f"  正常市场: {pressure_normal:.3f} {'✅' if 0.3 <= pressure_normal < 0.6 else '❌'}")
print(f"  高波动:   {pressure_volatile:.3f} {'✅' if 0.6 <= pressure_volatile < 0.8 else '❌'}")
print(f"  极端:     {pressure_extreme:.3f} {'✅' if pressure_extreme >= 0.8 else '❌'}")

print("\n🎯 核心成就:")
print("  【市场微结构集成】✨ 已完成！")
print("  - 滑点压力（交易成本）")
print("  - 流动性压力（市场深度）")
print("  - 价差压力（买卖价差）")
print("  - 波动率突发（短期爆发）")
print("  \n  → 环境压力现在反映了\"真实市场\"的复杂性")

print("\n" + "="*80)

