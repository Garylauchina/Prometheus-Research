#!/usr/bin/env python3
"""
WorldSignature相似度计算演示

展示：
1. 相似度计算的实际过程
2. 不同市场间的相似度
3. 计算性能测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import json
import time
import numpy as np
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.world_signature_simple import WorldSignatureSimple


def test_similarity_calculation():
    """测试相似度计算"""
    print("="*80)
    print("🔬 WorldSignature相似度计算演示")
    print("="*80)
    
    # 连接数据库
    db = ExperienceDB("experience/gene_collection_v6.db")
    
    # 获取三种市场的WorldSignature样本
    cursor = db.conn.execute("""
        SELECT market_type, world_signature
        FROM best_genomes
        GROUP BY market_type
        LIMIT 3
    """)
    
    samples = {}
    for market_type, ws_json in cursor:
        ws = WorldSignatureSimple.from_dict(json.loads(ws_json))
        samples[market_type] = ws
    
    print("\n1. 获取样本：")
    for market, ws in samples.items():
        print(f"   {market}: trend={ws.vector[1]:.3f}, rsi={ws.vector[6]:.3f}")
    
    # 计算两两相似度
    print("\n2. 相似度矩阵：")
    print(f"\n{'':10s} {'牛市':>10s} {'熊市':>10s} {'震荡市':>10s}")
    print("-" * 50)
    
    for m1 in ['bull', 'bear', 'sideways']:
        row = [f"{m1:10s}"]
        for m2 in ['bull', 'bear', 'sideways']:
            if m1 in samples and m2 in samples:
                sim = samples[m1].similarity(samples[m2])
                row.append(f"{sim:>10.3f}")
            else:
                row.append(f"{'N/A':>10s}")
        print("".join(row))
    
    print("\n3. 解读：")
    if 'bull' in samples and 'bear' in samples:
        sim_bb = samples['bull'].similarity(samples['bear'])
        print(f"   牛市 vs 熊市: {sim_bb:.3f}")
        if sim_bb < 0.3:
            print(f"      → 极度不相似（可以轻松区分）✅")
        elif sim_bb < 0.5:
            print(f"      → 不相似（容易区分）✅")
        else:
            print(f"      → 较相似（可能难区分）⚠️")
    
    if 'bull' in samples and 'sideways' in samples:
        sim_bs = samples['bull'].similarity(samples['sideways'])
        print(f"   牛市 vs 震荡: {sim_bs:.3f}")
        if sim_bs < 0.5:
            print(f"      → 不相似（容易区分）✅")
        elif sim_bs < 0.7:
            print(f"      → 中等相似（需要阈值调整）⚠️")
        else:
            print(f"      → 很相似（难以区分）❌")
    
    db.close()


def test_query_performance():
    """测试查询性能"""
    print("\n" + "="*80)
    print("⚡ 查询性能测试")
    print("="*80)
    
    db = ExperienceDB("experience/gene_collection_v6.db")
    
    # 获取一个牛市的WorldSignature作为查询条件
    cursor = db.conn.execute("""
        SELECT world_signature
        FROM best_genomes
        WHERE market_type = 'bull'
        LIMIT 1
    """)
    ws_json = cursor.fetchone()[0]
    current_ws = WorldSignatureSimple.from_dict(json.loads(ws_json))
    
    # 测试查询性能
    print(f"\n查询条件: trend={current_ws.vector[1]:.3f}, rsi={current_ws.vector[6]:.3f}")
    print(f"数据库记录数: 300条")
    
    # 执行查询
    start = time.time()
    results = db.query_similar_genomes(
        current_ws=current_ws,
        top_k=10,
        min_similarity=0.7
    )
    end = time.time()
    
    print(f"\n查询结果:")
    print(f"   耗时: {(end - start) * 1000:.2f}ms")
    print(f"   找到: {len(results)}个相似记录")
    
    if results:
        print(f"\n前3个相似记录:")
        for i, result in enumerate(results[:3], 1):
            print(f"   #{i} 相似度: {result['similarity']:.3f}, ROI: {result['roi']*100:+.1f}%")
    
    # 性能评估
    if (end - start) < 0.05:
        print(f"\n✅ 性能评估: 优秀（< 50ms）")
    elif (end - start) < 0.1:
        print(f"\n✅ 性能评估: 良好（< 100ms）")
    else:
        print(f"\n⚠️ 性能评估: 需要优化（> 100ms）")
    
    db.close()


def test_weighted_similarity():
    """测试加权相似度的效果"""
    print("\n" + "="*80)
    print("⚖️ 加权 vs 非加权相似度对比")
    print("="*80)
    
    # 创建两个WorldSignature
    ws1 = WorldSignatureSimple(np.array([
        0.13,  # trend_7d
        0.13,  # trend_30d
        0.13,  # trend_strength
        0.003, # volatility_7d
        0.003, # volatility_30d
        0.005, # atr
        0.97,  # rsi
        0.03,  # macd
        0.13,  # momentum_7d
        0.13,  # momentum_30d
        0.69,  # volume_ratio
        -0.12, # volume_trend
        2.0,   # market_phase
        0.0    # crash_signal
    ]))
    
    ws2 = WorldSignatureSimple(np.array([
        0.12,  # trend_7d (略低)
        0.12,  # trend_30d (略低)
        0.12,  # trend_strength
        0.004, # volatility_7d (略高)
        0.004, # volatility_30d
        0.006, # atr
        0.95,  # rsi (略低)
        0.02,  # macd
        0.12,  # momentum_7d
        0.12,  # momentum_30d
        0.70,  # volume_ratio
        -0.10, # volume_trend
        2.0,   # market_phase
        0.0    # crash_signal
    ]))
    
    # 计算非加权相似度
    sim_unweighted = ws1.similarity(ws2)
    
    print(f"\n两个牛市WorldSignature:")
    print(f"   WS1: trend=0.130, rsi=0.970")
    print(f"   WS2: trend=0.120, rsi=0.950")
    print(f"\n非加权相似度: {sim_unweighted:.4f}")
    
    # 手动计算加权相似度（演示）
    weights = np.array([
        2.0,  # trend_7d ← 重要
        3.0,  # trend_30d ← 最重要！
        2.0,  # trend_strength
        1.5,  # volatility_7d
        1.5,  # volatility_30d
        1.0,  # atr
        2.5,  # rsi ← 很重要！
        1.5,  # macd
        1.5,  # momentum_7d
        2.0,  # momentum_30d
        1.0,  # volume_ratio
        1.0,  # volume_trend
        2.0,  # market_phase
        3.0   # crash_signal ← 崩盘信号最重要！
    ])
    
    weighted_v1 = ws1.vector * weights
    weighted_v2 = ws2.vector * weights
    
    dot = np.dot(weighted_v1, weighted_v2)
    norm1 = np.linalg.norm(weighted_v1)
    norm2 = np.linalg.norm(weighted_v2)
    sim_weighted = dot / (norm1 * norm2)
    
    print(f"加权相似度:   {sim_weighted:.4f}")
    print(f"差异:         {abs(sim_weighted - sim_unweighted):.4f}")
    
    if sim_weighted > sim_unweighted:
        print(f"\n→ 加权后相似度更高（权重突出了相似的重要维度）")
    else:
        print(f"\n→ 加权后相似度更低（权重突出了差异的重要维度）")


if __name__ == '__main__':
    test_similarity_calculation()
    test_query_performance()
    test_weighted_similarity()

