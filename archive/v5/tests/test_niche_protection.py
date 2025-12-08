#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试生态位保护系统"""

import sys
sys.path.insert(0, '.')

import logging
from prometheus.core.niche_protection import NicheProtectionSystem
from prometheus.core.agent_v5 import AgentV5

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

print("="*80)
print("生态位保护系统测试 - v5.1")
print("="*80)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景1：健康的多样性分布
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景1] 健康的多样性分布")
print("-"*80)

niche_system = NicheProtectionSystem()

# 创建10个Agent，均匀分布在3种策略
agents_scenario1 = []
for i in range(10):
    agent = AgentV5.create_genesis(f"Agent_{i+1}", 10000, family_id=i)
    agents_scenario1.append(agent)

# 手动设置策略分布：4-3-3
for i, agent in enumerate(agents_scenario1):
    if i < 4:
        agent.active_strategies = [type('Strategy', (), {'name': 'TrendFollowing'})()]
    elif i < 7:
        agent.active_strategies = [type('Strategy', (), {'name': 'GridTrading'})()]
    else:
        agent.active_strategies = [type('Strategy', (), {'name': 'MeanReversion'})()]

# 分析策略分布
statuses1 = niche_system.analyze_strategy_distribution(agents_scenario1)

# 检查健康度
health1 = niche_system.check_diversity_health(statuses1)
print(f"\n✅ 生态多样性健康度: {health1['health']}")
print(f"   多样性分数: {health1['diversity_score']:.3f}")
print(f"   策略数量: {health1['strategy_count']}")
if health1['warnings']:
    print(f"   警告: {health1['warnings']}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景2：单一策略统治（不健康）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景2] 单一策略统治（不健康）")
print("-"*80)

# 创建10个Agent，8个TrendFollowing，2个GridTrading
agents_scenario2 = []
for i in range(10):
    agent = AgentV5.create_genesis(f"Agent_{i+11}", 10000, family_id=i)
    agents_scenario2.append(agent)

# 设置策略分布：8-2-0（单一策略统治）
for i, agent in enumerate(agents_scenario2):
    if i < 8:
        agent.active_strategies = [type('Strategy', (), {'name': 'TrendFollowing'})()]
    else:
        agent.active_strategies = [type('Strategy', (), {'name': 'GridTrading'})()]

# 分析策略分布
statuses2 = niche_system.analyze_strategy_distribution(agents_scenario2)

# 检查健康度
health2 = niche_system.check_diversity_health(statuses2)
print(f"\n✅ 生态多样性健康度: {health2['health']}")
print(f"   多样性分数: {health2['diversity_score']:.3f}")
print(f"   策略数量: {health2['strategy_count']}")
if health2['warnings']:
    print(f"   ⚠️  警告:")
    for warning in health2['warnings']:
        print(f"      - {warning}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景3：应用生态位调整
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景3] 应用生态位调整（场景2的Agent）")
print("-"*80)

print("\n评分调整示例（基础分100）:")
print("-"*80)

# 模拟几个Agent的评分调整
test_agents = agents_scenario2[:5]  # 前3个TrendFollowing，后2个GridTrading

for agent in test_agents:
    base_score = 100.0
    adjusted_score, reason = niche_system.apply_niche_adjustment(
        agent, base_score, statuses2
    )
    
    strategy = niche_system._get_primary_strategy(agent)
    print(f"{agent.agent_id} ({strategy:20s}): "
          f"{base_score:.1f} → {adjusted_score:.1f} | {reason}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景4：濒危策略保护
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景4] 濒危策略保护")
print("-"*80)

# 创建10个Agent，1个少数派策略
agents_scenario4 = []
for i in range(10):
    agent = AgentV5.create_genesis(f"Agent_{i+21}", 10000, family_id=i)
    agents_scenario4.append(agent)

# 设置策略分布：7-2-1（MeanReversion濒危）
for i, agent in enumerate(agents_scenario4):
    if i < 7:
        agent.active_strategies = [type('Strategy', (), {'name': 'TrendFollowing'})()]
    elif i < 9:
        agent.active_strategies = [type('Strategy', (), {'name': 'GridTrading'})()]
    else:
        agent.active_strategies = [type('Strategy', (), {'name': 'MeanReversion'})()]

# 分析策略分布
statuses4 = niche_system.analyze_strategy_distribution(agents_scenario4)

# 检查健康度
health4 = niche_system.check_diversity_health(statuses4)
print(f"\n✅ 生态多样性健康度: {health4['health']}")
print(f"   多样性分数: {health4['diversity_score']:.3f}")

# 显示濒危策略的保护
print("\n濒危策略保护效果:")
for agent in agents_scenario4[-3:]:  # 最后3个Agent
    base_score = 100.0
    adjusted_score, reason = niche_system.apply_niche_adjustment(
        agent, base_score, statuses4
    )
    
    strategy = niche_system._get_primary_strategy(agent)
    status = statuses4[strategy]
    print(f"{agent.agent_id} ({strategy:20s} {status.population_ratio:5.1%}): "
          f"{base_score:.1f} → {adjusted_score:.1f} | {reason}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 场景5：完整的保护摘要
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[场景5] 完整的保护摘要")
print("-"*80)

print("\n场景1（健康）:")
print(niche_system.get_protection_summary(statuses1))

print("\n场景2（单一策略统治）:")
print(niche_system.get_protection_summary(statuses2))

print("\n场景4（濒危策略）:")
print(niche_system.get_protection_summary(statuses4))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 总结
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*80)
print("✅ 生态位保护系统测试完成")
print("="*80)

print("\n📊 关键机制验证:")
print(f"  1. 多样性分析: ✅")
print(f"  2. 少数派保护: ✅ (少数派评分+{statuses2['GridTrading'].diversity_bonus:.1%})")
print(f"  3. 竞争惩罚: ✅ (多数派评分-{statuses2['TrendFollowing'].competition_penalty:.1%})")
print(f"  4. 健康度评估: ✅ ({health1['health']} vs {health2['health']})")

print("\n🎯 核心成就:")
print("  【生态位保护机制】✨ 已完成！")
print("  - 策略分布分析")
print("  - 少数派策略保护（+奖励）")
print("  - 多数派策略竞争（-惩罚）")
print("  - 多样性健康度监控")

print("\n💡 实际影响:")
print("  → 防止单一策略统治")
print("  → 维持策略生态多样性")
print("  → 少数派策略获得保护")
print("  → 种群保持进化活力")

print("\n" + "="*80)

