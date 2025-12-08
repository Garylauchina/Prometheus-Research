#!/usr/bin/env python3
"""
基因积累训练脚本

目标：在不同市场环境下训练，积累优秀基因到ExperienceDB

训练计划：
1. 牛市（1000周期）→ 筛选做多基因
2. 熊市（1000周期）→ 筛选做空基因
3. 震荡市（1000周期）→ 筛选中性基因
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def generate_bull_market(periods: int = 1200, seed: int = 42) -> pd.DataFrame:
    """生成牛市数据（持续上涨）"""
    np.random.seed(seed)
    base_price = 50000.0
    prices = []
    timestamps = pd.date_range(start='2024-01-01', periods=periods, freq='1h')
    
    for i in range(periods):
        trend = 0.005  # 每周期平均涨0.5%
        noise = np.random.normal(0, 0.003)
        price_change = trend + noise
        base_price *= (1 + price_change)
        
        high = base_price * (1 + abs(np.random.normal(0, 0.002)))
        low = base_price * (1 - abs(np.random.normal(0, 0.002)))
        open_price = base_price * (1 + np.random.normal(0, 0.001))
        
        prices.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': base_price,
            'volume': np.random.uniform(1000, 5000)
        })
    
    return pd.DataFrame(prices)


def generate_bear_market(periods: int = 1200, seed: int = 43) -> pd.DataFrame:
    """生成熊市数据（持续下跌）"""
    np.random.seed(seed)
    base_price = 100000.0  # 从高位开始
    prices = []
    timestamps = pd.date_range(start='2024-06-01', periods=periods, freq='1h')
    
    for i in range(periods):
        trend = -0.004  # 每周期平均跌0.4%
        noise = np.random.normal(0, 0.003)
        price_change = trend + noise
        base_price *= (1 + price_change)
        
        high = base_price * (1 + abs(np.random.normal(0, 0.002)))
        low = base_price * (1 - abs(np.random.normal(0, 0.002)))
        open_price = base_price * (1 + np.random.normal(0, 0.001))
        
        prices.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': base_price,
            'volume': np.random.uniform(1000, 5000)
        })
    
    return pd.DataFrame(prices)


def generate_sideways_market(periods: int = 1200, seed: int = 44) -> pd.DataFrame:
    """生成震荡市数据（横盘波动）"""
    np.random.seed(seed)
    base_price = 60000.0
    prices = []
    timestamps = pd.date_range(start='2024-09-01', periods=periods, freq='1h')
    
    for i in range(periods):
        # 震荡：围绕中心价格波动
        wave = np.sin(i / 20) * 0.02  # 周期性波动
        noise = np.random.normal(0, 0.005)  # 更大的噪声
        price_change = wave + noise
        
        price = base_price * (1 + price_change)
        
        high = price * (1 + abs(np.random.normal(0, 0.003)))
        low = price * (1 - abs(np.random.normal(0, 0.003)))
        open_price = price * (1 + np.random.normal(0, 0.002))
        
        prices.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': np.random.uniform(1000, 5000)
        })
    
    return pd.DataFrame(prices)


def train_round(
    round_name: str,
    market_data: pd.DataFrame,
    market_type: str,
    cycles: int,
    db_path: str
):
    """
    单轮训练
    """
    logger.info("="*80)
    logger.info(f"🎯 {round_name}")
    logger.info("="*80)
    logger.info(f"市场类型: {market_type}")
    logger.info(f"数据量: {len(market_data)}根K线")
    logger.info(f"起始价: ${market_data['close'].iloc[0]:.2f}")
    logger.info(f"结束价: ${market_data['close'].iloc[-1]:.2f}")
    logger.info(f"涨跌幅: {(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:+.2f}%")
    logger.info("")
    
    config = MockTrainingConfig(
        cycles=cycles,
        total_system_capital=500000.0,
        agent_count=50,  # 增加Agent数量，增加探索空间
        genesis_allocation_ratio=0.3,
        evolution_interval=10,
        market_type=market_type,
        genesis_strategy="random",  # 随机创世，充分探索
        experience_db_path=db_path,
        save_experience_interval=100,  # 每100周期保存一次
        top_k_to_save=10,  # 保存Top 10
        full_genome_unlock=False,  # 渐进解锁
        elite_ratio=0.2,
        elimination_rate=0.3
    )
    
    facade = V6Facade(num_families=10)
    result = facade.run_mock_training(market_data=market_data, config=config)
    
    logger.info("")
    logger.info(f"✅ {round_name}完成")
    logger.info(f"系统ROI: {result.system_roi*100:+.2f}%")
    logger.info(f"Agent平均ROI: {result.agent_avg_roi*100:+.2f}%")
    logger.info(f"Agent最佳ROI: {result.agent_best_roi*100:+.2f}%")
    logger.info(f"经验记录: {result.experience_db_records}条")
    logger.info("")
    
    return result


def main():
    """
    主训练流程
    """
    logger.info("="*80)
    logger.info("🧬 基因积累训练计划")
    logger.info("="*80)
    logger.info("目标: 在不同市场环境下积累优秀基因")
    logger.info("")
    
    db_path = "experience/gene_collection_v6.db"
    
    # 清理旧数据库
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        logger.info(f"🗑️  已删除旧数据库: {db_path}")
        logger.info("")
    
    # Round 1: 牛市训练
    bull_data = generate_bull_market(periods=1200, seed=42)
    r1 = train_round(
        round_name="Round 1: 牛市训练",
        market_data=bull_data,
        market_type="bull",
        cycles=1000,
        db_path=db_path
    )
    
    # Round 2: 熊市训练
    bear_data = generate_bear_market(periods=1200, seed=43)
    r2 = train_round(
        round_name="Round 2: 熊市训练",
        market_data=bear_data,
        market_type="bear",
        cycles=1000,
        db_path=db_path
    )
    
    # Round 3: 震荡市训练
    sideways_data = generate_sideways_market(periods=1200, seed=44)
    r3 = train_round(
        round_name="Round 3: 震荡市训练",
        market_data=sideways_data,
        market_type="sideways",
        cycles=1000,
        db_path=db_path
    )
    
    # 最终统计
    logger.info("="*80)
    logger.info("🎉 基因积累完成")
    logger.info("="*80)
    logger.info(f"数据库: {db_path}")
    logger.info(f"总经验记录: {r3.experience_db_records}条")
    logger.info("")
    logger.info("各市场表现:")
    logger.info(f"  牛市ROI: {r1.system_roi*100:+.2f}%")
    logger.info(f"  熊市ROI: {r2.system_roi*100:+.2f}%")
    logger.info(f"  震荡市ROI: {r3.system_roi*100:+.2f}%")
    logger.info("")
    logger.info("✅ 现在可以分析这些基因，设计种群调度机制了！")
    logger.info("="*80)


if __name__ == "__main__":
    main()

