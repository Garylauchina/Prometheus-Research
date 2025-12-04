"""快速测试v5.0基本功能"""
import sys
sys.path.insert(0, '.')

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 简单测试
print("="*70)
print("🚀 快速测试v5.0")
print("="*70)

# 1. 创建Moirai
moirai = Moirai(bulletin_board=None, num_families=50)
moirai.next_agent_id = 1

# 2. 创建Agent
print("\n创建10个Agent...")
agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
moirai.agents = agents
print(f"✅ 成功创建{len(agents)}个Agent")

# 3. 模拟交易
print("\n模拟交易...")
for i, agent in enumerate(agents):
    agent.total_pnl = 100 if i < 5 else -100
    agent.current_capital = 10000 + agent.total_pnl
    agent.trade_count = 10
    agent.win_count = 7 if i < 5 else 3

# 4. 测试进化
print("\n测试进化系统...")
evo_manager = EvolutionManagerV5(moirai, num_families=50)
initial = len(moirai.agents)

evo_manager.run_evolution_cycle(90000)

final = len(moirai.agents)

print(f"\n📊 结果:")
print(f"   初始: {initial}")
print(f"   最终: {final}")
print(f"   新生: {evo_manager.total_births}")
print(f"   死亡: {evo_manager.total_deaths}")
print(f"   差额: {final - initial}")

if abs(final - initial) <= 1:
    print("\n✅ 测试通过！")
else:
    print(f"\n❌ 测试失败！种群数量变化过大")

print("="*70)

