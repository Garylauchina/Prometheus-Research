#!/usr/bin/env python3
"""
测试Prophet和智能创世功能

测试场景：
1. 第一轮（无数据库）：随机创世，保存经验
2. 第二轮（有数据库）：智能创世，使用历史基因
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 项目路径
sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def generate_bull_market_data(periods: int = 200) -> pd.DataFrame:
    """
    生成牛市数据（持续上涨）
    """
    np.random.seed(42)
    
    base_price = 50000.0
    prices = []
    timestamps = pd.date_range(start='2024-01-01', periods=periods, freq='1h')
    
    for i in range(periods):
        # 牛市：平均每天上涨0.5%，波动±0.3%
        trend = 0.005
        noise = np.random.normal(0, 0.003)
        price_change = trend + noise
        
        base_price *= (1 + price_change)
        
        # 生成OHLC
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


def test_round1_random_genesis():
    """
    第一轮：随机创世（无数据库）
    """
    logger.info("="*80)
    logger.info("第一轮：随机创世测试（建立经验数据库）")
    logger.info("="*80)
    
    # 生成牛市数据
    market_data = generate_bull_market_data(periods=150)
    logger.info(f"✅ 生成牛市数据: {len(market_data)}根K线")
    logger.info(f"   起始价: ${market_data['close'].iloc[0]:.2f}")
    logger.info(f"   结束价: ${market_data['close'].iloc[-1]:.2f}")
    logger.info(f"   涨幅: {(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:.2f}%")
    
    # 创建配置（不使用ExperienceDB）
    config = MockTrainingConfig(
        cycles=100,
        total_system_capital=500000.0,
        agent_count=30,
        genesis_allocation_ratio=0.3,
        evolution_interval=10,
        market_type="bull",
        genesis_strategy="random",  # 随机创世
        experience_db_path="experience/test_smart_genesis.db",  # 保存路径
        save_experience_interval=50,  # 每50周期保存一次
        top_k_to_save=5,  # 保存Top 5
        full_genome_unlock=False,
        elite_ratio=0.2,
        elimination_rate=0.3
    )
    
    # 创建Facade并运行训练
    facade = V6Facade(num_families=10)
    result = facade.run_mock_training(market_data=market_data, config=config)
    
    # 显示结果
    logger.info("")
    logger.info("="*80)
    logger.info("第一轮结果汇总")
    logger.info("="*80)
    logger.info(f"✅ 训练完成: {result.actual_cycles}周期")
    logger.info(f"💰 系统盈亏: ${result.system_total_capital - config.total_system_capital:.2f}")
    logger.info(f"📈 系统ROI: {result.system_roi*100:.2f}%")
    logger.info(f"📊 Agent存活: {result.agent_count_final}/{config.agent_count}")
    logger.info(f"📈 Agent平均ROI: {result.agent_avg_roi*100:.2f}%")
    logger.info(f"💾 经验记录: {result.experience_db_records}条")
    logger.info("")
    
    return result


def test_round2_smart_genesis():
    """
    第二轮：智能创世（使用数据库）
    """
    logger.info("="*80)
    logger.info("第二轮：智能创世测试（使用历史经验）")
    logger.info("="*80)
    
    # 生成相似的牛市数据（但不完全一样）
    market_data = generate_bull_market_data(periods=150)
    logger.info(f"✅ 生成牛市数据: {len(market_data)}根K线")
    logger.info(f"   起始价: ${market_data['close'].iloc[0]:.2f}")
    logger.info(f"   结束价: ${market_data['close'].iloc[-1]:.2f}")
    logger.info(f"   涨幅: {(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:.2f}%")
    
    # 创建配置（使用ExperienceDB）
    config = MockTrainingConfig(
        cycles=100,
        total_system_capital=500000.0,
        agent_count=30,
        genesis_allocation_ratio=0.3,
        evolution_interval=10,
        market_type="bull",
        genesis_strategy="adaptive",  # 智能创世（全部使用历史基因）
        experience_db_path="experience/test_smart_genesis.db",  # 读取路径
        save_experience_interval=50,
        top_k_to_save=5,
        full_genome_unlock=False,
        elite_ratio=0.2,
        elimination_rate=0.3
    )
    
    # 创建Facade并运行训练
    facade = V6Facade(num_families=10)
    result = facade.run_mock_training(market_data=market_data, config=config)
    
    # 显示结果
    logger.info("")
    logger.info("="*80)
    logger.info("第二轮结果汇总")
    logger.info("="*80)
    logger.info(f"✅ 训练完成: {result.actual_cycles}周期")
    logger.info(f"💰 系统盈亏: ${result.system_total_capital - config.total_system_capital:.2f}")
    logger.info(f"📈 系统ROI: {result.system_roi*100:.2f}%")
    logger.info(f"📊 Agent存活: {result.agent_count_final}/{config.agent_count}")
    logger.info(f"📈 Agent平均ROI: {result.agent_avg_roi*100:.2f}%")
    logger.info(f"💾 经验记录: {result.experience_db_records}条")
    logger.info("")
    
    return result


def compare_results(r1, r2):
    """
    对比两轮结果
    """
    logger.info("="*80)
    logger.info("🔬 对比分析：随机创世 vs 智能创世")
    logger.info("="*80)
    
    logger.info(f"{'指标':<20} {'随机创世':<20} {'智能创世':<20} {'改进':<15}")
    logger.info("-"*80)
    
    # ROI对比
    roi_diff = r2.system_roi - r1.system_roi
    roi_improve = "✅" if roi_diff > 0 else "❌"
    logger.info(f"{'系统ROI':<20} {r1.system_roi*100:<20.2f}% {r2.system_roi*100:<20.2f}% {roi_improve} {roi_diff*100:+.2f}%")
    
    # Agent平均ROI对比
    agent_roi_diff = r2.agent_avg_roi - r1.agent_avg_roi
    agent_roi_improve = "✅" if agent_roi_diff > 0 else "❌"
    logger.info(f"{'Agent平均ROI':<20} {r1.agent_avg_roi*100:<20.2f}% {r2.agent_avg_roi*100:<20.2f}% {agent_roi_improve} {agent_roi_diff*100:+.2f}%")
    
    # 最佳Agent ROI对比
    best_roi_diff = r2.agent_best_roi - r1.agent_best_roi
    best_roi_improve = "✅" if best_roi_diff > 0 else "❌"
    logger.info(f"{'最佳Agent ROI':<20} {r1.agent_best_roi*100:<20.2f}% {r2.agent_best_roi*100:<20.2f}% {best_roi_improve} {best_roi_diff*100:+.2f}%")
    
    # 存活Agent对比
    survival_diff = r2.agent_count_final - r1.agent_count_final
    survival_improve = "✅" if survival_diff > 0 else "➖"
    logger.info(f"{'Agent存活':<20} {r1.agent_count_final:<20} {r2.agent_count_final:<20} {survival_improve} {survival_diff:+}")
    
    logger.info("-"*80)
    
    # 总结
    logger.info("")
    if roi_diff > 0:
        logger.info(f"✅ 智能创世ROI提升 {roi_diff*100:.2f}%，验证成功！")
    else:
        logger.info(f"⚠️  智能创世ROI未提升，可能需要更长训练周期或调整参数")
    
    logger.info("")


def main():
    """
    主测试流程
    """
    logger.info("="*80)
    logger.info("🧪 Prophet + 智能创世 完整测试")
    logger.info("="*80)
    logger.info("")
    
    # 清理旧数据库
    db_path = Path("experience/test_smart_genesis.db")
    if db_path.exists():
        db_path.unlink()
        logger.info(f"🗑️  已删除旧数据库: {db_path}")
        logger.info("")
    
    try:
        # 第一轮：随机创世
        result1 = test_round1_random_genesis()
        
        # 第二轮：智能创世
        result2 = test_round2_smart_genesis()
        
        # 对比结果
        compare_results(result1, result2)
        
        logger.info("="*80)
        logger.info("✅ 测试全部完成！")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

