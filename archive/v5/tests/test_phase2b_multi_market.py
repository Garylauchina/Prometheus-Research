#!/usr/bin/env python3
"""
Phase 2B: 多市场压力测试
========================

✅ 遵守三大铁律：
1. 统一封装：使用v6 Facade统一入口
2. 严格执行测试规范：基于Phase 2A模板
3. 不简化底层机制：完整系统逻辑链

目标：
验证Agent是否能在不同市场环境下自适应演化出不同策略

测试环境：
1. 牛市：BTC +536% (已测试，基准)
2. 熊市：BTC -50%
3. 震荡市：BTC ±10%
4. 崩盘：BTC -80%

测试配置：
- 每个环境使用相同种子（8004）
- 500周期
- 50个Agent
- 完整对账验证
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
log_file = f"results/phase2b_multi_market_{timestamp}.log"
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


def create_bear_market_data(base_data: pd.DataFrame, decline_pct: float = 0.5) -> pd.DataFrame:
    """
    创建熊市数据：从高点持续下跌
    
    Args:
        base_data: 原始牛市数据
        decline_pct: 下跌幅度（0.5 = 50%）
    
    Returns:
        熊市数据
    """
    bear_data = base_data.copy()
    
    # 反转价格序列并调整为下跌
    start_price = base_data['close'].iloc[0]
    end_price = start_price * (1 - decline_pct)
    
    # 线性下跌 + 随机波动
    prices = np.linspace(start_price, end_price, len(bear_data))
    # 添加±3%的随机波动
    noise = np.random.randn(len(prices)) * start_price * 0.03
    bear_data['close'] = prices + noise
    bear_data['open'] = bear_data['close'].shift(1).fillna(bear_data['close'].iloc[0])
    bear_data['high'] = bear_data[['open', 'close']].max(axis=1) * 1.01
    bear_data['low'] = bear_data[['open', 'close']].min(axis=1) * 0.99
    
    return bear_data


def create_sideways_market_data(base_data: pd.DataFrame, volatility: float = 0.1) -> pd.DataFrame:
    """
    创建震荡市数据：围绕均价上下波动
    
    Args:
        base_data: 原始数据
        volatility: 波动幅度（0.1 = ±10%）
    
    Returns:
        震荡市数据
    """
    sideways_data = base_data.copy()
    
    # 均价
    mean_price = base_data['close'].iloc[0]
    
    # 生成震荡价格（正弦波 + 随机噪声）
    cycles = 5  # 5个完整周期
    t = np.linspace(0, cycles * 2 * np.pi, len(sideways_data))
    wave = np.sin(t) * mean_price * volatility
    noise = np.random.randn(len(t)) * mean_price * 0.02
    
    sideways_data['close'] = mean_price + wave + noise
    sideways_data['open'] = sideways_data['close'].shift(1).fillna(sideways_data['close'].iloc[0])
    sideways_data['high'] = sideways_data[['open', 'close']].max(axis=1) * 1.005
    sideways_data['low'] = sideways_data[['open', 'close']].min(axis=1) * 0.995
    
    return sideways_data


def create_crash_market_data(base_data: pd.DataFrame, crash_pct: float = 0.8) -> pd.DataFrame:
    """
    创建崩盘数据：急速暴跌
    
    Args:
        base_data: 原始数据
        crash_pct: 崩盘幅度（0.8 = 80%跌幅）
    
    Returns:
        崩盘数据
    """
    crash_data = base_data.copy()
    
    start_price = base_data['close'].iloc[0]
    crash_bottom = start_price * (1 - crash_pct)
    
    # 前30%周期急跌，然后底部震荡
    crash_point = int(len(crash_data) * 0.3)
    
    # 急跌段
    crash_prices = np.linspace(start_price, crash_bottom, crash_point)
    # 底部震荡段
    bottom_prices = np.ones(len(crash_data) - crash_point) * crash_bottom
    bottom_prices += np.random.randn(len(bottom_prices)) * crash_bottom * 0.05
    
    all_prices = np.concatenate([crash_prices, bottom_prices])
    crash_data['close'] = all_prices
    crash_data['open'] = crash_data['close'].shift(1).fillna(crash_data['close'].iloc[0])
    crash_data['high'] = crash_data[['open', 'close']].max(axis=1) * 1.02
    crash_data['low'] = crash_data[['open', 'close']].min(axis=1) * 0.98
    
    return crash_data


def run_market_scenario(market_name: str, market_data: pd.DataFrame, seed: int = 8004):
    """
    运行单个市场场景测试
    
    ✅ 完全复用Phase 2A的逻辑，确保封装一致性
    
    Args:
        market_name: 市场名称
        market_data: 市场数据
        seed: 随机种子
    
    Returns:
        dict: 测试结果
    """
    logger.info("=" * 80)
    logger.info(f"🧪 市场场景: {market_name} (Seed {seed})")
    logger.info("=" * 80)
    
    try:
        # 创建market_feed函数
        prices = market_data['close'].values
        def make_market_feed():
            def feed(cycle):
                idx = min(cycle - 1, len(prices) - 1)
                return {'price': prices[idx]}, {}
            return feed
        
        # ✅ 统一封装：使用run_scenario
        facade = run_scenario(
            mode="backtest",
            total_cycles=500,
            market_feed=make_market_feed(),
            
            # 种群配置
            num_families=50,
            agent_count=50,
            capital_per_agent=10000.0,
            
            # 进化配置
            evo_interval=10,  # 每10个周期进化一次
            
            # 种子配置
            seed=seed,
            evolution_seed=None,  # 演化随机
            
            # AlphaZero式配置
            full_genome_unlock=True  # 全参数解锁
        )
        
        # 提取结果（包含实盈和浮盈）
        returns = []
        realized_pnls = []
        unrealized_pnls = []
        total_trades = 0
        final_price = prices[-1]
        start_price = prices[0]
        
        for agent in facade.moirai.agents:
            if hasattr(agent, 'account') and agent.account:
                initial = agent.account.private_ledger.initial_capital
                realized_capital = agent.account.private_ledger.virtual_capital
                unrealized_pnl = agent.calculate_unrealized_pnl(final_price)
                
                # 总资金 = 已实现资金 + 未实现盈亏
                current = realized_capital + unrealized_pnl
                agent_return = ((current - initial) / initial) * 100
                
                returns.append(agent_return)
                realized_pnls.append(realized_capital - initial)
                unrealized_pnls.append(unrealized_pnl)
                total_trades += agent.account.private_ledger.trade_count
        
        # 统计分析
        system_return = np.mean(returns) if returns else 0.0
        best_agent_return = np.max(returns) if returns else 0.0
        worst_agent_return = np.min(returns) if returns else 0.0
        avg_trades = total_trades / len(returns) if returns else 0.0
        avg_realized_pnl = np.mean(realized_pnls) if realized_pnls else 0.0
        avg_unrealized_pnl = np.mean(unrealized_pnls) if unrealized_pnls else 0.0
        
        # 市场基准
        market_return = ((final_price - start_price) / start_price) * 100
        
        # 对账验证（三大铁律）
        reconcile_summary = facade.reconcile()
        
        # 保存结果
        result = {
            "market_name": market_name,
            "seed": seed,
            "system_return_pct": round(system_return, 2),
            "avg_realized_pnl": round(avg_realized_pnl, 2),
            "avg_unrealized_pnl": round(avg_unrealized_pnl, 2),
            "realized_ratio_pct": round((avg_realized_pnl / (avg_realized_pnl + avg_unrealized_pnl) * 100) if (avg_realized_pnl + avg_unrealized_pnl) != 0 else 0, 2),
            "total_trades": total_trades,
            "avg_trades_per_agent": round(avg_trades, 1),
            "best_agent_return_pct": round(best_agent_return, 2),
            "worst_agent_return_pct": round(worst_agent_return, 2),
            "market_return_pct": round(market_return, 2),
            "alpha_pct": round(system_return - market_return, 2),  # 超额收益
            "reconcile_pass": reconcile_summary.get("all_passed", False),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("=" * 80)
        logger.info(f"✅ {market_name} 测试完成")
        logger.info(f"   市场表现: {market_return:+.2f}%")
        logger.info(f"   系统收益: {system_return:+.2f}%")
        logger.info(f"     ├─ 实盈: ${avg_realized_pnl:+.2f} ({result['realized_ratio_pct']:.2f}%)")
        logger.info(f"     └─ 浮盈: ${avg_unrealized_pnl:+.2f}")
        logger.info(f"   超额收益(Alpha): {result['alpha_pct']:+.2f}%")
        logger.info(f"   总交易数: {total_trades}笔")
        logger.info(f"   对账状态: {'✅ 通过' if result['reconcile_pass'] else '⚠️ 未通过'}")
        logger.info("=" * 80)
        logger.info("")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ {market_name} 测试失败: {e}", exc_info=True)
        return {
            "market_name": market_name,
            "seed": seed,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 Phase 2B: 多市场压力测试")
    logger.info("=" * 80)
    logger.info("")
    logger.info("测试目标：")
    logger.info("  验证Agent能否在不同市场环境下自适应演化")
    logger.info("")
    logger.info("测试环境：")
    logger.info("  1. 牛市：BTC +536%")
    logger.info("  2. 熊市：BTC -50%")
    logger.info("  3. 震荡市：BTC ±10%")
    logger.info("  4. 崩盘：BTC -80%")
    logger.info("")
    logger.info("测试配置：")
    logger.info("  种子: 8004 (Phase 1最佳)")
    logger.info("  周期: 500")
    logger.info("  Agent: 50")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # 加载原始牛市数据
    try:
        bull_data = pd.read_csv("data/okx/BTC_USDT_1d_20251206.csv")
        logger.info(f"✅ 牛市数据加载: {len(bull_data)}条记录")
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return
    
    # 设置随机种子（确保每次生成的模拟数据一致）
    np.random.seed(8004)
    
    # 创建其他市场数据
    logger.info("🔨 生成模拟市场数据...")
    bear_data = create_bear_market_data(bull_data, decline_pct=0.5)
    sideways_data = create_sideways_market_data(bull_data, volatility=0.1)
    crash_data = create_crash_market_data(bull_data, crash_pct=0.8)
    logger.info("✅ 模拟数据生成完成")
    logger.info("")
    
    # 定义测试场景
    scenarios = [
        ("1.牛市", bull_data, "BTC持续上涨，最优策略：买入持有"),
        ("2.熊市", bear_data, "BTC持续下跌，最优策略：做空持有或空仓"),
        ("3.震荡市", sideways_data, "BTC横盘波动，最优策略：高频波段"),
        ("4.崩盘", crash_data, "BTC急速暴跌，最优策略：空仓或做空")
    ]
    
    # 运行所有场景
    results = []
    seed = 8004  # 使用相同种子，观察不同环境下的策略演化
    
    for market_name, market_data, expected_strategy in scenarios:
        logger.info(f"📋 {market_name}")
        logger.info(f"   预期策略: {expected_strategy}")
        logger.info("")
        
        result = run_market_scenario(market_name, market_data, seed)
        results.append(result)
    
    # 分析结果
    analyze_results(results)
    
    # 保存结果
    final_file = f"results/phase2b_results_{timestamp}.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 结果已保存: {final_file}")
    logger.info(f"📋 日志文件: {log_file}")
    logger.info("")


def analyze_results(results: list):
    """分析多市场测试结果"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 Phase 2B 多市场对比分析")
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
    
    # 对比表
    logger.info("📊 多市场表现对比:")
    logger.info("")
    logger.info(f"{'市场':<12} {'市场表现':<12} {'系统收益':<12} {'实盈':<15} {'浮盈':<18} {'Alpha':<12} {'交易数':<10}")
    logger.info("-" * 100)
    
    for r in successful:
        market = r['market_name']
        market_ret = r['market_return_pct']
        sys_ret = r['system_return_pct']
        realized = r['avg_realized_pnl']
        unrealized = r['avg_unrealized_pnl']
        alpha = r['alpha_pct']
        trades = r['total_trades']
        realized_ratio = r['realized_ratio_pct']
        
        logger.info(f"{market:<12} {market_ret:>+10.2f}% {sys_ret:>+10.2f}% ${realized:>10.2f} ${unrealized:>13.2f} {alpha:>+10.2f}% {trades:>8}笔")
    
    logger.info("-" * 100)
    logger.info("")
    
    # 策略分析
    logger.info("🎯 策略分析:")
    logger.info("")
    
    for r in successful:
        market = r['market_name']
        realized_ratio = r['realized_ratio_pct']
        sys_ret = r['system_return_pct']
        market_ret = r['market_return_pct']
        
        # 判断策略类型
        if realized_ratio < 10:
            strategy = "买入持有（几乎不平仓）"
        elif realized_ratio < 50:
            strategy = "混合策略（部分平仓）"
        else:
            strategy = "频繁交易（大量平仓）"
        
        # 判断表现
        if sys_ret > abs(market_ret) * 2:
            performance = "🏆 优异"
        elif sys_ret > abs(market_ret):
            performance = "✅ 良好"
        elif sys_ret > 0:
            performance = "⚠️ 平庸"
        else:
            performance = "❌ 亏损"
        
        logger.info(f"{market}: {strategy} → {performance}")
    
    logger.info("")
    
    # 最终结论
    logger.info("=" * 80)
    logger.info("🎯 最终结论")
    logger.info("=" * 80)
    logger.info("")
    
    # 检查是否全天候
    all_positive = all(r['system_return_pct'] > 0 for r in successful)
    beat_market = sum(1 for r in successful if r['alpha_pct'] > 0)
    
    if all_positive and beat_market == len(successful):
        logger.info("🏆 结论: 系统具备全天候能力！")
        logger.info("   - 所有市场环境都盈利")
        logger.info("   - 所有环境都跑赢市场基准")
    elif all_positive:
        logger.info("✅ 结论: 系统表现良好")
        logger.info("   - 所有市场环境都盈利")
        logger.info(f"   - {beat_market}/{len(successful)} 环境跑赢市场")
    else:
        logger.info("⚠️ 结论: 系统存在弱点")
        logger.info("   - 部分市场环境亏损")
        logger.info("   - 需要改进策略")
    
    logger.info("")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

