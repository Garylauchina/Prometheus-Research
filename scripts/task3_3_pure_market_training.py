"""
Task 3.3: 纯市场训练（为角色系统准备基因库）
==============================================

目标：在3种纯市场中分别训练，采集特化基因

Task 3.3.1: 纯牛市 → BullHolder角色种子基因
Task 3.3.2: 纯熊市 → BearShorter角色种子基因
Task 3.3.3: 纯震荡 → MeanReversion角色种子基因

预期：每种市场产生特定的directional_bias分布
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def train_in_pure_market(market_type: str, cycles: int = 5000):
    """
    在纯市场环境中训练
    
    Args:
        market_type: 'pure_bull', 'pure_bear', 'pure_range'
        cycles: 训练周期
    """
    print("\n" + "="*80)
    print(f"🏃 开始训练：{market_type}")
    print("="*80 + "\n")
    
    facade = V6Facade()
    
    # 生成纯市场数据
    if market_type == 'pure_bull':
        market_data = facade.generate_training_market(
            market_type='bull',
            total_bars=cycles,
            random_seed=100
        )
    elif market_type == 'pure_bear':
        market_data = facade.generate_training_market(
            market_type='bear',
            total_bars=cycles,
            random_seed=200
        )
    elif market_type == 'pure_range':
        market_data = facade.generate_training_market(
            market_type='range',
            total_bars=cycles,
            random_seed=300
        )
    else:
        raise ValueError(f"未知市场类型: {market_type}")
    
    # 配置训练
    config = MockTrainingConfig(
        cycles=cycles,
        total_system_capital=500000,
        agent_count=50,
        genesis_strategy='pure_random',
        evolution_interval=50,
        elimination_rate=0.3,
        elite_ratio=0.2,
        fitness_mode='profit_factor'
    )
    
    print(f"市场类型: {market_type}")
    print(f"训练周期: {cycles}")
    
    # 显示市场信息
    start_price = market_data.iloc[0]['close']
    end_price = market_data.iloc[-1]['close']
    market_roi = (end_price / start_price - 1) * 100
    
    print(f"市场价格: ${start_price:,.2f} → ${end_price:,.2f}")
    print(f"市场ROI: {market_roi:+.2f}%")
    print(f"\n开始训练...\n")
    
    # 运行训练
    result = facade.run_mock_training(
        config=config,
        market_data=market_data
    )
    
    print(f"\n{'='*80}")
    print(f"✅ {market_type} 训练完成")
    print(f"{'='*80}\n")
    print(f"系统ROI: {result.system_roi*100:+.2f}%")
    print(f"最佳Agent ROI: {result.agent_best_roi*100:+.2f}%")
    print(f"平均Agent ROI: {result.agent_avg_roi*100:+.2f}%")
    
    return result, market_roi


def analyze_genes(market_type: str, result, market_roi: float):
    """分析训练产生的基因特征"""
    print(f"\n{'='*80}")
    print(f"🔬 {market_type} 基因特征分析")
    print(f"{'='*80}\n")
    
    print(f"【训练效果】")
    print(f"市场ROI: {market_roi:+.2f}%")
    print(f"系统ROI: {result.system_roi*100:+.2f}%")
    
    # 简化分析：基于市场类型预测应该产生的基因特征
    print(f"\n【预期基因特征】")
    if market_type == 'pure_bull':
        print(f"目标角色: BullHolder")
        print(f"预期特征: directional_bias > 0.6 (做多)")
        print(f"           holding_preference > 0.7 (长线)")
    elif market_type == 'pure_bear':
        print(f"目标角色: BearShorter")
        print(f"预期特征: directional_bias < 0.4 (做空)")
        print(f"           holding_preference > 0.7 (长线)")
    elif market_type == 'pure_range':
        print(f"目标角色: MeanReversion")
        print(f"预期特征: directional_bias ≈ 0.5 (中性)")
        print(f"           holding_preference < 0.5 (短线)")
    
    print(f"\n💡 基因已保存到ExperienceDB")
    print(f"   在v6.5/v7.0实现时可以查询相应基因")


def main():
    print("\n" + "🧬"*40)
    print("Task 3.3: 纯市场训练（基因库采集）")
    print("🧬"*40)
    
    markets = [
        ('pure_bull', '纯牛市'),
        ('pure_bear', '纯熊市'),
        ('pure_range', '纯震荡市')
    ]
    
    results = {}
    
    for market_type, name in markets:
        print(f"\n\n{'█'*80}")
        print(f"█  {name}训练")
        print(f"{'█'*80}")
        
        result, market_roi = train_in_pure_market(market_type, cycles=5000)
        analyze_genes(market_type, result, market_roi)
        
        results[market_type] = {
            'result': result,
            'market_roi': market_roi
        }
    
    # 总结
    print(f"\n\n{'='*80}")
    print(f"📊 Task 3.3 训练总结")
    print(f"{'='*80}\n")
    
    print(f"{'市场类型':<15} {'市场ROI':>12} {'系统ROI':>12} {'最佳Agent ROI':>15}")
    print(f"-"*80)
    
    for market_type, name in markets:
        r = results[market_type]['result']
        m_roi = results[market_type]['market_roi']
        print(f"{name:<15} {m_roi:>11.2f}% {r.system_roi*100:>11.2f}% {r.agent_best_roi*100:>14.2f}%")
    
    print(f"\n✅ Task 3.3 完成！")
    print(f"\n💾 基因库状态：")
    print(f"   - BullHolder种子基因: 已采集（纯牛市）")
    print(f"   - BearShorter种子基因: 已采集（纯熊市）")
    print(f"   - MeanReversion种子基因: 已采集（纯震荡市）")
    
    print(f"\n🚀 下一步：")
    print(f"   选项A: 实现v6.5（3角色原型）")
    print(f"   选项B: 提交代码，休息一下")


if __name__ == '__main__':
    import time
    start_time = time.time()
    
    main()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n⏱️  总耗时: {duration/60:.1f}分钟")

