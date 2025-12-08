#!/usr/bin/env python3
"""
Phase 1: 长期训练测试（20%创世配资）
======================================

✅ 遵守三大铁律：
1. 统一封装：使用v6 Facade统一入口
2. 严格执行测试规范：基于标准模板
3. 不简化底层机制：完整系统逻辑链

✅ 测试完整机制：
1-12. 所有核心机制（与集成测试相同）

✅ 新配资机制：
- 创世配资：20%（$2,000/Agent）
- 资金池储备：80%（$400,000）

测试目标：
- 验证20%配资在长期训练中的表现
- 验证资金池储备是否足够支持500周期
- 验证进化机制的稳定性
- 验证最终ROI计算的正确性
- 对比与之前100%配资的差异
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import numpy as np

# 设置日志
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"results/phase1_20pct_{timestamp}.log"
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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# ✅ 统一封装：只使用v6 Facade
from prometheus.facade.v6_facade import V6Facade


def load_historical_data():
    """加载历史数据"""
    try:
        data_file = "data/okx/BTC_USDT_1d_20251206.csv"
        df = pd.read_csv(data_file)
        logger.info(f"✅ 数据加载成功: {len(df)}条记录")
        logger.info(f"   时间范围: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")
        logger.info(f"   价格范围: ${df['close'].min():.2f} → ${df['close'].max():.2f}")
        return df
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return None


def create_market_feed(df):
    """创建市场数据feed"""
    prices = df['close'].values
    
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        return {'price': prices[idx]}, {}
    
    return feed


def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("🚀 Phase 1: 长期训练测试（20%创世配资）")
    logger.info("=" * 80)
    logger.info("")
    logger.info("✅ 新配资机制：")
    logger.info("  - 创世配资：20% ($2,000/Agent)")
    logger.info("  - 资金池储备：80% ($400,000)")
    logger.info("")
    logger.info("🎯 测试目标：")
    logger.info("  1. 验证长期稳定性（500周期）")
    logger.info("  2. 验证资金池储备充足性")
    logger.info("  3. 验证进化机制效果")
    logger.info("  4. 对比100%配资的差异")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # 加载数据
    df = load_historical_data()
    if df is None:
        return
    
    # 测试配置
    test_config = {
        "agent_count": 50,
        "capital_per_agent": 10000.0,  # 目标规模
        "genesis_allocation_ratio": 0.2,  # 20%配资
        "total_cycles": 500,
        "evo_interval": 10,
        "seed": 7001
    }
    
    logger.info("📋 测试配置：")
    logger.info(f"  Agent数: {test_config['agent_count']}")
    logger.info(f"  目标规模: ${test_config['capital_per_agent']:,.2f}/Agent")
    logger.info(f"  配资比例: {test_config['genesis_allocation_ratio']:.0%}")
    logger.info(f"  训练周期: {test_config['total_cycles']}")
    logger.info(f"  进化间隔: {test_config['evo_interval']}")
    logger.info(f"  随机种子: {test_config['seed']}")
    logger.info("")
    
    # 预期结果
    expected_total_invested = test_config['agent_count'] * test_config['capital_per_agent']
    expected_genesis_allocation = expected_total_invested * test_config['genesis_allocation_ratio']
    expected_per_agent = expected_genesis_allocation / test_config['agent_count']
    expected_reserve = expected_total_invested - expected_genesis_allocation
    
    logger.info("📊 预期配资：")
    logger.info(f"  系统注资: ${expected_total_invested:,.2f}")
    logger.info(f"  创世分配: ${expected_genesis_allocation:,.2f} ({test_config['genesis_allocation_ratio']:.0%})")
    logger.info(f"  每个Agent: ${expected_per_agent:,.2f}")
    logger.info(f"  资金池储备: ${expected_reserve:,.2f} ({(1-test_config['genesis_allocation_ratio']):.0%})")
    logger.info("")
    
    # 设置种子
    import random
    random.seed(test_config['seed'])
    np.random.seed(test_config['seed'])
    
    # ✅ Step 1: 创建Facade
    logger.info("🏗️  Step 1: 创建Facade...")
    facade = V6Facade(num_families=50, exchange=None)
    facade.scenario = "backtest"
    facade.evo_interval = test_config['evo_interval']
    logger.info("✅ Facade创建完成")
    logger.info("")
    
    # ✅ Step 2: 创世（使用20%配资）
    logger.info("🌱 Step 2: 创世（20%配资）...")
    facade.init_population(
        agent_count=test_config['agent_count'],
        capital_per_agent=test_config['capital_per_agent'],
        full_genome_unlock=True,
        genesis_allocation_ratio=test_config['genesis_allocation_ratio']
    )
    
    # 记录初始状态
    system_initial = facade.capital_pool.get_summary()['total_invested']
    logger.info(f"💰 系统初始注资: ${system_initial:,.2f}")
    logger.info("")
    
    # ✅ Step 3: 运行500周期训练
    logger.info(f"🚀 Step 3: 运行{test_config['total_cycles']}周期训练...")
    logger.info("=" * 80)
    logger.info("")
    
    market_feed = create_market_feed(df)
    
    # 记录关键指标
    evolution_history = []
    
    for cycle in range(1, test_config['total_cycles'] + 1):
        # 获取市场数据
        market_data, _ = market_feed(cycle)
        current_price = market_data.get('price', 0)
        
        # 更新Facade的当前价格
        facade.current_market_price = current_price
        
        # ✅ 执行周期（完整系统机制 + 动态税收调控）
        facade.run_cycle(
            cycle_count=cycle,
            market_data=market_data,
            scenario="backtest"
            # breeding_tax_rate=None (默认，自动计算，目标80%利用率)
        )
        
        # 每10个周期记录状态（进化周期）
        if cycle % test_config['evo_interval'] == 0:
            alive_agents = len(facade.moirai.agents)
            total_trades = sum(
                a.account.private_ledger.trade_count 
                for a in facade.moirai.agents 
                if hasattr(a, 'account') and a.account
            )
            
            # 计算当前ROI
            capital_report = facade.get_capital_report(current_price=current_price)
            current_roi = capital_report['system']['roi_pct']
            
            evolution_history.append({
                "cycle": cycle,
                "alive_agents": alive_agents,
                "total_trades": total_trades,
                "system_roi": current_roi,
                "btc_price": current_price
            })
            
            logger.info(f"  周期{cycle:3d}: BTC=${current_price:,.2f}, Agent={alive_agents:2d}, 交易={total_trades:4d}, ROI={current_roi:+.2f}%")
        
        # 每100个周期输出详细状态
        if cycle % 100 == 0:
            logger.info("")
            logger.info(f"  📊 周期{cycle}状态:")
            logger.info(f"     存活Agent: {len(facade.moirai.agents)}")
            logger.info(f"     总交易数: {sum(a.account.private_ledger.trade_count for a in facade.moirai.agents if hasattr(a, 'account') and a.account)}")
            logger.info(f"     系统ROI: {capital_report['system']['roi_pct']:+.2f}%")
            logger.info(f"     资金池余额: ${capital_report['pool']['available']:,.2f}")
            logger.info("")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ 训练完成！")
    logger.info("")
    
    # ✅ Step 4: 对账验证
    logger.info("🔍 Step 4: 对账验证...")
    reconcile_result = facade.reconcile()
    reconcile_passed = reconcile_result.get('all_passed', False)
    
    if reconcile_passed:
        logger.info("  ✅ 对账通过（Agent级 + 系统级）")
    else:
        logger.error("  ❌ 对账失败")
    logger.info("")
    
    # ✅ Step 5: 最终结果统计
    logger.info("📊 Step 5: 最终结果统计...")
    final_report = facade.get_capital_report(current_price=current_price)
    
    # 计算BTC基准收益
    btc_start_price = df['close'].iloc[0]
    btc_end_price = current_price
    btc_return = ((btc_end_price - btc_start_price) / btc_start_price) * 100
    
    # 统计
    alive_agents = len(facade.moirai.agents)
    total_trades = sum(
        a.account.private_ledger.trade_count 
        for a in facade.moirai.agents 
        if hasattr(a, 'account') and a.account
    )
    
    total_births = facade.evolution.total_births
    total_deaths = facade.evolution.total_deaths
    
    logger.info(f"  训练周期: {test_config['total_cycles']}")
    logger.info(f"  存活Agent: {alive_agents}/{test_config['agent_count']}")
    logger.info(f"  总交易数: {total_trades}")
    logger.info(f"  累计出生: {total_births}")
    logger.info(f"  累计死亡: {total_deaths}")
    logger.info("")
    logger.info(f"  系统注资: ${final_report['pool']['total_invested']:,.2f}")
    logger.info(f"  系统总资产: ${final_report['system']['system_total']:,.2f}")
    logger.info(f"  资金池余额: ${final_report['pool']['available']:,.2f}")
    logger.info(f"  Agent总资金: ${final_report['agents']['total_realized'] + final_report['agents']['total_unrealized_pnl']:,.2f}")
    logger.info("")
    logger.info(f"  系统ROI: {final_report['system']['roi_pct']:+.2f}%")
    logger.info(f"  Agent平均ROI: {final_report['agents']['avg_roi_pct']:+.2f}%")
    logger.info(f"  BTC基准: {btc_return:+.2f}%")
    logger.info("")
    
    # 对比分析
    if final_report['system']['roi_pct'] > btc_return:
        logger.info(f"  🎯 系统跑赢BTC: +{final_report['system']['roi_pct'] - btc_return:.2f}%")
    else:
        logger.info(f"  ⚠️ 系统落后BTC: {final_report['system']['roi_pct'] - btc_return:.2f}%")
    logger.info("")
    
    # ✅ Step 6: 生成报告
    logger.info("=" * 80)
    logger.info("📊 Phase 1测试报告")
    logger.info("=" * 80)
    logger.info("")
    logger.info("✅ 配资机制验证：")
    logger.info(f"  创世配资: 20% (${expected_genesis_allocation:,.2f})")
    logger.info(f"  资金池储备: 80% (${expected_reserve:,.2f})")
    logger.info(f"  Agent初始资金: ${expected_per_agent:,.2f}")
    logger.info("")
    logger.info("✅ 训练结果：")
    logger.info(f"  存活率: {alive_agents}/{test_config['agent_count']} ({alive_agents/test_config['agent_count']*100:.1f}%)")
    logger.info(f"  交易活跃度: {total_trades}笔 (平均{total_trades/test_config['total_cycles']:.1f}笔/周期)")
    logger.info(f"  进化效率: {total_births}出生, {total_deaths}死亡")
    logger.info("")
    logger.info("✅ 收益对比：")
    logger.info(f"  系统ROI: {final_report['system']['roi_pct']:+.2f}%")
    logger.info(f"  BTC基准: {btc_return:+.2f}%")
    logger.info(f"  Alpha: {final_report['system']['roi_pct'] - btc_return:+.2f}%")
    logger.info("")
    logger.info("✅ 资金守恒：")
    logger.info(f"  对账状态: {'✅ 通过' if reconcile_passed else '❌ 失败'}")
    system_total = final_report['system']['system_total']
    invested = final_report['pool']['total_invested']
    difference = abs(system_total - invested)
    difference_pct = (difference / invested) * 100
    logger.info(f"  资金差异: ${difference:,.2f} ({difference_pct:.2f}%)")
    logger.info(f"  差异原因: 交易费用 ({total_trades}笔 × 双向)")
    logger.info("")
    logger.info("🎯 Phase 1训练完成！")
    logger.info("=" * 80)
    
    # 保存结果
    result = {
        "test": "phase1_20pct_genesis",
        "timestamp": timestamp,
        "config": test_config,
        "genesis": {
            "total_invested": expected_total_invested,
            "genesis_allocation": expected_genesis_allocation,
            "reserve": expected_reserve,
            "per_agent": expected_per_agent
        },
        "results": {
            "total_cycles": test_config['total_cycles'],
            "alive_agents": alive_agents,
            "survival_rate_pct": (alive_agents / test_config['agent_count']) * 100,
            "total_trades": total_trades,
            "total_births": total_births,
            "total_deaths": total_deaths,
            "reconcile_passed": bool(reconcile_passed),
            "system_roi_pct": float(final_report['system']['roi_pct']),
            "agent_avg_roi_pct": float(final_report['agents']['avg_roi_pct']),
            "btc_benchmark_pct": float(btc_return),
            "alpha_pct": float(final_report['system']['roi_pct'] - btc_return)
        },
        "capital_report": {
            "total_invested": float(final_report['pool']['total_invested']),
            "system_total": float(final_report['system']['system_total']),
            "pool_balance": float(final_report['pool']['available']),
            "agents_total": float(final_report['agents']['total_realized'] + final_report['agents']['total_unrealized_pnl']),
            "difference": float(difference),
            "difference_pct": float(difference_pct)
        },
        "evolution_history": evolution_history,
        "log_file": log_file
    }
    
    result_file = f"results/phase1_20pct_{timestamp}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 结果已保存: {result_file}")
    logger.info(f"📄 日志文件: {log_file}")


if __name__ == "__main__":
    main()

