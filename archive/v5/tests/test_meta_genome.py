#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试元基因组系统"""

import sys
sys.path.insert(0, '.')

from prometheus.core.meta_genome import MetaGenome, MetaGenomeEvolution

print("="*70)
print("元基因组测试")
print("="*70)

# 1. 创建创世元基因组
print("\n[测试1] 创建创世元基因组")
print("-"*70)

meta1 = MetaGenome.create_genesis()
meta2 = MetaGenome.create_genesis()

print("\n父母1的决策风格:")
print(f"  {meta1.describe_decision_style()}")
print(f"  Daimon权重: {meta1.get_daimon_weights()}")

print("\n父母2的决策风格:")
print(f"  {meta2.describe_decision_style()}")
print(f"  Daimon权重: {meta2.get_daimon_weights()}")

# 2. 交叉繁殖
print("\n[测试2] 交叉繁殖")
print("-"*70)

child = MetaGenome.crossover(meta1, meta2)

print("\n子代的决策风格:")
print(f"  {child.describe_decision_style()}")
print(f"  Daimon权重: {child.get_daimon_weights()}")

# 3. 变异
print("\n[测试3] 变异")
print("-"*70)

print(f"变异前: {child.daimon_strategy_weight:.3f}")
child.mutate(mutation_rate=0.5)  # 50%变异率（测试用）
print(f"变异后: {child.daimon_strategy_weight:.3f}")
print(f"新风格: {child.describe_decision_style()}")

# 4. 多样性测试
print("\n[测试4] 种群多样性")
print("-"*70)

# 创建10个随机元基因组
population = [MetaGenome.create_genesis() for _ in range(10)]

diversity = MetaGenomeEvolution.calculate_diversity(population)
print(f"种群多样性: {diversity:.4f}")

# 5. 决策风格分布
print("\n[测试5] 决策风格分布")
print("-"*70)

for i, mg in enumerate(population, 1):
    print(f"  Agent_{i}: {mg.describe_decision_style()}")

# 6. 策略偏好测试
print("\n[测试6] 策略偏好")
print("-"*70)

for i in range(3):
    mg = population[i]
    prefs = mg.get_strategy_preferences()
    print(f"\nAgent_{i+1}:")
    for strategy, pref in prefs.items():
        print(f"  {strategy:20s}: {pref:.1%}")

# 7. 序列化测试
print("\n[测试7] 序列化与反序列化")
print("-"*70)

meta = MetaGenome.create_genesis()
print(f"原始: {meta.describe_decision_style()}")

# 转换为字典
data = meta.to_dict()
print(f"字典化: {len(data)}个字段")

# 从字典恢复
meta_restored = MetaGenome.from_dict(data)
print(f"恢复: {meta_restored.describe_decision_style()}")

print("\n" + "="*70)
print("✅ 元基因组测试完成")
print("="*70)

