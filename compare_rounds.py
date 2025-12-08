#!/usr/bin/env python3
"""
对比不同轮次的基因差异

分析内容：
1. 参数分布的一致性（均值、方差）
2. 进化收敛性（参数范围是否缩小）
3. Top基因的稳定性（是否出现相同模式）
4. 统计显著性检验

用法：
    python3 compare_rounds.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import json
import numpy as np
from prometheus.core.experience_db import ExperienceDB
from collections import defaultdict


def analyze_round_genes(db_path: str, market_type: str):
    """
    分析数据库中的基因，按时间戳分组（模拟round_id）
    
    Args:
        db_path: 数据库路径
        market_type: 市场类型
    """
    db = ExperienceDB(db_path)
    
    cursor = db.conn.execute("""
        SELECT genome, roi, sharpe, timestamp
        FROM best_genomes
        WHERE market_type = ?
        ORDER BY timestamp
    """, (market_type,))
    
    rows = cursor.fetchall()
    db.close()
    
    if not rows:
        print(f"❌ 没有{market_type}市场的数据")
        return None
    
    # 按时间戳分组（假设每批10个是一起保存的）
    from datetime import datetime
    
    genes_by_batch = []
    current_batch = []
    last_timestamp = None
    
    for genome_json, roi, sharpe, timestamp_str in rows:
        genome_dict = json.loads(genome_json)
        
        # 解析时间戳
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            # 如果解析失败，使用默认分组逻辑
            timestamp = None
        
        # 如果时间戳差距较大（超过10秒），认为是新一批
        if last_timestamp and timestamp:
            time_diff = (timestamp - last_timestamp).total_seconds()
            if time_diff > 10:
                if current_batch:
                    genes_by_batch.append(current_batch)
                    current_batch = []
        
        current_batch.append({
            'genome': genome_dict,
            'roi': roi,
            'sharpe': sharpe,
            'timestamp': timestamp_str
        })
        last_timestamp = timestamp
    
    if current_batch:
        genes_by_batch.append(current_batch)
    
    return genes_by_batch


def compare_parameter_distribution(batches: list, param_name: str):
    """
    对比不同批次的参数分布
    
    Args:
        batches: 基因批次列表
        param_name: 参数名
    """
    print(f"\n{'='*60}")
    print(f"📊 参数对比: {param_name}")
    print(f"{'='*60}")
    
    batch_stats = []
    
    for i, batch in enumerate(batches, 1):
        values = [g['genome'].get(param_name, 0.5) for g in batch]
        
        mean = np.mean(values)
        std = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        
        batch_stats.append({
            'batch': i,
            'mean': mean,
            'std': std,
            'min': min_val,
            'max': max_val,
            'range': max_val - min_val
        })
        
        print(f"\nBatch {i} (样本数: {len(values)}):")
        print(f"  均值: {mean:.3f}")
        print(f"  标准差: {std:.3f}")
        print(f"  范围: [{min_val:.3f}, {max_val:.3f}]")
        print(f"  区间宽度: {max_val - min_val:.3f}")
    
    # 计算批次间的一致性
    if len(batch_stats) > 1:
        means = [s['mean'] for s in batch_stats]
        mean_std = np.std(means)
        
        ranges = [s['range'] for s in batch_stats]
        avg_range = np.mean(ranges)
        range_trend = ranges[-1] - ranges[0] if len(ranges) > 1 else 0
        
        print(f"\n{'='*60}")
        print(f"🔍 一致性分析:")
        print(f"  批次间均值标准差: {mean_std:.3f}")
        if mean_std < 0.05:
            print(f"    → ✅ 非常一致（变异<0.05）")
        elif mean_std < 0.10:
            print(f"    → ✓ 较为一致（变异<0.10）")
        else:
            print(f"    → ⚠️ 差异较大（变异>0.10）")
        
        print(f"\n  区间宽度趋势: {range_trend:+.3f}")
        if abs(range_trend) < 0.05:
            print(f"    → ✅ 稳定（变化<0.05）")
        elif range_trend < 0:
            print(f"    → 📉 收敛（区间缩小 {range_trend:.3f}）")
        else:
            print(f"    → 📈 发散（区间扩大 {range_trend:+.3f}）")
    
    return batch_stats


def compare_top_performers(batches: list, top_k: int = 3):
    """
    对比不同批次的最佳基因
    
    Args:
        batches: 基因批次列表
        top_k: 前几名
    """
    print(f"\n{'='*60}")
    print(f"🏆 最佳基因对比 (Top {top_k})")
    print(f"{'='*60}")
    
    for i, batch in enumerate(batches, 1):
        # 按ROI排序
        sorted_batch = sorted(batch, key=lambda x: x['roi'], reverse=True)
        top_genes = sorted_batch[:top_k]
        
        print(f"\nBatch {i}:")
        for j, gene_data in enumerate(top_genes, 1):
            genome = gene_data['genome']
            print(f"  #{j} ROI: {gene_data['roi']*100:+.2f}%")
            print(f"      directional_bias: {genome.get('directional_bias', 0.5):.3f}")
            print(f"      position_size: {genome.get('position_size_base', 0.3):.3f}")
            print(f"      holding_pref: {genome.get('holding_preference', 0.5):.3f}")


def main():
    db_path = "experience/gene_collection_v6.db"
    
    # 检查数据库
    db = ExperienceDB(db_path)
    cursor = db.conn.execute("SELECT COUNT(*) FROM best_genomes")
    total_count = cursor.fetchone()[0]
    
    cursor = db.conn.execute("""
        SELECT market_type, COUNT(*) 
        FROM best_genomes 
        GROUP BY market_type
    """)
    market_counts = dict(cursor.fetchall())
    db.close()
    
    print("="*80)
    print("🔬 多轮基因对比分析")
    print("="*80)
    print(f"数据库: {db_path}")
    print(f"总基因数: {total_count}条")
    print(f"\n各市场分布:")
    for market, count in market_counts.items():
        print(f"  {market}: {count}条")
    
    # 分析各市场
    for market_type in ['bull', 'bear', 'sideways']:
        print(f"\n\n{'='*80}")
        print(f"🐂🐻📊 {market_type.upper()}市场分析")
        print(f"{'='*80}")
        
        batches = analyze_round_genes(db_path, market_type)
        
        if not batches:
            continue
        
        print(f"\n检测到 {len(batches)} 个训练批次")
        
        # 对比关键参数
        for param in ['directional_bias', 'position_size_base', 'holding_preference']:
            compare_parameter_distribution(batches, param)
        
        # 对比最佳基因
        compare_top_performers(batches)
    
    # 总结
    print(f"\n\n{'='*80}")
    print(f"💡 总结建议")
    print(f"{'='*80}")
    print(f"""
如果观察到：
✅ 批次间均值标准差 < 0.10 → 进化一致性好，找到了稳定的最优解
✅ 区间宽度收敛（缩小） → 进化在收敛，策略空间在优化
✅ Top基因参数相似 → 存在明显的优势策略模式

⚠️ 批次间差异大 > 0.15 → 随机性过强，考虑：
   - 增加训练周期数
   - 降低变异率
   - 增加种群规模

📈 区间宽度扩大 → 多样性探索中，可能：
   - 继续训练观察是否收敛
   - 检查是否有新的优势策略涌现
    """)


if __name__ == '__main__':
    main()

