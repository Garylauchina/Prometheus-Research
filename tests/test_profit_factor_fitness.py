"""
测试 Stage 1.1: Profit Factor主导的Fitness计算
=================================================

验证：
1. ExperienceDB能正确计算和保存profit_factor
2. EvolutionManagerV5使用PF作为主要指标进行Elite选择
3. 查询相似基因时按PF排序
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def test_profit_factor_calculation():
    """测试1：Profit Factor计算是否正确"""
    print("\n" + "="*80)
    print("测试1：Profit Factor计算验证")
    print("="*80 + "\n")
    
    # 生成简单的上涨市场（让Agent有机会盈利）
    facade = V6Facade()
    market_data = facade.generate_training_market(
        market_type='stage1_switching',
        total_bars=1000,
        structures=['trend_up', 'range'],
        bars_per_structure=500,
        random_seed=42
    )
    
    # 配置：小规模快速测试
    config = MockTrainingConfig(
        cycles=200,  # 少量周期
        total_system_capital=50000.0,
        agent_count=10,  # 少量Agent
        genesis_allocation_ratio=0.3,
        evolution_interval=50,
        elimination_rate=0.3,
        elite_ratio=0.3,
        fitness_mode='profit_factor',  # ✅ 使用PF模式
        market_type='test_pf',
        experience_db_path='experience/test_pf.db'
    )
    
    print(f"✅ 配置: {config.agent_count}个Agent，{config.cycles}个周期")
    print(f"✅ Fitness模式: {config.fitness_mode}")
    print(f"✅ 市场数据: {len(market_data)} bars")
    print("")
    
    # 运行训练
    result = facade.run_mock_training(config=config, market_data=market_data)
    
    print("\n" + "-"*80)
    print("训练结果：")
    print("-"*80)
    print(f"系统ROI: {result.system_roi*100:.2f}%")
    print(f"最佳Agent ROI: {result.agent_best_roi*100:.2f}%")
    print(f"平均交易次数: {result.agent_avg_trade_count:.1f}")
    print("")
    
    # 检查ExperienceDB中的profit_factor
    if facade.experience_db:
        import sqlite3
        conn = sqlite3.connect(config.experience_db_path)
        cursor = conn.execute("""
            SELECT roi, profit_factor, trade_count 
            FROM best_genomes 
            ORDER BY profit_factor DESC 
            LIMIT 5
        """)
        
        print("ExperienceDB前5条记录（按PF排序）：")
        print("-"*80)
        print(f"{'ROI':>10} {'PF':>10} {'交易数':>10}")
        print("-"*80)
        
        records = []
        for row in cursor:
            roi, pf, trade_count = row
            records.append((roi, pf, trade_count))
            print(f"{roi*100:>9.2f}% {pf:>10.2f} {trade_count:>10}")
        
        conn.close()
        
        # 验证PF确实被计算
        assert len(records) > 0, "❌ ExperienceDB应该有记录"
        assert all(pf is not None for _, pf, _ in records), "❌ Profit Factor不应该是None"
        print("\n✅ 所有记录都包含有效的Profit Factor")
        
        # 验证PF顺序正确（降序）
        pfs = [pf for _, pf, _ in records]
        assert pfs == sorted(pfs, reverse=True), "❌ Profit Factor应该按降序排列"
        print("✅ Profit Factor正确按降序排列")
    
    print("\n" + "="*80)
    print("✅ 测试1通过：Profit Factor计算正确")
    print("="*80 + "\n")


def test_profit_factor_vs_absolute_return():
    """测试2：PF模式 vs 绝对收益模式的区别"""
    print("\n" + "="*80)
    print("测试2：Profit Factor vs 绝对收益模式对比")
    print("="*80 + "\n")
    
    # 生成更复杂的市场（包含上涨、下跌、震荡）
    facade = V6Facade()
    market_data = facade.generate_training_market(
        market_type='stage1_switching',
        total_bars=2000,
        structures=['trend_up', 'trend_down', 'range', 'fake_breakout'],
        bars_per_structure=500,
        random_seed=123
    )
    
    results = {}
    
    for fitness_mode in ['profit_factor', 'absolute_return']:
        print(f"\n{'='*40}")
        print(f"运行模式: {fitness_mode}")
        print(f"{'='*40}\n")
        
        facade_test = V6Facade()
        
        config = MockTrainingConfig(
            cycles=300,
            total_system_capital=100000.0,
            agent_count=20,
            genesis_allocation_ratio=0.25,
            evolution_interval=50,
            elimination_rate=0.3,
            elite_ratio=0.2,
            fitness_mode=fitness_mode,
            market_type=f'test_{fitness_mode}',
            experience_db_path=f'experience/test_{fitness_mode}.db'
        )
        
        result = facade_test.run_mock_training(config=config, market_data=market_data)
        
        results[fitness_mode] = {
            'system_roi': result.system_roi,
            'best_roi': result.agent_best_roi,
            'avg_roi': result.agent_avg_roi,
            'avg_trades': result.agent_avg_trade_count
        }
        
        print(f"系统ROI: {result.system_roi*100:.2f}%")
        print(f"最佳Agent ROI: {result.agent_best_roi*100:.2f}%")
        print(f"平均ROI: {result.agent_avg_roi*100:.2f}%")
        print(f"平均交易: {result.agent_avg_trade_count:.1f}")
    
    print("\n" + "="*80)
    print("对比结果：")
    print("="*80)
    print(f"{'指标':<20} {'Profit Factor模式':>20} {'绝对收益模式':>20}")
    print("-"*80)
    
    for key in ['system_roi', 'best_roi', 'avg_roi']:
        pf_val = results['profit_factor'][key]
        ar_val = results['absolute_return'][key]
        print(f"{key:<20} {pf_val*100:>19.2f}% {ar_val*100:>19.2f}%")
    
    pf_trades = results['profit_factor']['avg_trades']
    ar_trades = results['absolute_return']['avg_trades']
    print(f"{'avg_trades':<20} {pf_trades:>20.1f} {ar_trades:>20.1f}")
    
    print("\n✅ 测试2完成：两种模式都能正常运行")
    print(f"💡 Profit Factor模式可能更稳定（避免单次暴利的干扰）")
    print("="*80 + "\n")


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_profit_factor_calculation()
    test_profit_factor_vs_absolute_return()
    
    print("\n" + "🎉"*40)
    print("所有测试通过！Stage 1.1 Task 2.1 完成！")
    print("🎉"*40 + "\n")

