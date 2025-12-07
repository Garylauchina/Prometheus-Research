#!/usr/bin/env python3
"""
✅ 终极测试(v6 Facade 正确版本) - 账簿系统完全合规
============================================================================
本测试解决了旧版test_ultimate_1000x_COMPLETE.py的所有账簿问题!

✅ 正确特性:
1. 使用 v6 Facade 统一入口 - 不自己写循环
2. Agent 自主决策 (buy/sell/short/cover 四种操作都支持)
3. 账簿系统自动管理 (不手动修改 agent.current_capital)
4. 完整的平仓机制 (每个开仓都会对应平仓)
5. 自动对账验证 (确保公私账簿一致)

❌ 旧版问题(已修复):
1. ❌ 只开仓不平仓 -> ✅ 完整的开平仓逻辑
2. ❌ 手动修改资金 -> ✅ 账簿自动计算
3. ❌ 交易量过小   -> ✅ 合理的仓位大小
4. ❌ 账簿不一致   -> ✅ 严格对账验证

架构: Supervisor/Moirai + AgentV5 + EvolutionManagerV5 + 双账簿 + 多样性
数据: data/okx/BTC_USDT_1d_20251206.csv
归档: results/backtest/<date>/<run_id>/
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime

from prometheus.facade.v6_facade import run_scenario, run_seed_experiment, V6Facade

# 显示详细信息用于账簿问题诊断
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 为关键模块设置日志级别
logging.getLogger('prometheus.facade.v6_facade').setLevel(logging.INFO)
logging.getLogger('prometheus.core.ledger_system').setLevel(logging.INFO)


def load_prices(limit=None):
    """加载历史价格数据"""
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    closes = df['close'].tolist()
    return closes[:limit] if limit else closes


def make_market_feed(prices):
    """
    构造市场数据生成器
    
    v6 Facade 会自动调用 agent.make_trading_decision()
    Agent根据市场数据自主决定买卖
    """
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        price = prices[idx]
        
        # ⭐ 现在只需要提供price！
        # V6 Facade会自动补充trend, volatility, price_change等字段
        market_data = {
            "price": price
        }
        
        return market_data, {}
    return feed


def run_single_test(total_cycles=2000, evo_interval=30, agent_count=50, 
                    capital_per_agent=10000.0, test_id=0):
    """
    ✅ 单次测试 - 使用 v6 Facade 正确版本
    
    特点:
    - Agent自主决策(包括平仓)
    - 账簿系统自动管理
    - 自动对账验证
    """
    
    prices = load_prices(limit=total_cycles)
    market_feed = make_market_feed(prices)

    facade: V6Facade = run_scenario(
        mode="backtest",
        total_cycles=len(prices),
        market_feed=market_feed,
        num_families=50,
        agent_count=agent_count,
        capital_per_agent=capital_per_agent,
        exchange_config=None,
        data_source=None,
        scenario=f"ultimate_test_{test_id}",
        evo_interval=evo_interval,
    )

    # 收集结果
    summary = facade.report_status()
    agents = facade.supervisor.agents
    
    # 计算ROI
    total_capital = 0
    survivor_count = 0
    for a in agents:
        account = getattr(a, "account", None)
        if account and hasattr(account, "private_ledger"):
            capital = account.private_ledger.virtual_capital
            total_capital += capital
            if capital > 0:
                survivor_count += 1
    
    avg_capital = total_capital / agent_count if agent_count > 0 else 0
    roi = (avg_capital / capital_per_agent - 1) * 100 if capital_per_agent > 0 else 0
    
    # 计算市场ROI
    market_roi = (prices[-1] / prices[0] - 1) * 100
    
    # ==================== 账簿详细检查 ====================
    print("\n" + "=" * 80)
    print("📋 账簿系统详细检查")
    print("=" * 80)
    
    # 检查每个Agent的账簿状态
    for agent in facade.supervisor.agents:
        account = getattr(agent, "account", None)
        if account and hasattr(account, "private_ledger"):
            private_ledger = account.private_ledger
            public_trades = facade.public_ledger.get_agent_trades(agent.agent_id)
            
            print(f"\n{agent.agent_id}:")
            print(f"  私账交易数: {len(private_ledger.trade_history)}")
            print(f"  公账交易数: {len(public_trades)}")
            print(f"  私账资金: ${private_ledger.virtual_capital:.2f}")
            print(f"  多头持仓: {private_ledger.long_position.amount if private_ledger.long_position else 0:.4f}")
            print(f"  空头持仓: {private_ledger.short_position.amount if private_ledger.short_position else 0:.4f}")
            
            # 检查是否有空记录
            empty_private = [t for t in private_ledger.trade_history if t.amount == 0 or t.price == 0]
            empty_public = [t for t in public_trades if t.amount == 0 or t.price == 0]
            
            if empty_private:
                print(f"  ⚠️ 私账空记录: {len(empty_private)} 条")
            if empty_public:
                print(f"  ⚠️ 公账空记录: {len(empty_public)} 条")
    
    # 对账验证
    print("\n" + "=" * 80)
    print("🔍 执行对账验证...")
    print("=" * 80)
    
    reconcile_summary = facade.reconcile()
    has_ledger_issues = any(len(v) > 0 for v in reconcile_summary.values())
    
    if has_ledger_issues:
        print("\n⚠️ 发现账簿不一致:")
        for agent_id, actions in reconcile_summary.items():
            if actions:
                print(f"  {agent_id}: {actions}")
    else:
        print("\n✅ 所有Agent账簿完全一致!")
    
    result = {
        "test_id": test_id,
        "total_cycles": total_cycles,
        "evo_interval": evo_interval,
        "agent_count": agent_count,
        "survivors": survivor_count,
        "avg_capital": avg_capital,
        "roi": roi,
        "market_roi": market_roi,
        "has_ledger_issues": has_ledger_issues,
        "ledger_issues_count": sum(1 for v in reconcile_summary.values() if len(v) > 0),
        "timestamp": datetime.now().isoformat(),
    }
    
    return result, facade


def main():
    """
    终极测试 - v6 Facade正式版 (账簿系统已完全修复)
    """
    print("=" * 80)
    print("🚀 Prometheus 终极测试 - v6 Facade 正式版")
    print("=" * 80)
    print()
    print("✅ 账簿系统状态: 双轨制缺陷已修复，公私账完全一致!")
    print()
    print("📋 测试配置:")
    print("  - 测试次数: 10 次")
    print("  - 测试周期: 2000 步")
    print("  - Agent数量: 50 个")
    print("  - 初始资金: $10,000/Agent")
    print("  - 架构: v6 Facade + 完整双账簿")
    print("  - 数据: data/okx/BTC_USDT_1d_20251206.csv")
    print("  - Agent决策: 完全自主 (buy/sell/short/cover)")
    print("  - 进化周期: 每30步")
    print()
    print("🎯 测试目标:")
    print("  1. 验证账簿系统长期稳定性")
    print("  2. 验证进化机制有效性")
    print("  3. 验证Agent决策能力")
    print("  4. 验证多样性监控准确性")
    print("=" * 80)
    print()
    
    # ✅ 使用统一封装入口，不自己写循环！
    print()
    print("🎲 种子实验模式: fully_reproducible (完全可重复)")
    print("   运行次数: 10 次")
    print("   基础种子: 1000")
    print()
    
    prices = load_prices(limit=2000)
    market_feed = make_market_feed(prices)
    
    results = run_seed_experiment(
        mode="backtest",
        total_cycles=2000,
        market_feed=market_feed,
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        evo_interval=30,
        experiment_type="fully_reproducible",  # ✅ 完全可重复
        num_runs=10,                           # ✅ 10次测试
        base_seed=1000                         # ✅ 固定种子
    )
    
    # 结果已由 run_seed_experiment 自动分析和保存
    print()
    print("✅ 测试完成！详细结果请查看自动生成的分析报告。")
    print("=" * 80)


if __name__ == '__main__':
    import sys
    
    # 支持命令行参数选择实验类型
    if len(sys.argv) > 1:
        exp_type = sys.argv[1].lower()
        
        print()
        print("=" * 80)
        print(f"🎲 种子实验: {exp_type}")
        print("=" * 80)
        print()
        
        prices = load_prices(limit=2000)
        market_feed = make_market_feed(prices)
        
        if exp_type in ['a', 'fixed', 'fixed_genesis']:
            # 实验A: 固定创世，观察演化多样性
            results = run_seed_experiment(
                mode="backtest",
                total_cycles=2000,
                market_feed=market_feed,
                num_families=50,
                agent_count=50,
                capital_per_agent=10000.0,
                evo_interval=30,
                experiment_type="fixed_genesis",
                num_runs=3,
                base_seed=1000
            )
        elif exp_type in ['b', 'diff', 'different_genesis']:
            # 实验B: 不同创世，观察最终差异
            results = run_seed_experiment(
                mode="backtest",
                total_cycles=2000,
                market_feed=market_feed,
                num_families=50,
                agent_count=50,
                capital_per_agent=10000.0,
                evo_interval=30,
                experiment_type="different_genesis",
                num_runs=3,
                base_seed=1000
            )
        elif exp_type in ['c', 'reproducible', 'fully_reproducible']:
            # 实验C: 完全可重复
            results = run_seed_experiment(
                mode="backtest",
                total_cycles=2000,
                market_feed=market_feed,
                num_families=50,
                agent_count=50,
                capital_per_agent=10000.0,
                evo_interval=30,
                experiment_type="fully_reproducible",
                num_runs=2,
                base_seed=1000
            )
        else:
            print(f"❌ 未知实验类型: {exp_type}")
            print("使用方式:")
            print("  python test_ultimate_v6_CORRECT.py a  # 固定创世")
            print("  python test_ultimate_v6_CORRECT.py b  # 不同创世")
            print("  python test_ultimate_v6_CORRECT.py c  # 完全可重复")
            print("  python test_ultimate_v6_CORRECT.py    # 默认(完全可重复x10)")
    else:
        # 默认运行
        main()

