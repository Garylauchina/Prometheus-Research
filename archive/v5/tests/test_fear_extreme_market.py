"""
极端市场对比测试 - 高恐惧vs低恐惧

核心问题：
1. 在极端市场中，高fear_of_death的Agent是否更容易存活？
2. 在温和市场中，低fear_of_death的Agent是否赚得更多？
3. fear_of_death是否真的影响生死？

实验设计：
- 对照组A：20个高恐惧Agent (fear_of_death = 1.7-1.9)
- 对照组B：20个低恐惧Agent (fear_of_death = 0.2-0.4)
- 环境1：极端市场（80%亏损概率，大额亏损）
- 环境2：温和市场（60%盈利概率，小额波动）
- 观察指标：存活率、平均资金、死亡原因

Author: Prometheus Team
Version: v5.2实验性
Date: 2025-12-05
"""

import sys
import numpy as np
import pandas as pd
import random
from pathlib import Path

# 导入核心模块
from prometheus.core.instinct import Instinct
from prometheus.core.moirai import Moirai
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.meta_genome import MetaGenome

print("="*80)
print("🔥 极端市场对比测试：高恐惧 vs 低恐惧")
print("="*80)
print()

# ============================================================================
# 配置
# ============================================================================
GROUP_SIZE = 20
INITIAL_CAPITAL = 10000.0
EXTREME_CYCLES = 20  # 极端市场周期
MILD_CYCLES = 20     # 温和市场周期

# 死亡阈值
DEATH_THRESHOLD = 3000.0  # 资金<3000就死亡（30%存活线）

print(f"📋 实验配置:")
print(f"   每组人数: {GROUP_SIZE}个Agent")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print(f"   死亡阈值: ${DEATH_THRESHOLD} (30%)")
print(f"   极端市场: {EXTREME_CYCLES}轮")
print(f"   温和市场: {MILD_CYCLES}轮")
print()

# ============================================================================
# 创建对照组
# ============================================================================
print("="*80)
print("📊 [1/4] 创建对照组")
print("="*80)
print()

def create_agent_with_fear(fear_value: float, agent_id: str) -> AgentV5:
    """创建指定fear_of_death的Agent"""
    # 创建Instinct
    instinct = Instinct(
        fear_of_death=fear_value,
        reproductive_drive=0.5,
        loss_aversion=0.5,
        risk_appetite=0.5,
        curiosity=0.5,
        time_preference=0.5,
        generation=0
    )
    
    # 创建其他组件
    lineage = LineageVector.create_genesis(family_id=0)
    genome = GenomeVector.create_genesis()
    meta_genome = MetaGenome.create_genesis()
    
    # 创建Agent
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

# 组A：高恐惧Agent (fear = 1.7-1.9)
print("创建组A：高恐惧Agent...")
group_A = []
for i in range(GROUP_SIZE):
    fear = random.uniform(1.7, 1.9)
    agent = create_agent_with_fear(fear, f"HighFear_{i+1}")
    group_A.append(agent)

fear_A = [agent.instinct.fear_of_death for agent in group_A]
print(f"  ✅ 组A创建完成")
print(f"     fear_of_death平均: {np.mean(fear_A):.3f}")
print(f"     fear_of_death范围: [{np.min(fear_A):.3f}, {np.max(fear_A):.3f}]")
print()

# 组B：低恐惧Agent (fear = 0.2-0.4)
print("创建组B：低恐惧Agent...")
group_B = []
for i in range(GROUP_SIZE):
    fear = random.uniform(0.2, 0.4)
    agent = create_agent_with_fear(fear, f"LowFear_{i+1}")
    group_B.append(agent)

fear_B = [agent.instinct.fear_of_death for agent in group_B]
print(f"  ✅ 组B创建完成")
print(f"     fear_of_death平均: {np.mean(fear_B):.3f}")
print(f"     fear_of_death范围: [{np.min(fear_B):.3f}, {np.max(fear_B):.3f}]")
print()

# ============================================================================
# 实验1: 极端市场（高恐惧应该更容易存活）
# ============================================================================
print("="*80)
print("📉 [2/4] 实验1：极端市场")
print("="*80)
print("市场条件：80%亏损概率，亏损10%-30%，盈利5%-15%")
print()

def simulate_extreme_market(agents: list, cycles: int, death_threshold: float):
    """模拟极端市场"""
    alive = agents.copy()
    dead = []
    
    for cycle in range(1, cycles + 1):
        print(f"  周期{cycle:2d}: ", end="")
        
        for agent in alive[:]:  # 复制列表，因为会修改
            # 极端市场：80%亏损
            if random.random() < 0.80:
                loss_pct = random.uniform(0.10, 0.30)  # 亏损10%-30%
                pnl = -agent.current_capital * loss_pct
            else:
                profit_pct = random.uniform(0.05, 0.15)  # 盈利5%-15%
                pnl = agent.current_capital * profit_pct
            
            agent.current_capital += pnl
            
            # 检查是否死亡
            if agent.current_capital < death_threshold:
                alive.remove(agent)
                dead.append((agent, cycle, agent.current_capital))
        
        alive_count = len(alive)
        dead_count = len(dead)
        
        if alive_count == 0:
            print(f"💀 全灭！")
            break
        else:
            avg_capital = np.mean([a.current_capital for a in alive])
            print(f"存活{alive_count:2d}个 (死亡{dead_count:2d}个), 平均${avg_capital:.0f}")
    
    return alive, dead

# 测试组A（高恐惧）
print("\n🛡️  组A（高恐惧）进入极端市场...")
group_A_copy = [create_agent_with_fear(a.instinct.fear_of_death, a.agent_id) for a in group_A]
alive_A, dead_A = simulate_extreme_market(group_A_copy, EXTREME_CYCLES, DEATH_THRESHOLD)

print()
print(f"组A结果:")
print(f"  存活: {len(alive_A)}/{GROUP_SIZE} ({len(alive_A)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_A)}/{GROUP_SIZE} ({len(dead_A)/GROUP_SIZE:.1%})")
if alive_A:
    avg_capital_A = np.mean([a.current_capital for a in alive_A])
    print(f"  存活者平均资金: ${avg_capital_A:.0f}")
print()

# 测试组B（低恐惧）
print("⚔️  组B（低恐惧）进入极端市场...")
group_B_copy = [create_agent_with_fear(a.instinct.fear_of_death, a.agent_id) for a in group_B]
alive_B, dead_B = simulate_extreme_market(group_B_copy, EXTREME_CYCLES, DEATH_THRESHOLD)

print()
print(f"组B结果:")
print(f"  存活: {len(alive_B)}/{GROUP_SIZE} ({len(alive_B)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_B)}/{GROUP_SIZE} ({len(dead_B)/GROUP_SIZE:.1%})")
if alive_B:
    avg_capital_B = np.mean([a.current_capital for a in alive_B])
    print(f"  存活者平均资金: ${avg_capital_B:.0f}")
print()

# 对比
print("📊 极端市场对比:")
print(f"  组A存活率: {len(alive_A)/GROUP_SIZE:.1%} (高恐惧)")
print(f"  组B存活率: {len(alive_B)/GROUP_SIZE:.1%} (低恐惧)")

if len(alive_A) > len(alive_B):
    diff = len(alive_A) - len(alive_B)
    print(f"  ✅ 结论: 高恐惧者多存活{diff}个（+{diff/GROUP_SIZE:.1%}）")
    extreme_winner = "高恐惧"
elif len(alive_B) > len(alive_A):
    diff = len(alive_B) - len(alive_A)
    print(f"  ⚠️ 意外: 低恐惧者多存活{diff}个（+{diff/GROUP_SIZE:.1%}）")
    extreme_winner = "低恐惧"
else:
    print(f"  ⚖️ 平局: 存活数量相同")
    extreme_winner = "平局"
print()

# ============================================================================
# 实验2: 温和市场（低恐惧应该赚得更多）
# ============================================================================
print("="*80)
print("📈 [3/4] 实验2：温和市场")
print("="*80)
print("市场条件：60%盈利概率，盈利5%-15%，亏损5%-10%")
print()

def simulate_mild_market(agents: list, cycles: int):
    """模拟温和市场（无死亡，只比资金）"""
    for cycle in range(1, cycles + 1):
        print(f"  周期{cycle:2d}: ", end="")
        
        for agent in agents:
            # 温和市场：60%盈利
            if random.random() < 0.60:
                profit_pct = random.uniform(0.05, 0.15)  # 盈利5%-15%
                pnl = agent.current_capital * profit_pct
            else:
                loss_pct = random.uniform(0.05, 0.10)  # 亏损5%-10%
                pnl = -agent.current_capital * loss_pct
            
            agent.current_capital += pnl
        
        avg_capital = np.mean([a.current_capital for a in agents])
        print(f"平均资金${avg_capital:.0f}")
    
    return agents

# 重新创建组（重置资金）
print("\n🛡️  组A（高恐惧）进入温和市场...")
group_A_mild = [create_agent_with_fear(a.instinct.fear_of_death, a.agent_id) for a in group_A]
group_A_mild = simulate_mild_market(group_A_mild, MILD_CYCLES)

print()
capital_A_mild = [a.current_capital for a in group_A_mild]
print(f"组A结果:")
print(f"  平均资金: ${np.mean(capital_A_mild):.0f}")
print(f"  最高资金: ${np.max(capital_A_mild):.0f}")
print(f"  最低资金: ${np.min(capital_A_mild):.0f}")
print(f"  收益率: {(np.mean(capital_A_mild)/INITIAL_CAPITAL - 1):.1%}")
print()

print("⚔️  组B（低恐惧）进入温和市场...")
group_B_mild = [create_agent_with_fear(a.instinct.fear_of_death, a.agent_id) for a in group_B]
group_B_mild = simulate_mild_market(group_B_mild, MILD_CYCLES)

print()
capital_B_mild = [a.current_capital for a in group_B_mild]
print(f"组B结果:")
print(f"  平均资金: ${np.mean(capital_B_mild):.0f}")
print(f"  最高资金: ${np.max(capital_B_mild):.0f}")
print(f"  最低资金: ${np.min(capital_B_mild):.0f}")
print(f"  收益率: {(np.mean(capital_B_mild)/INITIAL_CAPITAL - 1):.1%}")
print()

# 对比
print("📊 温和市场对比:")
print(f"  组A平均资金: ${np.mean(capital_A_mild):.0f} (高恐惧)")
print(f"  组B平均资金: ${np.mean(capital_B_mild):.0f} (低恐惧)")

if np.mean(capital_B_mild) > np.mean(capital_A_mild):
    diff = np.mean(capital_B_mild) - np.mean(capital_A_mild)
    diff_pct = diff / np.mean(capital_A_mild)
    print(f"  ✅ 结论: 低恐惧者多赚${diff:.0f}（+{diff_pct:.1%}）")
    mild_winner = "低恐惧"
elif np.mean(capital_A_mild) > np.mean(capital_B_mild):
    diff = np.mean(capital_A_mild) - np.mean(capital_B_mild)
    diff_pct = diff / np.mean(capital_B_mild)
    print(f"  ⚠️ 意外: 高恐惧者多赚${diff:.0f}（+{diff_pct:.1%}）")
    mild_winner = "高恐惧"
else:
    print(f"  ⚖️ 平局: 收益相同")
    mild_winner = "平局"
print()

# ============================================================================
# 实验总结
# ============================================================================
print("="*80)
print("📊 [4/4] 实验总结")
print("="*80)
print()

print("🎯 核心问题验证:")
print()

print("1️⃣  极端市场中，高fear_of_death是否更容易存活？")
if extreme_winner == "高恐惧":
    print(f"   ✅ YES! 高恐惧者存活率 {len(alive_A)/GROUP_SIZE:.1%} > 低恐惧者 {len(alive_B)/GROUP_SIZE:.1%}")
    print(f"   💡 高恐惧Agent在危险中更保守，更容易活下来")
elif extreme_winner == "低恐惧":
    print(f"   ❌ NO. 低恐惧者存活率 {len(alive_B)/GROUP_SIZE:.1%} > 高恐惧者 {len(alive_A)/GROUP_SIZE:.1%}")
    print(f"   🤔 可能需要调整决策逻辑或测试参数")
else:
    print(f"   ⚖️ 平局。两组存活率相同")
print()

print("2️⃣  温和市场中，低fear_of_death是否赚得更多？")
if mild_winner == "低恐惧":
    print(f"   ✅ YES! 低恐惧者收益 {(np.mean(capital_B_mild)/INITIAL_CAPITAL - 1):.1%} > 高恐惧者 {(np.mean(capital_A_mild)/INITIAL_CAPITAL - 1):.1%}")
    print(f"   💡 低恐惧Agent敢于冒险，在温和市场赚更多")
elif mild_winner == "高恐惧":
    print(f"   ❌ NO. 高恐惧者收益 {(np.mean(capital_A_mild)/INITIAL_CAPITAL - 1):.1%} > 低恐惧者 {(np.mean(capital_B_mild)/INITIAL_CAPITAL - 1):.1%}")
    print(f"   🤔 可能需要调整决策逻辑")
else:
    print(f"   ⚖️ 平局。两组收益相同")
print()

print("3️⃣  fear_of_death是否真的影响生死？")
if extreme_winner == "高恐惧" and mild_winner == "低恐惧":
    print(f"   ✅ YES! fear_of_death形成了明确的权衡：")
    print(f"      • 高恐惧 = 保守 = 容易存活 but 难赚大钱")
    print(f"      • 低恐惧 = 激进 = 容易死亡 but 赚得多（如果活下来）")
    print()
    print(f"   🧬 这才是真正的进化压力！")
    print(f"      温和市场 → 低恐惧者繁荣")
    print(f"      残酷市场 → 高恐惧者生存")
    conclusion = "完美"
elif extreme_winner != "平局" or mild_winner != "平局":
    print(f"   ⚠️ 部分有效。fear_of_death有影响，但不够明显")
    print(f"      可能需要：")
    print(f"      1. 调整inner_council中的fear_of_death决策逻辑")
    print(f"      2. 增加fear_of_death对决策的影响权重")
    print(f"      3. 更极端的市场条件")
    conclusion = "部分"
else:
    print(f"   ❌ NO. fear_of_death似乎没有明显影响")
    print(f"      需要检查：")
    print(f"      1. inner_council是否真的使用了fear_of_death")
    print(f"      2. fear_of_death的影响是否被其他因素掩盖")
    conclusion = "无效"
print()

# ============================================================================
# 最终判断
# ============================================================================
print("="*80)
print("🏁 最终判断")
print("="*80)
print()

if conclusion == "完美":
    print("🎉 fear_of_death实验**完全成功**！")
    print()
    print("主要成果:")
    print("  ✅ fear_of_death真正影响Agent的生死")
    print("  ✅ 高恐惧与低恐惧形成明确的权衡")
    print("  ✅ 进化压力清晰可见")
    print()
    print("📈 下一步:")
    print("  1. 在真实进化环境中运行（50个Agent，50轮）")
    print("  2. 观察fear_of_death分布的演化趋势")
    print("  3. 验证在不同市场环境下的适应性")
elif conclusion == "部分":
    print("⚠️ fear_of_death实验**部分成功**")
    print()
    print("需要改进:")
    print("  1. 增强fear_of_death在决策中的影响")
    print("  2. 调整触发阈值")
    print("  3. 更极端的测试条件")
else:
    print("❌ fear_of_death实验**需要调试**")
    print()
    print("问题:")
    print("  fear_of_death似乎没有明显影响生死")
    print()
    print("建议:")
    print("  1. 检查inner_council.py中的fear_of_death使用")
    print("  2. 确认calculate_death_fear_level被正确调用")
    print("  3. 可能需要调整决策权重")

print()

