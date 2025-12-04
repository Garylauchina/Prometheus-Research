#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试滑点模型"""

import sys
sys.path.insert(0, '.')

from prometheus.core.slippage_model import (
    SlippageModel, RealisticSlippageModel, LowSlippageModel,
    OrderSide, OrderType, MarketCondition, create_slippage_model
)

print("="*70)
print("滑点模型测试")
print("="*70)

# 1. 创建市场条件
market = MarketCondition(
    price=90000.0,           # BTC价格 $90,000
    volume=50000000,         # 成交量 $50M
    volatility=0.03,         # 波动率 3%
    liquidity_depth=5000000, # 流动性深度 $5M
    spread=0.0002            # 价差 0.02%
)

print(f"\n市场条件:")
print(f"  价格: ${market.price:,.2f}")
print(f"  波动率: {market.volatility:.2%}")
print(f"  流动性: ${market.liquidity_depth:,.0f}")
print(f"  价差: {market.spread:.4%}")

# 2. 测试不同模型
models = {
    "真实市场": RealisticSlippageModel(),
    "低滑点": LowSlippageModel(),
    "基础模型": SlippageModel(),
}

# 3. 测试不同订单大小
order_sizes = [1000, 5000, 10000, 50000, 100000]  # USD

print("\n" + "="*70)
print("测试：不同订单规模的滑点（市价买单）")
print("="*70)

for model_name, model in models.items():
    print(f"\n【{model_name}】")
    print(f"{'订单金额':>12} | {'滑点率':>8} | {'预期价格':>12} | {'实际价格':>12} | {'滑点损失':>10}")
    print("-" * 70)
    
    for size in order_sizes:
        result = model.calculate_slippage(
            OrderSide.BUY,
            size,
            OrderType.MARKET,
            market
        )
        
        print(
            f"${size:>10,.0f} | "
            f"{result.slippage_rate:>7.3%} | "
            f"${result.expected_price:>10,.2f} | "
            f"${result.actual_price:>10,.2f} | "
            f"${result.slippage_amount:>8,.2f}"
        )

# 4. 测试往返成本
print("\n" + "="*70)
print("测试：交易往返成本（买入 + 卖出）")
print("="*70)

order_size = 10000  # $10,000

for model_name, model in models.items():
    cost = model.estimate_execution_cost(order_size, market, OrderType.MARKET)
    print(f"\n【{model_name}】订单 ${order_size:,.0f}")
    print(f"  买入成本: ${cost['buy_cost']:.2f}")
    print(f"  卖出成本: ${cost['sell_cost']:.2f}")
    print(f"  往返成本: ${cost['round_trip']:.2f} ({cost['round_trip_rate']:.3%})")

# 5. 测试市价单 vs 限价单
print("\n" + "="*70)
print("测试：市价单 vs 限价单")
print("="*70)

model = RealisticSlippageModel()
order_size = 10000

for order_type in [OrderType.MARKET, OrderType.LIMIT]:
    result = model.calculate_slippage(
        OrderSide.BUY,
        order_size,
        order_type,
        market
    )
    
    print(f"\n{order_type.value.upper()} 订单 ${order_size:,.0f}:")
    print(f"  滑点率: {result.slippage_rate:.3%}")
    print(f"  实际价格: ${result.actual_price:,.2f}")
    print(f"  滑点损失: ${result.slippage_amount:.2f}")

# 6. 滑点来源分析
print("\n" + "="*70)
print("滑点来源分析")
print("="*70)

model = RealisticSlippageModel()
result = model.calculate_slippage(
    OrderSide.BUY,
    50000,  # $50k大单
    OrderType.MARKET,
    market
)

print(f"\n订单: ${50000:,.0f} 市价买单")
print(f"总滑点率: {result.slippage_rate:.3%}")
print(f"\n滑点来源:")
for source, value in result.breakdown.items():
    if isinstance(value, float):
        print(f"  {source:20s}: {value:>7.4%}")

print("\n" + "="*70)
print("✅ 滑点模型测试完成")
print("="*70)

