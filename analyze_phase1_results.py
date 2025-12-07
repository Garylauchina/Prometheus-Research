#!/usr/bin/env python3
"""
Phase 1 结果分析
==================

从日志中提取关键指标并分析
"""

import re
from pathlib import Path

def analyze_phase1_log():
    """分析Phase 1日志文件"""
    log_file = Path("results/phase1_500cycles.log")
    
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    print("=" * 80)
    print("📊 Phase 1 结果分析 (500周期)")
    print("=" * 80)
    print()
    
    # 提取进化代数
    generations = re.findall(r'第(\d+)代', content)
    if generations:
        max_gen = max(int(g) for g in generations)
        print(f"🧬 最高进化代数: 第{max_gen}代")
    
    # 提取累计统计
    births = re.findall(r'累计出生: (\d+)', content)
    deaths = re.findall(r'累计死亡: (\d+)', content)
    
    if births and deaths:
        final_births = int(births[-1])
        final_deaths = int(deaths[-1])
        print(f"👶 累计出生: {final_births}个Agent")
        print(f"💀 累计死亡: {final_deaths}个Agent")
        print(f"📊 净增长: {final_births - final_deaths}个")
        print(f"💪 进化强度: {final_deaths}次淘汰 → {final_births}次复制")
    
    # 提取繁殖成功率
    breeding_success = re.findall(r'繁殖成功：(\d+)/(\d+)', content)
    if breeding_success:
        total_success = sum(int(s) for s, t in breeding_success)
        total_target = sum(int(t) for s, t in breeding_success)
        success_rate = total_success / total_target * 100 if total_target > 0 else 0
        print(f"🦠 病毒式复制成功率: {success_rate:.1f}% ({total_success}/{total_target})")
    
    # 提取交易统计
    trade_stats = re.findall(r'周期 (\d+) 交易统计:.*成功=(\d+)', content)
    if trade_stats:
        total_trades = sum(int(t) for c, t in trade_stats)
        print(f"💼 总交易数: {total_trades}笔")
        print(f"📈 平均每周期: {total_trades/500:.1f}笔")
    
    # 提取种群数量变化
    population = re.findall(r'当前种群: (\d+)个', content)
    if population:
        pop_history = [int(p) for p in population]
        print(f"👥 最终种群: {pop_history[-1]}个")
        print(f"📉 种群变化: {min(pop_history)} - {max(pop_history)}个")
    
    # 提取家族分布
    families = re.findall(r'家族分布: (\d+)个活跃家族', content)
    if families:
        print(f"🏠 活跃家族数: {families[-1]}个 (初始50个)")
    
    print()
    print("=" * 80)
    print("🎯 关键观察")
    print("=" * 80)
    
    # 判断系统状态
    if population and int(population[-1]) >= 40:
        print("✅ 种群健康: 维持在高水平")
    elif population and int(population[-1]) >= 20:
        print("⚠️ 种群偏低: 但仍可持续")
    else:
        print("❌ 种群崩溃: 濒临灭绝")
    
    if breeding_success and success_rate > 90:
        print("✅ 繁殖能力: 强劲")
    elif breeding_success and success_rate > 70:
        print("⚠️ 繁殖能力: 一般")
    else:
        print("❌ 繁殖能力: 不足")
    
    if trade_stats and total_trades > 500:
        print(f"✅ 交易活跃: {total_trades}笔")
    elif trade_stats and total_trades > 100:
        print(f"⚠️ 交易偏低: {total_trades}笔")
    else:
        print(f"❌ 交易过少: {total_trades}笔 (可能过于保守)")
    
    print()
    print("=" * 80)
    print("💡 下一步建议")
    print("=" * 80)
    
    # 基于数据给出建议
    if breeding_success and success_rate > 90 and trade_stats and total_trades > 500:
        print("🎉 系统运行良好！")
        print("✅ 建议: 继续Phase 2 (多种子大规模训练)")
    elif breeding_success and success_rate > 70:
        print("⚠️ 系统基本正常，但需要优化")
        print("💡 建议: 调整参数后再次测试")
    else:
        print("❌ 系统存在问题")
        print("🛠️ 建议: 需要调试和修复")
    
    print()

if __name__ == "__main__":
    analyze_phase1_log()

