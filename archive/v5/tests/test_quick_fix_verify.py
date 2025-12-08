#!/usr/bin/env python3
"""
快速验证修复 - 只测试1个种子
"""

import logging
import sys
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import run_scenario

def main():
    logger.info("=" * 80)
    logger.info("🧪 快速验证修复")
    logger.info("=" * 80)
    
    # 加载数据
    data = pd.read_csv("data/okx/BTC_USDT_1d_20251206.csv")
    prices = data['close'].values
    
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    logger.info(f"✅ 数据加载完成: {len(data)}条")
    
    # 运行测试
    logger.info("\n测试配置:")
    logger.info("  Seed: 8004")
    logger.info("  周期: 500")
    logger.info("  Agent: 50")
    logger.info("  进化间隔: 10\n")
    
    facade = run_scenario(
        mode="backtest",
        total_cycles=500,
        market_feed=make_market_feed(),
        
        # 种群配置
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        
        # 进化配置
        evo_interval=10,  # ✅ 关键参数！
        
        # 种子配置
        seed=8004,
        evolution_seed=None,
        
        # AlphaZero式配置
        full_genome_unlock=True
    )
    
    # 提取结果
    returns = []
    total_trades = 0
    
    for agent in facade.moirai.agents:
        if hasattr(agent, 'account') and agent.account:
            initial = agent.account.private_ledger.initial_capital
            current = agent.account.private_ledger.virtual_capital
            agent_return = ((current - initial) / initial) * 100
            returns.append(agent_return)
            total_trades += agent.account.private_ledger.trade_count
    
    import numpy as np
    system_return = np.mean(returns) if returns else 0.0
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 测试结果")
    logger.info("=" * 80)
    logger.info(f"系统收益: {system_return:+.2f}%")
    logger.info(f"总交易数: {total_trades}笔")
    logger.info(f"人均交易: {total_trades/len(returns):.1f}笔")
    logger.info("=" * 80)
    
    if system_return > 1000:
        logger.info("✅ 修复成功！收益恢复正常！")
    elif total_trades > 0:
        logger.info("⚠️ 有交易了，但收益偏低")
    else:
        logger.info("❌ 仍然没有交易")

if __name__ == "__main__":
    main()

