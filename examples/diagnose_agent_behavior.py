#!/usr/bin/env python3
"""
诊断Agent行为：为什么在牛市中不赚钱？
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def generate_bull_market_data(periods: int = 200) -> pd.DataFrame:
    """生成牛市数据"""
    np.random.seed(42)
    base_price = 50000.0
    prices = []
    timestamps = pd.date_range(start='2024-01-01', periods=periods, freq='1h')
    
    for i in range(periods):
        trend = 0.005
        noise = np.random.normal(0, 0.003)
        price_change = trend + noise
        base_price *= (1 + price_change)
        
        high = base_price * (1 + abs(np.random.normal(0, 0.002)))
        low = base_price * (1 - abs(np.random.normal(0, 0.002)))
        open_price = base_price * (1 + np.random.normal(0, 0.001))
        close_price = base_price
        volume = np.random.uniform(1000, 5000)
        
        prices.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(prices)


def analyze_single_agent_trades():
    """
    诊断：运行50周期，详细分析单个Agent的交易行为
    """
    logger.info("="*80)
    logger.info("🔬 Agent行为诊断")
    logger.info("="*80)
    logger.info("")
    
    # 生成数据
    market_data = generate_bull_market_data(periods=100)
    logger.info(f"市场数据: {len(market_data)}根K线")
    logger.info(f"起始价: ${market_data['close'].iloc[0]:.2f}")
    logger.info(f"结束价: ${market_data['close'].iloc[-1]:.2f}")
    logger.info(f"涨幅: {(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:.2f}%")
    logger.info("")
    
    # 配置
    config = MockTrainingConfig(
        cycles=50,  # 只运行50周期，快速诊断
        total_system_capital=100000.0,  # 降低资金
        agent_count=10,  # 只创建10个Agent
        genesis_allocation_ratio=0.8,  # 80%给Agent（提高资金利用率）
        evolution_interval=999,  # 不进化（保持初始Agent）
        market_type="bull",
        genesis_strategy="random",
        full_genome_unlock=False,
        elite_ratio=0.2,
        elimination_rate=0.0  # 不淘汰
    )
    
    # 运行训练
    facade = V6Facade(num_families=5)
    result = facade.run_mock_training(market_data=market_data, config=config)
    
    logger.info("")
    logger.info("="*80)
    logger.info("📊 结果分析")
    logger.info("="*80)
    
    # 系统级
    logger.info(f"系统ROI: {result.system_roi*100:.2f}%")
    logger.info(f"资金利用率: {result.capital_utilization*100:.2f}%")
    logger.info(f"Agent平均ROI: {result.agent_avg_roi*100:.2f}%")
    logger.info(f"Agent最佳ROI: {result.agent_best_roi*100:.2f}%")
    logger.info(f"Agent平均交易次数: {result.agent_avg_trade_count:.1f}")
    logger.info("")
    
    # Agent级分析
    logger.info("="*80)
    logger.info("🔍 Agent详细分析")
    logger.info("="*80)
    
    agents = facade.moirai.agents
    for i, agent in enumerate(agents[:5], 1):  # 只看前5个
        logger.info(f"\n{'='*60}")
        logger.info(f"Agent {i}: {agent.agent_id}")
        logger.info(f"{'='*60}")
        
        # 基本信息
        logger.info(f"初始资金: ${agent.lineage.genesis_capital:.2f}")
        logger.info(f"当前资金: ${agent.current_capital:.2f}")
        roi = (agent.current_capital / agent.lineage.genesis_capital - 1) * 100
        logger.info(f"ROI: {roi:+.2f}%")
        
        # 策略信息
        if hasattr(agent, 'strategy_pool'):
            strategies = [s.name for s in agent.strategy_pool]
            logger.info(f"策略: {', '.join(strategies)}")
        
        if hasattr(agent, 'strategy_params'):
            sp = agent.strategy_params
            logger.info(f"仓位基数: {sp.position_size_base:.2f}")
            logger.info(f"持仓偏好: {sp.holding_preference:.2f}")
            logger.info(f"方向偏好: {sp.directional_bias:.2f}")
        
        # 交易统计
        if hasattr(agent, 'account') and agent.account:
            private_ledger = agent.account.private_ledger
            trades = private_ledger.trade_history
            logger.info(f"\n交易统计:")
            logger.info(f"  总交易次数: {len(trades)}")
            
            if len(trades) > 0:
                # 开仓/平仓统计
                opens = [t for t in trades if t.action == 'open']
                closes = [t for t in trades if t.action == 'close']
                logger.info(f"  开仓次数: {len(opens)}")
                logger.info(f"  平仓次数: {len(closes)}")
                
                # 多空统计
                long_trades = [t for t in trades if t.direction == 'long']
                short_trades = [t for t in trades if t.direction == 'short']
                logger.info(f"  做多次数: {len(long_trades)}")
                logger.info(f"  做空次数: {len(short_trades)}")
                
                # 手续费统计
                total_fees = sum(t.fee for t in trades)
                logger.info(f"  总手续费: ${total_fees:.2f} ({total_fees/agent.lineage.genesis_capital*100:.2f}%)")
                
                # 显示最近5笔交易
                logger.info(f"\n  最近5笔交易:")
                for trade in trades[-5:]:
                    logger.info(f"    {trade.action} {trade.direction} | "
                              f"价格${trade.price:.0f} | "
                              f"数量{trade.amount:.4f} | "
                              f"手续费${trade.fee:.2f}")
            else:
                logger.info(f"  ❌ 没有任何交易！")
        else:
            logger.info(f"  ❌ 没有账户系统！")
    
    logger.info("")
    logger.info("="*80)
    logger.info("💀 诊断结论")
    logger.info("="*80)
    
    # 诊断结论
    if result.agent_avg_trade_count < 5:
        logger.info("❌ 问题1: Agent交易次数太少！")
        logger.info("   可能原因:")
        logger.info("   - 决策逻辑有Bug")
        logger.info("   - 风险控制太严格")
        logger.info("   - 策略参数导致几乎不交易")
    
    if result.capital_utilization < 0.5:
        logger.info("❌ 问题2: 资金利用率太低！")
        logger.info(f"   只有{result.capital_utilization*100:.1f}%的资金在工作")
        logger.info("   可能原因:")
        logger.info("   - 仓位设置太小")
        logger.info("   - Agent大部分时间空仓")
    
    if result.agent_avg_roi < (market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1) * 0.1:
        logger.info("❌ 问题3: ROI远低于市场涨幅！")
        logger.info(f"   市场涨{(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:.1f}%")
        logger.info(f"   Agent只赚{result.agent_avg_roi*100:.2f}%")
        logger.info("   可能原因:")
        logger.info("   - 频繁交易导致手续费吃光利润")
        logger.info("   - 策略方向错误（做空）")
        logger.info("   - 持仓时间太短")
    
    logger.info("")


if __name__ == "__main__":
    analyze_single_agent_trades()

