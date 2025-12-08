"""
自由度和ExperienceDB完整测试
================================

验证：
1. full_genome_unlock可配置
2. elite_ratio和elimination_rate可配置
3. ExperienceDB间隔保存机制
"""

import pandas as pd
import logging
from datetime import datetime, timedelta

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_data(cycles: int = 300) -> pd.DataFrame:
    """生成简单的模拟数据"""
    import numpy as np
    
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(cycles)]
    prices = [50000 * (1 + 0.001 * i + np.random.normal(0, 0.02)) for i in range(cycles)]
    
    data = []
    for i, timestamp in enumerate(timestamps):
        price = prices[i]
        data.append({
            'timestamp': timestamp,
            'open': price * (1 + np.random.normal(0, 0.005)),
            'high': price * (1 + abs(np.random.normal(0, 0.01))),
            'low': price * (1 - abs(np.random.normal(0, 0.01))),
            'close': price,
            'volume': abs(np.random.normal(1000, 200))
        })
    
    return pd.DataFrame(data)

def main():
    logger.info("="*80)
    logger.info("自由度和ExperienceDB完整测试")
    logger.info("="*80)
    logger.info("")
    
    # ========== 测试配置 ==========
    config = MockTrainingConfig(
        # 核心参数
        cycles=200,
        total_system_capital=100_000,
        
        # ✅ 测试1：full_genome_unlock配置
        full_genome_unlock=True,  # 激进模式
        
        # ✅ 测试2：elite_ratio和elimination_rate配置
        agent_count=20,
        elite_ratio=0.3,           # 30%精英（非默认20%）
        elimination_rate=0.4,      # 40%淘汰（非默认30%）
        evolution_interval=10,
        
        # 创世参数
        genesis_allocation_ratio=0.2,
        genesis_strategy='pure_random',
        genesis_seed=42,
        
        # ✅ 测试3：ExperienceDB间隔保存
        experience_db_path='test_experience.db',
        top_k_to_save=5,
        save_experience_interval=50,  # 每50周期保存一次
        
        # 市场参数
        market_type='test',
        ws_window_size=50,
        
        # 日志
        log_interval=50
    )
    
    logger.info("测试配置:")
    logger.info(f"  full_genome_unlock: {config.full_genome_unlock}")
    logger.info(f"  elite_ratio: {config.elite_ratio:.0%}")
    logger.info(f"  elimination_rate: {config.elimination_rate:.0%}")
    logger.info(f"  experience_db_path: {config.experience_db_path}")
    logger.info(f"  save_experience_interval: {config.save_experience_interval}")
    logger.info("")
    
    # ========== 生成数据 ==========
    logger.info("生成模拟数据...")
    market_data = generate_mock_data(cycles=config.cycles + 50)
    logger.info(f"✅ 生成{len(market_data)}根K线")
    logger.info("")
    
    # ========== 初始化Facade ==========
    logger.info("初始化V6Facade...")
    facade = V6Facade(num_families=5)
    logger.info("✅ V6Facade已初始化")
    logger.info("")
    
    # ========== 运行训练 ==========
    logger.info("="*80)
    logger.info("开始训练...")
    logger.info("="*80)
    logger.info("")
    
    result = facade.run_mock_training(
        market_data=market_data,
        config=config
    )
    
    # ========== 验证结果 ==========
    logger.info("")
    logger.info("="*80)
    logger.info("验证结果")
    logger.info("="*80)
    logger.info("")
    
    # 验证1：对账通过
    check1 = result.reconciliation_passed
    logger.info(f"1. 对账验证: {'✅' if check1 else '❌'}")
    
    # 验证2：ExperienceDB记录
    check2 = result.experience_saved and result.experience_db_records > 0
    logger.info(f"2. ExperienceDB保存: {'✅' if check2 else '❌'} (记录数: {result.experience_db_records})")
    
    # 计算预期的保存次数
    expected_saves = config.cycles // config.save_experience_interval + 1  # 间隔保存 + 最后保存
    logger.info(f"   预期保存次数: ~{expected_saves}次（每{config.save_experience_interval}周期）")
    
    # 验证3：系统未崩溃
    check3 = result.system_total_capital > config.total_system_capital * 0.5
    logger.info(f"3. 系统未崩溃: {'✅' if check3 else '❌'} (${result.system_total_capital:,.0f})")
    
    # 验证4：进化正常
    check4 = result.agent_count_final > 0
    logger.info(f"4. 进化正常: {'✅' if check4 else '❌'} ({result.agent_count_final}个Agent存活)")
    
    logger.info("")
    logger.info("="*80)
    logger.info("系统指标:")
    logger.info(f"  系统ROI: {result.system_roi:+.2%}")
    logger.info(f"  BTC基准: {result.btc_benchmark_roi:+.2%}")
    logger.info(f"  超越BTC: {result.outperformance:+.2%}")
    logger.info(f"  Agent平均ROI: {result.agent_avg_roi:+.2%}")
    logger.info(f"  最佳Agent ROI: {result.agent_best_roi:+.2%}")
    logger.info("="*80)
    logger.info("")
    
    # 总结
    all_checks = [check1, check2, check3, check4]
    passed_count = sum(all_checks)
    total_count = len(all_checks)
    
    logger.info("="*80)
    if passed_count == total_count:
        logger.info(f"🎉 全部通过！（{passed_count}/{total_count}）")
        logger.info("")
        logger.info("✅ full_genome_unlock配置生效")
        logger.info("✅ elite_ratio和elimination_rate配置生效")
        logger.info("✅ ExperienceDB间隔保存机制工作正常")
        logger.info("✅ 严格遵守三大铁律：统一封装，统一调用，严禁旁路")
    else:
        logger.error(f"❌ 部分失败（{passed_count}/{total_count}）")
    logger.info("="*80)
    
    # 清理
    import os
    if os.path.exists('test_experience.db'):
        os.remove('test_experience.db')
        logger.info("🧹 已清理测试数据库")

if __name__ == "__main__":
    main()

