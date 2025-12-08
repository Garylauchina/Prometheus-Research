"""
Mock训练学校 - Phase 1测试

目标：
  验证核心假设：进化算法能否找到盈利的交易策略

步骤：
  1. 使用真实历史K线（2024-01 ~ 2024-03牛市）
  2. 首次训练（随机创世，无历史经验）
  3. 1000周期训练  4. 验证结果
  5. 与BTC基准对比

验证标准：
  - 系统平均ROI > BTC ROI (+536%)
  - 或至少：最佳Agent ROI > BTC ROI * 1.2 (+643%)
"""

import pandas as pd
import logging
from datetime import datetime

from prometheus.core.world_signature_simple import WorldSignatureSimple
from prometheus.core.experience_db import ExperienceDB
from prometheus.training.mock_training_school import MockTrainingSchool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("Mock训练学校 - Phase 1测试")
    logger.info("=" * 80)
    logger.info("")
    
    # 1. 加载市场数据
    logger.info("📊 加载市场数据...")
    try:
        market_data = pd.read_csv('data/btc_usdt_1h.csv')
        logger.info(f"✅ 加载成功: {len(market_data)}根K线")
        logger.info(f"   时间范围: {market_data['timestamp'].iloc[0]} ~ {market_data['timestamp'].iloc[-1]}")
    except FileNotFoundError:
        logger.error("❌ 数据文件不存在: data/btc_usdt_1h.csv")
        logger.info("   请先准备历史K线数据")
        return
    
    # 2. 计算BTC基准ROI
    btc_start_price = market_data['close'].iloc[0]
    btc_end_price = market_data['close'].iloc[-1]
    btc_roi = (btc_end_price / btc_start_price - 1)
    
    logger.info(f"📈 BTC基准:")
    logger.info(f"   起始价格: ${btc_start_price:,.2f}")
    logger.info(f"   结束价格: ${btc_end_price:,.2f}")
    logger.info(f"   ROI: {btc_roi*100:+.2f}%")
    logger.info("")
    
    # 3. 初始化ExperienceDB
    logger.info("💾 初始化ExperienceDB...")
    experience_db = ExperienceDB('data/experience.db')
    
    # 检查是否有历史经验
    stats = experience_db.get_statistics()
    logger.info(f"   历史记录: {stats['total_records']}条")
    if stats['total_records'] > 0:
        logger.info(f"   平均ROI: {stats['avg_roi']*100:.2f}%")
        logger.info(f"   最佳ROI: {stats['max_roi']*100:.2f}%")
    logger.info("")
    
    # 4. 配置训练
    config = {
        'market_type': 'bull',  # 牛市
        'agent_count': 50,
        'total_capital': 500000,  # $500K总资金
        'genesis_strategy': 'adaptive',  # 自适应创世
    }
    
    logger.info("⚙️  训练配置:")
    logger.info(f"   市场类型: {config['market_type']}")
    logger.info(f"   Agent数量: {config['agent_count']}")
    logger.info(f"   总资金: ${config['total_capital']:,}")
    logger.info(f"   创世策略: {config['genesis_strategy']}")
    logger.info("")
    
    # 5. 创建训练学校
    logger.info("🏫 创建Mock训练学校...")
    school = MockTrainingSchool(
        market_data=market_data,
        config=config,
        experience_db=experience_db
    )
    logger.info("")
    
    # 6. 开始训练
    run_id = f"phase1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cycles = min(1000, len(market_data) - 1)
    
    logger.info(f"🚀 开始训练: {run_id}")
    logger.info(f"   训练周期: {cycles}")
    logger.info("")
    
    try:
        best_agents = school.train(cycles=cycles, run_id=run_id)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 训练完成！")
        logger.info("=" * 80)
        logger.info("")
        
        # 7. 分析结果
        logger.info("📊 训练结果分析:")
        logger.info("")
        
        # 系统平均ROI
        from prometheus.core.agent_v5 import AgentState
        alive_agents = [a for a in school.agents if a.state != AgentState.DEAD]
        if alive_agents:
            avg_roi = sum(getattr(a, 'roi', 0) for a in alive_agents) / len(alive_agents)
            median_roi = sorted([getattr(a, 'roi', 0) for a in alive_agents])[len(alive_agents)//2]
            
            logger.info(f"系统级指标:")
            logger.info(f"  存活Agent: {len(alive_agents)}/{len(school.agents)}")
            logger.info(f"  平均ROI: {avg_roi*100:+.2f}%")
            logger.info(f"  中位数ROI: {median_roi*100:+.2f}%")
            logger.info("")
        
        # Top 10 Agent
        logger.info(f"Top 10 Agent:")
        for i, agent in enumerate(best_agents[:10], 1):
            roi = getattr(agent, 'roi', 0)
            trade_count = getattr(agent, 'trade_count', 0)
            logger.info(
                f"  {i:2d}. {agent.agent_id}: "
                f"ROI={roi*100:+7.2f}%, "
                f"交易={trade_count:3d}次"
            )
        logger.info("")
        
        # 对比BTC
        best_roi = getattr(best_agents[0], 'roi', 0)
        
        logger.info("=" * 80)
        logger.info("🎯 验证结果:")
        logger.info("=" * 80)
        logger.info(f"BTC基准:     {btc_roi*100:+.2f}%")
        logger.info(f"系统平均:    {avg_roi*100:+.2f}%  (差距: {(avg_roi-btc_roi)*100:+.2f}%)")
        logger.info(f"最佳Agent:   {best_roi*100:+.2f}%  (差距: {(best_roi-btc_roi)*100:+.2f}%)")
        logger.info("")
        
        # 判断是否通过
        if avg_roi > btc_roi:
            logger.info("✅ ✅ ✅ 验证通过！系统平均ROI > BTC！")
            logger.info("   核心假设成立：进化算法可以找到盈利策略")
        elif best_roi > btc_roi * 1.2:
            logger.info("✅ ⚠️  部分通过：最佳Agent显著跑赢BTC")
            logger.info("   说明：系统有潜力，但需要优化")
        else:
            logger.info("❌ 验证失败：未能跑赢BTC")
            logger.info("   需要：诊断问题，调整参数")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        # 关闭数据库
        experience_db.close()
    
    logger.info("=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

