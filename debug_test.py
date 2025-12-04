#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试进化 - 查看详细日志"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)

OUTPUT_FILE = 'DEBUG.txt'

# 重定向日志到文件
class TeeLogger:
    def __init__(self, filename):
        self.file = open(filename, 'w', encoding='utf-8')
        self.stdout = sys.stdout
        
    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)
        self.file.flush()
    
    def flush(self):
        self.stdout.flush()
        self.file.flush()

sys.stdout = TeeLogger(OUTPUT_FILE)

print("="*70)
print("调试v5.0进化系统")
print("="*70)

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 创建
print("\n创建Moirai...")
moirai = Moirai(bulletin_board=None, num_families=50)
moirai.next_agent_id = 1

# 创建Agent
print("创建10个Agent...")
agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
moirai.agents = agents
print(f"创建成功: {len(agents)}个\n")

# 模拟交易
print("设置交易结果...")
for i, agent in enumerate(agents):
    if i < 5:
        agent.total_pnl = 500
        agent.current_capital = 10500
        agent.trade_count = 10
        agent.win_count = 7
        print(f"  {agent.agent_id}: +500")
    else:
        agent.total_pnl = -300
        agent.current_capital = 9700
        agent.trade_count = 10
        agent.win_count = 3
        print(f"  {agent.agent_id}: -300")

# 创建进化管理器
print("\n创建进化管理器...")
evo = EvolutionManagerV5(moirai, num_families=50)

print(f"\n初始: {len(moirai.agents)}")
print("\n" + "="*70)
print("执行进化周期")
print("="*70)

evo.run_evolution_cycle(90000)

print("="*70)
print(f"最终: {len(moirai.agents)}")
print(f"新生: {evo.total_births}")
print(f"死亡: {evo.total_deaths}")
print("="*70)

sys.stdout.file.close()
print(f"\n详细输出已写入: {OUTPUT_FILE}")

