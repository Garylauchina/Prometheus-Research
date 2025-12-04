"""调试进化系统"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

print("="*70)
print("调试v5.0进化")
print("="*70)

# 创建Moirai（不需要bulletin_board进行测试）
moirai = Moirai(bulletin_board=None, num_families=50)
moirai.next_agent_id = 1

# 创建10个Agent
print("\n步骤1: 创建Agent")
agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
moirai.agents = agents
print(f"创建了{len(agents)}个Agent")

# 模拟交易结果
print("\n步骤2: 设置交易结果")
for i, agent in enumerate(agents):
    if i < 5:  # 前5个盈利
        agent.total_pnl = 500
        agent.current_capital = 10500
        agent.trade_count = 10
        agent.win_count = 7
        print(f"  {agent.agent_id}: 盈利 +500")
    else:  # 后5个亏损
        agent.total_pnl = -300
        agent.current_capital = 9700
        agent.trade_count = 10
        agent.win_count = 3
        print(f"  {agent.agent_id}: 亏损 -300")

# 创建进化管理器
print("\n步骤3: 创建进化管理器")
evo_manager = EvolutionManagerV5(
    moirai=moirai,
    elite_ratio=0.2,
    elimination_ratio=0.3,
    num_families=50
)

print(f"\n初始Agent数量: {len(moirai.agents)}")
print("\n步骤4: 执行进化周期")
print("-"*70)

evo_manager.run_evolution_cycle(90000)

print("-"*70)
print(f"\n最终Agent数量: {len(moirai.agents)}")
print(f"新生: {evo_manager.total_births}")
print(f"死亡: {evo_manager.total_deaths}")
print(f"差额: {len(moirai.agents) - 10}")

print("\n="*70)

