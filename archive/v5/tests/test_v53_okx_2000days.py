#!/usr/bin/env python3
"""
Prometheus v5.3 - OKX真实数据回测（2000天）
==================================================

历史性时刻：
- 第一次使用真实OKX数据
- 第一次在Python 3.12环境下运行
- 5.5年完整牛熊周期测试
- 验证Agent在真实市场的表现
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import logging
from datetime import datetime
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


def main():
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚀 Prometheus v5.3 - OKX真实数据回测（5.5年）")
    logger.info("=" * 80)
    logger.info("")
    
    # ========================================
    # 1. 加载真实OKX数据
    # ========================================
    logger.info("📥 Step 1: 加载真实OKX历史数据")
    logger.info("-" * 80)
    
    data_file = 'data/okx/BTC_USDT_1d_20251206.csv'
    df = pd.read_csv(data_file)
    
    logger.info(f"✅ 数据加载成功")
    logger.info(f"   数据文件: {data_file}")
    logger.info(f"   数据条数: {len(df):,}条")
    logger.info(f"   时间范围: {df.iloc[0]['timestamp']} → {df.iloc[-1]['timestamp']}")
    logger.info(f"   起始价格: ${df.iloc[0]['close']:,.2f}")
    logger.info(f"   最终价格: ${df.iloc[-1]['close']:,.2f}")
    logger.info(f"   市场表现: {(df.iloc[-1]['close']/df.iloc[0]['close']-1)*100:+.2f}%")
    logger.info("")
    
    # 转换为回测所需格式
    klines = []
    for _, row in df.iterrows():
        klines.append({
            'timestamp': row['timestamp'],
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume'])
        })
    
    logger.info(f"✅ 数据转换完成: {len(klines)}条K线")
    logger.info("")
    
    # ========================================
    # 2. 初始化Prometheus系统
    # ========================================
    logger.info("🧬 Step 2: 初始化Prometheus系统")
    logger.info("-" * 80)
    
    moirai = Moirai()
    logger.info("✅ Moirai初始化完成")
    
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    logger.info("✅ EvolutionManagerV5初始化完成")
    logger.info(f"   种群规模: {len(moirai.agents)}个Agent")
    logger.info(f"   基础变异率: {evolution_manager.base_mutation_rate}")
    logger.info(f"   移民机制: {'开启' if evolution_manager.immigration_enabled else '关闭'}")
    logger.info("")
    
    # ========================================
    # 3. 创建回测引擎
    # ========================================
    logger.info("⚙️  Step 3: 创建历史回测引擎")
    logger.info("-" * 80)
    
    # 转换klines为DataFrame并转换timestamp为datetime
    df_klines = pd.DataFrame(klines)
    df_klines['timestamp'] = pd.to_datetime(df_klines['timestamp'])
    
    backtest_engine = HistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=df_klines,
        evolution_interval=30,  # 每30天（1个月）进化一次
        initial_agents=50,
        initial_capital=10000.0
    )
    
    logger.info("✅ 回测引擎创建完成")
    logger.info(f"   初始Agent数量: {backtest_engine.initial_agents}")
    logger.info(f"   初始资金: ${backtest_engine.initial_capital:,.2f}")
    logger.info(f"   进化周期: {backtest_engine.evolution_interval}天")
    logger.info(f"   杠杆功能: 启用（1-100x）")
    logger.info(f"   做空功能: 启用")
    logger.info(f"   交易费率: 0.10% (OKX Taker)")
    logger.info(f"   滑点: 0.01%")
    logger.info(f"   资金费率: 0.03%/天")
    logger.info("")
    
    # ========================================
    # 4. 运行回测
    # ========================================
    logger.info("🚀 Step 4: 开始历史回测")
    logger.info("-" * 80)
    logger.info(f"⏱️  预计用时: 约3-5分钟")
    logger.info(f"📊 回测周期: {len(klines)}天 ≈ {len(klines)/365:.1f}年")
    logger.info(f"🔄 进化次数: {len(klines) // backtest_engine.evolution_interval}次")
    logger.info("")
    
    start_time = datetime.now()
    
    results = backtest_engine.run()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("")
    logger.info("✅ 回测完成！")
    logger.info(f"   用时: {duration:.2f}秒 ({duration/60:.2f}分钟)")
    logger.info("")
    
    # ========================================
    # 5. 分析结果
    # ========================================
    logger.info("=" * 80)
    logger.info("📊 回测结果分析")
    logger.info("=" * 80)
    logger.info("")
    
    backtest_engine.print_summary()
    
    # ========================================
    # 6. 保存结果
    # ========================================
    logger.info("")
    logger.info("💾 Step 6: 保存回测结果")
    logger.info("-" * 80)
    
    results_with_data = backtest_engine.generate_results()
    
    # 保存JSON
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_okx_2000days_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_with_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ 结果已保存: {results_file}")
    logger.info("")
    
    # ========================================
    # 7. 关键发现总结
    # ========================================
    logger.info("=" * 80)
    logger.info("🌟 关键发现")
    logger.info("=" * 80)
    logger.info("")
    
    perf = results['performance']
    
    logger.info(f"📈 收益表现:")
    logger.info(f"   总收益率: {perf['total_return_pct']:+.2f}%")
    logger.info(f"   年化收益率: {perf['annualized_return_pct']:+.2f}%")
    logger.info(f"   最大回撤: {perf['max_drawdown_pct']:.2f}%")
    logger.info("")
    
    logger.info(f"📊 Agent种群:")
    logger.info(f"   初始数量: {perf['initial_population']}个")
    logger.info(f"   最终数量: {perf['final_population']}个")
    logger.info(f"   存活率: {perf['survival_rate']*100:.1f}%")
    logger.info("")
    
    logger.info(f"💰 资金表现:")
    logger.info(f"   初始资金: ${perf['initial_avg_capital']:,.2f}")
    logger.info(f"   最终资金: ${perf['final_avg_capital']:,.2f}")
    logger.info(f"   收益: ${perf['final_avg_capital'] - perf['initial_avg_capital']:+,.2f}")
    logger.info("")
    
    if 'liquidation_count' in perf:
        logger.info(f"⚠️  爆仓统计:")
        logger.info(f"   爆仓次数: {perf['liquidation_count']}次")
        logger.info(f"   爆仓率: {perf['liquidation_rate']*100:.2f}%")
        logger.info("")
    
    # ========================================
    # 8. 与市场对比
    # ========================================
    logger.info("=" * 80)
    logger.info("📊 与市场表现对比")
    logger.info("=" * 80)
    logger.info("")
    
    market_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    agent_return = perf['annualized_return_pct']
    
    logger.info(f"🏦 市场（BTC/USDT）:")
    logger.info(f"   起始价格: ${df.iloc[0]['close']:,.2f}")
    logger.info(f"   最终价格: ${df.iloc[-1]['close']:,.2f}")
    logger.info(f"   总收益率: {market_return:+.2f}%")
    logger.info(f"   年化收益率: {market_return / (len(klines)/365):+.2f}%")
    logger.info("")
    
    logger.info(f"🤖 Agent种群:")
    logger.info(f"   年化收益率: {agent_return:+.2f}%")
    logger.info("")
    
    if agent_return > market_return / (len(klines)/365):
        logger.info(f"🎉 Agent表现 > 市场表现！超额收益: {agent_return - market_return / (len(klines)/365):+.2f}%")
    else:
        logger.info(f"📉 Agent表现 < 市场表现，差距: {agent_return - market_return / (len(klines)/365):+.2f}%")
    
    logger.info("")
    
    # ========================================
    # 9. 完成
    # ========================================
    logger.info("=" * 80)
    logger.info("✅ 历史性回测完成！")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🎯 这是Prometheus的历史性时刻:")
    logger.info("   ✅ 第一次使用真实OKX数据")
    logger.info("   ✅ 第一次在Python 3.12环境运行")
    logger.info("   ✅ 5.5年完整牛熊周期验证")
    logger.info("   ✅ 覆盖$9K → $126K → $89K的完整市场")
    logger.info("")
    logger.info(f"📄 详细结果: {results_file}")
    logger.info("")
    logger.info("🚀 下一步: v5.3完整收尾 → v5.5智能训练学校")
    logger.info("")


if __name__ == "__main__":
    main()

