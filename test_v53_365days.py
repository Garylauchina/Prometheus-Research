#!/usr/bin/env python3
"""
📈 v5.3 365天长期回测测试

穿越完整牛熊周期，测试Agent的长期表现
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

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


def generate_365days_data(start_price: float = 50000.0):
    """
    生成365天的真实风格数据
    
    特征：
    - 包含牛市、熊市、震荡市的自然交替
    - 模拟真实的市场周期
    - 包含黑天鹅事件
    
    市场周期设计（参考真实BTC历史）：
    - Q1 (1-90天): 牛市反弹 (+30-50%)
    - Q2 (91-180天): 高位震荡 (±10%)
    - Q3 (181-270天): 熊市下跌 (-40-50%)
    - Q4 (271-365天): 底部震荡 (±15%)
    """
    logger.info("\n" + "="*80)
    logger.info("📈 生成365天长期数据")
    logger.info("="*80)
    logger.info(f"起始价格: ${start_price:,.2f}")
    logger.info(f"周期设计:")
    logger.info(f"  Q1 (1-90天):   牛市反弹 (+40%)")
    logger.info(f"  Q2 (91-180天):  高位震荡 (±10%)")
    logger.info(f"  Q3 (181-270天): 熊市暴跌 (-45%)")
    logger.info(f"  Q4 (271-365天): 底部震荡 (±15%)")
    
    # 生成时间序列
    start_time = datetime(2024, 1, 1)
    timestamps = [start_time + timedelta(days=i) for i in range(365)]
    
    prices = [start_price]
    
    for i in range(1, 365):
        current_price = prices[-1]
        
        # 确定当前所处阶段
        if i <= 90:
            # Q1: 牛市反弹
            phase = "bull"
            daily_drift = 0.004  # 日均+0.4%
            volatility = 0.015   # 1.5%波动
            big_move_prob = 0.15  # 15%概率大阳线
        elif i <= 180:
            # Q2: 高位震荡
            phase = "sideways_high"
            mean_price = prices[90]  # Q1结束价格
            mean_reversion = (mean_price - current_price) / mean_price * 0.2
            daily_drift = mean_reversion
            volatility = 0.02     # 2%波动
            big_move_prob = 0.1   # 10%概率大波动
        elif i <= 270:
            # Q3: 熊市暴跌
            phase = "bear"
            daily_drift = -0.005  # 日均-0.5%
            volatility = 0.02     # 2%波动
            big_move_prob = 0.1   # 10%概率暴跌
        else:
            # Q4: 底部震荡
            phase = "sideways_low"
            mean_price = prices[270]  # Q3结束价格
            mean_reversion = (mean_price - current_price) / mean_price * 0.15
            daily_drift = mean_reversion
            volatility = 0.025    # 2.5%波动
            big_move_prob = 0.12  # 12%概率大波动
        
        # 基础变化
        noise = np.random.normal(0, volatility)
        daily_return = daily_drift + noise
        
        # 大波动事件
        if np.random.random() < big_move_prob:
            if phase == "bull":
                # 牛市大阳线
                big_move = np.random.uniform(0.05, 0.10)
                daily_return += big_move
                if i % 30 == 0:  # 每月报告一次
                    logger.info(f"💥 第{i}天（牛市）：大阳线 +{(daily_drift + noise + big_move)*100:.1f}%")
            elif phase == "bear":
                # 熊市暴跌
                big_move = -np.random.uniform(0.05, 0.15)
                daily_return += big_move
                if abs(big_move) > 0.10:
                    logger.info(f"💀 第{i}天（熊市）：暴跌 {(daily_drift + noise + big_move)*100:.1f}%")
            else:
                # 震荡市大波动
                big_move = np.random.uniform(0.04, 0.08) * np.random.choice([-1, 1])
                daily_return += big_move
        
        # 黑天鹅事件（1%概率）
        if np.random.random() < 0.01:
            black_swan = -np.random.uniform(0.15, 0.25)  # -15%到-25%
            daily_return = black_swan
            logger.warning(f"🦢 第{i}天：黑天鹅事件 {black_swan*100:.1f}%")
        
        # 限制单日最大变化
        daily_return = max(-0.25, min(0.15, daily_return))
        
        new_price = current_price * (1 + daily_return)
        prices.append(new_price)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices,
        'high': [p * 1.002 for p in prices],
        'low': [p * 0.998 for p in prices],
        'close': prices,
        'volume': [1000000] * 365
    })
    
    # 统计
    final_price = prices[-1]
    q1_price = prices[90]
    q2_price = prices[180]
    q3_price = prices[270]
    
    logger.info("\n📊 数据生成完成:")
    logger.info(f"   起始价格: ${start_price:,.2f}")
    logger.info(f"   Q1结束: ${q1_price:,.2f} ({(q1_price/start_price-1)*100:+.1f}%)")
    logger.info(f"   Q2结束: ${q2_price:,.2f} ({(q2_price/q1_price-1)*100:+.1f}%)")
    logger.info(f"   Q3结束: ${q3_price:,.2f} ({(q3_price/q2_price-1)*100:+.1f}%)")
    logger.info(f"   最终价格: ${final_price:,.2f} ({(final_price/q3_price-1)*100:+.1f}%)")
    logger.info(f"   全年涨跌: {(final_price/start_price-1)*100:+.2f}%")
    logger.info(f"   最高价: ${max(prices):,.2f} (+{(max(prices)/start_price-1)*100:.1f}%)")
    logger.info(f"   最低价: ${min(prices):,.2f} ({(min(prices)/start_price-1)*100:.1f}%)")
    
    return df


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("📅 v5.3 365天长期回测测试")
    logger.info("="*80)
    logger.info("🎯 目标：验证Agent穿越完整牛熊周期的能力")
    logger.info("⏱️  预计用时：2-3分钟")
    logger.info("="*80 + "\n")
    
    # 步骤1: 生成365天数据
    logger.info("📋 步骤1: 生成365天数据（含牛熊周期）")
    kline_data = generate_365days_data(start_price=50000.0)
    
    # 步骤2: 初始化
    logger.info("\n📋 步骤2: 初始化进化管理器")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 步骤3: 创建回测引擎
    logger.info("\n📋 步骤3: 创建长期回测引擎")
    backtest = HistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=30,  # 每30天（月度）进化一次
        initial_agents=50,
        initial_capital=10000.0
    )
    
    logger.info(f"   进化间隔: 30天（月度进化）")
    logger.info(f"   预计进化次数: 12次（每月一次）")
    
    # 步骤4: 运行回测
    logger.info("\n📋 步骤4: 运行365天长期回测")
    logger.info("🚀 这将需要2-3分钟，请耐心等待...")
    logger.info("")
    
    results = backtest.run()
    
    # 步骤5: 分析结果
    logger.info("\n" + "="*80)
    logger.info("📋 步骤5: 分析365天长期结果")
    logger.info("="*80)
    
    # 基础统计
    logger.info("\n📊 365天回测结果摘要")
    logger.info("="*60)
    
    logger.info(f"\n📈 市场表现:")
    logger.info(f"   起始价格: ${results['market_performance']['initial_price']:,.2f}")
    logger.info(f"   最终价格: ${results['market_performance']['final_price']:,.2f}")
    logger.info(f"   全年涨跌: {results['market_performance']['market_return']:+.2f}%")
    
    logger.info(f"\n👥 种群表现:")
    logger.info(f"   初始Agent: {results['population']['initial']}个")
    logger.info(f"   最终Agent: {results['population']['final']}个")
    logger.info(f"   存活率: {results['population']['survival_rate']:.1f}%")
    logger.info(f"   进化次数: {results['backtest_summary']['evolution_cycles']}次")
    
    logger.info(f"\n💰 资金表现:")
    logger.info(f"   初始资金: ${results['capital']['initial_avg']:,.2f}")
    logger.info(f"   最终资金: ${results['capital']['final_avg']:,.2f}")
    logger.info(f"   Agent年化收益: {results['returns']['avg_return']:+.2f}% ⭐⭐⭐")
    logger.info(f"   最高收益: {results['returns']['max_return']:+.2f}%")
    logger.info(f"   最低收益: {results['returns']['min_return']:+.2f}%")
    logger.info(f"   标准差: ${results['capital']['final_std']:,.2f}")
    
    logger.info(f"\n📈 交易统计:")
    logger.info(f"   总交易次数: {results['trading_stats']['total_trades']}次")
    logger.info(f"   日均交易: {results['trading_stats']['total_trades']/365:.1f}次/天")
    logger.info(f"   做多比例: {results['trading_stats']['long_pct']:.1f}%")
    logger.info(f"   做空比例: {results['trading_stats']['short_pct']:.1f}%")
    logger.info(f"   平均杠杆: {results['trading_stats']['avg_leverage']:.2f}x")
    
    logger.info(f"\n💥 风险统计:")
    logger.info(f"   爆仓Agent: {results['risk_stats']['liquidated_agents']}个")
    logger.info(f"   爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    # 计算关键指标
    agent_return = results['returns']['avg_return']
    market_return = results['market_performance']['market_return']
    outperformance = agent_return - market_return
    
    logger.info(f"\n🎯 关键指标:")
    logger.info(f"   Agent年化收益: {agent_return:+.2f}%")
    logger.info(f"   市场年化收益: {market_return:+.2f}%")
    if outperformance > 0:
        logger.info(f"   ✅ 跑赢市场: {outperformance:+.2f}个百分点 ⭐⭐⭐")
    else:
        logger.info(f"   ⚠️  跑输市场: {abs(outperformance):.2f}个百分点")
    
    # 计算最大回撤
    capitals = [results['capital']['initial_avg']]
    if hasattr(backtest, 'population_history'):
        for record in backtest.population_history:
            capitals.append(record['avg_capital'])
    
    max_capital = max(capitals)
    max_drawdown = 0
    for cap in capitals:
        drawdown = (max_capital - cap) / max_capital
        max_drawdown = max(max_drawdown, drawdown)
    
    logger.info(f"   最大回撤: {max_drawdown*100:.2f}%")
    
    # 夏普比率（简化版）
    if len(capitals) > 1:
        returns = [(capitals[i]/capitals[i-1] - 1) for i in range(1, len(capitals))]
        if len(returns) > 0:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = avg_return / std_return if std_return > 0 else 0
            sharpe_annualized = sharpe * np.sqrt(12)  # 月度数据年化
            logger.info(f"   夏普比率: {sharpe_annualized:.2f}")
    
    logger.info("\n" + "="*60)
    
    # 步骤6: 保存结果
    logger.info("\n📋 步骤6: 保存365天回测结果")
    backtest.save_results(output_dir="results/v53_365days")
    logger.info(f"💾 结果已保存到: results/v53_365days/")
    
    # 步骤7: 对比30天 vs 365天
    logger.info("\n" + "="*80)
    logger.info("📋 步骤7: 短期 vs 长期对比分析")
    logger.info("="*80)
    
    logger.info("\n📊 对比分析:")
    logger.info("   30天测试（熊市）:")
    logger.info("     - Agent收益: +9.89%")
    logger.info("     - 市场收益: -10.47%")
    logger.info("     - 爆仓率: 2%")
    logger.info("     - 进化次数: 3次")
    
    logger.info(f"\n   365天测试（牛熊周期）:")
    logger.info(f"     - Agent收益: {agent_return:+.2f}%")
    logger.info(f"     - 市场收益: {market_return:+.2f}%")
    logger.info(f"     - 爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    logger.info(f"     - 进化次数: {results['backtest_summary']['evolution_cycles']}次")
    logger.info(f"     - 最大回撤: {max_drawdown*100:.2f}%")
    
    logger.info("\n💡 关键洞察:")
    
    # 评估长期表现
    if agent_return > 50:
        logger.info(f"   🚀 年化收益惊人（{agent_return:+.2f}%）")
        logger.info("   这是顶级量化基金的水平！⭐⭐⭐⭐⭐")
    elif agent_return > 30:
        logger.info(f"   ✅ 年化收益优秀（{agent_return:+.2f}%）")
        logger.info("   这超过了大多数对冲基金！⭐⭐⭐⭐")
    elif agent_return > 10:
        logger.info(f"   ✅ 年化收益良好（{agent_return:+.2f}%）")
        logger.info("   这是稳健的表现！⭐⭐⭐")
    else:
        logger.info(f"   ⚠️  年化收益一般（{agent_return:+.2f}%）")
    
    # 评估回撤
    if max_drawdown < 0.15:
        logger.info(f"   ✅ 回撤控制优秀（{max_drawdown*100:.1f}%）⭐⭐⭐⭐")
    elif max_drawdown < 0.30:
        logger.info(f"   ✅ 回撤控制良好（{max_drawdown*100:.1f}%）⭐⭐⭐")
    else:
        logger.info(f"   ⚠️  回撤较大（{max_drawdown*100:.1f}%）")
    
    # 评估爆仓率
    liquidation_rate = results['risk_stats']['liquidation_rate']
    if liquidation_rate < 10:
        logger.info(f"   ✅ 长期爆仓率优秀（{liquidation_rate:.1f}%）⭐⭐⭐⭐")
    elif liquidation_rate < 30:
        logger.info(f"   ✅ 长期爆仓率可接受（{liquidation_rate:.1f}%）⭐⭐⭐")
    else:
        logger.info(f"   ⚠️  长期爆仓率偏高（{liquidation_rate:.1f}%）")
    
    # 评估跑赢市场
    if outperformance > 20:
        logger.info(f"   🚀 大幅跑赢市场（{outperformance:+.2f}%）⭐⭐⭐⭐⭐")
    elif outperformance > 10:
        logger.info(f"   ✅ 显著跑赢市场（{outperformance:+.2f}%）⭐⭐⭐⭐")
    elif outperformance > 0:
        logger.info(f"   ✅ 跑赢市场（{outperformance:+.2f}%）⭐⭐⭐")
    else:
        logger.info(f"   ⚠️  跑输市场（{abs(outperformance):.2f}%）")
    
    # 读取爆仓记录
    logger.info("\n📋 步骤8: 分析爆仓案例")
    if hasattr(backtest, 'liquidation_records') and backtest.liquidation_records:
        logger.info(f"\n💀 发现{len(backtest.liquidation_records)}个爆仓案例:")
        for i, record in enumerate(backtest.liquidation_records[:5], 1):  # 只显示前5个
            logger.info(f"\n   爆仓#{i}:")
            logger.info(f"     Agent: {record['agent_id']}")
            logger.info(f"     时刻: 第{record['step']}天")
            logger.info(f"     价格: ${record['price']:,.2f}")
            logger.info(f"     杠杆: {record['leverage']:.1f}x")
            logger.info(f"     方向: {'做空' if record['position'] < 0 else '做多'}")
            logger.info(f"     亏损: {record['leveraged_return']:.1f}%")
        
        if len(backtest.liquidation_records) > 5:
            logger.info(f"\n   （还有{len(backtest.liquidation_records)-5}个爆仓案例未显示）")
    else:
        logger.info("   ✅ 没有爆仓记录（所有Agent都存活！）")
    
    logger.info("\n" + "="*80)
    logger.info("✅ v5.3 365天长期回测完成！")
    logger.info("="*80)
    
    # 最终评价
    logger.info("\n🎯 最终评价:")
    
    # 综合评分
    score = 0
    if agent_return > 30:
        score += 30
    elif agent_return > 10:
        score += 20
    elif agent_return > 0:
        score += 10
    
    if outperformance > 10:
        score += 25
    elif outperformance > 0:
        score += 15
    
    if max_drawdown < 0.2:
        score += 20
    elif max_drawdown < 0.4:
        score += 10
    
    if liquidation_rate < 10:
        score += 25
    elif liquidation_rate < 30:
        score += 15
    
    logger.info(f"   综合评分: {score}/100")
    
    if score >= 80:
        logger.info("   评级: S级（顶级量化系统）⭐⭐⭐⭐⭐")
    elif score >= 60:
        logger.info("   评级: A级（优秀量化系统）⭐⭐⭐⭐")
    elif score >= 40:
        logger.info("   评级: B级（良好量化系统）⭐⭐⭐")
    else:
        logger.info("   评级: C级（需要改进）")
    
    logger.info("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

