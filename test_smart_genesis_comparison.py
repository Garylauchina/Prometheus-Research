"""
智能创世对比测试 - 验证ExperienceDB的有效性

对比两种创世策略：
1. 纯随机创世（pure_random）
2. 智能创世（adaptive）

目标：验证智能创世是否能提升系统性能
"""

import logging
import pandas as pd
from prometheus.training.mock_training_school import MockTrainingSchool
from prometheus.core.experience_db import ExperienceDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def run_single_test(genesis_strategy: str, run_id: str):
    """
    运行单次测试
    
    参数：
        genesis_strategy: 创世策略（'pure_random', 'adaptive'等）
        run_id: 运行ID
    
    返回：
        结果字典
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"开始测试: {genesis_strategy}")
    logger.info(f"{'='*80}\n")
    
    # 配置
    config = {
        'market_type': 'bear',  # 熊市测试（更有挑战性）
        'agent_count': 50,
        'total_capital': 500000,
        'genesis_strategy': genesis_strategy,
        'ws_window_size': 100
    }
    
    # 加载市场数据
    market_data = pd.read_csv('data/btc_usdt_1h.csv')
    market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
    
    # 初始化
    experience_db = ExperienceDB(db_path='data/experience.db')
    school = MockTrainingSchool(
        market_data=market_data,
        config=config,
        experience_db=experience_db
    )
    
    # 训练（短期测试：200周期）
    try:
        best_agents = school.train(cycles=200, run_id=run_id)
        
        # 统计结果
        alive_agents = [a for a in school.agents if hasattr(a, 'state') and a.state.value != 'dead']
        if alive_agents:
            avg_roi = sum(getattr(a, 'roi', 0) for a in alive_agents) / len(alive_agents)
            median_roi = sorted([getattr(a, 'roi', 0) for a in alive_agents])[len(alive_agents)//2]
            best_roi = max(getattr(a, 'roi', 0) for a in alive_agents)
            
            result = {
                'strategy': genesis_strategy,
                'run_id': run_id,
                'alive_count': len(alive_agents),
                'avg_roi': avg_roi,
                'median_roi': median_roi,
                'best_roi': best_roi,
                'success': True
            }
        else:
            result = {
                'strategy': genesis_strategy,
                'run_id': run_id,
                'alive_count': 0,
                'avg_roi': 0,
                'median_roi': 0,
                'best_roi': 0,
                'success': False
            }
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        result = {
            'strategy': genesis_strategy,
            'run_id': run_id,
            'error': str(e),
            'success': False
        }
    finally:
        experience_db.close()
    
    return result


def main():
    logger.info("="*80)
    logger.info("智能创世对比测试")
    logger.info("="*80)
    logger.info("")
    
    # 第1轮：纯随机创世（建立基线 + 积累经验）
    logger.info("📊 第1轮：纯随机创世（建立基线）")
    result1 = run_single_test('pure_random', 'baseline_20251208_001')
    
    # 第2轮：智能创世（利用经验）
    logger.info("\n📊 第2轮：智能创世（利用第1轮经验）")
    result2 = run_single_test('adaptive', 'smart_20251208_001')
    
    # 对比结果
    logger.info("\n" + "="*80)
    logger.info("📊 对比结果")
    logger.info("="*80)
    logger.info("")
    
    logger.info("第1轮（纯随机创世）:")
    logger.info(f"  存活Agent: {result1.get('alive_count', 0)}/50")
    logger.info(f"  平均ROI: {result1.get('avg_roi', 0)*100:+.2f}%")
    logger.info(f"  中位数ROI: {result1.get('median_roi', 0)*100:+.2f}%")
    logger.info(f"  最佳ROI: {result1.get('best_roi', 0)*100:+.2f}%")
    logger.info("")
    
    logger.info("第2轮（智能创世）:")
    logger.info(f"  存活Agent: {result2.get('alive_count', 0)}/50")
    logger.info(f"  平均ROI: {result2.get('avg_roi', 0)*100:+.2f}%")
    logger.info(f"  中位数ROI: {result2.get('median_roi', 0)*100:+.2f}%")
    logger.info(f"  最佳ROI: {result2.get('best_roi', 0)*100:+.2f}%")
    logger.info("")
    
    # 计算提升
    if result1.get('success') and result2.get('success'):
        avg_improvement = (result2['avg_roi'] - result1['avg_roi']) * 100
        median_improvement = (result2['median_roi'] - result1['median_roi']) * 100
        best_improvement = (result2['best_roi'] - result1['best_roi']) * 100
        
        logger.info("📈 智能创世的提升:")
        logger.info(f"  平均ROI提升: {avg_improvement:+.2f}%")
        logger.info(f"  中位数ROI提升: {median_improvement:+.2f}%")
        logger.info(f"  最佳ROI提升: {best_improvement:+.2f}%")
        logger.info("")
        
        if avg_improvement > 0:
            logger.info("✅ ✅ ✅ 验证成功！智能创世显著提升性能！")
            logger.info("   ExperienceDB有效！经验积累机制工作正常！")
        else:
            logger.info("⚠️  智能创世未显示优势，可能原因：")
            logger.info("   1. 经验积累不足（建议多轮训练）")
            logger.info("   2. 市场环境差异过大")
            logger.info("   3. 需要调整相似度阈值")
    else:
        logger.info("❌ 测试未能完成，无法对比")
    
    logger.info("")
    logger.info("="*80)
    logger.info("测试完成")
    logger.info("="*80)


if __name__ == "__main__":
    main()

