#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus v5.1 极端压力测试 - 批量版本

运行多次测试，取平均值，减少随机性影响
"""

import os
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("🔥 Prometheus v5.1 极端压力测试 - 批量版本")
print("="*80)
print()

# 配置
NUM_RUNS = 3  # 运行3次测试
RESULT_FILE = 'extreme_stress_test_results.csv'
BATCH_RESULT_FILE = f'extreme_stress_batch_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

all_results = []

for run in range(1, NUM_RUNS + 1):
    print(f"\n{'='*80}")
    print(f"📊 运行测试 {run}/{NUM_RUNS}")
    print(f"{'='*80}\n")
    
    # 运行测试
    result = subprocess.run(['python', 'test_extreme_stress.py'], 
                          capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ 测试{run}失败")
        continue
    
    # 读取结果
    if os.path.exists(RESULT_FILE):
        df = pd.read_csv(RESULT_FILE)
        df['run'] = run
        all_results.append(df)
        print(f"✅ 测试{run}完成")
    else:
        print(f"❌ 未找到测试{run}的结果文件")

print(f"\n{'='*80}")
print("📊 批量测试完成，分析结果...")
print(f"{'='*80}\n")

if not all_results:
    print("❌ 没有有效的测试结果")
    exit(1)

# 合并所有结果
all_df = pd.concat(all_results, ignore_index=True)
all_df.to_csv(BATCH_RESULT_FILE, index=False)
print(f"💾 所有结果已保存: {BATCH_RESULT_FILE}")

# 分析统计
print("\n" + "="*80)
print("📈 统计分析")
print("="*80)

for cycle in range(1, 11):
    cycle_data = all_df[all_df['cycle'] == cycle]
    mean_entropy = cycle_data['gene_entropy'].mean()
    std_entropy = cycle_data['gene_entropy'].std()
    min_entropy = cycle_data['gene_entropy'].min()
    max_entropy = cycle_data['gene_entropy'].max()
    
    print(f"\n轮次 {cycle:2d}:")
    print(f"  基因熵: {mean_entropy:.3f} ± {std_entropy:.3f} (范围: {min_entropy:.3f} - {max_entropy:.3f})")

# 第10轮统计
final_cycle = all_df[all_df['cycle'] == 10]
print(f"\n{'='*80}")
print(f"🎯 第10轮统计 (n={len(final_cycle)})")
print(f"{'='*80}")
print(f"基因熵: {final_cycle['gene_entropy'].mean():.3f} ± {final_cycle['gene_entropy'].std():.3f}")
print(f"血统熵: {final_cycle['lineage_entropy'].mean():.3f} ± {final_cycle['lineage_entropy'].std():.3f}")
print(f"平均盈亏: ${final_cycle['avg_pnl'].mean():.2f} ± ${final_cycle['avg_pnl'].std():.2f}")

# 健康状态分布
health_counts = final_cycle['health'].value_counts()
print(f"\n健康状态分布:")
for health, count in health_counts.items():
    print(f"  {health}: {count}/{len(final_cycle)} ({count/len(final_cycle)*100:.0f}%)")

print(f"\n{'='*80}")
print("✅ 批量测试分析完成")
print(f"{'='*80}")

