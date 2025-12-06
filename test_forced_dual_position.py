#!/usr/bin/env python3
"""
🔥 强制双向持仓测试

所有Agent必须同时做多做空！
看看纯粹的双向持仓策略效果如何！
"""

import sys
import os
import numpy as np
import logging
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.market.okx_data_loader import OKXDataLoader
from prometheus.backtest.crazy_mode_backtest import CrazyModeBacktest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ForcedDualPositionBacktest(CrazyModeBacktest):
    """
    强制双向持仓回测
    
    所有Agent必须同时持有多头和空头！
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning("\n" + "="*60)
        logger.warning("💥 强制双向持仓模式启动！")
        logger.warning("⚠️  所有Agent必须同时做多做空！")
        logger.warning("⚠️  让我们看看会发生什么...⚡")
        logger.warning("="*60 + "\n")
    
    def _agent_make_dual_position_decision(self, agent, price_change: float) -> Dict[str, float]:
        """
        强制双向持仓决策
        
        所有Agent必须同时做多做空！
        """
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
        time_preference = getattr(agent.instinct, 'time_preference', 0.5)
        
        # 计算趋势
        if len(self.price_history) >= 5:
            recent_prices = [p['price'] for p in self.price_history[-5:]]
            short_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        else:
            short_trend = 0
        
        # 强制双向持仓！
        # 策略：根据趋势判断，主方向仓位大，次方向仓位小
        
        if abs(short_trend) > 0.02:
            # 趋势明显
            if short_trend > 0:
                # 上涨趋势：做多为主，做空为辅
                long_position = 0.6 * (0.5 + 0.5 * risk_tolerance)
                short_position = 0.2 * (0.5 + 0.5 * risk_tolerance)
            else:
                # 下跌趋势：做空为主，做多为辅
                short_position = 0.6 * (0.5 + 0.5 * risk_tolerance)
                long_position = 0.2 * (0.5 + 0.5 * risk_tolerance)
        else:
            # 震荡市：两边都下注，接近平衡
            long_position = 0.4 * (0.5 + 0.5 * risk_tolerance)
            short_position = 0.4 * (0.5 + 0.5 * risk_tolerance)
        
        # 根据时间偏好调整
        factor = 0.5 + 0.5 * time_preference
        long_position *= factor
        short_position *= factor
        
        # 确保两边都有仓位（至少5%）
        long_position = max(0.05, long_position)
        short_position = max(0.05, short_position)
        
        # 杠杆
        long_leverage = self._agent_choose_leverage(agent)
        short_leverage = self._agent_choose_leverage(agent)
        
        return {
            'long_position': long_position,
            'short_position': short_position,
            'long_leverage': long_leverage,
            'short_leverage': short_leverage
        }


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("💥 强制双向持仓测试")
    logger.info("="*80)
    logger.info("")
    logger.info("⚠️  所有Agent必须同时做多做空！")
    logger.info("⚠️  这是最极端的测试...⚡⚡⚡")
    logger.info("")
    logger.info("="*80 + "\n")
    
    # 加载数据
    logger.info("📋 步骤1: 加载历史数据")
    loader = OKXDataLoader()
    kline_data = loader.load_or_generate(days=30)
    
    # 初始化
    logger.info("\n📋 步骤2: 初始化进化管理器")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建强制双向持仓回测
    logger.info("\n📋 步骤3: 创建强制双向持仓回测引擎")
    backtest = ForcedDualPositionBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,
        initial_agents=50,
        initial_capital=10000.0
    )
    
    # 运行
    logger.info("\n📋 步骤4: 运行强制双向持仓回测")
    logger.info("💥 准备好了吗？这可能会很疯狂...⚡⚡⚡")
    logger.info("")
    
    results = backtest.run()
    
    # 分析结果
    logger.info("\n" + "="*80)
    logger.info("📋 步骤5: 分析强制双向持仓结果")
    logger.info("="*80)
    
    logger.info("\n📊 基础结果:")
    logger.info(f"   Agent平均收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"   市场收益: {results['market_performance']['market_return']:+.2f}%")
    logger.info(f"   vs市场: {results['returns']['avg_return'] - results['market_performance']['market_return']:+.2f}%")
    
    logger.info(f"\n👥 种群表现:")
    logger.info(f"   存活率: {results['population']['survival_rate']:.1f}%")
    logger.info(f"   爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    if 'crazy_mode_stats' in results:
        crazy = results['crazy_mode_stats']
        logger.info(f"\n💥 双向持仓统计:")
        logger.info(f"   平均多头敞口: {crazy['avg_long_exposure']:.2f}x")
        logger.info(f"   平均空头敞口: {crazy['avg_short_exposure']:.2f}x")
        logger.info(f"   平均总敞口: {crazy['avg_total_exposure']:.2f}x ⚡⚡⚡")
        logger.info(f"   最高总敞口: {crazy['max_total_exposure']:.2f}x 💀💀💀")
        logger.info(f"   双向持仓次数: {crazy['dual_position_count']}次")
        logger.info(f"   双向持仓比例: {crazy['dual_position_rate']:.1f}% ⭐⭐⭐")
    
    # 三模式对比
    logger.info(f"\n💡 三模式对比:")
    logger.info(f"   正常模式（单向）:")
    logger.info(f"     收益: +9.89% | 爆仓率: 2% | 杠杆: 7.5x")
    logger.info(f"")
    logger.info(f"   自由模式（可选双向）:")
    logger.info(f"     收益: +9.49% | 爆仓率: 2% | 双向: 0%")
    logger.info(f"")
    logger.info(f"   强制模式（必须双向）:")
    logger.info(f"     收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"     爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    if 'crazy_mode_stats' in results:
        logger.info(f"     双向: {crazy['dual_position_rate']:.1f}%")
    
    # 关键发现
    logger.info(f"\n🎯 关键发现:")
    
    agent_return = results['returns']['avg_return']
    liquidation_rate = results['risk_stats']['liquidation_rate']
    
    if agent_return < 5:
        logger.info(f"   💀 强制双向持仓严重影响收益（{agent_return:+.2f}%）")
        logger.info(f"   这证明：双向持仓不是最优策略！⭐⭐⭐⭐⭐")
    elif agent_return < 9:
        logger.info(f"   ⚠️  强制双向持仓降低收益（{agent_return:+.2f}% vs +9.89%）")
        logger.info(f"   这证明：双向持仓有成本！")
    else:
        logger.info(f"   😮 强制双向持仓竟然有效（{agent_return:+.2f}%）")
        logger.info(f"   这可能值得进一步研究！")
    
    if liquidation_rate > 20:
        logger.info(f"   💀 爆仓率极高（{liquidation_rate:.1f}%）")
        logger.info(f"   双向持仓太危险了！")
    elif liquidation_rate > 10:
        logger.info(f"   ⚠️  爆仓率偏高（{liquidation_rate:.1f}%）")
    else:
        logger.info(f"   ✅ 爆仓率可控（{liquidation_rate:.1f}%）")
    
    if 'crazy_mode_stats' in results:
        dual_rate = crazy['dual_position_rate']
        if dual_rate > 90:
            logger.info(f"   ✅ 成功强制双向持仓（{dual_rate:.1f}%）")
        else:
            logger.info(f"   ⚠️  部分Agent可能被淘汰或爆仓")
    
    # 保存结果
    logger.info(f"\n📋 步骤6: 保存结果")
    backtest.save_results(output_dir="results/forced_dual")
    logger.info(f"💾 结果已保存到: results/forced_dual/")
    
    logger.info("\n" + "="*80)
    logger.info("💥 强制双向持仓测试完成！")
    logger.info("="*80)
    
    # 最终结论
    logger.info("\n💭 最终结论:")
    
    if agent_return < 5 and liquidation_rate < 10:
        logger.info("   强制双向持仓大幅降低了收益，但风险可控。")
        logger.info("   这证明：双向持仓的成本远大于收益！⭐⭐⭐⭐⭐")
        logger.info("   Agent在自由模式下拒绝双向持仓是正确的！")
    elif agent_return < 9:
        logger.info("   强制双向持仓降低了收益。")
        logger.info("   这证明：单向持仓更优！⭐⭐⭐⭐")
    elif liquidation_rate > 20:
        logger.info("   强制双向持仓导致大量爆仓！")
        logger.info("   这证明：双向持仓太危险！⚠️⚠️⚠️")
    else:
        logger.info("   强制双向持仓的结果出乎意料...")
        logger.info("   可能需要进一步分析。")
    
    logger.info("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

