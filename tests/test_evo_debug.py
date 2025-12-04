"""调试进化 - 启用详细日志"""
import sys
sys.path.insert(0, '.')

import logging
# 启用详细日志输出到文件
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('evolution_debug.log', 'w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

print("="*70)
print("调试v5.0进化系统")
print("="*70)

# 创建Moirai
print("\n创建Moirai...")
moirai = Moirai(bulletin_board=None, num_families=50)
moirai.next_agent_id = 1

# 创建10个Agent
print("创建10个Agent...")
agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
moirai.agents = agents
print(f"成功创建{len(agents)}个Agent\n")

# 设置交易结果
print("设置交易结果...")
for i, agent in enumerate(agents):
    if i < 5:
        agent.total_pnl = 500
        agent.current_capital = 10500
        agent.trade_count = 10
        agent.win_count = 7
    else:
        agent.total_pnl = -300
        agent.current_capital = 9700
        agent.trade_count = 10
        agent.win_count = 3

# 创建进化管理器
print("创建进化管理器...")
evo = EvolutionManagerV5(moirai, num_families=50)

# 执行进化
initial = len(moirai.agents)
print(f"\n初始Agent: {initial}")
print("\n执行进化周期（详细日志见 evolution_debug.log）...")
print("-"*70)

evo.run_evolution_cycle(90000)

print("-"*70)
final = len(moirai.agents)
print(f"\n结果:")
print(f"  初始: {initial}")
print(f"  最终: {final}")
print(f"  新生: {evo.total_births}")
print(f"  死亡: {evo.total_deaths}")

print("\n详细日志已写入: evolution_debug.log")
print("="*70)

