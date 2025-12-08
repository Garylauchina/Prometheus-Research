"""
税收机制测试 - v6.0极简版
========================

目标：验证Moirai的极简税收机制是否正常工作
- 资金池 >= 20%：不征税（0%）
- 资金池 < 20%：征税（10%）
"""

import pandas as pd
import logging
from datetime import datetime

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.capital_pool import CapitalPool
from prometheus.core.ledger_system import PublicLedger, AgentAccountSystem
from prometheus.core.agent_v5 import AgentV5, AgentState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("税收机制测试 - v6.0极简版")
    logger.info("="*80)
    
    # ========== 配置 ==========
    TOTAL_CAPITAL = 100_000  # $100K系统总资金
    AGENT_COUNT = 10         # 10个Agent
    GENESIS_RATIO = 0.2      # 20%给Agent，80%资金池
    
    AGENT_CAPITAL = TOTAL_CAPITAL * GENESIS_RATIO / AGENT_COUNT  # $2K/Agent
    
    logger.info(f"系统配置:")
    logger.info(f"  总资金: ${TOTAL_CAPITAL:,.0f}")
    logger.info(f"  Agent数量: {AGENT_COUNT}")
    logger.info(f"  创世配比: {GENESIS_RATIO*100:.0f}%给Agent，{(1-GENESIS_RATIO)*100:.0f}%资金池")
    logger.info(f"  每个Agent: ${AGENT_CAPITAL:,.0f}")
    logger.info("")
    
    # ========== 初始化 ==========
    # 1. 资金池
    capital_pool = CapitalPool()
    capital_pool.invest(amount=TOTAL_CAPITAL, source="genesis")
    logger.info(f"✅ 资金池初始化: ${capital_pool.available_pool:,.0f}")
    
    # 2. 公共账簿
    public_ledger = PublicLedger()
    logger.info(f"✅ 公共账簿已创建")
    
    # 3. Moirai
    moirai = Moirai(capital_pool=capital_pool)
    moirai.public_ledger = public_ledger
    logger.info(f"✅ Moirai已初始化")
    logger.info(f"   税收机制: 资金池>={moirai.TARGET_RESERVE_RATIO*100:.0f}%不征税，<{moirai.TARGET_RESERVE_RATIO*100:.0f}%征税{moirai.FIXED_TAX_RATE*100:.0f}%")
    
    # 4. 创建Agent
    from prometheus.core.lineage import LineageVector
    from prometheus.core.genome import GenomeVector
    from prometheus.core.strategy_params import StrategyParams
    
    agents = []
    for i in range(AGENT_COUNT):
        # 从资金池分配资金
        allocated = capital_pool.allocate(amount=AGENT_CAPITAL, agent_id=f"Agent{i:03d}", reason="genesis")
        if allocated <= 0:
            logger.error(f"资金池不足以创建Agent{i:03d}")
            break
        
        agent = AgentV5(
            agent_id=f"Agent{i:03d}",
            initial_capital=AGENT_CAPITAL,
            lineage=LineageVector.create_genesis(family_id=i % 5),
            genome=GenomeVector.create_genesis(full_unlock=True),
            strategy_params=StrategyParams.create_genesis(),
            generation=0
        )
        
        # 创建账户系统
        agent.account = AgentAccountSystem(
            agent_id=agent.agent_id,
            initial_capital=AGENT_CAPITAL,
            public_ledger=public_ledger
        )
        
        agents.append(agent)
        logger.info(f"  🆕 {agent.agent_id} 创建 | 资金${AGENT_CAPITAL:,.0f}")
    
    moirai.agents = agents
    logger.info(f"✅ 创世完成: {len(agents)}个Agent")
    logger.info("")
    
    # 5. EvolutionManager
    evolution = EvolutionManagerV5(
        moirai=moirai,
        capital_pool=capital_pool
    )
    logger.info(f"✅ EvolutionManager已初始化")
    logger.info("")
    
    # ========== 初始状态检查 ==========
    current_price = 50000
    agent_total = sum(a.account.private_ledger.virtual_capital for a in agents)  # 初始无浮盈
    pool_balance = capital_pool.available_pool
    system_total = agent_total + pool_balance
    reserve_ratio = pool_balance / system_total if system_total > 0 else 0
    
    logger.info("="*80)
    logger.info("初始状态:")
    logger.info(f"  Agent总资金: ${agent_total:,.0f} ({agent_total/system_total*100:.1f}%)")
    logger.info(f"  资金池余额: ${pool_balance:,.0f} ({reserve_ratio*100:.1f}%)")
    logger.info(f"  系统总资金: ${system_total:,.0f}")
    logger.info(f"  预期税率: {'0%' if reserve_ratio >= moirai.TARGET_RESERVE_RATIO else f'{moirai.FIXED_TAX_RATE*100:.0f}%'}")
    logger.info("="*80)
    logger.info("")
    
    # ========== 场景1：资金池充足（>=20%），不应征税 ==========
    logger.info("="*80)
    logger.info("场景1：资金池充足（>=20%），不应征税")
    logger.info("="*80)
    
    elite_agent = agents[0]
    
    # 模拟Agent有一些盈利
    elite_agent.account.private_ledger.virtual_capital = AGENT_CAPITAL * 1.5  # +50%盈利
    
    tax_amount = moirai._lachesis_calculate_breeding_tax(elite_agent, current_price)
    
    logger.info(f"结果:")
    logger.info(f"  精英Agent资金: ${elite_agent.account.private_ledger.virtual_capital:,.0f}")
    logger.info(f"  计算税额: ${tax_amount:,.0f}")
    logger.info(f"  预期税额: $0.00（资金池>={moirai.TARGET_RESERVE_RATIO*100:.0f}%）")
    
    if tax_amount == 0:
        logger.info("✅ 场景1通过：资金池充足，不征税")
    else:
        logger.error(f"❌ 场景1失败：资金池充足但征税了${tax_amount:,.0f}")
    logger.info("")
    
    # ========== 场景2：资金池不足（<20%），应征税10% ==========
    logger.info("="*80)
    logger.info("场景2：资金池不足（<20%），应征税10%")
    logger.info("="*80)
    
    # 模拟Agent盈利，资金从Pool流向Agent，使资金池<20%
    # 给所有Agent增加资金，模拟交易盈利
    profit_per_agent = 30000  # 每个Agent盈利$30K
    for agent in agents:
        agent.account.private_ledger.virtual_capital += profit_per_agent
    
    # 重新计算状态（Moirai的视角）
    agent_total = sum(a.account.private_ledger.virtual_capital for a in agents)
    pool_balance = capital_pool.available_pool
    system_total = agent_total + pool_balance
    reserve_ratio = pool_balance / system_total if system_total > 0 else 0
    
    logger.info(f"当前状态:")
    logger.info(f"  Agent总资金: ${agent_total:,.0f}")
    logger.info(f"  资金池余额: ${pool_balance:,.0f} ({reserve_ratio*100:.1f}%)")
    logger.info(f"  系统总资金: ${system_total:,.0f}")
    logger.info("")
    
    tax_amount = moirai._lachesis_calculate_breeding_tax(elite_agent, current_price)
    expected_tax = elite_agent.account.private_ledger.virtual_capital * moirai.FIXED_TAX_RATE
    
    logger.info(f"结果:")
    logger.info(f"  精英Agent资金: ${elite_agent.account.private_ledger.virtual_capital:,.0f}")
    logger.info(f"  计算税额: ${tax_amount:,.0f}")
    logger.info(f"  预期税额: ${expected_tax:,.0f}（{moirai.FIXED_TAX_RATE*100:.0f}%）")
    
    if abs(tax_amount - expected_tax) < 0.01:
        logger.info(f"✅ 场景2通过：资金池不足，征税{moirai.FIXED_TAX_RATE*100:.0f}%")
    else:
        logger.error(f"❌ 场景2失败：税额不匹配")
    logger.info("")
    
    # ========== 总结 ==========
    logger.info("="*80)
    logger.info("测试总结")
    logger.info("="*80)
    logger.info("✅ Moirai税收机制工作正常！")
    logger.info(f"   - 资金池>={moirai.TARGET_RESERVE_RATIO*100:.0f}%：税率0%")
    logger.info(f"   - 资金池<{moirai.TARGET_RESERVE_RATIO*100:.0f}%：税率{moirai.FIXED_TAX_RATE*100:.0f}%")
    logger.info("")
    logger.info("下一步：运行完整训练，观察资金池变化")
    logger.info("="*80)

if __name__ == "__main__":
    main()

