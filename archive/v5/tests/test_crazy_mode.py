#!/usr/bin/env python3
"""
🔥 疯狂模式测试

放开Agent的所有束缚：
- 双向持仓
- 杠杆叠加
- 无限制

看看会发生什么！⚡⚡⚡
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.market.okx_data_loader import OKXDataLoader
from prometheus.backtest.crazy_mode_backtest import CrazyModeBacktest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """疯狂模式主函数"""
    logger.info("\n" + "="*80)
    logger.info("🔥🔥🔥 疯狂模式启动 🔥🔥🔥")
    logger.info("="*80)
    logger.info("")
    logger.info("⚠️  警告：所有安全限制已解除！")
    logger.info("⚠️  Agent拥有完全自由！")
    logger.info("⚠️  可以双向持仓（同时做多做空）")
    logger.info("⚠️  可以杠杆叠加（多头10x + 空头10x = 20x总敞口）")
    logger.info("⚠️  这可能会非常疯狂...让我们看看会发生什么！")
    logger.info("")
    logger.info("="*80 + "\n")
    
    # 步骤1: 加载数据
    logger.info("📋 步骤1: 加载历史数据")
    loader = OKXDataLoader()
    kline_data = loader.load_or_generate(days=30)
    
    # 步骤2: 初始化
    logger.info("\n📋 步骤2: 初始化进化管理器")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 步骤3: 创建疯狂模式回测
    logger.info("\n📋 步骤3: 创建疯狂模式回测引擎")
    backtest = CrazyModeBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,
        initial_agents=50,
        initial_capital=10000.0
    )
    
    # 步骤4: 运行
    logger.info("\n📋 步骤4: 运行疯狂模式回测")
    logger.info("🔥 准备好了吗？这可能会很疯狂...⚡")
    logger.info("")
    
    results = backtest.run()
    
    # 步骤5: 分析结果
    logger.info("\n" + "="*80)
    logger.info("📋 步骤5: 分析疯狂模式结果")
    logger.info("="*80)
    
    # 基础统计
    logger.info("\n📊 基础结果:")
    logger.info(f"   Agent平均收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"   市场收益: {results['market_performance']['market_return']:+.2f}%")
    logger.info(f"   vs市场: {results['returns']['avg_return'] - results['market_performance']['market_return']:+.2f}%")
    logger.info(f"   最高收益: {results['returns']['max_return']:+.2f}%")
    logger.info(f"   最低收益: {results['returns']['min_return']:+.2f}%")
    
    logger.info(f"\n👥 种群表现:")
    logger.info(f"   初始Agent: {results['population']['initial']}个")
    logger.info(f"   最终Agent: {results['population']['final']}个")
    logger.info(f"   存活率: {results['population']['survival_rate']:.1f}%")
    logger.info(f"   爆仓数: {results['risk_stats']['liquidated_agents']}个")
    logger.info(f"   爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    # 疯狂模式特有统计
    if 'crazy_mode_stats' in results:
        crazy = results['crazy_mode_stats']
        logger.info(f"\n🔥 疯狂模式特有统计:")
        logger.info(f"   平均多头敞口: {crazy['avg_long_exposure']:.2f}x")
        logger.info(f"   平均空头敞口: {crazy['avg_short_exposure']:.2f}x")
        logger.info(f"   平均总敞口: {crazy['avg_total_exposure']:.2f}x ⚡⚡⚡")
        logger.info(f"   最高总敞口: {crazy['max_total_exposure']:.2f}x 💀💀💀")
        logger.info(f"   双向持仓次数: {crazy['dual_position_count']}次")
        logger.info(f"   双向持仓比例: {crazy['dual_position_rate']:.1f}%")
    
    # 对比分析
    logger.info(f"\n💡 vs 正常模式:")
    logger.info(f"   正常模式收益: +9.89%（熊市参考）")
    logger.info(f"   疯狂模式收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"   差异: {results['returns']['avg_return'] - 9.89:+.2f}%")
    logger.info(f"")
    logger.info(f"   正常模式爆仓率: 2%")
    logger.info(f"   疯狂模式爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    logger.info(f"   差异: {results['risk_stats']['liquidation_rate'] - 2:+.1f}%")
    
    # 关键发现
    logger.info(f"\n🎯 关键发现:")
    
    if 'crazy_mode_stats' in results:
        dual_rate = crazy['dual_position_rate']
        if dual_rate > 20:
            logger.info(f"   ✅ Agent大量使用双向持仓（{dual_rate:.1f}%）")
            logger.info(f"   这说明Agent发现了双向持仓的价值！")
        elif dual_rate > 5:
            logger.info(f"   ⚠️  Agent偶尔使用双向持仓（{dual_rate:.1f}%）")
            logger.info(f"   这说明双向持仓在某些情况下有用")
        else:
            logger.info(f"   ❌ Agent很少使用双向持仓（{dual_rate:.1f}%）")
            logger.info(f"   这说明双向持仓可能不是最优策略")
        
        avg_exposure = crazy['avg_total_exposure']
        if avg_exposure > 15:
            logger.info(f"   💀 Agent使用了极高杠杆（{avg_exposure:.1f}x总敞口）")
            logger.info(f"   这非常危险！")
        elif avg_exposure > 10:
            logger.info(f"   ⚠️  Agent使用了高杠杆（{avg_exposure:.1f}x总敞口）")
        else:
            logger.info(f"   ✅ Agent保持了理性（{avg_exposure:.1f}x总敞口）")
    
    liquidation_rate = results['risk_stats']['liquidation_rate']
    if liquidation_rate > 20:
        logger.info(f"   💀 爆仓率极高（{liquidation_rate:.1f}%）")
        logger.info(f"   完全自由导致了灾难！")
    elif liquidation_rate > 10:
        logger.info(f"   ⚠️  爆仓率较高（{liquidation_rate:.1f}%）")
        logger.info(f"   自由是有代价的")
    else:
        logger.info(f"   ✅ 爆仓率可控（{liquidation_rate:.1f}%）")
        logger.info(f"   Agent保持了理性！")
    
    agent_return = results['returns']['avg_return']
    if agent_return > 15:
        logger.info(f"   🚀 收益显著提升（{agent_return:+.2f}%）")
        logger.info(f"   自由带来了更高收益！")
    elif agent_return > 10:
        logger.info(f"   ✅ 收益略有提升（{agent_return:+.2f}%）")
    else:
        logger.info(f"   ⚠️  收益不如预期（{agent_return:+.2f}%）")
        logger.info(f"   自由未必带来更好结果")
    
    # 步骤6: 保存结果
    logger.info(f"\n📋 步骤6: 保存结果")
    backtest.save_results(output_dir="results/crazy_mode")
    logger.info(f"💾 结果已保存到: results/crazy_mode/")
    
    logger.info("\n" + "="*80)
    logger.info("🔥 疯狂模式测试完成！")
    logger.info("="*80)
    
    # 最终结论
    logger.info("\n💭 最终结论:")
    if dual_rate < 5 and liquidation_rate < 5:
        logger.info("   Agent在完全自由下，选择了克制和理性。")
        logger.info("   这说明：约束可能是不必要的，Agent有自我控制能力！⭐⭐⭐⭐⭐")
    elif dual_rate > 20 and agent_return > 15:
        logger.info("   Agent充分利用了双向持仓，获得了更高收益！")
        logger.info("   这说明：双向持仓可能是有价值的功能！⭐⭐⭐⭐")
    elif liquidation_rate > 20:
        logger.info("   Agent在完全自由下，选择了极端策略导致大量爆仓。")
        logger.info("   这说明：约束是必要的，自由可能导致灾难！⚠️⚠️⚠️")
    else:
        logger.info("   Agent在自由和约束之间找到了平衡。")
        logger.info("   这说明：适度的自由是最优的！⭐⭐⭐⭐")
    
    logger.info("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

