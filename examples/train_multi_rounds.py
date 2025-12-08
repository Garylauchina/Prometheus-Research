#!/usr/bin/env python3
"""
多轮基因积累训练脚本

目标：
1. 执行多轮训练（不清空数据库）
2. 每轮使用不同的round_id标记
3. 观察不同轮次的基因差异
4. 验证进化的一致性

用法：
    python3 train_multi_rounds.py --rounds 5 --cycles 1000
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import logging
from datetime import datetime
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def train_round(
    facade: V6Facade,
    round_id: int,
    market_type: str,
    cycles: int = 1000
):
    """
    执行单轮训练
    
    Args:
        facade: V6Facade实例
        round_id: 轮次ID
        market_type: 市场类型 (bull/bear/sideways)
        cycles: 训练周期数
    """
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"🔥 Round {round_id} - {market_type.upper()}市场训练")
    logger.info(f"{'='*80}")
    
    # 生成虚拟市场数据
    import numpy as np
    import pandas as pd
    
    if market_type == 'bull':
        # 生成牛市数据
        np.random.seed(42 + round_id)
        base_price = 50000.0
        prices = []
        timestamps = pd.date_range(start='2024-01-01', periods=cycles, freq='1h')
        
        for i in range(cycles):
            trend = 0.005
            noise = np.random.normal(0, 0.003)
            price_change = trend + noise
            base_price *= (1 + price_change)
            
            prices.append({
                'timestamp': timestamps[i],
                'open': base_price * (1 + np.random.normal(0, 0.001)),
                'high': base_price * (1 + abs(np.random.normal(0, 0.002))),
                'low': base_price * (1 - abs(np.random.normal(0, 0.002))),
                'close': base_price,
                'volume': np.random.uniform(1000, 5000)
            })
        market_data = pd.DataFrame(prices)
        
    elif market_type == 'bear':
        # 生成熊市数据
        np.random.seed(43 + round_id)
        base_price = 100000.0
        prices = []
        timestamps = pd.date_range(start='2024-06-01', periods=cycles, freq='1h')
        
        for i in range(cycles):
            trend = -0.004
            noise = np.random.normal(0, 0.003)
            price_change = trend + noise
            base_price *= (1 + price_change)
            
            prices.append({
                'timestamp': timestamps[i],
                'open': base_price * (1 + np.random.normal(0, 0.001)),
                'high': base_price * (1 + abs(np.random.normal(0, 0.002))),
                'low': base_price * (1 - abs(np.random.normal(0, 0.002))),
                'close': base_price,
                'volume': np.random.uniform(1000, 5000)
            })
        market_data = pd.DataFrame(prices)
        
    else:  # sideways
        # 生成震荡市数据
        np.random.seed(44 + round_id)
        base_price = 60000.0
        prices = []
        timestamps = pd.date_range(start='2024-09-01', periods=cycles, freq='1h')
        
        for i in range(cycles):
            trend = -0.0001
            noise = np.random.normal(0, 0.004)
            price_change = trend + noise
            base_price *= (1 + price_change)
            
            prices.append({
                'timestamp': timestamps[i],
                'open': base_price * (1 + np.random.normal(0, 0.001)),
                'high': base_price * (1 + abs(np.random.normal(0, 0.003))),
                'low': base_price * (1 - abs(np.random.normal(0, 0.003))),
                'close': base_price,
                'volume': np.random.uniform(1000, 5000)
            })
        market_data = pd.DataFrame(prices)
    
    # 训练配置
    config = MockTrainingConfig(
        cycles=cycles,
        total_system_capital=500_000,
        genesis_strategy='random',  # 随机创世，积累基因
        market_type=market_type,
        save_experience_interval=100,  # 每100周期保存一次
        top_k_to_save=10  # 每次保存前10名
    )
    
    # 执行训练
    result = facade.run_mock_training(market_data, config)
    
    # 输出结果
    logger.info(f"")
    logger.info(f"✅ Round {round_id}: {market_type}训练完成")
    logger.info(f"系统ROI: {result.system_roi:+.2%}")
    logger.info(f"Agent平均ROI: {result.agent_avg_roi:+.2%}")
    logger.info(f"Agent最佳ROI: {result.agent_best_roi:+.2%}")
    logger.info(f"经验记录: {len(result.saved_experiences) if hasattr(result, 'saved_experiences') else 'N/A'}条")
    
    return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='多轮基因积累训练')
    parser.add_argument('--rounds', type=int, default=3, help='训练轮数（默认3轮）')
    parser.add_argument('--cycles', type=int, default=1000, help='每轮周期数（默认1000）')
    parser.add_argument('--clear', action='store_true', help='清空现有数据库')
    parser.add_argument('--db', type=str, default='experience/gene_collection_v6.db', help='数据库路径')
    
    args = parser.parse_args()
    
    # 清空数据库（如果指定）
    if args.clear:
        import os
        if os.path.exists(args.db):
            os.remove(args.db)
            logger.info(f"🗑️  已清空数据库: {args.db}")
    
    # 检查数据库现有数据
    from prometheus.core.experience_db import ExperienceDB
    db = ExperienceDB(args.db)
    
    cursor = db.conn.execute("SELECT COUNT(*) FROM best_genomes")
    existing_count = cursor.fetchone()[0]
    db.close()
    
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"📊 多轮基因积累训练")
    logger.info(f"{'='*80}")
    logger.info(f"数据库: {args.db}")
    logger.info(f"现有基因: {existing_count}条")
    logger.info(f"训练轮数: {args.rounds}轮")
    logger.info(f"每轮周期: {args.cycles}")
    logger.info(f"预计新增: {args.rounds * 3 * 10}条（每种市场10条 × 3种市场 × {args.rounds}轮）")
    logger.info(f"预计总计: {existing_count + args.rounds * 3 * 10}条")
    logger.info(f"")
    
    # 执行多轮训练
    all_results = []
    
    for round_num in range(1, args.rounds + 1):
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"🎯 开始第 {round_num}/{args.rounds} 轮训练")
        logger.info(f"{'='*80}")
        
        # 为每轮创建新的Facade（确保状态独立）
        facade = V6Facade()
        
        # 初始化系统（每轮都需要）
        facade.invest_system_capital(total_amount=500_000)
        
        # 训练三种市场
        round_results = {}
        
        # 1. 牛市
        result_bull = train_round(facade, round_num, 'bull', args.cycles)
        round_results['bull'] = result_bull
        
        # 重置系统
        facade = V6Facade()
        facade.invest_system_capital(total_amount=500_000)
        
        # 2. 熊市
        result_bear = train_round(facade, round_num, 'bear', args.cycles)
        round_results['bear'] = result_bear
        
        # 重置系统
        facade = V6Facade()
        facade.invest_system_capital(total_amount=500_000)
        
        # 3. 震荡市
        result_sideways = train_round(facade, round_num, 'sideways', args.cycles)
        round_results['sideways'] = result_sideways
        
        all_results.append(round_results)
        
        logger.info(f"")
        logger.info(f"✅ 第 {round_num} 轮完成")
        logger.info(f"   牛市ROI: {result_bull.system_roi:+.2%}")
        logger.info(f"   熊市ROI: {result_bear.system_roi:+.2%}")
        logger.info(f"   震荡市ROI: {result_sideways.system_roi:+.2%}")
    
    # 最终统计
    db = ExperienceDB(args.db)
    cursor = db.conn.execute("SELECT COUNT(*) FROM best_genomes")
    final_count = cursor.fetchone()[0]
    
    # 统计各市场基因数
    cursor = db.conn.execute("""
        SELECT market_type, COUNT(*) 
        FROM best_genomes 
        GROUP BY market_type
    """)
    market_counts = dict(cursor.fetchall())
    db.close()
    
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"🎉 多轮训练完成")
    logger.info(f"{'='*80}")
    logger.info(f"数据库: {args.db}")
    logger.info(f"总基因数: {final_count}条")
    logger.info(f"")
    logger.info(f"各市场分布:")
    for market, count in market_counts.items():
        logger.info(f"  {market}: {count}条")
    logger.info(f"")
    logger.info(f"✅ 现在可以运行 analyze_genes.py 分析基因特征！")
    logger.info(f"✅ 或运行 compare_rounds.py 对比不同轮次的差异！")
    logger.info(f"{'='*80}")


if __name__ == '__main__':
    main()

