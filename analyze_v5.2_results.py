"""
分析v5.2完整测试结果

Author: Prometheus Team
Version: v5.2
Date: 2025-12-05
"""

import pandas as pd
import numpy as np

print("="*80)
print("📊 v5.2完整测试结果分析")
print("="*80)
print()

# 读取结果
df = pd.read_csv('v5.2_full_stress_results.csv')

INITIAL_POPULATION = 50
INITIAL_CAPITAL = 10000.0
CYCLES = len(df)

# ============================================================================
# 1. 种群波动分析 (Day 1特性)
# ============================================================================
print("1️⃣  种群波动分析 (v5.2 Day 1特性)")
print("="*80)
print()

growth_cycles = (df['population_change'] > 0).sum()
shrink_cycles = (df['population_change'] < 0).sum()
stable_cycles = (df['population_change'] == 0).sum()

final_population = df['population_after'].iloc[-1]
survival_rate = final_population / INITIAL_POPULATION

print(f"初始种群: {INITIAL_POPULATION}个Agent")
print(f"最终种群: {final_population}个Agent")
print(f"存活率: {survival_rate:.1%}")
print()

print(f"种群动态:")
print(f"  增长周期: {growth_cycles}/{CYCLES} ({growth_cycles/CYCLES:.1%})")
print(f"  萎缩周期: {shrink_cycles}/{CYCLES} ({shrink_cycles/CYCLES:.1%})")
print(f"  平衡周期: {stable_cycles}/{CYCLES} ({stable_cycles/CYCLES:.1%})")
print()

# 种群波动范围
max_pop = df['population_after'].max()
min_pop = df['population_after'].min()
fluctuation_range = max_pop - min_pop

print(f"种群波动范围:")
print(f"  最高: {max_pop}个 ({max_pop/INITIAL_POPULATION:.1%})")
print(f"  最低: {min_pop}个 ({min_pop/INITIAL_POPULATION:.1%})")
print(f"  波动幅度: {fluctuation_range}个 ({fluctuation_range/INITIAL_POPULATION:.1%})")
print()

# 判断
population_pass = survival_rate >= 0.80
fluctuation_pass = growth_cycles > 0 and shrink_cycles > 0

if population_pass:
    print("  ✅ 种群稳定性：存活率>80%")
else:
    print(f"  ❌ 种群稳定性：存活率{survival_rate:.1%}<80%")

if fluctuation_pass:
    print("  ✅ 真实波动：有增有减")
else:
    print("  ⚠️ 波动不足：缺少增长或萎缩")

print()

# ============================================================================
# 2. 市场噪声影响分析 (Day 2特性)
# ============================================================================
print("2️⃣  市场噪声影响分析 (v5.2 Day 2特性)")
print("="*80)
print()

total_noise_events = df['noise_events'].sum()
avg_noise_per_cycle = total_noise_events / CYCLES
cycles_with_noise = (df['noise_events'] > 0).sum()

print(f"总噪声事件: {total_noise_events}次")
print(f"平均每轮: {avg_noise_per_cycle:.2f}次")
print(f"触发噪声的周期: {cycles_with_noise}/{CYCLES} ({cycles_with_noise/CYCLES:.1%})")
print()

# 预期（moderate模式）
# 流动性冲击5% + 滑点尖峰10% + 资金费率3% + 订单簿断层8% = 26%总概率
# 每轮期望事件数 = 0.26次（单个事件）到 0.26*4（如果全独立）
# 实际上，由于是独立判断，期望约为 0.05+0.10+0.03+0.08 = 0.26次/轮
# 15轮期望约 3.9次

expected_events_per_cycle = 0.05 + 0.10 + 0.03 + 0.08  # 26%概率
expected_total_events = expected_events_per_cycle * CYCLES

print(f"预期（moderate模式）:")
print(f"  每轮期望: {expected_events_per_cycle:.2f}次")
print(f"  总计期望: {expected_total_events:.1f}次")
print()

noise_ratio = total_noise_events / expected_total_events if expected_total_events > 0 else 0

if noise_ratio >= 0.5:
    print(f"  ✅ 噪声触发率: {noise_ratio:.1%}（接近预期）")
    noise_pass = True
elif total_noise_events > 0:
    print(f"  ⚠️ 噪声触发率: {noise_ratio:.1%}（低于预期，但有触发）")
    noise_pass = True
else:
    print(f"  ❌ 噪声未触发")
    noise_pass = False

print()

# ============================================================================
# 3. 基因多样性维持
# ============================================================================
print("3️⃣  基因多样性维持")
print("="*80)
print()

initial_gene_entropy = df['gene_entropy'].iloc[0]
final_gene_entropy = df['gene_entropy'].iloc[-1]
min_gene_entropy = df['gene_entropy'].min()
max_gene_entropy = df['gene_entropy'].max()
entropy_change = final_gene_entropy - initial_gene_entropy
entropy_change_pct = entropy_change / initial_gene_entropy

print(f"基因熵:")
print(f"  初始: {initial_gene_entropy:.3f}")
print(f"  最终: {final_gene_entropy:.3f}")
print(f"  变化: {entropy_change:+.3f} ({entropy_change_pct:+.1%})")
print(f"  最低: {min_gene_entropy:.3f}")
print(f"  最高: {max_gene_entropy:.3f}")
print(f"  波动范围: {max_gene_entropy - min_gene_entropy:.3f}")
print()

initial_lineage_entropy = df['lineage_entropy'].iloc[0]
final_lineage_entropy = df['lineage_entropy'].iloc[-1]

print(f"血统熵:")
print(f"  初始: {initial_lineage_entropy:.3f}")
print(f"  最终: {final_lineage_entropy:.3f}")
print(f"  变化: {final_lineage_entropy - initial_lineage_entropy:+.3f}")
print()

diversity_pass = abs(entropy_change_pct) <= 0.15

if diversity_pass:
    print(f"  ✅ 基因多样性维持良好（变化<15%）")
else:
    print(f"  ⚠️ 基因多样性波动较大（变化{abs(entropy_change_pct):.1%}>15%）")

print()

# ============================================================================
# 4. 资金变化
# ============================================================================
print("4️⃣  资金变化")
print("="*80)
print()

initial_capital = df['avg_capital'].iloc[0]
final_capital = df['avg_capital'].iloc[-1]
capital_change = final_capital - initial_capital
capital_change_pct = capital_change / initial_capital

print(f"平均资金:")
print(f"  初始: ${initial_capital:.2f}")
print(f"  最终: ${final_capital:.2f}")
print(f"  变化: ${capital_change:+.2f} ({capital_change_pct:+.1%})")
print()

# 资金波动
max_capital = df['avg_capital'].max()
min_capital = df['avg_capital'].min()

print(f"资金波动:")
print(f"  最高: ${max_capital:.2f}")
print(f"  最低: ${min_capital:.2f}")
print(f"  波动幅度: ${max_capital - min_capital:.2f}")
print()

if capital_change_pct > 0:
    print(f"  ✅ 平均盈利: +{capital_change_pct:.1%}")
else:
    print(f"  ⚠️ 平均亏损: {capital_change_pct:.1%}")

print()

# ============================================================================
# 5. 健康状态分析
# ============================================================================
print("5️⃣  系统健康状态")
print("="*80)
print()

health_counts = df['health'].value_counts()

print(f"健康状态分布:")
for health_status, count in health_counts.items():
    print(f"  {health_status}: {count}/{CYCLES} ({count/CYCLES:.1%})")
print()

# ============================================================================
# 6. 成功标准判断
# ============================================================================
print("="*80)
print("🏁 v5.2成功标准判断")
print("="*80)
print()

all_pass = True

if population_pass:
    print("  ✅ 种群稳定（存活率>80%）")
else:
    print("  ❌ 种群萎缩过多")
    all_pass = False

if fluctuation_pass:
    print("  ✅ 真实波动（有增有减）")
else:
    print("  ❌ 波动不足")
    all_pass = False

if noise_pass:
    print("  ✅ 市场噪声应用")
else:
    print("  ❌ 市场噪声未触发")
    all_pass = False

if diversity_pass:
    print("  ✅ 基因多样性维持")
else:
    print("  ❌ 基因多样性波动过大")
    all_pass = False

print()

if all_pass:
    print("="*80)
    print("🎉 v5.2完整测试通过！")
    print("="*80)
    print()
    print("主要成果:")
    print(f"  ✅ Day 1改进（种群波动+变异率随机化）：正常工作")
    print(f"  ✅ Day 2改进（市场噪声层）：正常工作")
    print(f"  ✅ 种群存活率: {survival_rate:.1%}")
    print(f"  ✅ 基因多样性维持: {entropy_change_pct:+.1%}")
    print(f"  ✅ 平均资金增长: {capital_change_pct:+.1%}")
    print()
    print("🌪️ v5.2已成功引入可控的混乱！")
else:
    print("="*80)
    print("⚠️ v5.2测试部分通过")
    print("="*80)
    print()
    print("需要关注的问题:")
    if not population_pass:
        print(f"  - 种群存活率偏低（{survival_rate:.1%}）")
    if not fluctuation_pass:
        print(f"  - 种群波动不足")
    if not noise_pass:
        print(f"  - 市场噪声触发率低（{total_noise_events}次，预期{expected_total_events:.0f}次）")
    if not diversity_pass:
        print(f"  - 基因多样性波动较大")

print()

# ============================================================================
# 7. 噪声事件详细分析
# ============================================================================
if total_noise_events < expected_total_events * 0.5:
    print("="*80)
    print("⚠️ 噪声事件触发率偏低分析")
    print("="*80)
    print()
    print(f"实际触发: {total_noise_events}次")
    print(f"预期触发: {expected_total_events:.0f}次")
    print(f"差距: {expected_total_events - total_noise_events:.0f}次")
    print()
    print("可能原因:")
    print("  1. 随机波动（15轮样本较小）")
    print("  2. 代码中噪声应用有问题")
    print("  3. 噪声事件记录有误")
    print()
    print("建议:")
    print("  1. 运行更多轮次（50-100轮）验证")
    print("  2. 检查日志中的噪声事件警告")
    print("  3. 使用'high'或'extreme'预设提高触发率")
    print()

