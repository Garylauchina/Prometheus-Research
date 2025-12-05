"""
验证改进后的Daimon决策系统

核心改进：
1. ✅ fear_of_death动态阈值（高恐惧→低阈值→容易触发）
2. ✅ risk_appetite探索性开仓（高风险→主动开仓）
3. ✅ 降低开仓门槛（资金>50%即可，而非80%）

测试目标：
- Agent不再全都hold
- 高risk_appetite的Agent会开仓
- 高fear_of_death的Agent会更早平仓
- 低fear_of_death的Agent会更晚平仓

Author: Prometheus Team
Version: v5.2实验性 - 改进后
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
print("🔥 改进后Daimon测试：高恐惧 vs 低恐惧")
print("="*80)
print("核心改进：")
print("  1. fear_of_death动态阈值")
print("  2. risk_appetite探索性开仓")
print("  3. 降低开仓门槛（50%）")
print()

# ============================================================================
# 配置
# ============================================================================
GROUP_SIZE = 20
INITIAL_CAPITAL = 10000.0
EXTREME_CYCLES = 30
DEATH_THRESHOLD = 3000.0

print(f"📋 实验配置:")
print(f"   每组人数: {GROUP_SIZE}个Agent")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print(f"   死亡阈值: ${DEATH_THRESHOLD} (30%)")
print(f"   测试轮数: {EXTREME_CYCLES}轮")
print()

# ============================================================================
# 创建对照组（高risk_appetite，确保会开仓）
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
        risk_appetite=risk_value,  # 设置高risk_appetite确保会开仓
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

# 组A：高恐惧 + 高风险（应该：容易开仓，容易平仓）
print("创建组A：高恐惧 + 高风险...")
group_A = []
for i in range(GROUP_SIZE):
    fear = random.uniform(1.7, 1.9)
    risk = random.uniform(0.7, 0.9)  # 高风险偏好
    agent = create_agent_with_fear_and_risk(fear, risk, f"HighFear_HighRisk_{i+1}")
    group_A.append(agent)

print(f"  ✅ 组A: fear平均{np.mean([a.instinct.fear_of_death for a in group_A]):.3f}, risk平均{np.mean([a.instinct.risk_appetite for a in group_A]):.3f}")
print(f"     预期：会开仓（高风险），但会早平仓（高恐惧）")
print()

# 组B：低恐惧 + 高风险（应该：容易开仓，不容易平仓）
print("创建组B：低恐惧 + 高风险...")
group_B = []
for i in range(GROUP_SIZE):
    fear = random.uniform(0.2, 0.4)
    risk = random.uniform(0.7, 0.9)  # 同样高风险偏好
    agent = create_agent_with_fear_and_risk(fear, risk, f"LowFear_HighRisk_{i+1}")
    group_B.append(agent)

print(f"  ✅ 组B: fear平均{np.mean([a.instinct.fear_of_death for a in group_B]):.3f}, risk平均{np.mean([a.instinct.risk_appetite for a in group_B]):.3f}")
print(f"     预期：会开仓（高风险），但不易平仓（低恐惧）")
print()

# ============================================================================
# 极端市场决策测试
# ============================================================================
print("="*80)
print("📉 [2/3] 极端市场决策测试（改进后Daimon）")
print("="*80)
print("市场条件：连续下跌，80%亏损概率")
print()

def simulate_with_improved_daimon(agents: list, cycles: int, death_threshold: float, group_name: str):
    """使用改进后的Daimon进行测试"""
    alive = agents.copy()
    dead = []
    
    decision_stats = {'buy': 0, 'sell': 0, 'close': 0, 'hold': 0}
    
    for cycle in range(1, cycles + 1):
        # 市场趋势（80%下跌）
        if random.random() < 0.80:
            trend = 'bearish'
            market_pnl_factor = -1
        else:
            trend = 'bullish'
            market_pnl_factor = 1
        
        current_price = 50000 + random.uniform(-5000, 5000)
        
        cycle_actions = {'buy': 0, 'sell': 0, 'close': 0, 'hold': 0}
        
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
                    'volatility': 0.15,
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
            cycle_actions[action] += 1
            
            # 执行交易
            pnl = 0
            
            if action == 'buy':
                agent.position = {'side': 'long', 'amount': 1.0}
                agent.trade_count += 1
                
                if trend == 'bullish':
                    pnl = agent.current_capital * random.uniform(0.05, 0.10)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.10, 0.20)
                    agent.consecutive_losses += 1
            
            elif action == 'sell':
                agent.position = {'side': 'short', 'amount': 1.0}
                agent.trade_count += 1
                
                if trend == 'bearish':
                    pnl = agent.current_capital * random.uniform(0.05, 0.10)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.10, 0.20)
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
                            pnl = agent.current_capital * random.uniform(0.02, 0.05)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.05, 0.10)
                            agent.consecutive_losses += 1
                    else:
                        if trend == 'bearish':
                            pnl = agent.current_capital * random.uniform(0.02, 0.05)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.05, 0.10)
                            agent.consecutive_losses += 1
                else:
                    pnl = 0
            
            agent.current_capital += pnl
            agent.total_pnl += pnl
            
            # 检查死亡
            if agent.current_capital < death_threshold:
                alive.remove(agent)
                dead.append((agent, cycle))
        
        # 输出
        if len(alive) == 0:
            print(f"  周期{cycle:2d}: 💀 全灭！")
            break
        else:
            avg_capital = np.mean([a.current_capital for a in alive])
            print(f"  周期{cycle:2d}: 存活{len(alive):2d}个, 平均${avg_capital:.0f}, 决策[B:{cycle_actions['buy']:2d} S:{cycle_actions['sell']:2d} C:{cycle_actions['close']:2d} H:{cycle_actions['hold']:2d}]")
    
    return alive, dead, decision_stats

# 测试组A
print(f"\n🛡️ {group_A[0].agent_id.split('_')[0]}组（高恐惧+高风险）")
print("   预期：会开仓，但会早平仓止损")
print()
alive_A, dead_A, stats_A = simulate_with_improved_daimon(group_A, EXTREME_CYCLES, DEATH_THRESHOLD, "组A")

print()
print(f"组A结果:")
print(f"  存活: {len(alive_A)}/{GROUP_SIZE} ({len(alive_A)/GROUP_SIZE:.1%})")
print(f"  决策统计: Buy:{stats_A['buy']} Sell:{stats_A['sell']} Close:{stats_A['close']} Hold:{stats_A['hold']}")
if alive_A:
    print(f"  存活者平均资金: ${np.mean([a.current_capital for a in alive_A]):.0f}")
print()

# 测试组B
print(f"⚔️ {group_B[0].agent_id.split('_')[0]}组（低恐惧+高风险）")
print("   预期：会开仓，但不易平仓（更激进）")
print()
alive_B, dead_B, stats_B = simulate_with_improved_daimon(group_B, EXTREME_CYCLES, DEATH_THRESHOLD, "组B")

print()
print(f"组B结果:")
print(f"  存活: {len(alive_B)}/{GROUP_SIZE} ({len(alive_B)/GROUP_SIZE:.1%})")
print(f"  决策统计: Buy:{stats_B['buy']} Sell:{stats_B['sell']} Close:{stats_B['close']} Hold:{stats_B['hold']}")
if alive_B:
    print(f"  存活者平均资金: ${np.mean([a.current_capital for a in alive_B]):.0f}")
print()

# ============================================================================
# 对比分析
# ============================================================================
print("="*80)
print("📊 [3/3] 对比分析")
print("="*80)
print()

print("1️⃣  存活率对比:")
print(f"   组A（高恐惧）: {len(alive_A)}/{GROUP_SIZE} ({len(alive_A)/GROUP_SIZE:.1%})")
print(f"   组B（低恐惧）: {len(alive_B)}/{GROUP_SIZE} ({len(alive_B)/GROUP_SIZE:.1%})")

if len(alive_A) > len(alive_B):
    print(f"   ✅ 高恐惧者多存活{len(alive_A) - len(alive_B)}个")
    survival_pass = True
else:
    print(f"   ⚠️ 低恐惧者存活≥高恐惧者")
    survival_pass = False
print()

print("2️⃣  决策行为对比:")
total_A = sum(stats_A.values())
total_B = sum(stats_B.values())

print(f"   开仓行为（Buy + Sell）:")
print(f"     组A: {stats_A['buy'] + stats_A['sell']}/{total_A} ({(stats_A['buy'] + stats_A['sell'])/total_A:.1%})")
print(f"     组B: {stats_B['buy'] + stats_B['sell']}/{total_B} ({(stats_B['buy'] + stats_B['sell'])/total_B:.1%})")

print(f"\n   平仓行为（Close）:")
print(f"     组A: {stats_A['close']}/{total_A} ({stats_A['close']/total_A:.1%})")
print(f"     组B: {stats_B['close']}/{total_B} ({stats_B['close']/total_B:.1%})")

# 验证开仓
open_rate_A = (stats_A['buy'] + stats_A['sell']) / total_A
open_rate_B = (stats_B['buy'] + stats_B['sell']) / total_B

if open_rate_A > 0.1 or open_rate_B > 0.1:
    print(f"\n   ✅ Agent开始开仓了！（不再全都hold）")
    opening_pass = True
else:
    print(f"\n   ❌ Agent仍然不开仓（需要进一步调整）")
    opening_pass = False

# 验证平仓差异
close_rate_A = stats_A['close'] / total_A
close_rate_B = stats_B['close'] / total_B

if close_rate_A > close_rate_B:
    print(f"   ✅ 高恐惧者更频繁平仓 ({close_rate_A:.1%} vs {close_rate_B:.1%})")
    closing_pass = True
else:
    print(f"   ⚠️ 低恐惧者平仓≥高恐惧者")
    closing_pass = False

print()

# ============================================================================
# 最终判断
# ============================================================================
print("="*80)
print("🏁 最终判断")
print("="*80)
print()

if opening_pass and closing_pass and survival_pass:
    print("🎉 **Daimon改进成功！fear_of_death在真实环境中发挥作用！**")
    print()
    print("验证结果:")
    print("  ✅ Agent会开仓（不再全都hold）")
    print("  ✅ 高恐惧Agent更频繁平仓")
    print("  ✅ 高恐惧Agent存活率更高")
    print()
    print("💡 核心突破:")
    print("  fear_of_death现在在真实Daimon决策中发挥作用了！")
    print("  高恐惧vs低恐惧形成明确的生存策略差异！")
    print()
    print("🧬 这才是真正的进化压力！")
    print("  温和市场 → 低恐惧者繁荣（敢于冒险）")
    print("  残酷市场 → 高恐惧者生存（保守求生）")
elif opening_pass:
    print("⚠️ **Daimon改进部分成功**")
    print()
    print(f"  ✅ Agent会开仓了")
    print(f"  {'✅' if closing_pass else '❌'} 平仓行为差异")
    print(f"  {'✅' if survival_pass else '❌'} 存活率差异")
    print()
    print("可能需要：")
    print("  • 进一步调整fear_threshold公式")
    print("  • 增加fear_of_death在close决策中的权重")
    print("  • 更多轮次观察")
else:
    print("❌ **Daimon改进仍不足**")
    print()
    print("Agent仍然不开仓，需要：")
    print("  1. 检查risk_appetite的阈值设置")
    print("  2. 检查Daimon的权重配置")
    print("  3. 可能需要更强的market信号")

print()

