#!/usr/bin/env python3
"""
v5.3 震荡市回测测试
测试Agent在震荡市环境中的表现
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.backtest.historical_backtest import HistoricalBacktest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_sideways_data(days: int = 30, start_price: float = 50000.0, volatility: float = 0.02):
    """
    生成震荡市数据
    
    特征：
    - 整体横盘，没有明显趋势
    - 上下波动但回归中枢
    - 日均波动 ~2%
    - 偶尔有5%的大波动
    
    Args:
        days: 天数
        start_price: 起始价格
        volatility: 波动率（标准差）
    """
    logger.info("\n" + "="*80)
    logger.info("📊 生成震荡市数据")
    logger.info("="*80)
    logger.info(f"起始价格: ${start_price:,.2f}")
    logger.info(f"波动率: {volatility*100:.1f}%")
    logger.info(f"天数: {days}天")
    
    # 生成时间序列
    start_time = datetime(2025, 11, 6, 15, 24, 33)
    timestamps = [start_time + timedelta(days=i) for i in range(days)]
    
    # 震荡市特征：均值回归
    prices = [start_price]
    mean_price = start_price
    
    for i in range(1, days):
        current_price = prices[-1]
        
        # 均值回归力量：价格偏离中枢越远，回归力量越强
        mean_reversion = (mean_price - current_price) / mean_price * 0.3
        
        # 随机波动
        noise = np.random.normal(0, volatility)
        
        # 10%概率出现大波动（±4-5%）
        if np.random.random() < 0.1:
            big_move = np.random.uniform(0.04, 0.05) * np.random.choice([-1, 1])
            logger.info(f"💥 第{i}天：大波动 {big_move*100:+.1f}%")
            daily_return = big_move
        else:
            # 正常震荡（含均值回归）
            daily_return = mean_reversion + noise
        
        # 限制单日最大变化（±7%）
        daily_return = max(-0.07, min(0.07, daily_return))
        
        new_price = current_price * (1 + daily_return)
        prices.append(new_price)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices,
        'high': [p * 1.002 for p in prices],  # 简化
        'low': [p * 0.998 for p in prices],   # 简化
        'close': prices,
        'volume': [1000000] * days  # 简化
    })
    
    final_price = prices[-1]
    actual_return = (final_price / start_price - 1) * 100
    
    # 计算波动率
    returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
    actual_volatility = np.std(returns) * 100
    
    logger.info("\n📊 数据生成完成:")
    logger.info(f"   起始价格: ${start_price:,.2f}")
    logger.info(f"   最终价格: ${final_price:,.2f}")
    logger.info(f"   净变化: {actual_return:+.2f}%（应接近0）")
    logger.info(f"   实际波动率: {actual_volatility:.2f}%")
    logger.info(f"   最高价: ${max(prices):,.2f} (+{(max(prices)/start_price-1)*100:.1f}%)")
    logger.info(f"   最低价: ${min(prices):,.2f} ({(min(prices)/start_price-1)*100:.1f}%)")
    
    return df


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("📊 v5.3 震荡市回测测试")
    logger.info("="*80)
    
    # ============================================================================
    # 步骤1: 生成震荡市数据
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤1: 生成震荡市数据（横盘±5%）")
    logger.info("="*80)
    
    kline_data = generate_sideways_data(
        days=30,
        start_price=50000.0,
        volatility=0.02  # 2%日波动
    )
    
    # ============================================================================
    # 步骤2: 初始化进化管理器
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤2: 初始化进化管理器")
    logger.info("="*80)
    
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # ============================================================================
    # 步骤3: 创建回测引擎
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤3: 创建历史回测引擎")
    logger.info("="*80)
    
    backtest_engine = HistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,  # 每10根K线进化一次
        initial_agents=50,
        initial_capital=10000.0
    )
    
    # ============================================================================
    # 步骤4: 运行回测
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤4: 运行震荡市回测")
    logger.info("="*80)
    
    results = backtest_engine.run()
    
    # ============================================================================
    # 步骤5: 分析结果
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤5: 分析震荡市结果")
    logger.info("="*80)
    
    # 打印摘要
    logger.info("\n📊 回测结果摘要")
    logger.info("="*60)
    logger.info(f"\n📈 市场表现:")
    logger.info(f"   初始价格: ${results['market_performance']['initial_price']:,.2f}")
    logger.info(f"   最终价格: ${results['market_performance']['final_price']:,.2f}")
    logger.info(f"   市场收益: {results['market_performance']['market_return']:+.2f}%")
    
    logger.info(f"\n👥 种群表现:")
    logger.info(f"   初始Agent: {results['population']['initial']}个")
    logger.info(f"   最终Agent: {results['population']['final']}个")
    logger.info(f"   存活率: {results['population']['survival_rate']:.1f}%")
    
    logger.info(f"\n💰 资金表现:")
    logger.info(f"   初始资金: ${results['capital']['initial_avg']:,.2f}")
    logger.info(f"   最终资金: ${results['capital']['final_avg']:,.2f}")
    logger.info(f"   Agent平均收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"   最高收益: {results['returns']['max_return']:+.2f}%")
    logger.info(f"   最低收益: {results['returns']['min_return']:+.2f}%")
    
    logger.info(f"\n📈 交易统计（多空 + 杠杆）:")
    logger.info(f"   总交易次数: {results['trading_stats']['total_trades']}次")
    logger.info(f"   做多(Long): {results['trading_stats']['long_trades']}次 ({results['trading_stats']['long_pct']:.1f}%)")
    logger.info(f"   做空(Short): {results['trading_stats']['short_trades']}次 ({results['trading_stats']['short_pct']:.1f}%)")
    logger.info(f"   平均杠杆: {results['trading_stats']['avg_leverage']:.2f}x ⭐")
    logger.info(f"   最高杠杆: {results['trading_stats']['max_leverage']:.2f}x")
    
    logger.info(f"\n💥 风险统计（爆仓）:")
    logger.info(f"   初始Agent: {results['risk_stats']['initial_agents']}个")
    logger.info(f"   幸存Agent: {results['risk_stats']['survived_agents']}个")
    logger.info(f"   爆仓Agent: {results['risk_stats']['liquidated_agents']}个 💀")
    logger.info(f"   爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    logger.info("\n" + "="*60)
    outperformance = results['returns']['avg_return'] - results['market_performance']['market_return']
    if outperformance > 0:
        logger.info(f"✅ Agent平均跑赢市场 {outperformance:.2f}个百分点")
    else:
        logger.info(f"⚠️  Agent平均跑输市场 {abs(outperformance):.2f}个百分点")
    logger.info("="*60)
    
    # ============================================================================
    # 步骤6: 保存结果
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤6: 保存回测结果")
    logger.info("="*80)
    
    backtest_engine.save_results(output_dir="results/v53_sideways")
    
    logger.info(f"\n💾 结果已保存到: results/v53_sideways/")
    
    # ============================================================================
    # 步骤7: 对比分析
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤7: 震荡市 vs 熊市 vs 牛市对比")
    logger.info("="*80)
    
    logger.info("\n📊 对比分析:")
    logger.info("   震荡市回测:")
    logger.info(f"     - Agent平均收益: {results['returns']['avg_return']:+.2f}%")
    logger.info(f"     - 市场收益: {results['market_performance']['market_return']:+.2f}%")
    logger.info(f"     - 种群存活率: {results['population']['survival_rate']:.1f}%")
    logger.info(f"     - 平均杠杆: {results['trading_stats']['avg_leverage']:.2f}x")
    logger.info(f"     - 做多比例: {results['trading_stats']['long_pct']:.1f}%")
    logger.info(f"     - 做空比例: {results['trading_stats']['short_pct']:.1f}%")
    logger.info(f"     - 爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    logger.info("\n   熊市对比（参考）:")
    logger.info("     - Agent平均收益: +9.89%")
    logger.info("     - 市场收益: -10.47%")
    logger.info("     - 做空比例: 55%")
    
    logger.info("\n   牛市对比（参考）:")
    logger.info("     - 等待测试...")
    
    logger.info("\n💡 关键洞察:")
    agent_return = results['returns']['avg_return']
    market_return = results['market_performance']['market_return']
    
    # 震荡市的特殊评价标准
    if agent_return > 0:
        logger.info(f"   ✅ Agent在震荡市实现盈利: +{agent_return:.2f}%")
        logger.info("   （震荡市难以盈利，任何正收益都是成功！）")
    else:
        logger.info(f"   ⚠️  Agent在震荡市亏损: {agent_return:.2f}%")
    
    # 检查交易策略
    long_pct = results['trading_stats']['long_pct']
    short_pct = results['trading_stats']['short_pct']
    if abs(long_pct - short_pct) < 10:
        logger.info(f"   ✅ Agent多空平衡（多{long_pct:.0f}%/空{short_pct:.0f}%），适应震荡市")
    else:
        logger.info(f"   ⚠️  Agent策略偏向{'做多' if long_pct > short_pct else '做空'}，可能不适合震荡市")
    
    # 检查杠杆
    avg_leverage = results['trading_stats']['avg_leverage']
    if avg_leverage < 5:
        logger.info(f"   ✅ Agent降低杠杆({avg_leverage:.1f}x)，适应震荡市高波动")
    else:
        logger.info(f"   ⚠️  Agent杠杆较高({avg_leverage:.1f}x)，震荡市风险大")
    
    logger.info("\n" + "="*80)
    logger.info("✅ v5.3 震荡市回测完成！")
    logger.info("="*80)


if __name__ == "__main__":
    main()

