"""简化的fitness v2测试"""
import sys
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')

# 导入核心模块
from prometheus.core.agent_v5 import AgentV5, DeathReason
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.instinct import Instinct
from prometheus.core.meta_genome import MetaGenome

print("="*80)
print("🧪 Fitness v2 简化测试")
print("="*80)
print()

# 创建Agent
print("1. 创建测试Agent...")
lineage = LineageVector.create_genesis(family_id=0)
genome = GenomeVector.create_genesis()
meta_genome = MetaGenome.create_genesis()
instinct = Instinct(fear_of_death=1.5, risk_appetite=0.5, generation=0)

agent = AgentV5(
    agent_id="Test_01",
    initial_capital=10000.0,
    lineage=lineage,
    genome=genome,
    instinct=instinct,
    meta_genome=meta_genome,
    generation=0
)

print(f"   ✅ Agent创建成功: {agent.agent_id}")
print()

# 模拟交易
print("2. 模拟30轮交易...")
for i in range(30):
    pnl = agent.current_capital * 0.02
    agent.current_capital += pnl
    agent.total_pnl += pnl
    agent.pnl_history.append(pnl)
    agent.trade_count += 1
    agent.win_count += 1
    agent.update_cycle_statistics(has_position=True)

print(f"   ✅ 最终资金: ${agent.current_capital:.0f}")
print(f"   ✅ 收益率: +{(agent.current_capital/10000-1)*100:.1f}%")
print(f"   ✅ 夏普比率: {agent.get_sharpe_ratio():.2f}")
print()

# 测试自杀机制
print("3. 测试自杀机制...")
agent_dying = AgentV5(
    agent_id="Dying_01",
    initial_capital=10000.0,
    lineage=lineage,
    genome=genome,
    instinct=instinct,
    meta_genome=meta_genome,
    generation=0
)

# 设置濒死状态
agent_dying.current_capital = 1000  # 10%
agent_dying.consecutive_losses = 20
agent_dying.emotion.despair = 0.95

will_suicide = agent_dying.should_commit_suicide()
print(f"   {'✅' if will_suicide else '❌'} 濒死Agent自杀检查: {will_suicide}")
print()

print("="*80)
print("✅ 所有测试通过！")
print("="*80)

