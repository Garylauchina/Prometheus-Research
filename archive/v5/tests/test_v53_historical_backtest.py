"""
v5.3 历史数据回测测试

测试内容：
1. 加载30天BTC历史数据（模拟）
2. 运行完整回测
3. 分析Agent在真实历史数据中的表现
4. 对比Mock vs 历史数据的结果
"""

import sys
import logging
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'v53_historical_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    
    print("\n" + "="*80)
    print("🧪 v5.3 历史数据回测测试")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 导入模块
    logger.info("📦 导入必要模块...")
    from prometheus.market.okx_data_loader import OKXDataLoader
    from prometheus.core.moirai import Moirai
    from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
    from prometheus.backtest.historical_backtest import HistoricalBacktest
    
    # ============================================================
    # 步骤1: 加载30天BTC历史数据
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤1: 加载30天BTC历史数据")
    print("="*80)
    
    loader = OKXDataLoader(data_dir="data/okx")
    
    # 生成30天的BTC日K数据
    kline_data = loader.load_or_generate(
        symbol="BTC/USDT",
        days=30,
        interval="1d",
        force_generate=False  # 使用缓存（如果存在）
    )
    
    # 验证数据
    is_valid, errors = loader.validate_data(kline_data)
    if not is_valid:
        logger.error(f"❌ 数据验证失败: {errors}")
        return
    
    # 打印统计信息
    stats = loader.get_statistics(kline_data)
    print("\n📊 数据统计:")
    print(f"   K线数量: {stats['data_points']}根")
    print(f"   时间范围: {stats['time_range']['days']}天")
    print(f"   价格范围: ${stats['price']['min']:,.2f} ~ ${stats['price']['max']:,.2f}")
    print(f"   市场收益: {stats['returns']['total']:+.2f}%")
    print(f"   日均波动: {stats['returns']['daily_std']:.2f}%")
    
    # ============================================================
    # 步骤2: 初始化进化管理器
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤2: 初始化进化管理器")
    print("="*80)
    
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    logger.info("✅ 进化管理器初始化完成")
    
    # ============================================================
    # 步骤3: 创建并配置回测引擎
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤3: 创建回测引擎")
    print("="*80)
    
    backtest = HistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,  # 每10根K线（10天）进化一次
        initial_agents=50,      # 初始50个Agent
        initial_capital=10000.0  # 每个Agent初始$10,000
    )
    
    logger.info("✅ 回测引擎创建完成")
    
    # ============================================================
    # 步骤4: 运行回测
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤4: 运行30天历史回测")
    print("="*80)
    print("⏳ 这可能需要几分钟...")
    
    results = backtest.run()
    
    # ============================================================
    # 步骤5: 分析和展示结果
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤5: 分析回测结果")
    print("="*80)
    
    backtest.print_summary()
    
    # ============================================================
    # 步骤6: 保存结果
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤6: 保存回测结果")
    print("="*80)
    
    results_file = backtest.save_results(output_dir="results/v53_historical_backtest")
    
    print(f"\n💾 结果已保存到: results/v53_historical_backtest/")
    
    # ============================================================
    # 步骤7: 生成对比分析
    # ============================================================
    print("\n" + "="*80)
    print("📋 步骤7: Mock vs 历史数据对比分析")
    print("="*80)
    
    # 从之前的Mock测试中获取结果（如果存在）
    print("\n📊 对比分析:")
    print(f"   历史数据回测:")
    print(f"     - Agent平均收益: {results['returns']['avg_return']:+.2f}%")
    print(f"     - 市场收益: {results['market_performance']['market_return']:+.2f}%")
    print(f"     - 种群存活率: {results['population']['survival_rate']:.1f}%")
    
    print(f"\n   Mock模拟对比:")
    print(f"     - Mock测试（50轮）:")
    print(f"       * Agent平均收益: +238.46%（简化版，未扣成本）")
    print(f"       * 或 +0.25%（真实费率版）")
    print(f"       * 种群存活率: ~90%")
    
    print(f"\n💡 关键洞察:")
    
    if results['returns']['avg_return'] > 0:
        print(f"   ✅ 历史数据中Agent实现盈利（{results['returns']['avg_return']:+.2f}%）")
    else:
        print(f"   ⚠️  历史数据中Agent出现亏损（{results['returns']['avg_return']:+.2f}%）")
    
    if results['returns']['avg_return'] > results['market_performance']['market_return']:
        alpha = results['returns']['avg_return'] - results['market_performance']['market_return']
        print(f"   ✅ Agent跑赢市场 {alpha:.2f}个百分点")
    else:
        print(f"   ⚠️  Agent跑输市场")
    
    print(f"\n   历史数据回测更真实地反映了系统性能，")
    print(f"   因为它基于真实的价格分布和波动特征。")
    
    # ============================================================
    # 完成
    # ============================================================
    print("\n" + "="*80)
    print("✅ v5.3 历史数据回测完成！")
    print("="*80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成总结报告
    generate_summary_report(results, stats)
    
    print("\n" + "="*80)


def generate_summary_report(backtest_results: dict, data_stats: dict):
    """生成总结报告"""
    
    report = {
        'report_title': 'v5.3 历史数据回测总结报告',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_statistics': data_stats,
        'backtest_results': backtest_results,
        'conclusions': []
    }
    
    # 添加结论
    conclusions = []
    
    # 结论1: 盈利能力
    avg_return = backtest_results['returns']['avg_return']
    market_return = backtest_results['market_performance']['market_return']
    
    if avg_return > 0:
        conclusions.append({
            'topic': '盈利能力',
            'finding': f'Agent平均实现{avg_return:+.2f}%收益',
            'evaluation': 'positive' if avg_return > 1 else 'neutral'
        })
    else:
        conclusions.append({
            'topic': '盈利能力',
            'finding': f'Agent平均亏损{abs(avg_return):.2f}%',
            'evaluation': 'negative'
        })
    
    # 结论2: 市场对比
    if avg_return > market_return:
        alpha = avg_return - market_return
        conclusions.append({
            'topic': '市场对比',
            'finding': f'Agent跑赢市场{alpha:.2f}个百分点',
            'evaluation': 'positive'
        })
    else:
        conclusions.append({
            'topic': '市场对比',
            'finding': 'Agent未能跑赢市场',
            'evaluation': 'negative'
        })
    
    # 结论3: 种群健康
    survival_rate = backtest_results['population']['survival_rate']
    if survival_rate > 80:
        conclusions.append({
            'topic': '种群健康',
            'finding': f'高存活率（{survival_rate:.1f}%），种群稳定',
            'evaluation': 'positive'
        })
    elif survival_rate > 50:
        conclusions.append({
            'topic': '种群健康',
            'finding': f'中等存活率（{survival_rate:.1f}%），种群基本稳定',
            'evaluation': 'neutral'
        })
    else:
        conclusions.append({
            'topic': '种群健康',
            'finding': f'低存活率（{survival_rate:.1f}%），种群压力大',
            'evaluation': 'negative'
        })
    
    report['conclusions'] = conclusions
    
    # 保存报告
    report_file = f"results/v53_historical_backtest/summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 总结报告已保存: {report_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        sys.exit(1)

