"""
分析Task 3.3淘汰机制的效率
=============================

问题：为什么错误方向的Agent没有被快速淘汰？

分析维度：
1. 淘汰速度：多少周期内错误方向Agent被淘汰？
2. 淘汰压力：淘汰率30%是否足够？
3. 淘汰标准：基于PF是否能有效识别错误方向？
4. Immigration干扰：是否在注入后立即又淘汰？
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
import pandas as pd
from typing import Dict, List


def analyze_elimination_efficiency(db_path: str, market_name: str, expected_direction: str):
    """
    分析淘汰机制的效率
    
    Args:
        db_path: ExperienceDB路径
        market_name: 市场名称
        expected_direction: 期望方向（'bull', 'bear', 'neutral'）
    """
    
    print("\n" + "="*80)
    print(f"💀 {market_name} 淘汰机制效率分析")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    
    # 1. 加载所有基因数据
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
        ORDER BY profit_factor DESC
    """)
    
    all_data = []
    for row in cursor:
        roi, pf, trade_count, genome_str = row
        genome_dict = json.loads(genome_str)
        all_data.append({
            'roi': roi,
            'pf': pf,
            'trade_count': trade_count,
            **genome_dict
        })
    
    df = pd.DataFrame(all_data)
    
    print(f"\n【数据概览】")
    print(f"  总记录数: {len(df)}")
    print(f"  平均PF: {df['pf'].mean():.2f}")
    
    # 2. 方向分类
    if expected_direction == 'bull':
        df['direction_category'] = df['directional_bias'].apply(
            lambda x: 'correct' if x > 0.6 else ('neutral' if x >= 0.4 else 'wrong')
        )
        expected_bias_range = '>0.6'
        wrong_bias_range = '<0.4'
    elif expected_direction == 'bear':
        df['direction_category'] = df['directional_bias'].apply(
            lambda x: 'correct' if x < 0.4 else ('neutral' if x <= 0.6 else 'wrong')
        )
        expected_bias_range = '<0.4'
        wrong_bias_range = '>0.6'
    else:  # neutral
        df['direction_category'] = df['directional_bias'].apply(
            lambda x: 'correct' if 0.4 <= x <= 0.6 else 'wrong'
        )
        expected_bias_range = '0.4-0.6'
        wrong_bias_range = '<0.4 or >0.6'
    
    correct_count = len(df[df['direction_category'] == 'correct'])
    neutral_count = len(df[df['direction_category'] == 'neutral'])
    wrong_count = len(df[df['direction_category'] == 'wrong'])
    
    print(f"\n【方向分类】")
    print(f"  期望方向: {expected_direction.upper()} ({expected_bias_range})")
    print(f"  - 方向正确: {correct_count} ({correct_count/len(df)*100:.1f}%)")
    print(f"  - 方向中性: {neutral_count} ({neutral_count/len(df)*100:.1f}%)")
    print(f"  - 方向错误: {wrong_count} ({wrong_count/len(df)*100:.1f}%)")
    
    # 3. 分析错误方向Agent的表现
    print(f"\n【问题1：为什么错误方向的Agent没有被淘汰？】")
    print("-"*80)
    
    wrong_agents = df[df['direction_category'] == 'wrong']
    
    if len(wrong_agents) > 0:
        print(f"\n  错误方向Agent数量: {len(wrong_agents)} ({len(wrong_agents)/len(df)*100:.1f}%)")
        print(f"  平均PF: {wrong_agents['pf'].mean():.2f}")
        print(f"  平均交易数: {wrong_agents['trade_count'].mean():.1f}")
        
        # 分析错误方向Agent的PF分布
        pf_positive = len(wrong_agents[wrong_agents['pf'] > 1.0])
        pf_breakeven = len(wrong_agents[wrong_agents['pf'] == 1.0])
        pf_negative = len(wrong_agents[wrong_agents['pf'] < 1.0])
        pf_zero = len(wrong_agents[wrong_agents['pf'] == 0.0])
        
        print(f"\n  错误方向Agent的PF分布:")
        print(f"  - PF > 1.0（盈利）: {pf_positive} ({pf_positive/len(wrong_agents)*100:.1f}%)")
        print(f"  - PF = 1.0（保本）: {pf_breakeven} ({pf_breakeven/len(wrong_agents)*100:.1f}%)")
        print(f"  - 0 < PF < 1.0（亏损）: {pf_negative} ({pf_negative/len(wrong_agents)*100:.1f}%)")
        print(f"  - PF = 0.0（未交易或全亏）: {pf_zero} ({pf_zero/len(wrong_agents)*100:.1f}%)")
        
        # 关键发现：错误方向但PF>1.0的Agent
        if pf_positive > 0:
            print(f"\n  ⚠️ 关键发现：{pf_positive}个错误方向的Agent居然是盈利的（PF>1.0）！")
            print(f"     → 这些Agent不会被淘汰（基于PF排序）")
            print(f"     → 它们还可能被选为Elite繁殖！")
            
            # 展示Top 5错误方向但盈利的Agent
            wrong_profitable = wrong_agents[wrong_agents['pf'] > 1.0].sort_values('pf', ascending=False).head(5)
            print(f"\n  Top 5错误方向但盈利的Agent:")
            print(f"  {'ROI':>10} {'PF':>8} {'交易数':>8} {'方向偏好':>10}")
            print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*10}")
            for idx, row in wrong_profitable.iterrows():
                print(f"  {row['roi']*100:>9.2f}% {row['pf']:>8.2f} {row['trade_count']:>8.0f} {row['directional_bias']:>10.3f}")
    else:
        print(f"  ✅ 无错误方向Agent（已被完全淘汰）")
    
    # 4. 分析淘汰压力
    print(f"\n【问题2：淘汰压力是否足够？】")
    print("-"*80)
    
    # 当前配置
    elimination_rate = 0.3  # 30%
    evolution_interval = 50  # 每50周期
    total_cycles = 5000
    num_evolutions = total_cycles // evolution_interval  # 100次
    
    print(f"\n  当前淘汰配置:")
    print(f"  - 淘汰率: {elimination_rate*100:.0f}%")
    print(f"  - 进化间隔: {evolution_interval}周期")
    print(f"  - 总进化次数: {num_evolutions}次（5000周期）")
    
    # 计算错误方向Agent的存活概率
    # 假设错误方向Agent的PF总是在后30%
    survival_rate_per_round = 1 - elimination_rate
    survival_rate_after_100_rounds = survival_rate_per_round ** num_evolutions
    
    print(f"\n  理论淘汰分析（假设错误方向Agent的PF总是最低30%）:")
    print(f"  - 单轮存活率: {survival_rate_per_round*100:.1f}%")
    print(f"  - 100轮后存活率: {survival_rate_after_100_rounds*100:.2e}%")
    print(f"  - 结论: 理论上错误方向Agent应该被完全淘汰")
    
    print(f"\n  但实际上:")
    print(f"  - 错误方向Agent占比: {wrong_count/len(df)*100:.1f}%")
    print(f"  - ⚠️ 远高于理论值！")
    
    print(f"\n  可能的原因:")
    print(f"  1. Immigration持续注入新的错误方向Agent")
    print(f"  2. 错误方向Agent并非总是PF最低（短期侥幸盈利）")
    print(f"  3. Mutation导致正确方向Agent变异为错误方向")
    
    # 5. 优化建议
    print(f"\n【优化建议：加速淘汰】")
    print("="*80)
    
    # 计算需要多高的淘汰率才能在100轮内将错误方向Agent降到10%以下
    target_wrong_ratio = 0.1  # 目标：错误方向<10%
    current_wrong_ratio = wrong_count / len(df)
    
    # 假设Immigration每10代注入5个Agent（10%），Mutation导致5%正确方向变异为错误方向
    # 净增长率 = Immigration(10%) + Mutation(5%) = 15% per 10 generations
    # 需要的淘汰率 = 错误方向比例 + 净增长率
    
    required_elimination_rate = current_wrong_ratio + 0.15
    
    print(f"\n  1. 提高淘汰率:")
    print(f"     当前: {elimination_rate*100:.0f}%")
    print(f"     建议: {min(required_elimination_rate*100, 50):.0f}% （最高50%）")
    print(f"     理由: 需要抵消Immigration和Mutation带来的错误方向Agent增长")
    
    print(f"\n  2. 缩短淘汰周期:")
    print(f"     当前: 每{evolution_interval}周期")
    print(f"     建议: 每30周期")
    print(f"     理由: 更快发现和淘汰错误方向Agent，减少它们的繁殖机会")
    
    print(f"\n  3. 延长训练周期:")
    print(f"     当前: {total_cycles}周期")
    print(f"     建议: 10000周期")
    print(f"     理由: 给足够时间让淘汰机制发挥作用")
    
    print(f"\n  4. ✅ 保持高Mutation（包括directional_bias 1.5x）")
    print(f"     理由: 制造发散，强化探索，通过淘汰实现收敛")
    
    print(f"\n  5. ✅ 保持Immigration注入随机Agent")
    print(f"     理由: 防止早熟收敛，持续探索新的可能性")
    
    print(f"\n  预期效果:")
    print(f"     淘汰率50% + 周期30 + 训练10000周期")
    print(f"     → 333次进化（vs 当前100次）")
    print(f"     → 错误方向Agent占比: {current_wrong_ratio*100:.1f}% → <10%")
    print(f"     → 方向收敛度: {correct_count/len(df)*100:.1f}% → >70%")
    
    conn.close()


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print("\n" + "="*100)
    print("💀 Task 3.3 淘汰机制效率分析")
    print("="*100)
    print("")
    print("核心问题：为什么错误方向的Agent没有被快速淘汰？")
    print("")
    print("="*100)
    
    # 分析三种市场
    markets = [
        ('experience/task3_3_pure_bull.db', 'Pure Bull', 'bull'),
        ('experience/task3_3_pure_bear.db', 'Pure Bear', 'bear'),
        ('experience/task3_3_pure_range.db', 'Pure Range', 'neutral')
    ]
    
    for db_path, market_name, expected_direction in markets:
        try:
            analyze_elimination_efficiency(db_path, market_name, expected_direction)
        except Exception as e:
            print(f"\n❌ {market_name} 分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*100)
    print("✅ 分析完成！")
    print("="*100)

