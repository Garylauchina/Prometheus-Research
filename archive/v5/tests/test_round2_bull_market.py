"""
第二轮训练：牛市场景
=====================

目标：
1. 验证ExperienceDB保存机制
2. 验证完全自由度配置
3. 积累牛市经验数据
"""

import pandas as pd
import logging

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("第二轮训练：牛市场景")
    logger.info("="*80)
    logger.info("")
    
    # 加载真实历史数据
    DATA_PATH = 'data/btc_usdt_1h.csv'
    logger.info(f"加载历史数据: {DATA_PATH}")
    market_data = pd.read_csv(DATA_PATH)
    if 'timestamp' in market_data.columns:
        market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
    
    logger.info(f"✅ 加载{len(market_data)}根K线")
    logger.info("")
    
    # ========== 第二轮配置：完全自由度 ==========
    config = MockTrainingConfig(
        # 核心参数
        cycles=1000,
        total_system_capital=1_000_000,
        
        # 进化参数（完全自由）
        agent_count=50,
        genesis_allocation_ratio=0.2,
        evolution_interval=10,
        elimination_rate=0.3,           # 30%淘汰
        elite_ratio=0.2,                # 20%精英
        
        # 创世参数（激进模式）
        full_genome_unlock=True,        # ✅ 激进式：直接解锁所有基因
        genesis_strategy='pure_random',
        genesis_seed=7777,              # 第二轮种子
        
        # 交易参数
        max_leverage=100.0,
        max_position_pct=0.8,
        enable_short=True,
        fee_rate=0.0005,
        
        # 市场参数
        market_type='bull',             # ✅ 牛市
        ws_window_size=100,
        
        # ✅ 经验库参数（使用统一数据库）
        experience_db_path='experience/prometheus_v6.db',  # ✅ 统一数据库（智能创世会自动查询）
        top_k_to_save=10,
        save_experience_interval=100,   # ✅ 每100周期保存一次
        
        # 日志
        log_dir='mock_training_logs',
        log_interval=100,
        enable_debug_log=False
    )
    
    logger.info("第二轮配置:")
    logger.info(f"  周期数: {config.cycles}")
    logger.info(f"  系统资金: ${config.total_system_capital:,.0f}")
    logger.info(f"  Agent数量: {config.agent_count}")
    logger.info(f"  full_genome_unlock: {config.full_genome_unlock} (激进模式)")
    logger.info(f"  elite_ratio: {config.elite_ratio:.0%}")
    logger.info(f"  elimination_rate: {config.elimination_rate:.0%}")
    logger.info(f"  市场类型: {config.market_type}")
    logger.info(f"  ExperienceDB: {config.experience_db_path}")
    logger.info(f"  保存间隔: 每{config.save_experience_interval}周期")
    logger.info("")
    
    # 初始化Facade
    logger.info("初始化V6Facade...")
    facade = V6Facade(num_families=10)
    logger.info("✅ V6Facade已初始化")
    logger.info("")
    
    # 运行训练
    logger.info("="*80)
    logger.info("开始第二轮训练...")
    logger.info("="*80)
    logger.info("")
    
    result = facade.run_mock_training(
        market_data=market_data,
        config=config
    )
    
    # 分析结果
    logger.info("")
    logger.info("="*80)
    logger.info("第二轮训练结果")
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
    
    logger.info("ExperienceDB统计:")
    logger.info(f"  已保存经验: {result.experience_saved}")
    logger.info(f"  数据库记录数: {result.experience_db_records}")
    logger.info(f"  预期保存次数: {config.cycles // config.save_experience_interval + 1}")
    logger.info("")
    
    logger.info("资金池状态:")
    logger.info(f"  资金池余额: ${result.capital_pool_balance:,.0f}")
    logger.info(f"  资金利用率: {result.capital_utilization*100:.1f}%")
    logger.info("")
    
    logger.info("对账验证:")
    logger.info(f"  对账结果: {'✅ 通过' if result.reconciliation_passed else '❌ 失败'}")
    logger.info("")
    
    # 验证
    logger.info("="*80)
    logger.info("验证")
    logger.info("="*80)
    
    checks = []
    
    check1 = result.reconciliation_passed
    checks.append(("对账通过", check1))
    logger.info(f"{'✅' if check1 else '❌'} 对账100%通过")
    
    check2 = result.experience_saved and result.experience_db_records > 0
    checks.append(("ExperienceDB保存", check2))
    logger.info(f"{'✅' if check2 else '❌'} ExperienceDB保存成功（{result.experience_db_records}条）")
    
    check3 = result.system_total_capital > config.total_system_capital * 0.5
    checks.append(("系统未崩溃", check3))
    logger.info(f"{'✅' if check3 else '❌'} 系统未崩溃")
    
    check4 = result.agent_count_final > 0
    checks.append(("有Agent存活", check4))
    logger.info(f"{'✅' if check4 else '❌'} 有Agent存活")
    
    logger.info("")
    
    passed_count = sum(1 for _, passed in checks if passed)
    total_count = len(checks)
    
    logger.info("="*80)
    if passed_count == total_count:
        logger.info(f"🎉 全部通过！（{passed_count}/{total_count}）")
        logger.info("")
        logger.info("✅ 第二轮训练成功！")
        logger.info("✅ ExperienceDB已积累牛市经验数据")
        logger.info("✅ 可以开始第三轮训练（熊市场景）")
    else:
        logger.error(f"❌ 部分失败（{passed_count}/{total_count}）")
    logger.info("="*80)

if __name__ == "__main__":
    main()

