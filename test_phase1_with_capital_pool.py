#!/usr/bin/env python3
"""
Phase 1: 长期训练测试（资金池版本）
====================================

✅ 遵守三大铁律：
1. 统一封装：使用v6 Facade统一入口
2. 严格执行测试规范：基于标准模板
3. 不简化底层机制：完整系统逻辑链

✅ v6.0资金池验证：
1. 系统注资到资金池
2. 创世从资金池分配
3. 淘汰回收到资金池
4. 繁殖从资金池分配
5. Agent死亡前强制平仓
6. 系统级对账(资金守恒)

目标：
- 验证资金池机制正确性
- 验证资金守恒
- 对比修复前后的结果
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import numpy as np

# 设置日志
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"results/phase1_capital_pool_{timestamp}.log"
Path("results").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# ✅ 统一封装：只使用v6 Facade
from prometheus.facade.v6_facade import run_scenario


def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("🚀 Phase 1: 长期训练测试（资金池版本）")
    logger.info("=" * 80)
    logger.info("")
    logger.info("测试目标：")
    logger.info("  1. 验证资金池机制")
    logger.info("  2. 验证资金守恒")
    logger.info("  3. 对比修复前后差异")
    logger.info("")
    logger.info("测试配置：")
    logger.info("  数据: BTC/USDT 1D (2020-2024)")
    logger.info("  Agent: 50")
    logger.info("  周期: 500")
    logger.info("  初始资金: $10,000/Agent")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # 加载历史数据
    try:
        data_file = "data/okx/BTC_USDT_1d_20251206.csv"
        df = pd.read_csv(data_file)
        logger.info(f"✅ 数据加载成功: {len(df)}条记录")
        logger.info(f"   时间范围: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")
        logger.info(f"   价格范围: ${df['close'].min():.2f} → ${df['close'].max():.2f}")
        logger.info("")
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return
    
    # 创建market_feed
    prices = df['close'].values
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    # 测试配置
    test_config = {
        "mode": "backtest",
        "total_cycles": 500,
        "market_feed": make_market_feed(),
        
        # 种群配置
        "num_families": 50,
        "agent_count": 50,
        "capital_per_agent": 10000.0,
        
        # 进化配置
        "evo_interval": 10,
        
        # 种子配置
        "seed": 8004,  # 使用Phase 1最佳种子
        "evolution_seed": None,  # 演化随机
        
        # AlphaZero式配置
        "full_genome_unlock": True
    }
    
    logger.info("🧪 开始运行测试...")
    logger.info("")
    
    # ✅ 运行scenario
    start_time = datetime.now()
    
    try:
        facade = run_scenario(**test_config)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 测试运行完成")
        logger.info(f"   耗时: {duration:.2f}秒")
        logger.info("=" * 80)
        logger.info("")
        
        # ========== 提取结果 ==========
        current_price = prices[-1]
        start_price = prices[0]
        
        # Agent统计
        moirai = facade.moirai
        agent_count = len(moirai.agents)
        
        # 系统资金统计（包含未实现盈亏）
        system_initial = test_config["agent_count"] * test_config["capital_per_agent"]
        system_current = sum(
            a.account.private_ledger.virtual_capital + a.calculate_unrealized_pnl(current_price)
            for a in moirai.agents if hasattr(a, 'account') and a.account
        )
        system_return = (system_current - system_initial) / system_initial * 100
        
        # 交易统计
        total_trades = sum(
            a.account.private_ledger.trade_count
            for a in moirai.agents if hasattr(a, 'account') and a.account
        )
        
        # Agent ROI统计
        returns = []
        for agent in moirai.agents:
            if hasattr(agent, 'account') and agent.account:
                initial = agent.account.private_ledger.initial_capital
                current = agent.account.private_ledger.virtual_capital + agent.calculate_unrealized_pnl(current_price)
                roi = (current - initial) / initial * 100
                returns.append(roi)
        
        best_agent_return = np.max(returns) if returns else 0
        worst_agent_return = np.min(returns) if returns else 0
        avg_agent_return = np.mean(returns) if returns else 0
        
        # BTC基准
        btc_return = (current_price - start_price) / start_price * 100
        
        # ========== ✅ 完整对账（Agent级 + 系统级）==========
        logger.info("=" * 80)
        logger.info("🔍 执行完整对账...")
        logger.info("=" * 80)
        logger.info("")
        
        reconcile_result = facade.reconcile(current_price=current_price)
        
        logger.info("")
        
        # ========== ✅ 资金统计报告 ==========
        logger.info("=" * 80)
        logger.info("💰 资金统计报告")
        logger.info("=" * 80)
        logger.info("")
        
        capital_report = facade.get_capital_report(current_price=current_price)
        
        logger.info("📊 系统级统计:")
        logger.info(f"   总注资: ${capital_report['system']['total_invested']:,.2f}")
        logger.info(f"   Agent资金: ${capital_report['system']['total_agent_capital']:,.2f}")
        logger.info(f"   资金池余额: ${capital_report['system']['pool_balance']:,.2f}")
        logger.info(f"   系统总资金: ${capital_report['system']['system_total']:,.2f}")
        logger.info(f"   系统ROI: {capital_report['system']['roi_pct']:+.2f}%")
        logger.info("")
        
        logger.info("👥 Agent级统计:")
        logger.info(f"   Agent数量: {capital_report['agents']['total_count']}")
        logger.info(f"   初始资金总和: ${capital_report['agents']['total_initial']:,.2f}")
        logger.info(f"   已实现资金: ${capital_report['agents']['total_realized']:,.2f}")
        logger.info(f"   未实现盈亏: ${capital_report['agents']['total_unrealized_pnl']:+,.2f}")
        logger.info(f"   平均ROI: {capital_report['agents']['avg_roi_pct']:+.2f}%")
        logger.info("")
        
        logger.info("💰 资金池统计:")
        logger.info(f"   总注资: ${capital_report['pool']['total_invested']:,.2f}")
        logger.info(f"   可用余额: ${capital_report['pool']['available']:,.2f}")
        logger.info(f"   累计分配: ${capital_report['pool']['allocated']:,.2f}")
        logger.info(f"   累计回收: ${capital_report['pool']['reclaimed']:,.2f}")
        logger.info(f"   净流出: ${capital_report['pool']['net_flow']:,.2f}")
        logger.info("")
        
        logger.info("=" * 80)
        logger.info("")
        
        # ========== 测试结果总结 ==========
        logger.info("=" * 80)
        logger.info("📊 Phase 1 测试结果")
        logger.info("=" * 80)
        logger.info("")
        
        logger.info("🎯 性能指标:")
        logger.info(f"   系统ROI: {system_return:+.2f}%")
        logger.info(f"   BTC基准: {btc_return:+.2f}%")
        logger.info(f"   Alpha: {system_return - btc_return:+.2f}%")
        logger.info("")
        
        logger.info("📈 交易统计:")
        logger.info(f"   总交易数: {total_trades}笔")
        logger.info(f"   平均交易: {total_trades/agent_count:.1f}笔/Agent")
        logger.info("")
        
        logger.info("🏆 Agent表现:")
        logger.info(f"   最佳: {best_agent_return:+.2f}%")
        logger.info(f"   平均: {avg_agent_return:+.2f}%")
        logger.info(f"   最差: {worst_agent_return:+.2f}%")
        logger.info("")
        
        logger.info("✅ 对账验证:")
        logger.info(f"   Agent级: {'✅ 通过' if reconcile_result['agent_reconcile']['all_passed'] else '❌ 未通过'}")
        logger.info(f"   系统级: {'✅ 通过' if reconcile_result['system_reconcile']['passed'] else '❌ 未通过'}")
        logger.info(f"   综合: {'🎉 全部通过' if reconcile_result['all_passed'] else '❌ 存在问题'}")
        logger.info("")
        
        logger.info("=" * 80)
        logger.info("")
        
        # ========== 保存结果 ==========
        result = {
            "timestamp": timestamp,
            "test_type": "phase1_with_capital_pool",
            "config": {
                "agent_count": test_config["agent_count"],
                "cycles": test_config["total_cycles"],
                "seed": test_config["seed"],
                "capital_per_agent": test_config["capital_per_agent"]
            },
            "performance": {
                "system_return_pct": round(system_return, 2),
                "btc_return_pct": round(btc_return, 2),
                "alpha_pct": round(system_return - btc_return, 2),
                "total_trades": total_trades,
                "avg_trades_per_agent": round(total_trades / agent_count, 1),
                "best_agent_return_pct": round(best_agent_return, 2),
                "avg_agent_return_pct": round(avg_agent_return, 2),
                "worst_agent_return_pct": round(worst_agent_return, 2)
            },
            "reconcile": {
                "agent_passed": reconcile_result['agent_reconcile']['all_passed'],
                "system_passed": reconcile_result['system_reconcile']['passed'],
                "all_passed": reconcile_result['all_passed'],
                "agent_details": {
                    "total": reconcile_result['agent_reconcile']['total_agents'],
                    "passed": reconcile_result['agent_reconcile']['passed_agents'],
                    "failed": reconcile_result['agent_reconcile']['failed_agents']
                },
                "system_details": {
                    "total_invested": reconcile_result['system_reconcile']['total_invested'],
                    "system_total": reconcile_result['system_reconcile']['system_total'],
                    "discrepancy": reconcile_result['system_reconcile']['discrepancy'],
                    "discrepancy_pct": reconcile_result['system_reconcile']['discrepancy_pct']
                }
            },
            "capital_report": capital_report,
            "duration_seconds": duration
        }
        
        result_file = f"results/phase1_capital_pool_result_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 结果已保存: {result_file}")
        logger.info(f"📋 日志文件: {log_file}")
        logger.info("")
        
        # ========== 最终判断 ==========
        logger.info("=" * 80)
        logger.info("🎯 最终判断")
        logger.info("=" * 80)
        logger.info("")
        
        if reconcile_result['all_passed']:
            logger.info("🎉 测试完全成功！")
            logger.info("   ✅ 资金池机制正常")
            logger.info("   ✅ 资金守恒验证通过")
            logger.info("   ✅ Agent级对账通过")
            logger.info("   ✅ 系统级对账通过")
        else:
            logger.error("❌ 测试发现问题！")
            if not reconcile_result['agent_reconcile']['all_passed']:
                logger.error(f"   ❌ Agent级对账失败: {reconcile_result['agent_reconcile']['failed_agents']}个未通过")
            if not reconcile_result['system_reconcile']['passed']:
                logger.error(f"   ❌ 系统级对账失败: 差异${reconcile_result['system_reconcile']['discrepancy']:.2f}")
        
        logger.info("")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ 测试运行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

