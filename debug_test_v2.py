#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试进化 - 改进版，正确捕获所有日志"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置logging输出到文件和控制台
OUTPUT_FILE = 'DEBUG_V2.txt'

# 创建文件handler
file_handler = logging.FileHandler(OUTPUT_FILE, 'w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s - %(message)s'))

# 创建控制台handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

# 配置root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

print("="*70)
print("Debug v5.0 Evolution System")
print("="*70)

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 创建
logger.info("Creating Moirai...")
moirai = Moirai(bulletin_board=None, num_families=50)
moirai.next_agent_id = 1

# 创建Agent
logger.info("Creating 10 Agents...")
agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
moirai.agents = agents
logger.info(f"Created {len(agents)} Agents")

# 模拟交易
logger.info("Setting trading results...")
for i, agent in enumerate(agents):
    if i < 5:
        agent.total_pnl = 500
        agent.current_capital = 10500
        agent.trade_count = 10
        agent.win_count = 7
        logger.info(f"  {agent.agent_id}: +500 (profit)")
    else:
        agent.total_pnl = -300
        agent.current_capital = 9700
        agent.trade_count = 10
        agent.win_count = 3
        logger.info(f"  {agent.agent_id}: -300 (loss)")

# 创建进化管理器
logger.info("Creating EvolutionManager...")
evo = EvolutionManagerV5(moirai, num_families=50)

initial = len(moirai.agents)
logger.info(f"\nInitial population: {initial}")

print("\n" + "="*70)
print("Running Evolution Cycle")
print("="*70 + "\n")

# 执行进化
evo.run_evolution_cycle(90000)

final = len(moirai.agents)

print("\n" + "="*70)
print("Results:")
print(f"  Initial: {initial}")
print(f"  Final: {final}")
print(f"  Births: {evo.total_births}")
print(f"  Deaths: {evo.total_deaths}")
print(f"  Difference: {final - initial:+d}")
print("="*70)

logger.info(f"\nDetailed log written to: {OUTPUT_FILE}")
print(f"\nDetailed log written to: {OUTPUT_FILE}")

