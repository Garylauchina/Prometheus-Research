#!/usr/bin/env python3
"""检查最终Agent的资金状况"""

import logging
import sys
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import run_scenario

def main():
    print("加载数据...")
    data = pd.read_csv("data/okx/BTC_USDT_1d_20251206.csv")
    prices = data['close'].values
    
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    print("运行测试...")
    facade = run_scenario(
        mode="backtest",
        total_cycles=500,
        market_feed=make_market_feed(),
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        evo_interval=10,
        seed=8004,
        evolution_seed=None,
        full_genome_unlock=True
    )
    
    print("\n" + "=" * 80)
    print("📊 最终存活Agent分析")
    print("=" * 80)
    
    for i, agent in enumerate(facade.moirai.agents[:10], 1):  # 只看前10个
        initial = agent.account.private_ledger.initial_capital
        current = agent.account.private_ledger.virtual_capital
        trades = agent.account.private_ledger.trade_count
        pnl = current - initial
        
        print(f"\nAgent {i}: {agent.agent_id}")
        print(f"  初始资金: ${initial:.2f}")
        print(f"  当前资金: ${current:.2f}")
        print(f"  盈亏: ${pnl:+.2f}")
        print(f"  交易数: {trades}笔")
        print(f"  收益率: {(pnl/initial)*100:+.2f}%")

if __name__ == "__main__":
    main()

