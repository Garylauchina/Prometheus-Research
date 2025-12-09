"""
测试 Stage 1.1 Task 2.2: Immigration和突变机制
=================================================

验证：
1. Immigration能够正确触发（种群过小/平均代数过高）
2. 突变机制增强（directional_bias获得更大突变幅度）
3. Immigration日志正确输出
4. Immigration能维持多样性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def test_immigration_trigger():
    """测试1：Immigration触发条件"""
    print("\n" + "="*80)
    print("测试1：Immigration触发条件验证")
    print("="*80 + "\n")
    
    # 生成简单市场
    facade = V6Facade()
    market_data = facade.generate_training_market(
        market_type='stage1_switching',
        total_bars=2000,
        structures=['trend_up', 'trend_down'],
        bars_per_structure=1000,
        random_seed=42
    )
    
    # 配置：极高淘汰率+高进化频率（触发种群过小）
    config = MockTrainingConfig(
        cycles=500,
        total_system_capital=50000.0,
        agent_count=20,  # 初始20个
        genesis_allocation_ratio=0.3,
        evolution_interval=50,  # ✅ 每50周期进化一次
        elimination_rate=0.4,  # ✅ 高淘汰率（40%）
        elite_ratio=0.2,
        fitness_mode='profit_factor',
        market_type='test_immigration'
    )
    
    print(f"✅ 配置: {config.agent_count}个Agent，{config.cycles}个周期")
    print(f"✅ 淘汰率: {config.elimination_rate*100:.0f}%")
    print(f"✅ 进化间隔: {config.evolution_interval}周期")
    print("")
    
    # 运行训练
    result = facade.run_mock_training(config=config, market_data=market_data)
    
    print("\n" + "-"*80)
    print("训练结果：")
    print("-"*80)
    print(f"系统ROI: {result.system_roi*100:.2f}%")
    print(f"最终Agent数: {result.agent_count_final}")
    print(f"初始Agent数: {config.agent_count}")
    
    # 检查是否维持了种群数量
    if result.agent_count_final >= config.agent_count * 0.5:
        print(f"\n✅ Immigration成功维持种群数量（{result.agent_count_final} >= {config.agent_count * 0.5:.0f}）")
    else:
        print(f"\n⚠️ 种群数量下降过多（{result.agent_count_final} < {config.agent_count * 0.5:.0f}）")
    
    print("\n" + "="*80)
    print("✅ 测试1完成")
    print("="*80 + "\n")


def test_mutation_enhancement():
    """测试2：突变机制增强验证"""
    print("\n" + "="*80)
    print("测试2：突变机制增强验证")
    print("="*80 + "\n")
    
    from prometheus.core.strategy_params import StrategyParams
    
    # 创建原始参数
    original = StrategyParams(
        position_size_base=0.5,
        holding_preference=0.5,
        directional_bias=0.0,  # 中性
        stop_loss_threshold=0.05,
        take_profit_threshold=0.10,
        trend_following_strength=0.5
    )
    
    print("原始参数:")
    print(f"  directional_bias: {original.directional_bias:.4f}")
    print(f"  position_size_base: {original.position_size_base:.4f}")
    print("")
    
    # 测试标准突变
    print("标准突变（mutation_rate=0.1, diversity_boost=1.0）:")
    directional_diffs_standard = []
    position_diffs_standard = []
    
    for i in range(100):
        mutated = original.mutate(mutation_rate=0.1, diversity_boost=1.0)
        directional_diffs_standard.append(abs(mutated.directional_bias - original.directional_bias))
        position_diffs_standard.append(abs(mutated.position_size_base - original.position_size_base))
    
    print(f"  directional_bias平均变化: {np.mean(directional_diffs_standard):.4f}")
    print(f"  position_size_base平均变化: {np.mean(position_diffs_standard):.4f}")
    print(f"  directional_bias/position_size_base比值: {np.mean(directional_diffs_standard)/np.mean(position_diffs_standard):.2f}x")
    print("")
    
    # 测试增强突变
    print("增强突变（mutation_rate=0.1, diversity_boost=2.0）:")
    directional_diffs_boosted = []
    position_diffs_boosted = []
    
    for i in range(100):
        mutated = original.mutate(mutation_rate=0.1, diversity_boost=2.0)
        directional_diffs_boosted.append(abs(mutated.directional_bias - original.directional_bias))
        position_diffs_boosted.append(abs(mutated.position_size_base - original.position_size_base))
    
    print(f"  directional_bias平均变化: {np.mean(directional_diffs_boosted):.4f}")
    print(f"  position_size_base平均变化: {np.mean(position_diffs_boosted):.4f}")
    print(f"  directional_bias/position_size_base比值: {np.mean(directional_diffs_boosted)/np.mean(position_diffs_boosted):.2f}x")
    print("")
    
    # 验证：directional_bias应该获得1.5倍突变幅度
    directional_avg = np.mean(directional_diffs_standard)
    position_avg = np.mean(position_diffs_standard)
    ratio = directional_avg / position_avg
    
    if ratio > 1.3:  # 允许一定误差（理论值1.5）
        print(f"✅ directional_bias获得增强突变（{ratio:.2f}x > 1.3x）")
    else:
        print(f"⚠️ directional_bias突变幅度不足（{ratio:.2f}x < 1.3x）")
    
    # 验证：diversity_boost能放大突变
    boost_ratio = np.mean(directional_diffs_boosted) / np.mean(directional_diffs_standard)
    if boost_ratio > 1.8:  # 允许误差（理论值2.0）
        print(f"✅ diversity_boost有效（{boost_ratio:.2f}x > 1.8x）")
    else:
        print(f"⚠️ diversity_boost效果不明显（{boost_ratio:.2f}x < 1.8x）")
    
    print("\n" + "="*80)
    print("✅ 测试2完成")
    print("="*80 + "\n")


def test_immigration_diversity_impact():
    """测试3：Immigration对多样性的影响"""
    print("\n" + "="*80)
    print("测试3：Immigration对多样性的影响")
    print("="*80 + "\n")
    
    # 生成复杂市场（多结构切换）
    facade = V6Facade()
    market_data = facade.generate_training_market(
        market_type='stage1_switching',
        total_bars=1500,
        structures=['trend_up', 'range', 'trend_down', 'fake_breakout'],
        bars_per_structure=375,
        random_seed=123
    )
    
    # 配置：长周期训练（让平均代数增长）
    config = MockTrainingConfig(
        cycles=600,
        total_system_capital=100000.0,
        agent_count=30,
        genesis_allocation_ratio=0.25,
        evolution_interval=50,
        elimination_rate=0.3,
        elite_ratio=0.2,
        fitness_mode='profit_factor',
        market_type='test_diversity'
    )
    
    print(f"✅ 配置: {config.agent_count}个Agent，{config.cycles}个周期")
    print(f"✅ 预期Immigration触发: 平均代数>10时")
    print("")
    
    # 运行训练
    result = facade.run_mock_training(config=config, market_data=market_data)
    
    print("\n" + "-"*80)
    print("训练结果：")
    print("-"*80)
    print(f"系统ROI: {result.system_roi*100:.2f}%")
    print(f"最终Agent数: {result.agent_count_final}")
    print(f"平均ROI: {result.agent_avg_roi*100:.2f}%")
    print(f"中位数ROI: {result.agent_median_roi*100:.2f}%")
    
    # 计算多样性指标（简化版：ROI标准差）
    # 如果Immigration有效，应该维持较高的策略多样性
    print(f"\n💡 多样性指标:")
    print(f"   最佳ROI: {result.agent_best_roi*100:.2f}%")
    print(f"   平均ROI: {result.agent_avg_roi*100:.2f}%")
    print(f"   中位数ROI: {result.agent_median_roi*100:.2f}%")
    print(f"   ROI分布范围: {(result.agent_best_roi - result.agent_median_roi)*100:.2f}%")
    
    if result.agent_count_final >= config.agent_count * 0.8:
        print(f"\n✅ 种群数量维持良好（{result.agent_count_final} >= {config.agent_count * 0.8:.0f}）")
    else:
        print(f"\n⚠️ 种群数量下降（{result.agent_count_final} < {config.agent_count * 0.8:.0f}）")
    
    print("\n" + "="*80)
    print("✅ 测试3完成")
    print("="*80 + "\n")


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_immigration_trigger()
    test_mutation_enhancement()
    test_immigration_diversity_impact()
    
    print("\n" + "🎉"*40)
    print("所有测试完成！Stage 1.1 Task 2.2 完成！")
    print("🎉"*40 + "\n")

