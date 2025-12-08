"""
Prometheus v6.0 标准测试模板

⚠️ 警告：这是v6.0的标准测试模板
⚠️ 所有测试必须基于此模板
⚠️ 不能自创简化版
⚠️ 违反将导致测试失败

三大铁律：
  1. 使用Facade统一入口（build_facade/run_scenario）
  2. 基于此模板
  3. 完整机制，不简化

使用方法：
  1. 复制此文件，重命名为test_<your_feature>.py
  2. 填写测试目标和参数
  3. 运行测试
  4. 验证对账通过率=100%

Version: 6.0.0
Date: 2025-12-08
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import logging
import time
from datetime import datetime
from prometheus.v6 import build_facade, run_scenario
from prometheus.v6.config import SystemCapitalConfig

# ========== 配置日志 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    标准测试流程
    
    遵守三大铁律：
      1. 使用Facade统一入口
      2. 基于标准模板
      3. 完整机制，自动对账
    """
    
    print("=" * 80)
    print("🚀 Prometheus v6.0 标准测试")
    print("=" * 80)
    print()
    
    # ========== 1. 数据准备 ==========
    logger.info("📊 加载市场数据...")
    try:
        btc_data = pd.read_csv('data/btc_usdt_1h.csv')
        logger.info(f"✅ 数据加载成功: {len(btc_data)}条K线")
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return
    
    # ========== 2. 配置系统 ==========
    logger.info("⚙️ 配置系统参数...")
    config = SystemCapitalConfig(
        total_capital=1000000,          # 系统总资金
        agent_count=50,                 # Agent数量
        capital_per_agent=2000,         # 每个Agent初始资金
        genesis_allocation_ratio=0.20   # 创世配资比例（20%）
    )
    
    # ========== 3. 构建Facade（铁律1：统一入口）==========
    logger.info("🏗️ 构建Facade...")
    try:
        facade = build_facade(
            market_data=btc_data,
            config=config,
            scenario='backtest',        # 场景：'backtest', 'mock', 'live_demo'
            seed=7001,                  # 随机种子（可重复性）
            use_intelligent_genesis=True,  # 使用智能创世
            experience_db_path="data/experience_db.json"  # 经验数据库路径
        )
        logger.info("✅ Facade构建成功")
    except Exception as e:
        logger.error(f"❌ Facade构建失败: {e}")
        return
    
    # ========== 4. 运行场景（铁律1：统一入口）==========
    logger.info("🎯 开始运行场景...")
    start_time = time.time()
    
    try:
        results = run_scenario(
            facade=facade,
            max_cycles=500,              # 最大周期数
            breeding_tax_rate=None,      # 动态税率（None=自动计算）
            evolution_interval=50        # 进化间隔（每50周期进化一次）
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ 场景运行完成，耗时: {elapsed_time:.2f}秒")
    except Exception as e:
        logger.error(f"❌ 场景运行失败: {e}")
        return
    
    # ========== 5. 验证结果（铁律3：对账验证）==========
    print()
    print("=" * 80)
    print("📊 测试结果")
    print("=" * 80)
    print()
    
    # 系统级指标
    print("系统级指标:")
    print(f"  系统ROI:          {results['system_roi']:.2%}")
    print(f"  系统Sharpe:       {results.get('system_sharpe', 0.0):.2f}")
    print(f"  最大回撤:         {results.get('max_drawdown', 0.0):.2%}")
    print()
    
    # Agent级指标
    print("Agent级指标:")
    print(f"  Agent平均ROI:    {results['agent_avg_roi']:.2%}")
    print(f"  Agent总资金:      ${results.get('agent_total_capital', 0):,.2f}")
    print(f"  存活Agent数量:    {results.get('alive_agent_count', 0)}")
    print()
    
    # 账簿对账（铁律3：强制验证）
    print("账簿对账:")
    print(f"  对账通过率:       {results['reconciliation_pass_rate']:.2%}")
    print(f"  对账检查次数:     {results.get('reconciliation_checks', 0)}")
    print()
    
    # 资金池
    print("资金池:")
    print(f"  资金池余额:       ${results.get('capital_pool_balance', 0):,.2f}")
    print(f"  资金利用率:       {results.get('capital_utilization', 0.0):.2%}")
    print()
    
    # ========== 6. 断言验证（铁律3：强制检查）==========
    print("=" * 80)
    print("🔍 断言验证")
    print("=" * 80)
    print()
    
    # 断言1: 对账通过率必须100%（铁律3）
    try:
        assert results['reconciliation_pass_rate'] == 1.0, \
            f"❌ 对账失败！通过率: {results['reconciliation_pass_rate']:.2%}"
        print("✅ 断言1通过: 对账通过率100%")
    except AssertionError as e:
        logger.error(str(e))
        print(str(e))
        return
    
    # 断言2: 系统ROI合理（不应该是-100%或异常值）
    try:
        assert results['system_roi'] > -1.0, \
            f"❌ 系统ROI异常: {results['system_roi']:.2%}"
        print(f"✅ 断言2通过: 系统ROI合理 ({results['system_roi']:.2%})")
    except AssertionError as e:
        logger.error(str(e))
        print(str(e))
        return
    
    # 断言3: Agent总资金不为0（不应该全死光）
    try:
        agent_total = results.get('agent_total_capital', 0)
        assert agent_total > 0, \
            f"❌ Agent总资金为0！可能全部死亡或资金池错误"
        print(f"✅ 断言3通过: Agent总资金正常 (${agent_total:,.2f})")
    except AssertionError as e:
        logger.error(str(e))
        print(str(e))
        return
    
    # 断言4: 至少有一些Agent存活
    try:
        alive_count = results.get('alive_agent_count', 0)
        assert alive_count > 0, \
            f"❌ 没有Agent存活！"
        print(f"✅ 断言4通过: 有{alive_count}个Agent存活")
    except AssertionError as e:
        logger.error(str(e))
        print(str(e))
        return
    
    # ========== 7. 保存结果 ==========
    output_dir = f"test_results/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存结果到JSON
    import json
    with open(f"{output_dir}/results.json", 'w') as f:
        json.dump(results, f, indent=4)
    logger.info(f"💾 结果已保存到: {output_dir}/results.json")
    
    # ========== 8. 最终总结 ==========
    print()
    print("=" * 80)
    print("✅ 所有检查通过！")
    print("=" * 80)
    print()
    print("三大铁律验证:")
    print("  ✅ 铁律1: 使用Facade统一入口")
    print("  ✅ 铁律2: 基于标准测试模板")
    print("  ✅ 铁律3: 对账验证100%通过")
    print()
    print(f"测试用时: {elapsed_time:.2f}秒")
    print(f"结果保存: {output_dir}/")
    print()


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('test_results', exist_ok=True)
    
    # 运行测试
    main()

