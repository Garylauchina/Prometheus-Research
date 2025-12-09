"""
分析Task 3.3训练结果：系统策略收敛 vs Agent特征发散
==========================================================

理论目标：
- 系统策略强收敛（方向快速统一）
- Agent特征强发散（参数保持多样）

分析维度：
1. 方向收敛度（directional_bias分布）
2. 参数多样性（其他5个参数的标准差）
3. Top基因vs全体基因的方向差异
4. 收敛速度（如果有时间序列数据）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
import pandas as pd
from typing import Dict, List


def analyze_single_market(db_path: str, market_name: str):
    """分析单个市场的收敛度和多样性"""
    
    print("\n" + "="*80)
    print(f"📊 {market_name} 市场分析")
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
    print(f"  PF范围: [{df['pf'].min():.2f}, {df['pf'].max():.2f}]")
    
    # 2. 方向收敛度分析
    print(f"\n【维度1：方向收敛度】")
    print("-"*80)
    
    bias_all = df['directional_bias']
    
    # 全体基因方向分布
    bulls_all = np.sum(bias_all > 0.6)
    bears_all = np.sum(bias_all < 0.4)
    neutral_all = np.sum((bias_all >= 0.4) & (bias_all <= 0.6))
    
    print(f"\n  全体基因方向分布 (n={len(df)}):")
    print(f"  - 偏多 (>0.6): {bulls_all} ({bulls_all/len(df)*100:.1f}%)")
    print(f"  - 中性 (0.4-0.6): {neutral_all} ({neutral_all/len(df)*100:.1f}%)")
    print(f"  - 偏空 (<0.4): {bears_all} ({bears_all/len(df)*100:.1f}%)")
    print(f"  - 平均: {bias_all.mean():.3f} ± {bias_all.std():.3f}")
    
    # Top 10%基因方向分布
    top10_idx = int(len(df) * 0.1)
    df_top = df.head(top10_idx)
    bias_top = df_top['directional_bias']
    
    bulls_top = np.sum(bias_top > 0.6)
    bears_top = np.sum(bias_top < 0.4)
    neutral_top = np.sum((bias_top >= 0.4) & (bias_top <= 0.6))
    
    print(f"\n  Top 10%基因方向分布 (n={len(df_top)}):")
    print(f"  - 偏多 (>0.6): {bulls_top} ({bulls_top/len(df_top)*100:.1f}%)")
    print(f"  - 中性 (0.4-0.6): {neutral_top} ({neutral_top/len(df_top)*100:.1f}%)")
    print(f"  - 偏空 (<0.4): {bears_top} ({bears_top/len(df_top)*100:.1f}%)")
    print(f"  - 平均: {bias_top.mean():.3f} ± {bias_top.std():.3f}")
    
    # 方向收敛度指标
    # 使用方向分布的熵来衡量收敛度（熵越低，收敛度越高）
    p_bull = bulls_all / len(df)
    p_bear = bears_all / len(df)
    p_neutral = neutral_all / len(df)
    
    direction_entropy = -np.sum([
        p if p == 0 else p * np.log(p + 1e-10)
        for p in [p_bull, p_neutral, p_bear]
    ])
    max_entropy = np.log(3)  # 完全均匀分布的熵
    direction_convergence = 1 - (direction_entropy / max_entropy)
    
    print(f"\n  方向收敛度指标:")
    print(f"  - 方向熵: {direction_entropy:.3f} / {max_entropy:.3f}")
    print(f"  - 收敛度: {direction_convergence*100:.1f}%")
    
    if direction_convergence > 0.5:
        print(f"  ✅ 方向收敛良好（>50%）")
    elif direction_convergence > 0.3:
        print(f"  ⚠️  方向收敛中等（30-50%）")
    else:
        print(f"  ❌ 方向收敛不足（<30%）")
    
    # 期望的方向（基于市场类型）
    if 'bull' in market_name.lower():
        expected_direction = 'bull'
        expected_bias_range = (0.6, 1.0)
    elif 'bear' in market_name.lower():
        expected_direction = 'bear'
        expected_bias_range = (0.0, 0.4)
    else:  # range
        expected_direction = 'neutral'
        expected_bias_range = (0.4, 0.6)
    
    # 计算收敛到期望方向的比例
    if expected_direction == 'bull':
        converged_ratio = bulls_all / len(df)
    elif expected_direction == 'bear':
        converged_ratio = bears_all / len(df)
    else:
        converged_ratio = neutral_all / len(df)
    
    print(f"\n  期望方向: {expected_direction.upper()}")
    print(f"  收敛到期望方向的比例: {converged_ratio*100:.1f}%")
    
    if converged_ratio > 0.7:
        print(f"  ✅ 强收敛（>70%）")
    elif converged_ratio > 0.5:
        print(f"  ⚠️  中等收敛（50-70%）")
    else:
        print(f"  ❌ 弱收敛（<50%）")
    
    # 3. Agent特征多样性分析
    print(f"\n【维度2：Agent特征多样性】")
    print("-"*80)
    
    param_names = [
        'position_size_base',
        'holding_preference',
        'directional_bias',
        'stop_loss_threshold',
        'take_profit_threshold',
        'trend_following_strength'
    ]
    
    print(f"\n  所有6个参数的标准差（多样性指标）:")
    print(f"  {'参数名':30} {'全体标准差':15} {'Top10%标准差':15}")
    print(f"  {'-'*30} {'-'*15} {'-'*15}")
    
    diversity_scores = {}
    for param in param_names:
        if param in df.columns:
            std_all = df[param].std()
            std_top = df_top[param].std()
            diversity_scores[param] = {'all': std_all, 'top': std_top}
            print(f"  {param:30} {std_all:15.3f} {std_top:15.3f}")
    
    # 平均多样性（排除directional_bias）
    non_direction_params = [p for p in param_names if p != 'directional_bias']
    avg_diversity_all = np.mean([diversity_scores[p]['all'] for p in non_direction_params if p in diversity_scores])
    avg_diversity_top = np.mean([diversity_scores[p]['top'] for p in non_direction_params if p in diversity_scores])
    
    print(f"\n  平均多样性（排除方向偏好）:")
    print(f"  - 全体: {avg_diversity_all:.3f}")
    print(f"  - Top10%: {avg_diversity_top:.3f}")
    
    if avg_diversity_all > 0.15:
        print(f"  ✅ 多样性良好（>0.15）")
    elif avg_diversity_all > 0.10:
        print(f"  ⚠️  多样性中等（0.10-0.15）")
    else:
        print(f"  ❌ 多样性不足（<0.10）")
    
    # 4. Top基因深度分析
    print(f"\n【维度3：Top基因 vs 期望方向】")
    print("-"*80)
    
    top10 = df.head(10)
    
    print(f"\n  Top 10基因详细数据:")
    print(f"  {'ROI':>10} {'PF':>8} {'交易数':>8} {'方向':>10} {'仓位':>8} {'持仓':>8} {'止损':>8}")
    print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
    
    for idx, row in top10.iterrows():
        roi = row['roi']
        pf = row['pf']
        trades = row['trade_count']
        bias = row['directional_bias']
        pos_size = row.get('position_size_base', 0)
        holding = row.get('holding_preference', 0)
        stop_loss = row.get('stop_loss_threshold', 0)
        
        print(f"  {roi*100:>9.2f}% {pf:>8.2f} {trades:>8} {bias:>10.3f} {pos_size:>8.3f} {holding:>8.3f} {stop_loss:>8.3f}")
    
    # 分析Top基因的方向是否符合期望
    top10_bias = top10['directional_bias'].values
    
    if expected_direction == 'bull':
        correct_direction = np.sum(top10_bias > 0.6)
    elif expected_direction == 'bear':
        correct_direction = np.sum(top10_bias < 0.4)
    else:
        correct_direction = np.sum((top10_bias >= 0.4) & (top10_bias <= 0.6))
    
    print(f"\n  Top 10基因中符合期望方向的数量: {correct_direction} / 10")
    
    if correct_direction >= 7:
        print(f"  ✅ Top基因方向正确（≥7/10）")
    elif correct_direction >= 5:
        print(f"  ⚠️  Top基因方向部分正确（5-6/10）")
    else:
        print(f"  ❌ Top基因方向错误（<5/10）")
    
    # 5. 综合评估
    print(f"\n【综合评估】")
    print("="*80)
    
    print(f"\n  目标：系统策略强收敛 + Agent特征强发散")
    print(f"  {'维度':30} {'评分':10} {'状态':10}")
    print(f"  {'-'*30} {'-'*10} {'-'*10}")
    
    # 评分1：方向收敛度
    score1 = converged_ratio * 100
    status1 = '✅' if score1 > 70 else ('⚠️' if score1 > 50 else '❌')
    print(f"  {'方向收敛到期望（目标>70%）':30} {score1:>9.1f}% {status1:>10}")
    
    # 评分2：特征多样性
    score2 = avg_diversity_all * 100
    status2 = '✅' if score2 > 15 else ('⚠️' if score2 > 10 else '❌')
    print(f"  {'特征多样性（目标>15%）':30} {score2:>9.1f}% {status2:>10}")
    
    # 评分3：Top基因方向正确率
    score3 = (correct_direction / 10) * 100
    status3 = '✅' if score3 >= 70 else ('⚠️' if score3 >= 50 else '❌')
    print(f"  {'Top基因方向正确（目标>70%）':30} {score3:>9.1f}% {status3:>10}")
    
    # 综合得分
    overall_score = (score1 * 0.4 + score2 * 0.3 + score3 * 0.3)
    
    print(f"\n  综合得分: {overall_score:.1f} / 100")
    
    if overall_score > 70:
        print(f"  ✅ 优秀：达到理论目标（系统策略强收敛 + Agent特征强发散）")
    elif overall_score > 50:
        print(f"  ⚠️  中等：部分达到理论目标，需要优化")
    else:
        print(f"  ❌ 不足：未达到理论目标，需要大幅优化")
    
    conn.close()
    
    return {
        'market': market_name,
        'direction_convergence': converged_ratio,
        'feature_diversity': avg_diversity_all,
        'top_direction_correctness': correct_direction / 10,
        'overall_score': overall_score
    }


def compare_markets(results: List[Dict]):
    """对比三种市场的表现"""
    
    print("\n" + "="*80)
    print("📊 三种市场对比分析")
    print("="*80 + "\n")
    
    print(f"{'市场':15} {'方向收敛':15} {'特征多样性':15} {'Top方向正确':15} {'综合得分':15}")
    print("-"*80)
    
    for r in results:
        print(f"{r['market']:15} {r['direction_convergence']*100:>14.1f}% {r['feature_diversity']*100:>14.1f}% {r['top_direction_correctness']*100:>14.1f}% {r['overall_score']:>14.1f}")
    
    print("")
    
    # 平均表现
    avg_convergence = np.mean([r['direction_convergence'] for r in results])
    avg_diversity = np.mean([r['feature_diversity'] for r in results])
    avg_correctness = np.mean([r['top_direction_correctness'] for r in results])
    avg_score = np.mean([r['overall_score'] for r in results])
    
    print(f"{'平均':15} {avg_convergence*100:>14.1f}% {avg_diversity*100:>14.1f}% {avg_correctness*100:>14.1f}% {avg_score:>14.1f}")
    
    print("\n" + "="*80)
    print("💡 优化建议")
    print("="*80 + "\n")
    
    suggestions = []
    
    # 建议1：方向收敛
    if avg_convergence < 0.7:
        suggestions.append({
            'issue': f'方向收敛不足（{avg_convergence*100:.1f}% < 70%）',
            'root_cause': '淘汰率太低或Immigration太频繁，错误方向Agent存活太久',
            'solution': [
                '提高淘汰率：30% → 50%',
                '降低Immigration频率：每10代 → 每20代',
                '提高精英比例：20% → 30%（加速正确方向繁殖）'
            ]
        })
    
    # 建议2：特征多样性
    if avg_diversity < 0.15:
        suggestions.append({
            'issue': f'特征多样性不足（{avg_diversity*100:.1f}% < 15%）',
            'root_cause': 'Mutation太弱或Immigration注入的Agent太相似',
            'solution': [
                '增强非方向参数的Mutation：1.0x → 1.2x',
                'Immigration时确保参数随机分布更广（扩大随机范围）',
                '保留更多精英基因的变种（增加Elite复制次数）'
            ]
        })
    
    # 建议3：Top基因方向
    if avg_correctness < 0.7:
        suggestions.append({
            'issue': f'Top基因方向正确率不足（{avg_correctness*100:.1f}% < 70%）',
            'root_cause': '训练周期不够或进化压力不足',
            'solution': [
                '增加训练周期：5000 → 10000',
                '提高进化频率：每50周期 → 每30周期',
                '使用更激进的淘汰策略（淘汰所有PF<1.0的Agent）'
            ]
        })
    
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            print(f"{i}. 【问题】{s['issue']}")
            print(f"   【原因】{s['root_cause']}")
            print(f"   【方案】")
            for solution in s['solution']:
                print(f"   - {solution}")
            print("")
    else:
        print("✅ 当前配置已经很好！无需优化。")
        print("")
    
    print("="*80 + "\n")


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print("\n" + "="*100)
    print("📊 Task 3.3 收敛度与多样性分析")
    print("="*100)
    print("")
    print("理论目标：系统策略强收敛 + Agent特征强发散")
    print("")
    print("="*100)
    
    results = []
    
    # 分析三种市场
    markets = [
        ('experience/task3_3_pure_bull.db', 'Pure Bull'),
        ('experience/task3_3_pure_bear.db', 'Pure Bear'),
        ('experience/task3_3_pure_range.db', 'Pure Range')
    ]
    
    for db_path, market_name in markets:
        try:
            result = analyze_single_market(db_path, market_name)
            results.append(result)
        except Exception as e:
            print(f"\n❌ {market_name} 分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 对比分析
    if len(results) == 3:
        compare_markets(results)
    
    print("✅ 分析完成！")

