"""
极端市场对比测试 v2 - 真正的决策测试

核心改进：
- ✅ Agent调用Daimon做决策
- ✅ fear_of_death参与投票
- ✅ 模拟持仓、开仓、平仓
- ✅ 高恐惧Agent可以选择避险
- ✅ 低恐惧Agent可以选择冒险

实验设计：
- 对照组A：20个高恐惧Agent (fear_of_death = 1.7-1.9)
- 对照组B：20个低恐惧Agent (fear_of_death = 0.2-0.4)
- 环境：极端市场（高波动，80%亏损概率）
- 观察：存活率、决策差异、fear_of_death是否真的影响生死

Author: Prometheus Team
Version: v5.2实验性 v2
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
print("🔥 极端市场对比测试 v2：真正的决策测试")
print("="*80)
print("核心改进：Agent调用Daimon，fear_of_death真正参与决策")
print()

# ============================================================================
# 配置
# ============================================================================
GROUP_SIZE = 20
INITIAL_CAPITAL = 10000.0
EXTREME_CYCLES = 30  # 增加到30轮
DEATH_THRESHOLD = 3000.0  # 30%存活线

print(f"📋 实验配置:")
print(f"   每组人数: {GROUP_SIZE}个Agent")
print(f"   初始资金: ${INITIAL_CAPITAL}")
print(f"   死亡阈值: ${DEATH_THRESHOLD} (30%)")
print(f"   测试轮数: {EXTREME_CYCLES}轮")
print()

# ============================================================================
# 创建对照组
# ============================================================================
print("="*80)
print("📊 [1/3] 创建对照组")
print("="*80)
print()

def create_agent_with_fear(fear_value: float, agent_id: str) -> AgentV5:
    """创建指定fear_of_death的Agent"""
    instinct = Instinct(
        fear_of_death=fear_value,
        reproductive_drive=0.5,
        loss_aversion=0.5,
        risk_appetite=0.5,
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
    agent.position = {}  # 无持仓
    agent.consecutive_losses = 0
    agent.total_pnl = 0
    agent.trade_count = 0
    
    return agent

# 组A：高恐惧Agent
print("创建组A：高恐惧Agent...")
group_A = []
for i in range(GROUP_SIZE):
    fear = random.uniform(1.7, 1.9)
    agent = create_agent_with_fear(fear, f"HighFear_{i+1}")
    group_A.append(agent)

fear_A = [agent.instinct.fear_of_death for agent in group_A]
print(f"  ✅ 组A创建完成: fear平均{np.mean(fear_A):.3f}, 范围[{np.min(fear_A):.3f}, {np.max(fear_A):.3f}]")
print()

# 组B：低恐惧Agent
print("创建组B：低恐惧Agent...")
group_B = []
for i in range(GROUP_SIZE):
    fear = random.uniform(0.2, 0.4)
    agent = create_agent_with_fear(fear, f"LowFear_{i+1}")
    group_B.append(agent)

fear_B = [agent.instinct.fear_of_death for agent in group_B]
print(f"  ✅ 组B创建完成: fear平均{np.mean(fear_B):.3f}, 范围[{np.min(fear_B):.3f}, {np.max(fear_B):.3f}]")
print()

# ============================================================================
# 极端市场决策测试（让Agent真正决策！）
# ============================================================================
print("="*80)
print("📉 [2/3] 极端市场决策测试")
print("="*80)
print("市场条件：高波动，80%亏损概率")
print("关键改进：Agent调用Daimon做决策，fear_of_death参与投票")
print()

def simulate_extreme_market_with_decisions(agents: list, cycles: int, death_threshold: float, group_name: str):
    """
    模拟极端市场 - 让Agent真正做决策
    
    关键改进：
    1. Agent调用daimon.make_decision()
    2. 根据决策执行不同的交易
    3. fear_of_death可以投票'close'或'hold'来避险
    """
    alive = agents.copy()
    dead = []
    
    # 统计决策
    decision_stats = {
        'buy': 0, 'sell': 0, 'close': 0, 'hold': 0
    }
    
    for cycle in range(1, cycles + 1):
        # 构造市场环境（极端波动）
        base_price = 50000
        price_change = random.uniform(-0.15, 0.15)  # ±15%波动
        current_price = base_price * (1 + price_change)
        
        # 市场趋势（80%概率下跌）
        if random.random() < 0.80:
            trend = 'bearish'  # 下跌
            market_pnl_factor = -1
        else:
            trend = 'bullish'  # 上涨
            market_pnl_factor = 1
        
        cycle_actions = {'buy': 0, 'sell': 0, 'close': 0, 'hold': 0}
        
        for agent in alive[:]:
            # 1. 构造context（Agent的当前状态）
            capital_ratio = agent.current_capital / agent.initial_capital
            recent_pnl = agent.total_pnl / agent.initial_capital if agent.trade_count > 0 else 0
            
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
            
            # 2. Agent调用Daimon做决策
            try:
                decision = agent.daimon.make_decision(context)
                action = decision.action
            except Exception as e:
                # 如果决策失败，默认hold
                action = 'hold'
            
            decision_stats[action] += 1
            cycle_actions[action] += 1
            
            # 3. 根据决策执行交易，模拟盈亏
            pnl = 0
            
            if action == 'buy':
                # 开多仓
                agent.position = {'side': 'long', 'size': 1.0}
                agent.trade_count += 1
                
                # 盈亏：多头在上涨市场赚钱，下跌市场亏钱
                if trend == 'bullish':
                    pnl = agent.current_capital * random.uniform(0.05, 0.10)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.10, 0.20)
                    agent.consecutive_losses += 1
            
            elif action == 'sell':
                # 开空仓
                agent.position = {'side': 'short', 'size': 1.0}
                agent.trade_count += 1
                
                # 盈亏：空头在下跌市场赚钱，上涨市场亏钱
                if trend == 'bearish':
                    pnl = agent.current_capital * random.uniform(0.05, 0.10)
                    agent.consecutive_losses = 0
                else:
                    pnl = -agent.current_capital * random.uniform(0.10, 0.20)
                    agent.consecutive_losses += 1
            
            elif action == 'close':
                # 平仓（fear_of_death可能触发这个！）
                if agent.position:
                    # 有持仓，平仓避免继续亏损
                    agent.position = {}
                    pnl = 0  # 平仓，不继续亏损
                    agent.consecutive_losses = 0
                else:
                    # 无持仓，close等同于hold
                    pnl = 0
            
            else:  # hold
                # 观望
                if agent.position:
                    # 持仓期间，继续受市场影响
                    if agent.position['side'] == 'long':
                        if trend == 'bullish':
                            pnl = agent.current_capital * random.uniform(0.02, 0.05)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.05, 0.10)
                            agent.consecutive_losses += 1
                    else:  # short
                        if trend == 'bearish':
                            pnl = agent.current_capital * random.uniform(0.02, 0.05)
                            agent.consecutive_losses = 0
                        else:
                            pnl = -agent.current_capital * random.uniform(0.05, 0.10)
                            agent.consecutive_losses += 1
                else:
                    # 无持仓，观望，不受影响
                    pnl = 0
            
            # 4. 更新Agent状态
            agent.current_capital += pnl
            agent.total_pnl += pnl
            
            # 5. 检查是否死亡
            if agent.current_capital < death_threshold:
                alive.remove(agent)
                dead.append((agent, cycle, agent.current_capital))
        
        # 输出当前状态
        alive_count = len(alive)
        dead_count = len(dead)
        
        if alive_count == 0:
            print(f"  周期{cycle:2d}: 💀 全灭！")
            break
        else:
            avg_capital = np.mean([a.current_capital for a in alive])
            print(f"  周期{cycle:2d}: 存活{alive_count:2d}个, 平均${avg_capital:.0f}, 决策[B:{cycle_actions['buy']} S:{cycle_actions['sell']} C:{cycle_actions['close']} H:{cycle_actions['hold']}]")
    
    return alive, dead, decision_stats

# 测试组A（高恐惧）
print("\n🛡️  组A（高恐惧）进入极端市场...")
print("   预期：更频繁选择'close'或'hold'来避险")
print()
alive_A, dead_A, stats_A = simulate_extreme_market_with_decisions(group_A, EXTREME_CYCLES, DEATH_THRESHOLD, "组A")

print()
print(f"组A结果:")
print(f"  存活: {len(alive_A)}/{GROUP_SIZE} ({len(alive_A)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_A)}/{GROUP_SIZE} ({len(dead_A)/GROUP_SIZE:.1%})")
if alive_A:
    avg_capital_A = np.mean([a.current_capital for a in alive_A])
    print(f"  存活者平均资金: ${avg_capital_A:.0f}")

print(f"\n  决策统计:")
print(f"    Buy:   {stats_A['buy']:4d}次 ({stats_A['buy']/sum(stats_A.values()):.1%})")
print(f"    Sell:  {stats_A['sell']:4d}次 ({stats_A['sell']/sum(stats_A.values()):.1%})")
print(f"    Close: {stats_A['close']:4d}次 ({stats_A['close']/sum(stats_A.values()):.1%}) ← 避险")
print(f"    Hold:  {stats_A['hold']:4d}次 ({stats_A['hold']/sum(stats_A.values()):.1%}) ← 观望")
print()

# 测试组B（低恐惧）
print("⚔️  组B（低恐惧）进入极端市场...")
print("   预期：更频繁选择'buy'或'sell'来冒险")
print()
alive_B, dead_B, stats_B = simulate_extreme_market_with_decisions(group_B, EXTREME_CYCLES, DEATH_THRESHOLD, "组B")

print()
print(f"组B结果:")
print(f"  存活: {len(alive_B)}/{GROUP_SIZE} ({len(alive_B)/GROUP_SIZE:.1%})")
print(f"  死亡: {len(dead_B)}/{GROUP_SIZE} ({len(dead_B)/GROUP_SIZE:.1%})")
if alive_B:
    avg_capital_B = np.mean([a.current_capital for a in alive_B])
    print(f"  存活者平均资金: ${avg_capital_B:.0f}")

print(f"\n  决策统计:")
print(f"    Buy:   {stats_B['buy']:4d}次 ({stats_B['buy']/sum(stats_B.values()):.1%})")
print(f"    Sell:  {stats_B['sell']:4d}次 ({stats_B['sell']/sum(stats_B.values()):.1%})")
print(f"    Close: {stats_B['close']:4d}次 ({stats_B['close']/sum(stats_B.values()):.1%}) ← 避险")
print(f"    Hold:  {stats_B['hold']:4d}次 ({stats_B['hold']/sum(stats_B.values()):.1%}) ← 观望")
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
    diff = len(alive_A) - len(alive_B)
    print(f"   ✅ 高恐惧者多存活{diff}个 (+{diff/GROUP_SIZE:.1%})")
    survival_winner = "高恐惧"
elif len(alive_B) > len(alive_A):
    diff = len(alive_B) - len(alive_A)
    print(f"   ⚠️ 低恐惧者多存活{diff}个 (+{diff/GROUP_SIZE:.1%})")
    survival_winner = "低恐惧"
else:
    print(f"   ⚖️ 平局")
    survival_winner = "平局"
print()

print("2️⃣  决策行为对比:")
total_A = sum(stats_A.values())
total_B = sum(stats_B.values())

print(f"   避险行为（Close + Hold）:")
print(f"     组A: {stats_A['close'] + stats_A['hold']}/{total_A} ({(stats_A['close'] + stats_A['hold'])/total_A:.1%})")
print(f"     组B: {stats_B['close'] + stats_B['hold']}/{total_B} ({(stats_B['close'] + stats_B['hold'])/total_B:.1%})")

print(f"\n   冒险行为（Buy + Sell）:")
print(f"     组A: {stats_A['buy'] + stats_A['sell']}/{total_A} ({(stats_A['buy'] + stats_A['sell'])/total_A:.1%})")
print(f"     组B: {stats_B['buy'] + stats_B['sell']}/{total_B} ({(stats_B['buy'] + stats_B['sell'])/total_B:.1%})")

avoid_ratio_A = (stats_A['close'] + stats_A['hold']) / total_A
avoid_ratio_B = (stats_B['close'] + stats_B['hold']) / total_B

if avoid_ratio_A > avoid_ratio_B:
    print(f"\n   ✅ 高恐惧者更倾向避险 ({avoid_ratio_A:.1%} vs {avoid_ratio_B:.1%})")
    behavior_match = True
else:
    print(f"\n   ⚠️ 低恐惧者更倾向避险 ({avoid_ratio_B:.1%} vs {avoid_ratio_A:.1%})")
    behavior_match = False
print()

# ============================================================================
# 最终判断
# ============================================================================
print("="*80)
print("🏁 最终判断")
print("="*80)
print()

if survival_winner == "高恐惧" and behavior_match:
    print("🎉 **fear_of_death实验成功！**")
    print()
    print("验证结果:")
    print("  ✅ 高恐惧Agent存活率更高")
    print("  ✅ 高恐惧Agent更倾向避险行为")
    print("  ✅ fear_of_death真正影响了决策和生死")
    print()
    print("💡 核心发现:")
    print("  • fear_of_death形成了明确的生存策略差异")
    print("  • 高恐惧 = 保守 = 容易存活")
    print("  • 低恐惧 = 激进 = 容易死亡")
    print()
    print("🧬 这才是真正的进化压力！")
elif behavior_match:
    print("⚠️ **fear_of_death部分有效**")
    print()
    print("验证结果:")
    if survival_winner == "平局":
        print("  ⚖️ 存活率相同，但行为差异明显")
    else:
        print("  ⚠️ 低恐惧者存活率更高（意外）")
    print("  ✅ 高恐惧Agent更倾向避险行为")
    print()
    print("可能原因:")
    print("  • fear_of_death影响了行为，但市场太极端")
    print("  • 或者需要更多轮次观察")
else:
    print("❌ **fear_of_death效果不明显**")
    print()
    print("需要进一步调查:")
    print("  1. fear_of_death的触发阈值是否合理")
    print("  2. Daimon的权重分配是否合理")
    print("  3. 测试参数是否需要调整")

print()

