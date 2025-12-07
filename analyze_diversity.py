#!/usr/bin/env python3
"""
🔍 多样性警告分析
============================================================================
目标：分析"多样性过低"警告是否正常

当前警告：
- 基因熵过低: 0.155 < 2.000
- 血统熵过低: 2.118 < 2.500  
- 活跃家族过少: 4-8 < 10
- 综合得分过低: 0.429 < 0.500

分析内容：
1. 这些指标的含义
2. 为什么会出现这些值
3. 是否正常
4. 如何改进
============================================================================
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from scipy.stats import entropy as shannon_entropy

from prometheus.facade.v6_facade import run_scenario

logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

def analyze_diversity_in_detail(facade):
    """详细分析种群多样性"""
    print("\n" + "="*80)
    print("🔬 详细多样性分析")
    print("="*80)
    
    agents = facade.moirai.agents
    
    # 1. 基因多样性分析
    print("\n【1. 基因多样性】")
    print("-"*80)
    
    gene_vectors = []
    for agent in agents:
        if hasattr(agent, 'genome') and agent.genome:
            # 获取已解锁的基因向量
            unlocked_params = agent.genome.to_dict()
            if unlocked_params:
                gene_vectors.append(list(unlocked_params.values()))
    
    if gene_vectors:
        gene_vectors = np.array(gene_vectors)
        print(f"Agent数量: {len(agents)}")
        print(f"基因维度: {gene_vectors.shape[1] if len(gene_vectors.shape) > 1 else 0}")
        
        # 计算基因熵（每个维度）
        if len(gene_vectors.shape) > 1 and gene_vectors.shape[1] > 0:
            gene_entropies = []
            for i in range(gene_vectors.shape[1]):
                # 离散化基因值（分成10个bin）
                hist, _ = np.histogram(gene_vectors[:, i], bins=10, range=(0, 1))
                hist = hist + 1e-10  # 避免log(0)
                hist = hist / hist.sum()
                ent = shannon_entropy(hist, base=2)
                gene_entropies.append(ent)
            
            avg_gene_entropy = np.mean(gene_entropies)
            print(f"平均基因熵: {avg_gene_entropy:.3f}")
            print(f"理论最大值: {np.log2(10):.3f} (10个bins)")
            print(f"达到率: {avg_gene_entropy/np.log2(10)*100:.1f}%")
            
            # 分析基因差异
            from scipy.spatial.distance import pdist
            distances = pdist(gene_vectors, metric='euclidean')
            print(f"平均基因距离: {np.mean(distances):.3f}")
            print(f"基因距离标准差: {np.std(distances):.3f}")
            
            if avg_gene_entropy < 2.0:
                print(f"⚠️ 基因熵低于阈值2.0！")
                print(f"   原因可能：")
                print(f"   1. 解锁的基因参数太少（只有{gene_vectors.shape[1]}个）")
                print(f"   2. 基因值过于集中（变异不足）")
                print(f"   3. 进化选择压力太强（淘汰了多样性）")
        else:
            print("⚠️ 基因向量为空或维度为0")
    
    # 2. 血统多样性分析
    print("\n【2. 血统多样性】")
    print("-"*80)
    
    family_counts = {}
    for agent in agents:
        if hasattr(agent, 'lineage') and agent.lineage:
            family_id = agent.lineage.family_id
            family_counts[family_id] = family_counts.get(family_id, 0) + 1
    
    active_families = len(family_counts)
    print(f"活跃家族数: {active_families}")
    print(f"理论最大值: {facade.num_families if hasattr(facade, 'num_families') else 50}")
    print(f"家族分布:")
    
    for family_id, count in sorted(family_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / len(agents) * 100
        print(f"  家族{family_id}: {count}个Agent ({pct:.1f}%)")
    
    # 计算血统熵
    family_probs = np.array(list(family_counts.values())) / len(agents)
    lineage_entropy = shannon_entropy(family_probs, base=2)
    print(f"\n血统熵: {lineage_entropy:.3f}")
    print(f"理论最大值: {np.log2(active_families):.3f}")
    print(f"达到率: {lineage_entropy/np.log2(active_families)*100:.1f}%" if active_families > 1 else "N/A")
    
    if active_families < 10:
        print(f"⚠️ 活跃家族少于阈值10！")
        print(f"   原因可能：")
        print(f"   1. 初始家族数太少")
        print(f"   2. 某些家族被完全淘汰")
        print(f"   3. Immigration机制未启动")
    
    # 3. 策略多样性分析
    print("\n【3. 策略多样性】")
    print("-"*80)
    
    # 分析Agent的交易行为
    long_agents = 0
    short_agents = 0
    no_position = 0
    
    for agent in agents:
        if hasattr(agent, 'account') and agent.account:
            ledger = agent.account.private_ledger
            if ledger.long_position and ledger.long_position.amount > 0:
                long_agents += 1
            elif ledger.short_position and ledger.short_position.amount > 0:
                short_agents += 1
            else:
                no_position += 1
    
    print(f"持仓分布:")
    print(f"  多头: {long_agents} ({long_agents/len(agents)*100:.1f}%)")
    print(f"  空头: {short_agents} ({short_agents/len(agents)*100:.1f}%)")
    print(f"  无持仓: {no_position} ({no_position/len(agents)*100:.1f}%)")
    
    # 计算策略熵
    position_counts = [long_agents, short_agents, no_position]
    position_probs = np.array([c for c in position_counts if c > 0]) / len(agents)
    strategy_entropy = shannon_entropy(position_probs, base=2)
    print(f"\n策略熵: {strategy_entropy:.3f}")
    print(f"理论最大值: {np.log2(3):.3f} (3种策略)")
    print(f"达到率: {strategy_entropy/np.log2(3)*100:.1f}%")
    
    # 4. 综合评估
    print("\n" + "="*80)
    print("💡 综合评估")
    print("="*80)
    
    issues = []
    recommendations = []
    
    if gene_vectors.shape[1] < 5:
        issues.append(f"基因参数太少（{gene_vectors.shape[1]}个），应该≥10个")
        recommendations.append("增加解锁的基因参数数量")
    
    if avg_gene_entropy < 2.0:
        issues.append(f"基因熵过低（{avg_gene_entropy:.2f}），基因值过于集中")
        recommendations.append("增加变异率或变异强度")
    
    if active_families < 10:
        issues.append(f"活跃家族过少（{active_families}个），种群单一化")
        recommendations.append("启动Immigration机制，引入新家族")
    
    if lineage_entropy < 2.5:
        issues.append(f"血统熵过低（{lineage_entropy:.2f}），家族分布不均")
        recommendations.append("保护弱势家族，降低淘汰率")
    
    print("\n发现的问题：")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n改进建议：")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    # 5. 判断是否正常
    print("\n" + "="*80)
    print("🎯 结论")
    print("="*80)
    
    if len(issues) == 0:
        print("✅ 多样性健康，警告为误报")
    elif len(issues) <= 2:
        print("⚠️ 有一些多样性问题，但可能在可接受范围内")
        print("   特别是在进化早期，多样性下降是正常的")
    else:
        print("❌ 多样性严重不足，需要立即改进")
        print("   这会影响系统的探索能力和收敛性")
    
    return {
        'gene_entropy': avg_gene_entropy if 'avg_gene_entropy' in locals() else 0,
        'lineage_entropy': lineage_entropy,
        'strategy_entropy': strategy_entropy,
        'active_families': active_families,
        'issues_count': len(issues)
    }

def main():
    print("="*80)
    print("🔍 Prometheus多样性警告分析")
    print("="*80)
    print()
    
    # 运行一次测试
    print("🚀 运行测试（200周期，50 Agent）...")
    prices = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')['close'].tolist()[:200]
    market_feed = lambda c: ({'price': prices[min(c-1, len(prices)-1)]}, {})
    
    facade = run_scenario(
        mode="backtest",
        total_cycles=200,
        market_feed=market_feed,
        num_families=50,
        agent_count=50,
        capital_per_agent=10000.0,
        scenario="diversity_analysis",
        evo_interval=30,
        seed=7001,
        evolution_seed=None
    )
    
    # 详细分析
    result = analyze_diversity_in_detail(facade)
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

