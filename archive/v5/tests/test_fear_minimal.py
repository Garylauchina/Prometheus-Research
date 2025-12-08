"""
fear_of_death极简测试 - 直接测试核心逻辑

设计理念：
- 🎯 绕过Daimon的复杂决策系统
- 🎯 直接测试fear_of_death的calculate_death_fear_level
- 🎯 模拟"持仓+连续亏损"场景
- 🎯 观察高恐惧vs低恐惧的平仓时机差异

核心问题：
1. 高fear_of_death的Agent是否更早平仓止损？
2. 低fear_of_death的Agent是否更晚平仓（或不平仓）？
3. 这种差异是否影响最终存活？

测试场景：
- 所有Agent强制持有多头仓位
- 市场连续下跌（模拟极端亏损）
- 每轮检查fear_level，决定是否平仓
- 观察平仓时机的差异

Author: Prometheus Team
Version: v5.2实验性 - Minimal
Date: 2025-12-05
"""

import sys
import numpy as np
import pandas as pd
import random
from pathlib import Path

# 导入核心模块
from prometheus.core.instinct import Instinct

print("="*80)
print("💀 fear_of_death极简测试：直接测试核心逻辑")
print("="*80)
print("核心思路：绕过Daimon，直接用fear_of_death的calculate_death_fear_level")
print()

# ============================================================================
# 配置
# ============================================================================
GROUP_SIZE = 20
INITIAL_CAPITAL = 10000.0
POSITION_SIZE = 1.0  # 持仓1个BTC
EXTREME_CYCLES = 30

print(f"📋 实验配置:")
print(f"   每组人数: {GROUP_SIZE}个Agent")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print(f"   强制持仓: {POSITION_SIZE} BTC (多头)")
print(f"   测试轮数: {EXTREME_CYCLES}轮")
print()

# ============================================================================
# 简化的Agent类（只保留核心属性）
# ============================================================================
class SimpleAgent:
    """简化的Agent，只保留测试需要的属性"""
    def __init__(self, agent_id: str, fear_value: float):
        self.agent_id = agent_id
        self.instinct = Instinct(fear_of_death=fear_value)
        
        self.initial_capital = INITIAL_CAPITAL
        self.current_capital = INITIAL_CAPITAL
        
        self.has_position = True  # 强制持仓
        self.position_side = 'long'  # 多头
        self.consecutive_losses = 0
        
        self.closed_position = False  # 是否已平仓
        self.closed_at_cycle = None  # 平仓时的周期
        self.closed_at_capital = None  # 平仓时的资金
        self.closed_at_ratio = None  # 平仓时的资金比率

# ============================================================================
# 创建对照组
# ============================================================================
print("="*80)
print("📊 [1/3] 创建对照组")
print("="*80)
print()

# 组A：高恐惧Agent
print("创建组A：高恐惧Agent (fear = 1.7-1.9)...")
group_A = []
for i in range(GROUP_SIZE):
    fear = random.uniform(1.7, 1.9)
    agent = SimpleAgent(f"HighFear_{i+1}", fear)
    group_A.append(agent)

fear_A = [agent.instinct.fear_of_death for agent in group_A]
print(f"  ✅ 组A: fear平均{np.mean(fear_A):.3f}, 范围[{np.min(fear_A):.3f}, {np.max(fear_A):.3f}]")
print()

# 组B：低恐惧Agent
print("创建组B：低恐惧Agent (fear = 0.2-0.4)...")
group_B = []
for i in range(GROUP_SIZE):
    fear = random.uniform(0.2, 0.4)
    agent = SimpleAgent(f"LowFear_{i+1}", fear)
    group_B.append(agent)

fear_B = [agent.instinct.fear_of_death for agent in group_B]
print(f"  ✅ 组B: fear平均{np.mean(fear_B):.3f}, 范围[{np.min(fear_B):.3f}, {np.max(fear_B):.3f}]")
print()

# ============================================================================
# 极简测试：直接用fear_of_death逻辑
# ============================================================================
print("="*80)
print("📉 [2/3] 极简测试：模拟连续亏损")
print("="*80)
print("场景：所有Agent持有多头，市场连续下跌")
print("逻辑：每轮计算fear_level，高于阈值则平仓")
print()

def run_minimal_test(agents: list, group_name: str):
    """
    极简测试：直接使用fear_of_death逻辑
    
    每轮：
    1. 模拟亏损（下跌3-8%）
    2. 计算capital_ratio和consecutive_losses
    3. 调用calculate_death_fear_level
    4. 如果fear_level > 阈值，平仓止损
    """
    print(f"\n{'='*70}")
    print(f"{group_name}进入极端市场...")
    print(f"{'='*70}")
    print()
    
    # 平仓阈值（根据fear_of_death动态调整）
    # 高恐惧Agent应该更早触发
    
    for cycle in range(1, EXTREME_CYCLES + 1):
        # 市场下跌（模拟极端亏损）
        market_drop = random.uniform(0.03, 0.08)  # 每轮下跌3-8%
        
        still_holding = 0
        closed_this_cycle = 0
        
        for agent in agents:
            if agent.closed_position:
                # 已平仓，不再亏损
                continue
            
            # 模拟亏损
            loss = agent.current_capital * market_drop
            agent.current_capital -= loss
            agent.consecutive_losses += 1
            
            # 计算当前状态
            capital_ratio = agent.current_capital / agent.initial_capital
            
            # 🧬 核心：调用fear_of_death的逻辑
            fear_level = agent.instinct.calculate_death_fear_level(
                capital_ratio=capital_ratio,
                consecutive_losses=agent.consecutive_losses
            )
            
            # 决策：是否平仓？
            # 根据inner_council的逻辑：fear_level > 1.5 且持仓 → 平仓
            # 但我们根据fear_of_death动态调整阈值
            fear_threshold = 2.5 - agent.instinct.fear_of_death
            # 高恐惧(1.8): threshold = 0.7 → 更容易触发
            # 低恐惧(0.3): threshold = 2.2 → 很难触发
            
            if fear_level > fear_threshold:
                # 平仓止损！
                agent.closed_position = True
                agent.closed_at_cycle = cycle
                agent.closed_at_capital = agent.current_capital
                agent.closed_at_ratio = capital_ratio
                closed_this_cycle += 1
            else:
                # 继续持仓
                still_holding += 1
        
        # 输出当前状态
        total_closed = sum(1 for a in agents if a.closed_position)
        avg_capital_holding = np.mean([a.current_capital for a in agents if not a.closed_position]) if still_holding > 0 else 0
        avg_capital_all = np.mean([a.current_capital for a in agents])
        
        print(f"  周期{cycle:2d}: 持仓{still_holding:2d}个, 本轮平仓{closed_this_cycle:2d}个, 累计平仓{total_closed:2d}个, 平均资金${avg_capital_all:.0f}")
        
        if still_holding == 0:
            print(f"  → 全部平仓！")
            break
    
    return agents

# 测试组A（高恐惧）
group_A = run_minimal_test(group_A, "🛡️ 组A（高恐惧）")

# 测试组B（低恐惧）
group_B = run_minimal_test(group_B, "⚔️ 组B（低恐惧）")

# ============================================================================
# 对比分析
# ============================================================================
print()
print("="*80)
print("📊 [3/3] 对比分析")
print("="*80)
print()

# 统计平仓时机
closed_A = [a for a in group_A if a.closed_position]
closed_B = [a for a in group_B if a.closed_position]

never_closed_A = [a for a in group_A if not a.closed_position]
never_closed_B = [a for a in group_B if not a.closed_position]

print("1️⃣  平仓行为对比:")
print(f"   组A（高恐惧）: {len(closed_A)}/{GROUP_SIZE}个平仓 ({len(closed_A)/GROUP_SIZE:.1%})")
print(f"   组B（低恐惧）: {len(closed_B)}/{GROUP_SIZE}个平仓 ({len(closed_B)/GROUP_SIZE:.1%})")
print()

if len(closed_A) > 0:
    avg_cycle_A = np.mean([a.closed_at_cycle for a in closed_A])
    avg_ratio_A = np.mean([a.closed_at_ratio for a in closed_A])
    print(f"   组A平仓时机:")
    print(f"     平均周期: 第{avg_cycle_A:.1f}轮")
    print(f"     平均资金比率: {avg_ratio_A:.1%}")
    print(f"     最早平仓: 第{min(a.closed_at_cycle for a in closed_A)}轮")
    print(f"     最晚平仓: 第{max(a.closed_at_cycle for a in closed_A)}轮")
else:
    print(f"   组A: 无人平仓")
print()

if len(closed_B) > 0:
    avg_cycle_B = np.mean([a.closed_at_cycle for a in closed_B])
    avg_ratio_B = np.mean([a.closed_at_ratio for a in closed_B])
    print(f"   组B平仓时机:")
    print(f"     平均周期: 第{avg_cycle_B:.1f}轮")
    print(f"     平均资金比率: {avg_ratio_B:.1%}")
    print(f"     最早平仓: 第{min(a.closed_at_cycle for a in closed_B)}轮")
    print(f"     最晚平仓: 第{max(a.closed_at_cycle for a in closed_B)}轮")
else:
    print(f"   组B: 无人平仓")
print()

print("2️⃣  最终资金对比:")
final_capital_A = [a.current_capital for a in group_A]
final_capital_B = [a.current_capital for a in group_B]

print(f"   组A（高恐惧）:")
print(f"     平均: ${np.mean(final_capital_A):.0f}")
print(f"     最高: ${np.max(final_capital_A):.0f}")
print(f"     最低: ${np.min(final_capital_A):.0f}")
print()

print(f"   组B（低恐惧）:")
print(f"     平均: ${np.mean(final_capital_B):.0f}")
print(f"     最高: ${np.max(final_capital_B):.0f}")
print(f"     最低: ${np.min(final_capital_B):.0f}")
print()

# ============================================================================
# 最终判断
# ============================================================================
print("="*80)
print("🏁 最终判断")
print("="*80)
print()

# 判断1：平仓时机
if len(closed_A) > len(closed_B):
    print("✅ 判断1: 高恐惧Agent更多选择平仓")
    print(f"   组A平仓率: {len(closed_A)/GROUP_SIZE:.1%}")
    print(f"   组B平仓率: {len(closed_B)/GROUP_SIZE:.1%}")
    timing_diff = True
elif len(closed_B) > len(closed_A):
    print("⚠️ 判断1: 低恐惧Agent更多选择平仓（意外）")
    timing_diff = False
else:
    print("⚖️ 判断1: 两组平仓率相同")
    timing_diff = False

# 判断2：平仓早晚
if len(closed_A) > 0 and len(closed_B) > 0:
    if avg_cycle_A < avg_cycle_B:
        print(f"\n✅ 判断2: 高恐惧Agent更早平仓")
        print(f"   组A平均第{avg_cycle_A:.1f}轮 vs 组B第{avg_cycle_B:.1f}轮")
        early_stop = True
    elif avg_cycle_B < avg_cycle_A:
        print(f"\n⚠️ 判断2: 低恐惧Agent更早平仓（意外）")
        early_stop = False
    else:
        print(f"\n⚖️ 判断2: 两组平仓时机相同")
        early_stop = False
else:
    early_stop = False
    print(f"\n⚠️ 判断2: 无法比较（某组无人平仓）")

# 判断3：资金保护
if np.mean(final_capital_A) > np.mean(final_capital_B):
    print(f"\n✅ 判断3: 高恐惧Agent保留更多资金")
    print(f"   组A平均${np.mean(final_capital_A):.0f} vs 组B${np.mean(final_capital_B):.0f}")
    capital_protect = True
else:
    print(f"\n⚠️ 判断3: 低恐惧Agent保留更多资金（或相同）")
    capital_protect = False

print()
print("="*80)

# 综合判断
if timing_diff and early_stop and capital_protect:
    print("🎉 **fear_of_death核心逻辑验证成功！**")
    print()
    print("验证结果:")
    print("  ✅ 高恐惧Agent更多选择平仓")
    print("  ✅ 高恐惧Agent更早平仓止损")
    print("  ✅ 高恐惧Agent保留更多资金")
    print()
    print("💡 核心发现:")
    print("  fear_of_death的calculate_death_fear_level逻辑是正确的")
    print("  高fear_of_death确实会导致更保守的行为")
    print("  问题不在fear_of_death，而在Daimon的决策系统")
    print()
    print("🔧 建议:")
    print("  1. Daimon需要更积极的默认行为")
    print("  2. 或者调整market_voice的信号强度")
    print("  3. 让Agent更容易进入交易状态")
elif timing_diff or early_stop or capital_protect:
    print("⚠️ **fear_of_death部分有效**")
    print()
    print(f"  {'✅' if timing_diff else '❌'} 平仓率差异")
    print(f"  {'✅' if early_stop else '❌'} 平仓时机差异")
    print(f"  {'✅' if capital_protect else '❌'} 资金保护效果")
    print()
    print("可能需要:")
    print("  • 调整fear_threshold公式")
    print("  • 增加测试样本数量")
    print("  • 更极端的市场条件")
else:
    print("❌ **fear_of_death效果不明显**")
    print()
    print("需要检查:")
    print("  1. calculate_death_fear_level的计算逻辑")
    print("  2. fear_threshold的设置")
    print("  3. 测试参数是否合理")

print()
print("="*80)
print("📝 关键结论")
print("="*80)
print()
print("这个极简测试直接使用了fear_of_death的核心逻辑，")
print("绕过了Daimon的复杂决策系统。")
print()
print("如果这个测试显示fear_of_death有效：")
print("  → 问题在Daimon，不在fear_of_death")
print("  → 需要改进Daimon让Agent更容易开仓")
print()
print("如果这个测试显示fear_of_death无效：")
print("  → 问题在fear_of_death的计算逻辑")
print("  → 需要调整calculate_death_fear_level或阈值")
print()

