#!/usr/bin/env python3
"""
创世探索方案验证 - 20%配资测试
==================================

测试目标：
1. 验证20%配资逻辑正确性
2. 验证资金池80%储备机制
3. 验证资金守恒

测试配置：
- 系统注资: $500,000
- 创世配资: 20% ($100,000)
- Agent数: 50
- 每个Agent: $2,000
- 资金池储备: 80% ($400,000)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json

# 设置日志
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"results/genesis_20pct_{timestamp}.log"
Path("results").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import V6Facade


def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("🧪 创世探索方案验证 - 20%配资测试")
    logger.info("=" * 80)
    logger.info("")
    
    # 测试配置
    agent_count = 50
    capital_per_agent_target = 10000.0  # 目标规模
    genesis_allocation_ratio = 0.2  # 20%配资
    
    # 预期结果
    expected_system_investment = agent_count * capital_per_agent_target  # $500,000
    expected_genesis_allocation = expected_system_investment * genesis_allocation_ratio  # $100,000
    expected_capital_per_agent = expected_genesis_allocation / agent_count  # $2,000
    expected_pool_reserve = expected_system_investment - expected_genesis_allocation  # $400,000
    
    logger.info("📋 测试配置：")
    logger.info(f"  Agent数: {agent_count}")
    logger.info(f"  目标规模: ${capital_per_agent_target:,.2f}/Agent")
    logger.info(f"  配资比例: {genesis_allocation_ratio:.0%}")
    logger.info("")
    logger.info("📊 预期结果：")
    logger.info(f"  系统注资: ${expected_system_investment:,.2f}")
    logger.info(f"  创世分配: ${expected_genesis_allocation:,.2f} ({genesis_allocation_ratio:.0%})")
    logger.info(f"  每个Agent: ${expected_capital_per_agent:,.2f}")
    logger.info(f"  资金池储备: ${expected_pool_reserve:,.2f} ({(1-genesis_allocation_ratio):.0%})")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # 设置种子
    import random
    import numpy as np
    random.seed(7001)
    np.random.seed(7001)
    
    # 直接构建Facade（不使用build_facade以避免重复init_population）
    logger.info("🏗️  构建Facade...")
    facade = V6Facade(num_families=50, exchange=None)  # ✅ 测试只需验证资金池，不需要真实exchange
    facade.scenario = "backtest"
    facade.evo_interval = 10
    
    # 初始化种群（使用20%配资）
    logger.info("🌱 初始化种群（20%配资）...")
    logger.info("")
    facade.init_population(
        agent_count=agent_count,
        capital_per_agent=capital_per_agent_target,
        full_genome_unlock=True,
        genesis_allocation_ratio=genesis_allocation_ratio  # ✅ 20%配资
    )
    logger.info("")
    
    # 验证结果
    logger.info("=" * 80)
    logger.info("🔍 验证结果")
    logger.info("=" * 80)
    
    # 1. 验证资金池状态
    capital_report = facade.get_capital_report()
    actual_invested = capital_report['pool']['total_invested']
    actual_allocated = capital_report['pool']['allocated']
    actual_pool_available = capital_report['pool']['available']
    
    logger.info(f"1️⃣ 资金池验证：")
    logger.info(f"   系统注资: ${actual_invested:,.2f} (预期: ${expected_system_investment:,.2f}) {'✅' if abs(actual_invested - expected_system_investment) < 1 else '❌'}")
    logger.info(f"   已分配: ${actual_allocated:,.2f} (预期: ${expected_genesis_allocation:,.2f}) {'✅' if abs(actual_allocated - expected_genesis_allocation) < 1 else '❌'}")
    logger.info(f"   余额: ${actual_pool_available:,.2f} (预期: ${expected_pool_reserve:,.2f}) {'✅' if abs(actual_pool_available - expected_pool_reserve) < 1 else '❌'}")
    logger.info("")
    
    # 2. 验证Agent初始资金
    actual_agents = len(facade.moirai.agents)
    if actual_agents > 0:
        sample_agent = facade.moirai.agents[0]
        sample_capital = sample_agent.account.private_ledger.virtual_capital
        logger.info(f"2️⃣ Agent初始资金验证：")
        logger.info(f"   Agent数: {actual_agents} (预期: {agent_count}) {'✅' if actual_agents == agent_count else '❌'}")
        logger.info(f"   样本Agent: {sample_agent.agent_id}")
        logger.info(f"   初始资金: ${sample_capital:,.2f} (预期: ${expected_capital_per_agent:,.2f}) {'✅' if abs(sample_capital - expected_capital_per_agent) < 1 else '❌'}")
        logger.info("")
    
    # 3. 验证资金守恒
    total_capital_in_system = actual_allocated + actual_pool_available
    logger.info(f"3️⃣ 资金守恒验证：")
    logger.info(f"   系统注资: ${actual_invested:,.2f}")
    logger.info(f"   系统总额: ${total_capital_in_system:,.2f} (已分配 + 池余额)")
    logger.info(f"   差异: ${abs(actual_invested - total_capital_in_system):.2f} {'✅' if abs(actual_invested - total_capital_in_system) < 1 else '❌'}")
    logger.info("")
    
    # 4. 统计摘要
    logger.info("=" * 80)
    logger.info("📊 统计摘要")
    logger.info("=" * 80)
    logger.info(f"✅ 系统注资: ${actual_invested:,.2f}")
    logger.info(f"✅ 创世分配: ${actual_allocated:,.2f} ({actual_allocated/actual_invested*100:.1f}%)")
    logger.info(f"✅ 资金池储备: ${actual_pool_available:,.2f} ({actual_pool_available/actual_invested*100:.1f}%)")
    logger.info(f"✅ Agent数: {actual_agents}")
    logger.info(f"✅ 每个Agent: ${sample_capital:,.2f}")
    logger.info("")
    logger.info(f"🎯 创世探索方案验证: {'✅ 通过' if abs(actual_pool_available - expected_pool_reserve) < 1 else '❌ 失败'}")
    logger.info("=" * 80)
    
    # 保存结果
    result = {
        "test": "genesis_allocation_20pct",
        "config": {
            "agent_count": agent_count,
            "capital_per_agent_target": capital_per_agent_target,
            "genesis_allocation_ratio": genesis_allocation_ratio
        },
        "expected": {
            "system_investment": expected_system_investment,
            "genesis_allocation": expected_genesis_allocation,
            "capital_per_agent": expected_capital_per_agent,
            "pool_reserve": expected_pool_reserve
        },
        "actual": {
            "system_investment": actual_invested,
            "genesis_allocation": actual_allocated,
            "capital_per_agent": sample_capital,
            "pool_reserve": actual_pool_available
        },
        "verification": {
            "capital_conservation": abs(actual_invested - total_capital_in_system) < 1,
            "allocation_ratio_correct": abs(actual_allocated - expected_genesis_allocation) < 1,
            "reserve_ratio_correct": abs(actual_pool_available - expected_pool_reserve) < 1
        },
        "log_file": log_file
    }
    
    result_file = f"results/genesis_20pct_{timestamp}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 结果已保存: {result_file}")
    logger.info(f"📄 日志文件: {log_file}")


if __name__ == "__main__":
    main()

