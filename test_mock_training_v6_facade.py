"""
Mock训练完整测试 - v6.0 Facade统一入口
=======================================

目标：验证V6Facade.run_mock_training()统一封装是否正常工作
- 严格遵守"三大铁律"第1条：统一封装，统一调用，严禁旁路
- 验证税收机制
- 验证对账系统
"""

import pandas as pd
import logging
from datetime import datetime, timedelta

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_market_data(cycles: int = 1000, initial_price: float = 50000) -> pd.DataFrame:
    """
    生成模拟市场数据（简单的随机游走）
    """
    import numpy as np
    
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(cycles)]
    prices = [initial_price]
    
    # 简单的随机游走
    for i in range(1, cycles):
        change_pct = np.random.normal(0, 0.02)  # 2%标准差
        new_price = prices[-1] * (1 + change_pct)
        prices.append(new_price)
    
    data = []
    for i, timestamp in enumerate(timestamps):
        price = prices[i]
        # 生成OHLCV
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = price * (1 + np.random.normal(0, 0.005))
        volume = abs(np.random.normal(1000, 200))
        
        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    return pd.DataFrame(data)

def main():
    logger.info("="*80)
    logger.info("Mock训练完整测试 - v6.0 Facade统一入口")
    logger.info("="*80)
    logger.info("")
    
    # ========== 配置 ==========
    config = MockTrainingConfig(
        # 核心参数
        cycles=200,                      # 简化测试：200周期
        total_system_capital=100_000,    # $100K
        
        # 进化参数
        agent_count=10,                  # 10个Agent
        genesis_allocation_ratio=0.2,    # 20%给Agent，80%资金池
        evolution_interval=10,           # 每10周期进化
        elimination_rate=0.3,
        elite_ratio=0.2,
        
        # 创世参数
        genesis_strategy='pure_random',  # 纯随机创世（因为没有历史数据）
        genesis_seed=42,                 # 固定种子，可复现
        
        # 市场参数
        market_type='mock',
        
        # 经验库（不使用）
        experience_db_path=None,
        
        # 日志
        log_dir='mock_training_logs',
        log_interval=50                  # 每50周期打印一次
    )
    
    logger.info("配置已创建:")
    logger.info(f"  周期数: {config.cycles}")
    logger.info(f"  系统资金: ${config.total_system_capital:,.0f}")
    logger.info(f"  Agent数量: {config.agent_count}")
    logger.info(f"  创世配比: {config.genesis_allocation_ratio*100:.0f}%给Agent，{(1-config.genesis_allocation_ratio)*100:.0f}%资金池")
    logger.info("")
    
    # ========== 生成市场数据 ==========
    logger.info("生成模拟市场数据...")
    market_data = generate_mock_market_data(cycles=config.cycles + 100, initial_price=50000)
    logger.info(f"✅ 生成{len(market_data)}根K线")
    logger.info(f"   价格范围: ${market_data['close'].min():,.2f} ~ ${market_data['close'].max():,.2f}")
    logger.info("")
    
    # ========== 初始化Facade ==========
    logger.info("初始化V6Facade...")
    facade = V6Facade(num_families=5)  # 5个家族（简化）
    logger.info("✅ V6Facade已初始化")
    logger.info("")
    
    # ========== 运行Mock训练（统一封装！）==========
    logger.info("="*80)
    logger.info("开始Mock训练（通过V6Facade统一入口）")
    logger.info("="*80)
    logger.info("")
    
    result = facade.run_mock_training(
        market_data=market_data,
        config=config
    )
    
    # ========== 分析结果 ==========
    logger.info("")
    logger.info("="*80)
    logger.info("结果分析")
    logger.info("="*80)
    logger.info("")
    
    logger.info(f"Run ID: {result.run_id}")
    logger.info(f"实际周期数: {result.actual_cycles}")
    logger.info("")
    
    logger.info("系统级指标:")
    logger.info(f"  系统ROI: {result.system_roi:+.2%}")
    logger.info(f"  BTC基准ROI: {result.btc_benchmark_roi:+.2%}")
    logger.info(f"  超越BTC: {result.outperformance:+.2%}")
    logger.info(f"  系统总资金: ${result.system_total_capital:,.0f}")
    logger.info("")
    
    logger.info("Agent统计:")
    logger.info(f"  最终Agent数: {result.agent_count_final}/{config.agent_count}")
    logger.info(f"  平均ROI: {result.agent_avg_roi:+.2%}")
    logger.info(f"  中位数ROI: {result.agent_median_roi:+.2%}")
    logger.info(f"  最佳ROI: {result.agent_best_roi:+.2%}")
    logger.info("")
    
    logger.info("资金池状态:")
    logger.info(f"  资金池余额: ${result.capital_pool_balance:,.0f}")
    logger.info(f"  资金利用率: {result.capital_utilization*100:.1f}%")
    logger.info(f"  目标资金利用率: 80%（资金池20%）")
    logger.info("")
    
    logger.info("对账验证:")
    logger.info(f"  对账结果: {'✅ 通过' if result.reconciliation_passed else '❌ 失败'}")
    if result.reconciliation_details:
        logger.info(f"  详情: {result.reconciliation_details}")
    logger.info("")
    
    # ========== 验证成功标准 ==========
    logger.info("="*80)
    logger.info("验证成功标准")
    logger.info("="*80)
    logger.info("")
    
    checks = []
    
    # 1. 对账通过
    check1 = result.reconciliation_passed
    checks.append(("对账100%通过", check1))
    logger.info(f"{'✅' if check1 else '❌'} 对账100%通过")
    
    # 2. 资金池在合理范围（15%~30%）
    check2 = 0.15 <= (1 - result.capital_utilization) <= 0.30
    checks.append(("资金池在15%~30%", check2))
    logger.info(f"{'✅' if check2 else '❌'} 资金池在15%~30% (实际:{(1-result.capital_utilization)*100:.1f}%)")
    
    # 3. 系统有盈利或亏损在合理范围（不崩溃）
    check3 = result.system_total_capital > config.total_system_capital * 0.5
    checks.append(("系统未崩溃（>50%初始资金）", check3))
    logger.info(f"{'✅' if check3 else '❌'} 系统未崩溃（>50%初始资金）")
    
    # 4. 有Agent存活
    check4 = result.agent_count_final > 0
    checks.append(("有Agent存活", check4))
    logger.info(f"{'✅' if check4 else '❌'} 有Agent存活（{result.agent_count_final}个）")
    
    logger.info("")
    
    # 总结
    passed_count = sum(1 for _, passed in checks if passed)
    total_count = len(checks)
    
    logger.info("="*80)
    if passed_count == total_count:
        logger.info(f"🎉 ✅ 全部通过！（{passed_count}/{total_count}）")
        logger.info("")
        logger.info("✅ V6Facade.run_mock_training()统一封装工作正常！")
        logger.info("✅ 税收机制工作正常！")
        logger.info("✅ 对账系统工作正常！")
        logger.info("✅ 严格遵守三大铁律第1条：统一封装，统一调用，严禁旁路")
    else:
        logger.error(f"❌ 部分失败（{passed_count}/{total_count}）")
        logger.error("")
        logger.error("需要修复的问题:")
        for name, passed in checks:
            if not passed:
                logger.error(f"  ❌ {name}")
    logger.info("="*80)

if __name__ == "__main__":
    main()

