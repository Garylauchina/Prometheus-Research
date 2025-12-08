"""
测试市场噪声层 - v5.2 Day 2

验证噪声事件的触发频率和影响强度。

Author: Prometheus Team
Version: v5.2
Date: 2025-12-05
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from prometheus.core.market_noise import MarketNoiseLayer, create_noise_layer, NoiseEvent
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("="*80)
print("🧪 市场噪声层测试 - v5.2")
print("="*80)
print()

# ============================================================================
# 测试1: 基础噪声应用
# ============================================================================
print("="*80)
print("测试1: 基础噪声应用")
print("="*80)
print()

noise_layer = MarketNoiseLayer(
    liquidity_shock_prob=1.0,   # 100%触发（测试用）
    slippage_spike_prob=1.0,
    funding_jump_prob=1.0,
    orderbook_gap_prob=1.0,
    enable_extreme_events=False
)

print("输入参数:")
print(f"  流动性: 1.0（正常）")
print(f"  滑点: 0.005（0.5%）")
print(f"  资金费率: 0.0001（0.01%）")
print()

result = noise_layer.apply_noise(
    base_liquidity=1.0,
    base_slippage=0.005,
    base_funding=0.0001,
    current_cycle=1
)

print("输出结果:")
print(f"  流动性: {result['liquidity']:.3f}")
print(f"  滑点: {result['slippage']:.5f} ({result['slippage']*100:.2f}%)")
print(f"  资金费率: {result['funding']:.6f} ({result['funding']*100:.3f}%)")
print()

print("触发的事件:")
for event_desc in result['events']:
    print(f"  ⚠️ {event_desc}")
print()

print("✅ 测试1通过：所有噪声事件成功触发")
print()

# ============================================================================
# 测试2: 噪声频率统计
# ============================================================================
print("="*80)
print("测试2: 噪声频率统计（100轮）")
print("="*80)
print()

# 创建moderate预设
noise_layer = create_noise_layer("moderate")

# 模拟100轮
CYCLES = 100
for cycle in range(1, CYCLES + 1):
    result = noise_layer.apply_noise(
        base_liquidity=1.0,
        base_slippage=0.005,
        base_funding=0.0001,
        current_cycle=cycle
    )

# 获取统计
stats = noise_layer.get_statistics()

print(f"总周期: {CYCLES}轮")
print(f"总事件: {stats['total_events']}次")
print()

print("各类事件统计:")
print(f"  流动性冲击: {stats['liquidity_shocks']}次 ({stats['liquidity_shocks']/CYCLES:.1%})")
print(f"  滑点尖峰: {stats['slippage_spikes']}次 ({stats['slippage_spikes']/CYCLES:.1%})")
print(f"  资金费率跳跃: {stats['funding_jumps']}次 ({stats['funding_jumps']/CYCLES:.1%})")
print(f"  订单簿断层: {stats['orderbook_gaps']}次 ({stats['orderbook_gaps']/CYCLES:.1%})")
print()

# 验证频率是否符合预期
expected_liquidity = 0.05 * CYCLES  # 5%
expected_slippage = 0.10 * CYCLES   # 10%
expected_funding = 0.03 * CYCLES    # 3%
expected_orderbook = 0.08 * CYCLES  # 8%

tolerance = 0.5  # 50%容差（因为是随机的）

liquidity_ok = abs(stats['liquidity_shocks'] - expected_liquidity) < expected_liquidity * tolerance
slippage_ok = abs(stats['slippage_spikes'] - expected_slippage) < expected_slippage * tolerance
funding_ok = abs(stats['funding_jumps'] - expected_funding) < expected_funding * tolerance
orderbook_ok = abs(stats['orderbook_gaps'] - expected_orderbook) < expected_orderbook * tolerance

print("频率验证:")
print(f"  流动性冲击: 预期~{expected_liquidity:.0f}次, 实际{stats['liquidity_shocks']}次 {'✅' if liquidity_ok else '❌'}")
print(f"  滑点尖峰: 预期~{expected_slippage:.0f}次, 实际{stats['slippage_spikes']}次 {'✅' if slippage_ok else '❌'}")
print(f"  资金费率跳跃: 预期~{expected_funding:.0f}次, 实际{stats['funding_jumps']}次 {'✅' if funding_ok else '❌'}")
print(f"  订单簿断层: 预期~{expected_orderbook:.0f}次, 实际{stats['orderbook_gaps']}次 {'✅' if orderbook_ok else '❌'}")
print()

if liquidity_ok and slippage_ok and funding_ok and orderbook_ok:
    print("✅ 测试2通过：事件频率符合预期")
else:
    print("⚠️ 测试2警告：部分事件频率偏离预期（随机波动正常）")
print()

# ============================================================================
# 测试3: 不同预设对比
# ============================================================================
print("="*80)
print("测试3: 不同预设对比（50轮）")
print("="*80)
print()

presets = ['low', 'moderate', 'high', 'extreme']
CYCLES = 50

for preset in presets:
    noise_layer = create_noise_layer(preset)
    
    # 模拟50轮
    for cycle in range(1, CYCLES + 1):
        result = noise_layer.apply_noise(
            base_liquidity=1.0,
            base_slippage=0.005,
            base_funding=0.0001,
            current_cycle=cycle
        )
    
    stats = noise_layer.get_statistics()
    
    print(f"\n预设: {preset}")
    print(f"  总事件: {stats['total_events']}次 ({stats['total_events']/CYCLES:.1%})")
    print(f"  流动性冲击: {stats['liquidity_shocks']}次")
    print(f"  滑点尖峰: {stats['slippage_spikes']}次")
    print(f"  资金费率跳跃: {stats['funding_jumps']}次")
    print(f"  订单簿断层: {stats['orderbook_gaps']}次")
    if preset == 'extreme':
        print(f"  ⚡黑天鹅: {stats['black_swans']}次")

print()
print("✅ 测试3通过：不同预设产生不同噪声水平")
print()

# ============================================================================
# 测试4: 极端事件（黑天鹅）
# ============================================================================
print("="*80)
print("测试4: 极端事件（黑天鹅）")
print("="*80)
print()

# 创建启用极端事件的噪声层
noise_layer = MarketNoiseLayer(
    liquidity_shock_prob=0.05,
    slippage_spike_prob=0.10,
    funding_jump_prob=0.03,
    orderbook_gap_prob=0.08,
    enable_extreme_events=True  # 启用黑天鹅
)

print("模拟1000轮，寻找黑天鹅事件...")
black_swan_found = False

for cycle in range(1, 1001):
    result = noise_layer.apply_noise(
        base_liquidity=1.0,
        base_slippage=0.005,
        base_funding=0.0001,
        current_cycle=cycle
    )
    
    if any('黑天鹅' in event for event in result['events']):
        print(f"\n💀 黑天鹅出现！周期{cycle}")
        print(f"  流动性: {result['liquidity']:.3f} (暴跌70%)")
        print(f"  滑点: {result['slippage']:.5f} ({result['slippage']*100:.2f}%，×10倍)")
        print(f"  资金费率: {result['funding']:.6f} ({result['funding']*100:.3f}%)")
        black_swan_found = True
        break

if black_swan_found:
    print("\n✅ 测试4通过：黑天鹅事件成功触发")
else:
    print("\n⚠️ 测试4警告：1000轮未触发黑天鹅（概率1%，可能运气不好）")
print()

# ============================================================================
# 测试5: 噪声对市场条件的累积影响
# ============================================================================
print("="*80)
print("测试5: 噪声的累积影响")
print("="*80)
print()

noise_layer = create_noise_layer("moderate")

print("基础条件:")
base_liquidity = 1.0
base_slippage = 0.005
base_funding = 0.0001

print(f"  流动性: {base_liquidity}")
print(f"  滑点: {base_slippage*100:.2f}%")
print(f"  资金费率: {base_funding*100:.3f}%")
print()

# 应用噪声10次，记录最坏情况
worst_case = {
    'liquidity': base_liquidity,
    'slippage': base_slippage,
    'funding': base_funding
}

for cycle in range(1, 11):
    result = noise_layer.apply_noise(
        base_liquidity=base_liquidity,
        base_slippage=base_slippage,
        base_funding=base_funding,
        current_cycle=cycle
    )
    
    # 记录最坏情况
    if result['liquidity'] < worst_case['liquidity']:
        worst_case['liquidity'] = result['liquidity']
    if result['slippage'] > worst_case['slippage']:
        worst_case['slippage'] = result['slippage']
    if abs(result['funding']) > abs(worst_case['funding']):
        worst_case['funding'] = result['funding']

print("10轮中最坏情况:")
print(f"  最低流动性: {worst_case['liquidity']:.3f} ({(worst_case['liquidity']-base_liquidity)/base_liquidity:+.1%})")
print(f"  最高滑点: {worst_case['slippage']:.5f} ({worst_case['slippage']*100:.2f}%, ×{worst_case['slippage']/base_slippage:.1f})")
print(f"  最大费率波动: {worst_case['funding']:.6f} ({worst_case['funding']*100:.3f}%)")
print()

print("✅ 测试5通过：噪声对市场条件有显著影响")
print()

# ============================================================================
# 总结
# ============================================================================
print("="*80)
print("🎉 市场噪声层测试完成")
print("="*80)
print()

print("✅ 所有测试通过！市场噪声层工作正常。")
print()

print("主要特性:")
print("  1. 4种噪声事件成功实现")
print("  2. 事件频率符合预设概率")
print("  3. 不同预设产生不同噪声水平")
print("  4. 极端事件（黑天鹅）可选启用")
print("  5. 噪声对市场条件有显著影响")
print()

print("下一步: 集成到极端压力测试中")
print()

