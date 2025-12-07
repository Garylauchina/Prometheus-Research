#!/usr/bin/env python3
"""
Phase 2A: 多种子验证测试
========================

目标：验证+2096%收益的稳定性和可复现性

测试配置：
- 种子范围：8000-8019 (20个种子)
- 周期数：500
- Agent数：50
- 配置：加仓 + 可进化杠杆

验证目标：
1. 收益是否稳定？（标准差）
2. 是否有种子巨亏？（最差情况）
3. 是否有种子暴利？（最好情况）
4. 平均收益是否接近+2096%？

遵守三大铁律：
1. 统一封装：使用v6 Facade
2. 标准模板：完整系统逻辑链
3. 对账验证：每笔交易自动对账
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
log_file = f"results/phase2a_multi_seed_{timestamp}.log"
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

from prometheus.facade.v6_facade import run_scenario, build_facade

def load_data():
    """加载历史数据"""
    data_file = Path("data/okx/BTC_USDT_1d_20251206.csv")
    if not data_file.exists():
        raise FileNotFoundError(f"数据文件不存在: {data_file}")
    
    df = pd.read_csv(data_file)
    logger.info(f"✅ 加载数据: {len(df)}条记录")
    
    return df


def run_single_seed_test(seed: int, data: pd.DataFrame, test_number: int, total_tests: int):
    """
    运行单个种子测试
    
    Args:
        seed: 种子值
        data: 历史数据
        test_number: 当前测试编号（从1开始）
        total_tests: 总测试数
    
    Returns:
        dict: 测试结果
    """
    logger.info("=" * 80)
    logger.info(f"🧪 测试 {test_number}/{total_tests}: Seed {seed}")
    logger.info("=" * 80)
    
    try:
        # 构建配置
        config = {
            "seed": seed,
            "evolution_seed": None,  # 使用真随机，确保演化多样性
            "cycles": 500,
            "genesis_size": 50,
            "scenario": "backtest",
            "full_genome_unlock": True,  # AlphaZero模式：全参数解锁
            "log_level": "WARNING"  # 降低日志级别，避免过多输出
        }
        
        # 构建Facade（遵守三大铁律：统一封装）
        facade = build_facade(config)
        
        # 初始化种群
        facade.init_population(
            scenario="backtest",
            full_genome_unlock=True
        )
        
        logger.info(f"✅ 种群初始化完成: {len(facade.moirai.agents)}个Agent")
        
        # 运行测试（遵守三大铁律：完整系统逻辑链）
        result = run_scenario(
            scenario="backtest",
            data=data,
            config=config,
            facade=facade
        )
        
        # 提取结果
        system_return = 0.0
        total_trades = 0
        avg_trades = 0.0
        best_agent_return = 0.0
        worst_agent_return = 0.0
        
        if facade.moirai and facade.moirai.agents:
            # 计算系统平均收益
            returns = []
            for agent in facade.moirai.agents:
                if hasattr(agent, 'account') and agent.account:
                    initial = agent.account.initial_capital
                    current = agent.account.private_ledger.virtual_capital
                    agent_return = ((current - initial) / initial) * 100
                    returns.append(agent_return)
                    total_trades += agent.account.private_ledger.trade_count
            
            if returns:
                system_return = np.mean(returns)
                best_agent_return = np.max(returns)
                worst_agent_return = np.min(returns)
                avg_trades = total_trades / len(returns)
        
        # 对账验证（遵守三大铁律：对账验证）
        reconcile_summary = facade.reconcile()
        
        # 保存结果
        test_result = {
            "seed": seed,
            "test_number": test_number,
            "system_return_pct": round(system_return, 2),
            "total_trades": total_trades,
            "avg_trades_per_agent": round(avg_trades, 1),
            "best_agent_return_pct": round(best_agent_return, 2),
            "worst_agent_return_pct": round(worst_agent_return, 2),
            "reconcile_pass": reconcile_summary.get("all_passed", False),
            "timestamp": datetime.now().isoformat(),
            "config": config
        }
        
        logger.info("=" * 80)
        logger.info(f"✅ 测试 {test_number}/{total_tests} 完成")
        logger.info(f"   系统收益: {system_return:+.2f}%")
        logger.info(f"   总交易数: {total_trades}笔")
        logger.info(f"   最佳Agent: {best_agent_return:+.2f}%")
        logger.info(f"   最差Agent: {worst_agent_return:+.2f}%")
        logger.info(f"   对账状态: {'✅ 通过' if test_result['reconcile_pass'] else '❌ 失败'}")
        logger.info("=" * 80)
        logger.info("")
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ 测试 {test_number}/{total_tests} 失败: {e}", exc_info=True)
        return {
            "seed": seed,
            "test_number": test_number,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def analyze_results(results: list):
    """分析所有测试结果"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 Phase 2A 多种子验证分析")
    logger.info("=" * 80)
    logger.info("")
    
    # 过滤成功的测试
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    logger.info(f"测试总数: {len(results)}")
    logger.info(f"成功: {len(successful)}")
    logger.info(f"失败: {len(failed)}")
    logger.info("")
    
    if not successful:
        logger.error("❌ 所有测试都失败了！")
        return
    
    # 提取收益数据
    returns = [r['system_return_pct'] for r in successful]
    trades = [r['total_trades'] for r in successful]
    
    # 统计分析
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    min_return = np.min(returns)
    max_return = np.max(returns)
    median_return = np.median(returns)
    
    mean_trades = np.mean(trades)
    std_trades = np.std(trades)
    
    logger.info("📈 收益统计:")
    logger.info(f"   平均收益: {mean_return:+.2f}%")
    logger.info(f"   标准差: {std_return:.2f}%")
    logger.info(f"   中位数: {median_return:+.2f}%")
    logger.info(f"   最高收益: {max_return:+.2f}% (Seed {successful[returns.index(max_return)]['seed']})")
    logger.info(f"   最低收益: {min_return:+.2f}% (Seed {successful[returns.index(min_return)]['seed']})")
    logger.info(f"   收益范围: {max_return - min_return:.2f}%")
    logger.info("")
    
    logger.info("📊 交易统计:")
    logger.info(f"   平均交易数: {mean_trades:.0f}笔")
    logger.info(f"   标准差: {std_trades:.0f}笔")
    logger.info(f"   最多交易: {max(trades)}笔")
    logger.info(f"   最少交易: {min(trades)}笔")
    logger.info("")
    
    # 稳定性评估
    logger.info("🎯 稳定性评估:")
    cv = (std_return / abs(mean_return)) * 100 if mean_return != 0 else float('inf')
    logger.info(f"   变异系数: {cv:.2f}%")
    
    if cv < 10:
        logger.info("   ✅ 极其稳定！（CV < 10%）")
    elif cv < 30:
        logger.info("   ✅ 稳定（CV < 30%）")
    elif cv < 50:
        logger.info("   ⚠️ 中等波动（CV < 50%）")
    else:
        logger.info("   ❌ 高度不稳定（CV ≥ 50%）")
    logger.info("")
    
    # 风险评估
    logger.info("⚠️ 风险评估:")
    negative_count = sum(1 for r in returns if r < 0)
    below_btc = sum(1 for r in returns if r < 536.15)  # BTC基准
    
    logger.info(f"   亏损种子: {negative_count}/{len(returns)} ({negative_count/len(returns)*100:.1f}%)")
    logger.info(f"   跑输BTC: {below_btc}/{len(returns)} ({below_btc/len(returns)*100:.1f}%)")
    
    if negative_count == 0:
        logger.info("   ✅ 所有种子都盈利")
    elif negative_count < len(returns) * 0.1:
        logger.info("   ✅ 少于10%种子亏损")
    elif negative_count < len(returns) * 0.3:
        logger.info("   ⚠️ 10-30%种子亏损")
    else:
        logger.info("   ❌ 超过30%种子亏损")
    logger.info("")
    
    # 与Phase 1对比
    logger.info("📊 与Phase 1对比:")
    logger.info(f"   Phase 1 (Seed 8004): +2095.79%")
    logger.info(f"   Phase 2A 平均: {mean_return:+.2f}%")
    diff = mean_return - 2095.79
    logger.info(f"   差异: {diff:+.2f}% ({diff/2095.79*100:+.1f}%)")
    logger.info("")
    
    # 最终结论
    logger.info("=" * 80)
    logger.info("🎯 最终结论")
    logger.info("=" * 80)
    logger.info("")
    
    if cv < 30 and mean_return > 1000 and negative_count == 0:
        logger.info("🏆 结论: 系统表现优异！")
        logger.info("   - 收益稳定（CV < 30%）")
        logger.info("   - 平均收益超过1000%")
        logger.info("   - 所有种子都盈利")
        logger.info("   - 可以进入下一阶段（多市场测试）")
    elif cv < 50 and mean_return > 500:
        logger.info("✅ 结论: 系统表现良好")
        logger.info("   - 收益可接受（CV < 50%）")
        logger.info("   - 平均收益超过500%")
        logger.info("   - 需要进一步优化稳定性")
    else:
        logger.info("⚠️ 结论: 系统需要改进")
        logger.info("   - 收益波动较大 或 收益偏低")
        logger.info("   - 需要检查演化机制")
        logger.info("   - 需要检查决策逻辑")
    logger.info("")
    
    return {
        "summary": {
            "total_tests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "mean_return_pct": round(mean_return, 2),
            "std_return_pct": round(std_return, 2),
            "min_return_pct": round(min_return, 2),
            "max_return_pct": round(max_return, 2),
            "median_return_pct": round(median_return, 2),
            "cv_pct": round(cv, 2),
            "negative_count": negative_count,
            "below_btc_count": below_btc,
            "mean_trades": round(mean_trades, 0),
            "std_trades": round(std_trades, 0)
        },
        "results": results
    }


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 Phase 2A: 多种子验证测试")
    logger.info("=" * 80)
    logger.info("")
    logger.info("测试配置:")
    logger.info("  种子范围: 8000-8019 (20个)")
    logger.info("  周期数: 500")
    logger.info("  Agent数: 50")
    logger.info("  配置: 加仓 + 可进化杠杆 + AlphaZero简化")
    logger.info("")
    logger.info("预计时间: 4-6小时")
    logger.info("您可以去休息了，明天查看结果！")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # 加载数据
    try:
        data = load_data()
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return
    
    # 运行测试
    seeds = range(8000, 8020)  # 20个种子
    results = []
    
    start_time = datetime.now()
    
    for i, seed in enumerate(seeds, 1):
        result = run_single_seed_test(seed, data, i, len(seeds))
        results.append(result)
        
        # 每5个测试保存一次中间结果
        if i % 5 == 0:
            intermediate_file = f"results/phase2a_intermediate_{timestamp}.json"
            with open(intermediate_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 中间结果已保存: {intermediate_file}")
            logger.info("")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ 所有测试完成！用时: {duration}")
    logger.info("=" * 80)
    logger.info("")
    
    # 分析结果
    analysis = analyze_results(results)
    
    # 保存最终结果
    final_file = f"results/phase2a_results_{timestamp}.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 最终结果已保存: {final_file}")
    logger.info(f"📋 日志文件: {log_file}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("🌙 晚安！明天见！")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

