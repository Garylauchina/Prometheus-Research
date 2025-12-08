#!/usr/bin/env python3
"""
📊 v5.3 滑点场景对比测试

测试4种不同市场条件下的滑点影响：
1. 理想市场（0.01%滑点）- 高流动性，对手盘充足
2. 正常市场（0.03%滑点）- 中等流动性，最常见
3. 波动市场（0.05%滑点）- 流动性下降，高波动
4. 极端市场（0.10%滑点）- 低流动性，恐慌性市场
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.backtest.historical_backtest import HistoricalBacktest

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING及以上，减少输出
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_standard_365days_data(start_price: float = 50000.0, seed: int = 42):
    """
    生成标准365天数据（固定随机种子，确保可重复）
    
    Args:
        start_price: 起始价格
        seed: 随机种子
    """
    # 固定随机种子，确保每次生成相同的市场数据
    np.random.seed(seed)
    
    # 生成时间序列
    start_time = datetime(2024, 1, 1)
    timestamps = [start_time + timedelta(days=i) for i in range(365)]
    
    prices = [start_price]
    
    for i in range(1, 365):
        current_price = prices[-1]
        
        # 确定当前所处阶段
        if i <= 90:
            # Q1: 牛市反弹
            daily_drift = 0.004  # 日均+0.4%
            volatility = 0.015   # 1.5%波动
            big_move_prob = 0.15
        elif i <= 180:
            # Q2: 高位震荡
            mean_price = prices[90]
            mean_reversion = (mean_price - current_price) / mean_price * 0.2
            daily_drift = mean_reversion
            volatility = 0.02
            big_move_prob = 0.1
        elif i <= 270:
            # Q3: 熊市暴跌
            daily_drift = -0.005  # 日均-0.5%
            volatility = 0.02
            big_move_prob = 0.1
        else:
            # Q4: 底部震荡
            mean_price = prices[270]
            mean_reversion = (mean_price - current_price) / mean_price * 0.15
            daily_drift = mean_reversion
            volatility = 0.025
            big_move_prob = 0.12
        
        # 基础变化
        noise = np.random.normal(0, volatility)
        daily_return = daily_drift + noise
        
        # 大波动事件
        if np.random.random() < big_move_prob:
            if i <= 90:
                big_move = np.random.uniform(0.05, 0.10)
                daily_return += big_move
            elif i > 180 and i <= 270:
                big_move = -np.random.uniform(0.05, 0.15)
                daily_return += big_move
            else:
                big_move = np.random.uniform(0.04, 0.08) * np.random.choice([-1, 1])
                daily_return += big_move
        
        # 黑天鹅事件
        if np.random.random() < 0.01:
            black_swan = -np.random.uniform(0.15, 0.25)
            daily_return = black_swan
        
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
    
    return df


def run_single_scenario(scenario_name: str, slippage_pct: float, market_data: pd.DataFrame):
    """
    运行单个滑点场景测试
    
    Args:
        scenario_name: 场景名称
        slippage_pct: 滑点百分比
        market_data: 市场数据
        
    Returns:
        测试结果字典
    """
    print(f"\n{'='*80}")
    print(f"📊 场景测试: {scenario_name}")
    print(f"   滑点: {slippage_pct*100:.2f}%")
    print(f"{'='*80}")
    
    # 临时修改滑点参数（通过修改源代码文件）
    # 读取historical_backtest.py
    backtest_file = 'prometheus/backtest/historical_backtest.py'
    with open(backtest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原始内容
    original_content = content
    
    # 替换滑点值
    # 查找 slippage = 0.0001 这一行（或其他值）
    import re
    content = re.sub(
        r'slippage = 0\.\d+  # 0\.\d+%',
        f'slippage = {slippage_pct}  # {slippage_pct*100:.2f}%',
        content
    )
    
    # 写回文件
    with open(backtest_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        # 初始化
        moirai = Moirai()
        evolution_manager = EvolutionManagerV5(moirai=moirai)
        
        # 创建回测引擎
        backtest = HistoricalBacktest(
            evolution_manager=evolution_manager,
            kline_data=market_data,
            evolution_interval=30,
            initial_agents=50,
            initial_capital=10000.0
        )
        
        # 运行回测
        start_time = time.time()
        results = backtest.run()
        elapsed_time = time.time() - start_time
        
        # 提取关键指标
        scenario_results = {
            'scenario_name': scenario_name,
            'slippage_pct': slippage_pct,
            'annual_return': results['returns']['avg_return'],
            'max_return': results['returns']['max_return'],
            'min_return': results['returns']['min_return'],
            'final_capital': results['capital']['final_avg'],
            'market_return': results['market_performance']['market_return'],
            'outperformance': results['returns']['avg_return'] - results['market_performance']['market_return'],
            'sharpe_ratio': results.get('sharpe_ratio', 0),
            'max_drawdown': results.get('max_drawdown', 0),
            'liquidation_rate': results['risk_stats']['liquidation_rate'],
            'total_trades': results['trading_stats']['total_trades'],
            'avg_leverage': results['trading_stats']['avg_leverage'],
            'elapsed_time': elapsed_time
        }
        
        print(f"\n✅ 测试完成:")
        print(f"   年化收益: {scenario_results['annual_return']:+.2f}%")
        print(f"   最终资金: ${scenario_results['final_capital']:,.2f}")
        print(f"   夏普比率: {scenario_results['sharpe_ratio']:.2f}")
        print(f"   爆仓率: {scenario_results['liquidation_rate']:.1f}%")
        print(f"   耗时: {elapsed_time:.1f}秒")
        
        return scenario_results
        
    finally:
        # 恢复原始内容
        with open(backtest_file, 'w', encoding='utf-8') as f:
            f.write(original_content)


def main():
    """主函数"""
    print("\n" + "="*80)
    print("📊 v5.3 滑点场景对比测试")
    print("="*80)
    print("🎯 目标：测试不同市场流动性条件下的系统表现")
    print("📋 场景：理想/正常/波动/极端 四种市场条件")
    print("⏱️  预计用时：3-4分钟（4个场景）")
    print("="*80 + "\n")
    
    # 步骤1: 生成标准市场数据（固定种子）
    print("📋 步骤1: 生成标准365天市场数据（固定种子=42）")
    market_data = generate_standard_365days_data(start_price=50000.0, seed=42)
    print(f"✅ 数据生成完成: {len(market_data)}天")
    print(f"   起始价格: ${market_data['close'].iloc[0]:,.2f}")
    print(f"   最终价格: ${market_data['close'].iloc[-1]:,.2f}")
    print(f"   市场涨跌: {(market_data['close'].iloc[-1]/market_data['close'].iloc[0]-1)*100:+.2f}%")
    
    # 步骤2: 定义测试场景
    scenarios = [
        {
            'name': '理想市场（高流动性）',
            'slippage': 0.0001,  # 0.01%
            'description': '充足对手盘，订单簿深度大，小额交易'
        },
        {
            'name': '正常市场（中等流动性）',
            'slippage': 0.0003,  # 0.03%
            'description': '正常对手盘，典型市场条件，最常见'
        },
        {
            'name': '波动市场（流动性下降）',
            'slippage': 0.0005,  # 0.05%
            'description': '对手盘减少，价格波动加剧，中大额交易'
        },
        {
            'name': '极端市场（低流动性）',
            'slippage': 0.0010,  # 0.10%
            'description': '恐慌性市场，订单簿稀薄，大额交易困难'
        }
    ]
    
    print(f"\n📋 步骤2: 定义{len(scenarios)}个测试场景")
    for i, scenario in enumerate(scenarios, 1):
        print(f"   场景{i}: {scenario['name']}")
        print(f"      滑点: {scenario['slippage']*100:.2f}%")
        print(f"      特征: {scenario['description']}")
    
    # 步骤3: 运行所有场景测试
    print(f"\n📋 步骤3: 运行{len(scenarios)}个场景测试")
    print("⏱️  每个场景约需40-60秒...")
    
    all_results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*80}")
        print(f"🚀 开始测试场景 {i}/{len(scenarios)}")
        print(f"{'='*80}")
        
        result = run_single_scenario(
            scenario_name=scenario['name'],
            slippage_pct=scenario['slippage'],
            market_data=market_data
        )
        
        all_results.append(result)
        
        # 休息1秒
        time.sleep(1)
    
    # 步骤4: 生成对比分析
    print("\n" + "="*80)
    print("📋 步骤4: 生成对比分析")
    print("="*80)
    
    # 创建对比表格
    print("\n📊 场景对比总览:")
    print("="*80)
    print(f"{'场景':<20} {'滑点':<8} {'年化收益':<12} {'最终资金':<15} {'夏普':<8} {'爆仓率':<8}")
    print("-"*80)
    
    for result in all_results:
        print(f"{result['scenario_name']:<20} "
              f"{result['slippage_pct']*100:>6.2f}% "
              f"{result['annual_return']:>10.2f}% "
              f"${result['final_capital']:>13,.0f} "
              f"{result['sharpe_ratio']:>6.2f} "
              f"{result['liquidation_rate']:>6.1f}%")
    
    print("="*80)
    
    # 计算滑点影响
    print("\n📊 滑点影响分析:")
    print("="*80)
    
    baseline = all_results[0]  # 理想市场
    
    for i, result in enumerate(all_results):
        if i == 0:
            print(f"{result['scenario_name']}:")
            print(f"   基准场景（不对比）")
        else:
            return_drop = baseline['annual_return'] - result['annual_return']
            return_drop_pct = (return_drop / baseline['annual_return']) * 100
            slippage_increase = (result['slippage_pct'] - baseline['slippage_pct']) * 100
            
            print(f"\n{result['scenario_name']}:")
            print(f"   滑点增加: +{slippage_increase:.2f}个百分点")
            print(f"   收益下降: {return_drop:,.2f}个百分点 ({return_drop_pct:.1f}%)")
            print(f"   资金减少: ${baseline['final_capital'] - result['final_capital']:,.0f}")
            
            # 计算每0.01%滑点的影响
            slippage_impact_per_bp = return_drop / (slippage_increase * 100)
            print(f"   每0.01%滑点影响: {slippage_impact_per_bp:.2f}%收益")
    
    # 关键洞察
    print("\n" + "="*80)
    print("💡 关键洞察:")
    print("="*80)
    
    worst_case = all_results[-1]
    best_case = all_results[0]
    
    total_drop = best_case['annual_return'] - worst_case['annual_return']
    total_drop_pct = (total_drop / best_case['annual_return']) * 100
    
    print(f"\n1. 滑点的巨大影响:")
    print(f"   理想→极端: 收益从+{best_case['annual_return']:.0f}%降至+{worst_case['annual_return']:.0f}%")
    print(f"   总下降: {total_drop:.0f}个百分点 ({total_drop_pct:.1f}%)")
    
    print(f"\n2. 但仍是顶级表现:")
    if worst_case['annual_return'] > 1000:
        print(f"   即使在极端市场（0.10%滑点）")
        print(f"   年化收益仍达+{worst_case['annual_return']:.0f}%")
        print(f"   远超顶级量化基金（30-40%）⚡⚡⚡")
    else:
        print(f"   在极端市场下收益显著下降")
        print(f"   需要避免在低流动性时段交易")
    
    print(f"\n3. 7.5x杠杆的一致性:")
    avg_leverage = sum([r['avg_leverage'] for r in all_results]) / len(all_results)
    print(f"   4个场景平均杠杆: {avg_leverage:.2f}x")
    if all([abs(r['avg_leverage'] - 7.5) < 0.5 for r in all_results]):
        print(f"   ✅ 全部场景都是7.5x左右！")
        print("   这是进化的\"宇宙常数\"⚡")
    
    print(f"\n4. 真实世界建议:")
    normal_case = all_results[1]  # 正常市场
    print(f"   最常见的正常市场（0.03%滑点）:")
    print(f"   年化收益: +{normal_case['annual_return']:.0f}%")
    print(f"   这是最接近真实世界的预期 ⭐⭐⭐")
    
    # 保存结果
    print(f"\n📋 步骤5: 保存测试结果")
    output_dir = Path("results/v53_slippage_scenarios")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存为JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"slippage_scenarios_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'test_date': datetime.now().isoformat(),
                'market_seed': 42,
                'scenarios_count': len(scenarios)
            },
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 结果已保存: {output_file}")
    
    print("\n" + "="*80)
    print("✅ v5.3 滑点场景对比测试完成！")
    print("="*80)
    
    # 最终评级
    print(f"\n🎯 综合评价:")
    
    if worst_case['annual_return'] > 1000:
        print(f"   即使在最差条件下（0.10%滑点）")
        print(f"   系统仍能实现+{worst_case['annual_return']:.0f}%年化")
        print(f"   评级: S级（顶级量化系统）⭐⭐⭐⭐⭐")
    elif worst_case['annual_return'] > 500:
        print(f"   在极端条件下收益下降明显")
        print(f"   但仍保持+{worst_case['annual_return']:.0f}%年化")
        print(f"   评级: A级（优秀量化系统）⭐⭐⭐⭐")
    else:
        print(f"   极端条件下收益大幅下降")
        print(f"   需要优化交易策略")
        print(f"   评级: B级（良好，需改进）⭐⭐⭐")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

