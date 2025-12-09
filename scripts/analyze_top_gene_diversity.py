"""
分析v2 Top基因的多样性（移植性指标）
==========================================

目标：
验证Top基因是否多样化，评估移植性

关键指标：
- 平均成对距离（avg_pairwise_distance）
- 目标：> 0.4（理想 > 0.5）

决策逻辑：
- avg_dist > 0.4 → ✅ 移植性好，使用基础v3配置
- 0.3 < avg_dist < 0.4 → ⚠️ 移植性中等，微调v3配置
- avg_dist < 0.3 → ❌ 移植性差，增强v3配置
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
from scipy.spatial.distance import pdist
from typing import List, Dict


def analyze_top_gene_diversity(db_path: str, market_name: str, top_k: int = 20):
    """
    分析Top K基因的多样性
    
    Args:
        db_path: ExperienceDB路径
        market_name: 市场名称
        top_k: Top K数量
    """
    
    print("\n" + "="*80)
    print(f"📊 {market_name} Top {top_k} 基因多样性分析")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    
    # 1. 加载Top K基因（按PF排序）
    cursor = conn.execute(f"""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
        ORDER BY profit_factor DESC
        LIMIT {top_k}
    """)
    
    top_genes = []
    for row in cursor:
        roi, pf, trade_count, genome_str = row
        genome_dict = json.loads(genome_str)
        top_genes.append({
            'roi': roi,
            'pf': pf,
            'trade_count': trade_count,
            **genome_dict
        })
    
    if len(top_genes) < top_k:
        print(f"⚠️ 只有{len(top_genes)}个基因（少于{top_k}个）")
        if len(top_genes) < 5:
            print(f"❌ 基因数量太少，无法分析")
            conn.close()
            return None
    
    print(f"\n【Top {len(top_genes)} 基因概览】")
    print(f"  平均PF: {np.mean([g['pf'] for g in top_genes]):.2f}")
    print(f"  PF范围: [{np.min([g['pf'] for g in top_genes]):.2f}, {np.max([g['pf'] for g in top_genes]):.2f}]")
    print(f"  平均ROI: {np.mean([g['roi'] for g in top_genes])*100:.2f}%")
    
    # 2. 提取6个参数向量
    param_names = [
        'position_size_base',
        'holding_preference',
        'directional_bias',
        'stop_loss_threshold',
        'take_profit_threshold',
        'trend_following_strength'
    ]
    
    vectors = []
    for gene in top_genes:
        vector = [gene.get(param, 0.5) for param in param_names]
        vectors.append(vector)
    
    vectors = np.array(vectors)
    
    # 3. 计算平均成对距离
    if len(vectors) < 2:
        print(f"❌ 向量数量不足，无法计算距离")
        conn.close()
        return None
    
    distances = pdist(vectors, metric='euclidean')
    avg_distance = np.mean(distances)
    min_distance = np.min(distances)
    max_distance = np.max(distances)
    
    print(f"\n【多样性指标（移植性）】")
    print(f"  平均成对距离: {avg_distance:.3f}")
    print(f"  最小距离: {min_distance:.3f}")
    print(f"  最大距离: {max_distance:.3f}")
    
    # 4. 评估移植性
    print(f"\n【移植性评估】")
    
    if avg_distance > 0.5:
        status = "✅✅ 极强"
        color = "🟢"
        recommendation = "使用基础v3配置"
    elif avg_distance > 0.4:
        status = "✅ 强"
        color = "🟢"
        recommendation = "使用基础v3配置"
    elif avg_distance > 0.3:
        status = "⚠️ 中等"
        color = "🟡"
        recommendation = "微调v3配置（轻度增强mutation）"
    elif avg_distance > 0.2:
        status = "❌ 弱"
        color = "🟠"
        recommendation = "增强v3配置（强化探索）"
    else:
        status = "❌❌ 极弱"
        color = "🔴"
        recommendation = "增强v3配置（强化探索+延长训练）"
    
    print(f"  移植性等级: {color} {status}")
    print(f"  建议: {recommendation}")
    
    # 5. 分析每个参数的分布（诊断）
    print(f"\n【参数分布诊断】")
    print(f"  {'参数名':30} {'均值':>10} {'标准差':>10} {'范围':>15}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*15}")
    
    for i, param in enumerate(param_names):
        values = vectors[:, i]
        mean_val = np.mean(values)
        std_val = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        
        print(f"  {param:30} {mean_val:>10.3f} {std_val:>10.3f} [{min_val:.2f}, {max_val:.2f}]")
    
    # 6. 识别高度相似的基因对（诊断）
    print(f"\n【高度相似基因对（距离<0.15）】")
    
    similar_pairs = []
    n = len(vectors)
    idx = 0
    for i in range(n):
        for j in range(i+1, n):
            if distances[idx] < 0.15:
                similar_pairs.append((i, j, distances[idx]))
            idx += 1
    
    if similar_pairs:
        print(f"  发现{len(similar_pairs)}对高度相似的基因:")
        for i, j, dist in similar_pairs[:5]:  # 只显示前5对
            print(f"    Gene {i+1} vs Gene {j+1}: 距离={dist:.3f}")
            if len(similar_pairs) > 5:
                print(f"  ... 还有{len(similar_pairs)-5}对")
        print(f"  ⚠️ 这些基因几乎相同，可能导致移植性差")
    else:
        print(f"  ✅ 没有高度相似的基因对（所有距离>0.15）")
    
    conn.close()
    
    return {
        'market': market_name,
        'top_k': len(top_genes),
        'avg_distance': avg_distance,
        'min_distance': min_distance,
        'max_distance': max_distance,
        'status': status,
        'recommendation': recommendation
    }


def recommend_v3_config(results: List[Dict]):
    """
    基于分析结果，推荐v3配置
    
    Args:
        results: 三种市场的分析结果
    """
    
    print("\n" + "="*100)
    print("🎯 v3配置建议")
    print("="*100 + "\n")
    
    # 计算平均移植性
    avg_distances = [r['avg_distance'] for r in results if r]
    avg_overall = np.mean(avg_distances) if avg_distances else 0
    
    print(f"【三种市场移植性汇总】\n")
    print(f"{'市场':15} {'平均距离':15} {'移植性':15} {'建议':40}")
    print("-"*100)
    
    for r in results:
        if r:
            print(f"{r['market']:15} {r['avg_distance']:>14.3f} {r['status']:15} {r['recommendation']:40}")
    
    print("-"*100)
    print(f"{'平均':15} {avg_overall:>14.3f}")
    print("")
    
    # 决策逻辑
    print(f"【最终建议】\n")
    
    if avg_overall > 0.4:
        print(f"✅ 平均移植性良好（{avg_overall:.3f} > 0.4）")
        print(f"\n建议配置：【基础v3】")
        print(f"```python")
        print(f"config = MockTrainingConfig(")
        print(f"    cycles=10000,              # +100%")
        print(f"    elimination_rate=0.5,      # +20%")
        print(f"    evolution_interval=30,     # -40%")
        print(f"    elite_ratio=0.3,           # +10%")
        print(f"    # 保持当前mutation和immigration")
        print(f")")
        print(f"```")
        print(f"\n预期效果：")
        print(f"  - 方向收敛度：35% → 75%")
        print(f"  - 移植性：保持 > 0.4")
        print(f"  - 训练时间：~40分钟")
        
    elif avg_overall > 0.3:
        print(f"⚠️ 平均移植性中等（{avg_overall:.3f} ∈ [0.3, 0.4]）")
        print(f"\n建议配置：【微调v3】")
        print(f"```python")
        print(f"config = MockTrainingConfig(")
        print(f"    cycles=12000,              # +140%（略微延长）")
        print(f"    elimination_rate=0.5,      # +20%")
        print(f"    evolution_interval=30,     # -40%")
        print(f"    elite_ratio=0.3,           # +10%")
        print(f"    # ✅ 轻度增强mutation")
        print(f"    # diversity_boost=1.2     # mutation幅度（需要在EvolutionManager中设置）")
        print(f")")
        print(f"```")
        print(f"\n预期效果：")
        print(f"  - 方向收敛度：35% → 70%")
        print(f"  - 移植性：0.35 → 0.45")
        print(f"  - 训练时间：~48分钟")
        
    else:
        print(f"❌ 平均移植性较差（{avg_overall:.3f} < 0.3）")
        print(f"\n建议配置：【增强v3】")
        print(f"```python")
        print(f"config = MockTrainingConfig(")
        print(f"    cycles=15000,              # +200%（大幅延长）")
        print(f"    elimination_rate=0.5,      # +20%")
        print(f"    evolution_interval=30,     # -40%")
        print(f"    elite_ratio=0.3,           # +10%")
        print(f"    # ✅ 强化探索")
        print(f"    # diversity_boost=1.5     # mutation幅度（需要在EvolutionManager中设置）")
        print(f"    # immigration_interval=15 # Immigration频率")
        print(f"    # immigration_count=10    # Immigration数量")
        print(f")")
        print(f"```")
        print(f"\n预期效果：")
        print(f"  - 方向收敛度：35% → 70%")
        print(f"  - 移植性：{avg_overall:.2f} → 0.50")
        print(f"  - 训练时间：~60分钟")
    
    print("\n" + "="*100)
    print("")


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print("\n" + "="*100)
    print("🔬 v2 Top基因多样性分析（移植性验证）")
    print("="*100)
    print("")
    print("目标：验证Top基因是否多样化，评估移植性")
    print("决策：根据移植性指标，确定v3配置方案")
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
            result = analyze_top_gene_diversity(db_path, market_name, top_k=20)
            results.append(result)
        except Exception as e:
            print(f"\n❌ {market_name} 分析失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(None)
    
    # 推荐v3配置
    recommend_v3_config(results)
    
    print("✅ 分析完成！请根据建议调整v3配置。")

