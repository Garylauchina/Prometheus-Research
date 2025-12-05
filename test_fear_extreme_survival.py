"""
极端生存测试：真正的死亡压力

这次的关键改进：
1. ✅ 90%亏损概率（而非80%）
2. ✅ 更大的亏损幅度（15-30%）
3. ✅ 确保Agent进入濒死状态（资金<50%）

只有在真正的生死关头，fear_of_death的差异才会显现！

Author: Prometheus Team
Version: v5.2 - 极端生存测试
Date: 2025-12-05
"""

import sys
import numpy as np
import pandas as pd
import random
from pathlib import Path

# 导入核心模块
from prometheus.core.instinct import Instinct
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.meta_genome import MetaGenome

print("="*80)
print("💀 极端生存测试：生死关头的fear_of_death")
print("="*80)
print("核心改进：")
print("  1. 90%亏损概率（极端市场）")
print("  2. 更大亏损幅度（15-30%）")
print("  3. 确保濒死状态（资金<50%）")
print()

# ============================================================================
# 配置
# ============================================================================
GROUP_SIZE = 30  # 增加样本量
INITIAL_CAPITAL = 10000.0
EXTREME_CYCLES = 50  # 增加轮次
DEATH_THRESHOLD = 2000.0  # 20%才算死亡

print(f"📋 实验配置:")
print(f"   每组人数: {GROUP_SIZE}个Agent")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print(f"   死亡阈值: ${DEATH_THRESHOLD} (20%)")
print(f"   测试轮数: {EXTREME_CYCLES}轮")
print(f"   市场条件: 90%亏损概率，亏损15-30%")
print()

# ============================================================================
# 创建对照组
# ============================================================================
print("="*80)
print("📊 [1/3] 创建对照组")
print("="*80)
print()

def create_agent_with_fear_and_risk(fear_value: float, risk_value: float, agent_id: str) -> AgentV5:
    """创建指定fear_of_death和risk_appetite的Agent"""
    instinct = Instinct(
        fear_of_death=fear_value,
        reproductive_drive=0.5,
        loss_aversion=0.5,
        risk_appetite=risk_value,
        curiosity=0.5,
        time_preference=0.5,
        generation=0
    )
    
    lineage = LineageVector.create_genesis(family_id=0)
    genome = GenomeVector.create_genesis()
    meta_genome = MetaGenome.create_genesis()
    
    agent = AgentV5(
        agent_id=agent_id,
        initial_capital=INITIAL_CAPITAL,
        lineage=lineage,
        genome=genome,
        instinct=instinct,
        meta_genome=meta_genome,
        generation=0
    )
    
    # 初始化Agent状态
    agent.position = {}
    agent.consecutive_losses = 0
    agent.total_pnl = 0
    agent.trade_count = 0
    
    return agent

# 组A：高恐惧 + 高风险
print("创建组A：高恐惧 + 高风险...")
group_A = []
for i in range(GROUP_SIZE):
    fear = random.uniform(1.7, 1.9)
    risk = random.uniform(0.7, 0.9)
    agent = create_agent_with_fear_and_risk(fear, risk, f"HighFear_{i+1}")
    group_A.append(agent)

print(f"  ✅ 组A: fear平均{np.mean([a.instinct.fear_of_death for a in group_A]):.3f}")
print()

# 组B：低恐惧 + 高风险
print("创建组B：低恐惧 + 高风险...")
group_B = []
for i in range(GROUP_SIZE):
    fear = random.uniform(0.2, 0.4)
    risk = random.uniform(0.7, 0.9)
    agent = create_agent_with_fear_and_risk(fear, risk, f"LowFear_{i+1}")
    group_B.append(agent)

print(f"  ✅ 组B: fear平均{np.mean([a.instinct.fear_of_death for a in group_B]):.3f}")
print()

# ============================================================================
# 极端生存测试
# ============================================================================
print("="*80)
print("💀 [2/3] 极端生存测试（90%亏损概率）")
print("="*80)
print()

def extreme_survival_test(agents: list, cycles: int, death_threshold: float, group_name: str):
    """极端生存测试"""
    alive = agents.copy()
    dead = []
    
    decision_stats = {'buy': 0, 'sell': 0, 'close': 0, 'hold': 0}
    close_when_low_capital = {'A': 0, 'B': 0}  # 低资金时平仓次数
    
    for cycle in range(1, cycles + 1):
        # 极端市场：90%亏损
        if random.random() < 0.90:
            trend = 'bearish'
        else:
            trend = 'bullish'
        
        current_price = 50000 + random.uniform(-5000, 5000)
        
        for agent in alive[:]:
            capital_ratio = agent.current_capital / agent.initial_capital
            recent_pnl = agent.total_pnl / agent.initial_capital if agent.trade_count > 0 else 0
            
            # 构造context
            context = {
                'capital_ratio': capital_ratio,
                'recent_pnl': recent_pnl,
                'consecutive_losses': agent.consecutive_losses,
                'position': agent.position,
                'market_data': {
                    'price': current_price,
                    'volatility': 0.20,  # 高波动
                    'trend': trend
                }
            }
            
            # 调用Daimon做决策
            try:
                decision = agent.daimon.guide(context)
                action = decision.action
            except Exception as e:
                action = 'hold'
            
            decision_stats[action] += 1
            
            # 记录低资金时的平仓行为
            if capital_ratio < 0.5 and action == 'close':
                if 'HighFear' in agent.agent_id:
                    close_when_low_capital['A'] += 1
                else:
                    close_when_low_capital['B'] += 1
            
            # 执行交易（极端亏损）
            pnl = 0
            
            if action == 'buy':
                agent.position = {'side': 'long', 'amount': 1.0}
                agent.trade_count += 1
                
                if trend == 'bullish':
                    pnl = agent.current_capital * random.uniform(0.08, 0.15)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.15, 0.30)  # 更大亏损
                    agent.consecutive_losses += 1
            
            elif action == 'sell':
                agent.position = {'side': 'short', 'amount': 1.0}
                agent.trade_count += 1
                
                if trend == 'bearish':
                    pnl = agent.current_capital * random.uniform(0.08, 0.15)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.15, 0.30)
                    agent.consecutive_losses += 1
            
            elif action == 'close':
                if agent.position:
                    agent.position = {}
                    pnl = 0
                    agent.consecutive_losses = 0
            
            else:  # hold
                if agent.position:
                    if agent.position.get('side') == 'long':
                        if trend == 'bullish':
                            pnl = agent.current_capital * random.uniform(0.03, 0.08)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.10, 0.20)
                            agent.consecutive_losses += 1
                    else:
                        if trend == 'bearish':
                            pnl = agent.current_capital * random.uniform(0.03, 0.08)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.10, 0.20)
                            agent.consecutive_losses += 1
                else:
                    pnl = 0
            
            agent.current_capital += pnl
            agent.total_pnl += pnl
            
            # 检查死亡
            if agent.current_capital < death_threshold:
                alive.remove(agent)
                dead.append((agent, cycle))
        
        # 输出（每5轮）
        if cycle % 5 == 0 or len(alive) < len(agents) * 0.5:
            if len(alive) == 0:
                print(f"  周期{cycle:2d}: 💀 全灭！")
                break
            else:
                avg_capital = np.mean([a.current_capital for a in alive])
                print(f"  周期{cycle:2d}: 存活{len(alive):2d}/{len(agents):2d}, 平均${avg_capital:.0f} ({avg_capital/INITIAL_CAPITAL:.1%})")
    
    return alive, dead, decision_stats, close_when_low_capital

# 测试组A
print(f"🛡️ 组A（高恐惧）")
print()
alive_A, dead_A, stats_A, close_low_A = extreme_survival_test(group_A, EXTREME_CYCLES, DEATH_THRESHOLD, "组A")

print()
print(f"组A最终结果:")
print(f"  存活: {len(alive_A)}/{GROUP_SIZE} ({len(alive_A)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_A)}/{GROUP_SIZE} ({len(dead_A)/GROUP_SIZE:.1%})")
if alive_A:
    print(f"  存活者平均资金: ${np.mean([a.current_capital for a in alive_A]):.0f}")
if dead_A:
    avg_death_cycle = np.mean([cycle for _, cycle in dead_A])
    print(f"  死亡者平均寿命: {avg_death_cycle:.1f}轮")
print()

# 测试组B
print(f"⚔️ 组B（低恐惧）")
print()
alive_B, dead_B, stats_B, close_low_B = extreme_survival_test(group_B, EXTREME_CYCLES, DEATH_THRESHOLD, "组B")

print()
print(f"组B最终结果:")
print(f"  存活: {len(alive_B)}/{GROUP_SIZE} ({len(alive_B)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_B)}/{GROUP_SIZE} ({len(dead_B)/GROUP_SIZE:.1%})")
if alive_B:
    print(f"  存活者平均资金: ${np.mean([a.current_capital for a in alive_B]):.0f}")
if dead_B:
    avg_death_cycle = np.mean([cycle for _, cycle in dead_B])
    print(f"  死亡者平均寿命: {avg_death_cycle:.1f}轮")
print()

# ============================================================================
# 对比分析
# ============================================================================
print("="*80)
print("📊 [3/3] 对比分析")
print("="*80)
print()

print("1️⃣  生存率对比（关键指标）:")
survival_A = len(alive_A) / GROUP_SIZE
survival_B = len(alive_B) / GROUP_SIZE
print(f"   组A（高恐惧）: {len(alive_A)}/{GROUP_SIZE} ({survival_A:.1%})")
print(f"   组B（低恐惧）: {len(alive_B)}/{GROUP_SIZE} ({survival_B:.1%})")

if survival_A > survival_B:
    print(f"   ✅ 高恐惧者生存率更高 (+{(survival_A - survival_B)*100:.1f}个百分点)")
    survival_pass = True
else:
    print(f"   ❌ 低恐惧者生存率≥高恐惧者")
    survival_pass = False
print()

print("2️⃣  濒死时平仓行为（资金<50%）:")
print(f"   组A（高恐惧）: {close_low_A['A']}次")
print(f"   组B（低恐惧）: {close_low_B['B']}次")
if close_low_A['A'] > close_low_B['B']:
    print(f"   ✅ 高恐惧者在危险时更频繁平仓")
    close_behavior_pass = True
else:
    print(f"   ⚠️ 低恐惧者平仓≥高恐惧者")
    close_behavior_pass = False
print()

print("3️⃣  死亡分析:")
if dead_A and dead_B:
    avg_death_A = np.mean([cycle for _, cycle in dead_A])
    avg_death_B = np.mean([cycle for _, cycle in dead_B])
    print(f"   组A平均死亡轮数: {avg_death_A:.1f}")
    print(f"   组B平均死亡轮数: {avg_death_B:.1f}")
    
    if avg_death_A > avg_death_B:
        print(f"   ✅ 高恐惧者平均存活更久")
elif dead_B and not dead_A:
    print(f"   ✅ 组A无人死亡，组B有{len(dead_B)}人死亡")
elif dead_A and not dead_B:
    print(f"   ❌ 组B无人死亡，组A有{len(dead_A)}人死亡")
else:
    print(f"   ⚠️ 双方都无人死亡（市场不够极端）")

print()

# ============================================================================
# 最终判断
# ============================================================================
print("="*80)
print("🏁 最终判断")
print("="*80)
print()

if survival_pass:
    print("🎉 **fear_of_death在真实环境中有效！**")
    print()
    print("验证结果:")
    print(f"  ✅ 高恐惧者生存率更高 ({survival_A:.1%} vs {survival_B:.1%})")
    if close_behavior_pass:
        print(f"  ✅ 高恐惧者在危险时更频繁平仓")
    print()
    print("💡 核心结论:")
    print("  在真正的生死关头，fear_of_death发挥了作用！")
    print("  高恐惧者通过及时止损，保住了性命！")
    print("  低恐惧者虽然激进，但在极端市场中更容易死亡！")
    print()
    print("🧬 进化意义:")
    print("  极端市场 → 高恐惧者生存优势")
    print("  温和市场 → 低恐惧者可能有优势（更激进）")
    print("  这才是真正的进化压力！")
else:
    print("⚠️ **效果不明显，需要进一步调试**")
    print()
    if survival_A == survival_B:
        print("  可能原因：")
        print("    1. 市场还不够极端")
        print("    2. 测试样本量不够")
        print("    3. 随机性影响")
    else:
        print("  意外：低恐惧者生存率更高")
        print("    可能原因：")
        print("      1. Daimon其他声音影响过大")
        print("      2. fear_of_death权重仍不够")
        print("      3. 测试设计有问题")

print()

