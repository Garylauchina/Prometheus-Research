"""
Stage 1.1 完整训练脚本
======================

目标：
1. 运行5000周期完整训练
2. 验证PF主导+Immigration+增强突变的综合效果
3. 记录详细的进化过程
4. 分析基因收敛和多样性

配置：
- 市场: stage1_switching（4种结构切换）
- 周期: 5000
- Agent: 50
- Fitness: Profit Factor主导
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig


def run_full_training():
    """运行完整训练"""
    
    print("\n" + "="*80)
    print("🚀 Stage 1.1 完整训练")
    print("="*80 + "\n")
    
    # ========== 1. 生成训练市场 ==========
    print("📊 Step 1: 生成训练市场数据")
    print("-"*80)
    
    facade = V6Facade()
    
    market_data = facade.generate_training_market(
        market_type='stage1_switching',
        total_bars=5000,
        structures=['trend_up', 'range', 'trend_down', 'fake_breakout'],
        bars_per_structure=1250,  # 每种结构1250 bars
        random_seed=42,
        save_path='data/stage1_1_training_market.csv'
    )
    
    print(f"✅ 市场数据生成完成: {len(market_data)} bars")
    print(f"   价格范围: [{market_data['close'].min():.2f}, {market_data['close'].max():.2f}]")
    
    # 统计市场结构分布
    if 'structure_type' in market_data.columns:
        structure_dist = market_data['structure_type'].value_counts()
        print(f"\n   市场结构分布:")
        for structure, count in structure_dist.items():
            print(f"   - {structure}: {count} bars ({count/len(market_data)*100:.1f}%)")
    
    print("")
    
    # ========== 2. 配置训练参数 ==========
    print("⚙️  Step 2: 配置训练参数")
    print("-"*80)
    
    config = MockTrainingConfig(
        # 基础配置
        cycles=5000,
        total_system_capital=500000.0,  # 50万初始资金
        agent_count=50,
        
        # 创世配置
        genesis_allocation_ratio=0.3,  # 30%给Agent，70%资金池
        genesis_strategy='random',  # 纯随机创世（Stage 1测试基因进化）
        
        # 进化配置
        evolution_interval=50,  # 每50周期进化一次
        elimination_rate=0.3,  # 淘汰30%
        elite_ratio=0.2,  # 保留20%精英
        fitness_mode='profit_factor',  # ✅ Stage 1.1: PF主导
        
        # 市场配置
        market_type='stage1_switching',
        
        # 经验库配置
        experience_db_path='experience/stage1_1_full_training.db',
        top_k_to_save=20,  # 保存前20名
        save_experience_interval=50,  # 每50周期保存一次
        
        # 日志配置
        log_dir='logs/stage1_1_full_training',
        log_interval=100,
        enable_debug_log=False
    )
    
    print(f"✅ 训练配置:")
    print(f"   周期数: {config.cycles}")
    print(f"   系统资金: ${config.total_system_capital:,.0f}")
    print(f"   Agent数量: {config.agent_count}")
    print(f"   Fitness模式: {config.fitness_mode} ✅")
    print(f"   进化间隔: {config.evolution_interval}")
    print(f"   淘汰率: {config.elimination_rate*100:.0f}%")
    print(f"   精英比例: {config.elite_ratio*100:.0f}%")
    print("")
    
    # ========== 3. 运行训练 ==========
    print("🏃 Step 3: 开始训练")
    print("-"*80)
    print(f"   开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    start_time = datetime.now()
    
    result = facade.run_mock_training(
        config=config,
        market_data=market_data
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("")
    print("-"*80)
    print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   训练耗时: {duration/60:.1f}分钟 ({duration:.0f}秒)")
    print("")
    
    # ========== 4. 分析结果 ==========
    print("📊 Step 4: 训练结果分析")
    print("="*80)
    
    print(f"\n【系统级指标】")
    print(f"  系统ROI: {result.system_roi*100:+.2f}%")
    print(f"  系统总资产: ${result.system_total_capital:,.2f}")
    print(f"  BTC基准ROI: {result.btc_benchmark_roi*100:+.2f}%")
    print(f"  超越BTC: {result.outperformance*100:+.2f}%")
    
    print(f"\n【Agent级指标】")
    print(f"  最终Agent数: {result.agent_count_final}")
    print(f"  最佳ROI: {result.agent_best_roi*100:+.2f}%")
    print(f"  平均ROI: {result.agent_avg_roi*100:+.2f}%")
    print(f"  中位数ROI: {result.agent_median_roi*100:+.2f}%")
    print(f"  平均交易数: {result.agent_avg_trade_count:.1f}")
    
    print(f"\n【资金池状态】")
    print(f"  资金池余额: ${result.capital_pool_balance:,.2f}")
    print(f"  资金利用率: {result.capital_utilization*100:.1f}%")
    
    print(f"\n【对账验证】")
    print(f"  对账状态: {'✅ 通过' if result.reconciliation_passed else '❌ 失败'}")
    
    print(f"\n【经验库】")
    print(f"  总记录数: {result.experience_db_records}")
    print(f"  本次保存: {'✅ 是' if result.experience_saved else '❌ 否'}")
    
    print("")
    
    # ========== 5. 分析ExperienceDB ==========
    if facade.experience_db and result.experience_db_records > 0:
        print("📊 Step 5: 基因数据分析")
        print("="*80)
        
        import sqlite3
        conn = sqlite3.connect(config.experience_db_path)
        
        # 5.1 Profit Factor分布
        print(f"\n【Profit Factor分布】")
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(profit_factor) as avg_pf,
                MIN(profit_factor) as min_pf,
                MAX(profit_factor) as max_pf,
                COUNT(CASE WHEN profit_factor >= 2.0 THEN 1 END) as excellent,
                COUNT(CASE WHEN profit_factor >= 1.5 AND profit_factor < 2.0 THEN 1 END) as good,
                COUNT(CASE WHEN profit_factor >= 1.0 AND profit_factor < 1.5 THEN 1 END) as profitable,
                COUNT(CASE WHEN profit_factor < 1.0 THEN 1 END) as losing
            FROM best_genomes
        """)
        
        row = cursor.fetchone()
        total, avg_pf, min_pf, max_pf, excellent, good, profitable, losing = row
        
        print(f"  总记录: {total}")
        print(f"  平均PF: {avg_pf:.2f}")
        print(f"  PF范围: [{min_pf:.2f}, {max_pf:.2f}]")
        print(f"\n  分级统计:")
        print(f"  - 优秀 (PF≥2.0): {excellent} ({excellent/total*100:.1f}%)")
        print(f"  - 良好 (1.5≤PF<2.0): {good} ({good/total*100:.1f}%)")
        print(f"  - 盈利 (1.0≤PF<1.5): {profitable} ({profitable/total*100:.1f}%)")
        print(f"  - 亏损 (PF<1.0): {losing} ({losing/total*100:.1f}%)")
        
        # 5.2 directional_bias分布（多样性指标）
        print(f"\n【方向偏好分布（多样性指标）】")
        cursor = conn.execute("""
            SELECT genome FROM best_genomes
        """)
        
        import json
        biases = []
        for row in cursor:
            genome_dict = json.loads(row[0])
            bias = genome_dict.get('directional_bias', 0.5)
            biases.append(bias)
        
        biases = np.array(biases)
        
        bulls = np.sum(biases > 0.6)  # 偏多
        bears = np.sum(biases < 0.4)  # 偏空
        neutral = np.sum((biases >= 0.4) & (biases <= 0.6))  # 中性
        
        print(f"  平均方向偏好: {np.mean(biases):.3f}")
        print(f"  标准差: {np.std(biases):.3f}")
        print(f"\n  方向分布:")
        print(f"  - 偏多 (>0.6): {bulls} ({bulls/len(biases)*100:.1f}%)")
        print(f"  - 中性 (0.4-0.6): {neutral} ({neutral/len(biases)*100:.1f}%)")
        print(f"  - 偏空 (<0.4): {bears} ({bears/len(biases)*100:.1f}%)")
        
        # 计算多样性熵
        diversity_entropy = -np.sum([
            (bulls/len(biases)) * np.log(bulls/len(biases) + 1e-10),
            (neutral/len(biases)) * np.log(neutral/len(biases) + 1e-10),
            (bears/len(biases)) * np.log(bears/len(biases) + 1e-10)
        ])
        max_entropy = np.log(3)
        diversity_score = diversity_entropy / max_entropy
        
        print(f"\n  多样性熵: {diversity_entropy:.3f} / {max_entropy:.3f}")
        print(f"  多样性分数: {diversity_score*100:.1f}%")
        
        if diversity_score > 0.8:
            print(f"  ✅ 多样性优秀（>80%）")
        elif diversity_score > 0.6:
            print(f"  ⚠️  多样性中等（60-80%）")
        else:
            print(f"  ❌ 多样性不足（<60%）- Immigration可能需要增强")
        
        # 5.3 Top 10基因
        print(f"\n【Top 10 基因（按PF排序）】")
        cursor = conn.execute("""
            SELECT roi, profit_factor, trade_count, genome
            FROM best_genomes
            ORDER BY profit_factor DESC
            LIMIT 10
        """)
        
        print(f"\n  {'ROI':>10} {'PF':>8} {'交易数':>8} {'方向偏好':>10}")
        print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*10}")
        
        for row in cursor:
            roi, pf, trade_count, genome_str = row
            genome_dict = json.loads(genome_str)
            bias = genome_dict.get('directional_bias', 0.5)
            
            print(f"  {roi*100:>9.2f}% {pf:>8.2f} {trade_count:>8} {bias:>10.3f}")
        
        conn.close()
    
    print("\n" + "="*80)
    print("✅ Stage 1.1 完整训练完成！")
    print("="*80 + "\n")
    
    print(f"📁 输出文件:")
    print(f"   - 市场数据: data/stage1_1_training_market.csv")
    print(f"   - 经验库: {config.experience_db_path}")
    print(f"   - 日志: {result.log_file}")
    print(f"   - 报告: {result.report_file}")
    print("")
    
    return result


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_full_training()
        print("\n🎉 训练成功完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️  训练被用户中断")
    except Exception as e:
        print(f"\n\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()

