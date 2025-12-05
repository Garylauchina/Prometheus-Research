"""
Daimon改进验证测试（简化版）

测试目标：
1. 验证Agent会开仓（不再全都hold）
2. 验证高恐惧vs低恐惧的决策差异
3. 验证探索性开仓机制

Author: Prometheus Team
Version: v5.2
Date: 2025-12-05
"""

import sys
import numpy as np
import random
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING, format='%(message)s')  # 只显示WARNING以上

from prometheus.core.instinct import Instinct
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.meta_genome import MetaGenome

print("="*80)
print("🤖 Daimon改进验证测试")
print("="*80)
print("测试目标：")
print("  1. Agent会开仓（不再全都hold）")
print("  2. 高恐惧vs低恐惧决策差异")
print("  3. 探索性开仓机制验证")
print()

# ============================================================================
# 配置
# ============================================================================
TEST_CYCLES = 30
INITIAL_CAPITAL = 10000.0

print("📋 配置:")
print(f"   测试周期: {TEST_CYCLES}轮")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print()

# ============================================================================
# 创建对照组
# ============================================================================
print("="*80)
print("📊 [1/3] 创建对照组")
print("="*80)
print()

def create_test_agent(agent_id: str, fear: float, risk: float) -> AgentV5:
    """创建测试Agent"""
    lineage = LineageVector.create_genesis(family_id=0)
    genome = GenomeVector.create_genesis()
    meta_genome = MetaGenome.create_genesis()
    
    instinct = Instinct(
        fear_of_death=fear,
        risk_appetite=risk,
        loss_aversion=0.5,
        curiosity=0.5,
        time_preference=0.5,
        generation=0
    )
    
    agent = AgentV5(
        agent_id=agent_id,
        initial_capital=INITIAL_CAPITAL,
        lineage=lineage,
        genome=genome,
        instinct=instinct,
        meta_genome=meta_genome,
        generation=0
    )
    
    return agent

# 创建3个Agent
agent_high_fear_low_risk = create_test_agent("HighFear_LowRisk", fear=1.8, risk=0.3)
agent_low_fear_high_risk = create_test_agent("LowFear_HighRisk", fear=0.3, risk=0.8)
agent_balanced = create_test_agent("Balanced", fear=1.0, risk=0.5)

print("✅ 高恐惧低风险: fear=1.8, risk=0.3")
print("✅ 低恐惧高风险: fear=0.3, risk=0.8")
print("✅ 平衡型: fear=1.0, risk=0.5")
print()

# ============================================================================
# 决策测试
# ============================================================================
print("="*80)
print("🤖 [2/3] Daimon决策测试")
print("="*80)
print()

def test_daimon_decisions(agent: AgentV5, cycles: int, agent_name: str):
    """测试Daimon的决策"""
    print(f"\n{'='*70}")
    print(f"测试: {agent_name}")
    print(f"{'='*70}")
    
    decision_stats = {'buy': 0, 'sell': 0, 'close': 0, 'hold': 0}
    
    for cycle in range(cycles):
        capital_ratio = agent.current_capital / agent.initial_capital
        
        # 构造context
        context = {
            'capital_ratio': capital_ratio,
            'recent_pnl': 0,
            'consecutive_losses': 0,
            'position': {},  # 无持仓
            'market_data': {
                'price': 50000,
                'volatility': 0.10,
                'trend': 'neutral'
            }
        }
        
        # 调用Daimon决策
        try:
            decision = agent.daimon.guide(context)
            action = decision.action
            decision_stats[action] += 1
        except Exception as e:
            decision_stats['hold'] += 1
    
    # 统计
    total = sum(decision_stats.values())
    print(f"\n决策统计（{total}轮）:")
    print(f"  Buy:   {decision_stats['buy']:3d} ({decision_stats['buy']/total*100:5.1f}%)")
    print(f"  Sell:  {decision_stats['sell']:3d} ({decision_stats['sell']/total*100:5.1f}%)")
    print(f"  Close: {decision_stats['close']:3d} ({decision_stats['close']/total*100:5.1f}%)")
    print(f"  Hold:  {decision_stats['hold']:3d} ({decision_stats['hold']/total*100:5.1f}%)")
    
    open_rate = (decision_stats['buy'] + decision_stats['sell']) / total
    print(f"\n开仓率: {open_rate:.1%}")
    
    return decision_stats, open_rate

# 测试3个Agent
stats_high_fear, open_high = test_daimon_decisions(
    agent_high_fear_low_risk, TEST_CYCLES, "高恐惧低风险"
)

stats_low_fear, open_low = test_daimon_decisions(
    agent_low_fear_high_risk, TEST_CYCLES, "低恐惧高风险"
)

stats_balanced, open_balanced = test_daimon_decisions(
    agent_balanced, TEST_CYCLES, "平衡型"
)

# ============================================================================
# 分析对比
# ============================================================================
print("\n" + "="*80)
print("📊 [3/3] 分析对比")
print("="*80)
print()

print("1️⃣  开仓率对比:")
print(f"   高恐惧低风险: {open_high:.1%}")
print(f"   低恐惧高风险: {open_low:.1%}")
print(f"   平衡型: {open_balanced:.1%}")
print()

# 验证
print("2️⃣  行为差异验证:")

# 检查1：Agent会开仓（不再全都hold）
any_opens = open_high > 0.1 or open_low > 0.1 or open_balanced > 0.1
if any_opens:
    print("   ✅ Agent会开仓了！（不再全都hold）")
    opening_check = True
else:
    print("   ❌ Agent仍然不开仓（需要进一步调试）")
    opening_check = False

# 检查2：高风险Agent开仓更多
risk_difference = open_low > open_high
if risk_difference:
    diff = (open_low - open_high) * 100
    print(f"   ✅ 高风险Agent开仓更多（+{diff:.1f}个百分点）")
    risk_check = True
else:
    print(f"   ⚠️ 高风险Agent开仓未明显更多")
    risk_check = False

# 检查3：有行为多样性
diversity = len(set([open_high, open_low, open_balanced])) > 1
if diversity:
    print("   ✅ 不同Agent有不同行为（多样性）")
    diversity_check = True
else:
    print("   ⚠️ 所有Agent行为相同（缺乏多样性）")
    diversity_check = False

print()

# ============================================================================
# 总结
# ============================================================================
print("="*80)
print("🏁 验证结果")
print("="*80)
print()

checks = {
    'Agent会开仓': opening_check,
    '风险影响决策': risk_check,
    '行为多样性': diversity_check,
}

for check, passed in checks.items():
    status = "✅" if passed else "⚠️"
    print(f"   {status} {check}")

print()

if all(checks.values()):
    print("🎉 所有验证通过！Daimon改进完全成功！")
    print()
    print("💡 关键突破:")
    print("  • Agent不再全都hold")
    print("  • risk_appetite影响开仓决策")
    print("  • fear_of_death影响行为")
elif opening_check:
    print("✅ 核心改进成功：Agent会开仓了！")
    print()
    if not risk_check:
        print("⚠️ 风险差异不够明显，可能需要调整参数")
    if not diversity_check:
        print("⚠️ 行为多样性不足，可能需要增加randomness")
else:
    print("⚠️ Daimon仍然太保守，需要进一步调试")
    print()
    print("可能原因：")
    print("  1. market_voice权重过高")
    print("  2. instinct_voice权重不够")
    print("  3. 需要更强的信号")

print()
print("="*80)
print("✅ Daimon改进验证测试完成！")
print("="*80)

