#!/usr/bin/env python3
"""
v5.3 牛市回测测试
测试Agent在牛市环境中的表现
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


def generate_bullmarket_data(days: int = 30, start_price: float = 50000.0, total_return: float = 0.20):
    """
    生成牛市数据
    
    特征：
    - 整体上涨趋势
    - 有回调但幅度小
    - 日均上涨 ~0.7%
    - 偶尔有3-5%的大阳线
    
    Args:
        days: 天数
        start_price: 起始价格
        total_return: 总涨幅（例如0.20表示+20%）
    """
    logger.info("\n" + "="*80)
    logger.info("📈 生成牛市数据")
    logger.info("="*80)
    logger.info(f"起始价格: ${start_price:,.2f}")
    logger.info(f"目标涨幅: +{total_return*100:.1f}%")
    logger.info(f"目标价格: ${start_price * (1 + total_return):,.2f}")
    logger.info(f"天数: {days}天")
    
    # 生成时间序列
    start_time = datetime(2025, 11, 6, 15, 24, 33)
    timestamps = [start_time + timedelta(days=i) for i in range(days)]
    
    # 牛市特征参数
    daily_drift = total_return / days  # 日均趋势
    base_volatility = 0.01  # 基础波动1%
    
    prices = [start_price]
    
    for i in range(1, days):
        current_price = prices[-1]
        
        # 牛市趋势
        trend = daily_drift
        
        # 随机波动
        noise = np.random.normal(0, base_volatility)
        
        # 10%概率出现大阳线（+3-5%）
        if np.random.random() < 0.1:
            big_rally = np.random.uniform(0.03, 0.05)
            logger.info(f"💥 第{i}天：大阳线 +{big_rally*100:.1f}%")
            daily_return = trend + big_rally
        # 15%概率出现回调（-2-3%）
        elif np.random.random() < 0.15:
            pullback = -np.random.uniform(0.02, 0.03)
            logger.info(f"📉 第{i}天：回调 {pullback*100:.1f}%")
            daily_return = pullback
        else:
            # 正常上涨
            daily_return = trend + noise
        
        # 限制单日最大变化（±8%）
        daily_return = max(-0.08, min(0.08, daily_return))
        
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
    
    logger.info("\n📊 数据生成完成:")
    logger.info(f"   起始价格: ${start_price:,.2f}")
    logger.info(f"   最终价格: ${final_price:,.2f}")
    logger.info(f"   实际涨幅: +{actual_return:.2f}%")
    logger.info(f"   目标涨幅: +{total_return*100:.1f}%")
    logger.info(f"   误差: {abs(actual_return - total_return*100):.2f}%")
    
    return df


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("🐂 v5.3 牛市回测测试")
    logger.info("="*80)
    
    # ============================================================================
    # 步骤1: 生成牛市数据
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤1: 生成牛市数据（+20%涨幅）")
    logger.info("="*80)
    
    kline_data = generate_bullmarket_data(
        days=30,
        start_price=50000.0,
        total_return=0.20  # +20%
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
    logger.info("📋 步骤4: 运行牛市回测")
    logger.info("="*80)
    
    results = backtest_engine.run()
    
    # ============================================================================
    # 步骤5: 分析结果
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤5: 分析牛市结果")
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
    logger.info(f"✅ Agent平均跑赢市场 {outperformance:.2f}个百分点")
    logger.info("="*60)
    
    # ============================================================================
    # 步骤6: 保存结果
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤6: 保存回测结果")
    logger.info("="*80)
    
    backtest_engine.save_results(output_dir="results/v53_bullmarket")
    
    logger.info(f"\n💾 结果已保存到: results/v53_bullmarket/")
    
    # ============================================================================
    # 步骤7: 对比分析
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("📋 步骤7: 牛市 vs 熊市对比分析")
    logger.info("="*80)
    
    logger.info("\n📊 对比分析:")
    logger.info("   牛市回测:")
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
    logger.info("     - 爆仓率: 2%")
    
    logger.info("\n💡 关键洞察:")
    agent_return = results['returns']['avg_return']
    market_return = results['market_performance']['market_return']
    outperformance = agent_return - market_return
    
    if outperformance > 0:
        logger.info(f"   ✅ Agent跑赢市场 {outperformance:.2f}个百分点")
    else:
        logger.info(f"   ⚠️  Agent跑输市场 {abs(outperformance):.2f}个百分点")
    
    # 判断做多/做空比例是否合理
    long_pct = results['trading_stats']['long_pct']
    if long_pct > 55:
        logger.info(f"   ✅ Agent正确识别牛市，做多{long_pct:.1f}%")
    else:
        logger.info(f"   ⚠️  Agent在牛市中做多比例较低: {long_pct:.1f}%")
    
    logger.info("\n" + "="*80)
    logger.info("✅ v5.3 牛市回测完成！")
    logger.info("="*80)


if __name__ == "__main__":
    main()

