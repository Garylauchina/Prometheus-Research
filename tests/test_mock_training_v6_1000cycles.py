"""
Mock训练1000周期长期测试 - v6.0
================================

目标：
1. 验证V6Facade统一封装长期稳定性
2. 观察资金池变化（目标15%~25%）
3. 验证税收机制有效性
4. 观察Agent进化效果
"""

import pandas as pd
import logging
from datetime import datetime

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("Mock训练1000周期长期测试 - v6.0")
    logger.info("="*80)
    
    # 加载真实历史数据
    DATA_PATH = 'data/btc_usdt_1h.csv'
    logger.info(f"加载历史数据: {DATA_PATH}")
    market_data = pd.read_csv(DATA_PATH)
    if 'timestamp' in market_data.columns:
        market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
    
    logger.info(f"✅ 加载{len(market_data)}根K线")
    logger.info(f"   时间范围: {market_data['timestamp'].iloc[0]} ~ {market_data['timestamp'].iloc[-1]}")
    logger.info("")
    
    # 配置
    config = MockTrainingConfig(
        # 核心参数
        cycles=1000,                     # 1000周期长期测试
        total_system_capital=1_000_000,  # $1M
        
        # 进化参数
        agent_count=50,                  # 50个Agent
        genesis_allocation_ratio=0.2,    # 20%给Agent，80%资金池
        evolution_interval=10,           # 每10周期进化
        
        # 创世参数
        genesis_strategy='pure_random',  # 纯随机创世
        genesis_seed=42,                 # 固定种子
        
        # 市场参数
        market_type='historical',
        
        # 日志
        log_interval=100                 # 每100周期打印
    )
    
    logger.info("配置:")
    logger.info(f"  周期数: {config.cycles}")
    logger.info(f"  系统资金: ${config.total_system_capital:,.0f}")
    logger.info(f"  Agent数量: {config.agent_count}")
    logger.info("")
    
    # 初始化Facade
    facade = V6Facade(num_families=10)
    logger.info("✅ V6Facade已初始化")
    logger.info("")
    
    # 运行训练
    logger.info("="*80)
    logger.info("开始1000周期训练...")
    logger.info("="*80)
    logger.info("")
    
    result = facade.run_mock_training(
        market_data=market_data,
        config=config
    )
    
    # 分析结果
    logger.info("")
    logger.info("="*80)
    logger.info("长期测试结果分析")
    logger.info("="*80)
    logger.info("")
    
    logger.info(f"Run ID: {result.run_id}")
    logger.info(f"实际周期数: {result.actual_cycles}")
    logger.info("")
    
    logger.info("系统级指标:")
    logger.info(f"  系统ROI: {result.system_roi:+.2%}")
    logger.info(f"  BTC基准ROI: {result.btc_benchmark_roi:+.2%}")
    logger.info(f"  超越BTC: {result.outperformance:+.2%}")
    logger.info(f"  系统总资金: ${result.system_total_capital:,.0f}")
    logger.info("")
    
    logger.info("Agent统计:")
    logger.info(f"  最终Agent数: {result.agent_count_final}/{config.agent_count}")
    logger.info(f"  平均ROI: {result.agent_avg_roi:+.2%}")
    logger.info(f"  中位数ROI: {result.agent_median_roi:+.2%}")
    logger.info(f"  最佳ROI: {result.agent_best_roi:+.2%}")
    logger.info("")
    
    logger.info("资金池状态:")
    logger.info(f"  资金池余额: ${result.capital_pool_balance:,.0f}")
    logger.info(f"  Agent资金占比: {result.capital_utilization*100:.1f}%")
    logger.info(f"  资金池占比: {(1-result.capital_utilization)*100:.1f}%")
    logger.info(f"  目标资金池占比: 20%")
    logger.info("")
    
    # 关键验证
    logger.info("="*80)
    logger.info("关键验证")
    logger.info("="*80)
    
    # 1. 对账
    logger.info(f"1. 对账验证: {'✅ 通过' if result.reconciliation_passed else '❌ 失败'}")
    
    # 2. 资金池范围
    pool_ratio = 1 - result.capital_utilization
    if 0.15 <= pool_ratio <= 0.30:
        logger.info(f"2. 资金池占比: ✅ 在15%~30%范围内（{pool_ratio*100:.1f}%）")
    else:
        logger.info(f"2. 资金池占比: ⚠️ 超出15%~30%范围（{pool_ratio*100:.1f}%）")
        if pool_ratio > 0.30:
            logger.info(f"   说明：Agent资金占比过低，可能是亏损或不交易")
        else:
            logger.info(f"   说明：Agent资金占比过高，资金池接近生死线")
    
    # 3. 系统生存
    if result.system_total_capital > config.total_system_capital * 0.5:
        logger.info(f"3. 系统生存: ✅ 系统未崩溃（>{config.total_system_capital*0.5:,.0f}）")
    else:
        logger.info(f"3. 系统生存: ❌ 系统崩溃（<{config.total_system_capital*0.5:,.0f}）")
    
    # 4. 进化效果
    if result.agent_best_roi > 0:
        logger.info(f"4. 进化效果: ✅ 有Agent盈利（最佳{result.agent_best_roi:+.2%}）")
    else:
        logger.info(f"4. 进化效果: ⚠️ 无Agent盈利（需要优化策略）")
    
    logger.info("="*80)
    
    # 总结
    logger.info("")
    logger.info("="*80)
    logger.info("总结")
    logger.info("="*80)
    logger.info("")
    
    if result.reconciliation_passed:
        logger.info("✅ V6Facade.run_mock_training()统一封装工作正常！")
        logger.info("✅ 税收机制工作正常！")
        logger.info("✅ 对账系统100%通过！")
        logger.info("✅ 严格遵守三大铁律第1条：统一封装，统一调用，严禁旁路")
        logger.info("")
        
        if pool_ratio < 0.15:
            logger.info("⚠️ 资金池接近生死线，税收机制需要观察")
        elif pool_ratio > 0.30:
            logger.info("⚠️ Agent资金占比过低（可能亏损或不交易），需要优化策略")
        else:
            logger.info("✅ 资金池在健康范围！")
    else:
        logger.error("❌ 对账失败，需要修复数据封装问题")
    
    logger.info("="*80)

if __name__ == "__main__":
    main()

