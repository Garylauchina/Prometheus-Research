#!/usr/bin/env python3
"""单种子完整测试 - 使用Phase 2A的正确逻辑"""

import logging
import sys
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import run_scenario

def main():
    print("=" * 80)
    print("🧪 单种子完整测试 (Seed 8004)")
    print("=" * 80)
    
    # 加载数据
    data = pd.read_csv("data/okx/BTC_USDT_1d_20251206.csv")
    prices = data['close'].values
    
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    # 运行测试
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
    
    # 提取结果（包含未实现盈亏）
    returns = []
    total_trades = 0
    final_price = prices[-1]
    
    for agent in facade.moirai.agents:
        if hasattr(agent, 'account') and agent.account:
            initial = agent.account.private_ledger.initial_capital
            # ✅ 包含未实现盈亏
            current = agent.account.private_ledger.virtual_capital + agent.calculate_unrealized_pnl(final_price)
            agent_return = ((current - initial) / initial) * 100
            returns.append(agent_return)
            total_trades += agent.account.private_ledger.trade_count
    
    system_return = np.mean(returns) if returns else 0.0
    
    print("\n" + "=" * 80)
    print("📊 测试结果")
    print("=" * 80)
    print(f"系统收益: {system_return:+.2f}%")
    print(f"总交易数: {total_trades}笔")
    print(f"人均交易: {total_trades/len(returns):.1f}笔")
    print(f"最终价格: ${final_price:.2f}")
    print("=" * 80)
    
    # 显示前5个Agent的详情
    print("\n前5个Agent详情:")
    for i, agent in enumerate(facade.moirai.agents[:5], 1):
        if hasattr(agent, 'account') and agent.account:
            initial = agent.account.private_ledger.initial_capital
            virt_cap = agent.account.private_ledger.virtual_capital
            unrealized = agent.calculate_unrealized_pnl(final_price)
            current = virt_cap + unrealized
            ret = ((current - initial) / initial) * 100
            
            print(f"\nAgent {i}: {agent.agent_id}")
            print(f"  初始资金: ${initial:.2f}")
            print(f"  已实现资金: ${virt_cap:.2f}")
            print(f"  未实现盈亏: ${unrealized:+.2f}")
            print(f"  总资金: ${current:.2f}")
            print(f"  收益率: {ret:+.2f}%")
            print(f"  交易数: {agent.account.private_ledger.trade_count}笔")
    
    if system_return > 1000:
        print("\n🎉 成功！收益超过1000%！")
    elif system_return > 0:
        print("\n✅ 有盈利，但低于预期")
    else:
        print("\n❌ 系统亏损")

if __name__ == "__main__":
    main()

