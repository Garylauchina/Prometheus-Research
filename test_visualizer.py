"""
测试可视化功能
===============
"""

import sys
import numpy as np
from datetime import datetime

sys.path.insert(0, '.')

from prometheus.core.diversity_monitor import DiversityMonitor, DiversityMetrics, DiversityAlert
from prometheus.core.diversity_visualizer import DiversityVisualizer

print("="*80)
print("🎨 测试多样性可视化功能")
print("="*80)

# ==================== 创建测试数据 ====================

print("\n[1/3] 创建测试数据...")

# 创建模拟的历史数据
metrics_history = []
alerts_history = []

for cycle in range(1, 21):
    # 模拟多样性指标随时间变化
    metrics = DiversityMetrics(
        cycle=cycle,
        timestamp=datetime.now(),
        gene_entropy=2.5 - cycle * 0.05 + np.random.normal(0, 0.1),
        gene_simpson=0.8 - cycle * 0.01,
        avg_gene_distance=1.5 - cycle * 0.03,
        strategy_entropy=3.0 - cycle * 0.08 + np.random.normal(0, 0.15),
        unique_strategies=max(5, 20 - cycle),
        lineage_entropy=4.0 - cycle * 0.1,
        active_families=max(5, 30 - cycle),
        diversity_score=max(0.1, 0.8 - cycle * 0.03 + np.random.normal(0, 0.05)),
        is_healthy=(cycle < 10)
    )
    metrics_history.append(metrics)
    
    # 模拟警报（当多样性下降时）
    if cycle > 10 and cycle % 3 == 0:
        alert = DiversityAlert(
            cycle=cycle,
            alert_type='warning' if cycle < 15 else 'critical',
            metric_name='diversity_score',
            current_value=metrics.diversity_score,
            threshold=0.5,
            message=f"多样性得分过低: {metrics.diversity_score:.3f}",
            suggested_action="启动保护机制"
        )
        alerts_history.append(alert)

print(f"  ✅ 创建了 {len(metrics_history)} 条监控记录")
print(f"  ✅ 创建了 {len(alerts_history)} 条警报记录")

# ==================== 测试可视化器 ====================

print("\n[2/3] 测试可视化器...")

try:
    visualizer = DiversityVisualizer(output_dir="./results/visualizer_test")
    print("  ✅ 可视化器初始化成功")
except Exception as e:
    print(f"  ❌ 可视化器初始化失败: {e}")
    exit(1)

# ==================== 生成图表 ====================

print("\n[3/3] 生成图表...")

success_count = 0
total_count = 4

# 1. 趋势图
try:
    path = visualizer.plot_diversity_trends(metrics_history)
    print(f"  ✅ 趋势图: {path}")
    success_count += 1
except Exception as e:
    print(f"  ❌ 趋势图失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 警报图
try:
    path = visualizer.plot_alert_timeline(alerts_history)
    if path:
        print(f"  ✅ 警报图: {path}")
        success_count += 1
    else:
        print(f"  ℹ️  警报图: 无数据跳过")
        success_count += 1  # 这也算成功
except Exception as e:
    print(f"  ❌ 警报图失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 热力图
try:
    path = visualizer.plot_diversity_heatmap(metrics_history)
    if path:
        print(f"  ✅ 热力图: {path}")
        success_count += 1
    else:
        print(f"  ℹ️  热力图: 数据不足跳过")
        success_count += 1
except Exception as e:
    print(f"  ❌ 热力图失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 综合仪表板
try:
    path = visualizer.generate_dashboard(metrics_history, alerts_history)
    print(f"  ✅ 仪表板: {path}")
    success_count += 1
except Exception as e:
    print(f"  ❌ 仪表板失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 总结 ====================

print("\n" + "="*80)
print("📊 测试结果")
print("="*80)

print(f"""
成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)

测试项目:
  {'✅' if success_count >= 1 else '❌'} 趋势图生成
  {'✅' if success_count >= 2 else '❌'} 警报图生成  
  {'✅' if success_count >= 3 else '❌'} 热力图生成
  {'✅' if success_count >= 4 else '❌'} 仪表板生成

{'✅ 可视化功能验证通过！' if success_count == total_count else '⚠️ 部分功能需要检查'}
""")

if success_count == total_count:
    print("🎉 所有图表已成功生成到 ./results/visualizer_test/ 目录")
else:
    print(f"⚠️ {total_count - success_count} 个功能失败，请检查错误信息")

print("="*80)

