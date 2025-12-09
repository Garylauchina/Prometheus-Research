"""
收敛质量分析（v6.0视角）
========================

基于新理解：
  ✅ 快速收敛 = 快速响应能力
  ✅ 方向垄断 = 成功适应市场
  
分析目标：
1. 收敛速度：多快找到最优策略？
2. 收敛质量：最优策略是否真的匹配市场？
3. 淘汰效率：劣质基因清除速度？
4. 市场适应性：策略与市场结构的匹配度？
5. 改进空间：如何让收敛更快更准？
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
import pandas as pd
from collections import Counter


def analyze_convergence_speed():
    """分析1：收敛速度 - 多快找到优秀基因？"""
    print("\n" + "="*80)
    print("分析1：收敛速度 - 系统的学习曲线")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 按周期分组，看每个周期的最佳表现
    cursor = conn.execute("""
        SELECT 
            run_id,
            MAX(profit_factor) as max_pf,
            AVG(profit_factor) as avg_pf,
            MAX(roi) as max_roi,
            AVG(roi) as avg_roi
        FROM best_genomes
        GROUP BY run_id
        ORDER BY run_id
    """)
    
    records = list(cursor)
    
    # 提取周期数
    cycles = []
    max_pfs = []
    avg_pfs = []
    max_rois = []
    
    for run_id, max_pf, avg_pf, max_roi, avg_roi in records:
        if '_cycle' in run_id:
            cycle = int(run_id.split('_cycle')[-1])
            cycles.append(cycle)
            max_pfs.append(max_pf)
            avg_pfs.append(avg_pf)
            max_rois.append(max_roi)
    
    if not cycles:
        print("⚠️ 无法提取周期信息")
        conn.close()
        return
    
    print(f"训练周期范围: {min(cycles)} - {max(cycles)}")
    print(f"保存次数: {len(cycles)}\n")
    
    # 找到关键时间点
    print("【关键时间点】")
    print(f"{'阶段':<30} {'周期':>10} {'最高PF':>15} {'最高ROI':>12}")
    print("-"*80)
    
    # 第一次出现PF > 0
    first_profit_idx = next((i for i, pf in enumerate(max_pfs) if pf > 0), None)
    if first_profit_idx is not None:
        print(f"{'首次出现盈利基因':<30} {cycles[first_profit_idx]:>10} {max_pfs[first_profit_idx]:>15,.2f} {max_rois[first_profit_idx]*100:>11.2f}%")
    
    # 第一次出现PF > 1.0
    first_good_idx = next((i for i, pf in enumerate(max_pfs) if pf > 1.0), None)
    if first_good_idx is not None:
        print(f"{'首次出现优秀基因(PF>1.0)':<30} {cycles[first_good_idx]:>10} {max_pfs[first_good_idx]:>15,.2f} {max_rois[first_good_idx]*100:>11.2f}%")
    
    # 第一次出现PF > 2.0
    first_excellent_idx = next((i for i, pf in enumerate(max_pfs) if pf > 2.0), None)
    if first_excellent_idx is not None:
        print(f"{'首次出现卓越基因(PF>2.0)':<30} {cycles[first_excellent_idx]:>10} {max_pfs[first_excellent_idx]:>15,.2f} {max_rois[first_excellent_idx]*100:>11.2f}%")
    
    # 达到峰值
    peak_idx = max_pfs.index(max(max_pfs))
    print(f"{'达到峰值性能':<30} {cycles[peak_idx]:>10} {max_pfs[peak_idx]:>15,.2f} {max_rois[peak_idx]*100:>11.2f}%")
    
    # 最后一轮
    print(f"{'最后一轮':<30} {cycles[-1]:>10} {max_pfs[-1]:>15,.2f} {max_rois[-1]*100:>11.2f}%")
    
    print(f"\n💡 收敛速度评估:")
    if first_excellent_idx is not None and cycles[first_excellent_idx] < 500:
        print(f"   ✅ 优秀！在{cycles[first_excellent_idx]}周期就找到卓越基因")
        print(f"   ✅ 响应速度：< 500周期")
    elif first_excellent_idx is not None and cycles[first_excellent_idx] < 1000:
        print(f"   ⚠️ 良好。在{cycles[first_excellent_idx]}周期找到卓越基因")
        print(f"   ⚠️ 响应速度：500-1000周期")
    elif first_excellent_idx is None:
        print(f"   ❌ 较慢。整个训练期间未出现PF>2.0的基因")
        print(f"   ❌ 需要优化进化参数")
    
    # 检查是否持续改进
    print(f"\n【持续改进趋势】")
    if len(max_pfs) >= 3:
        early_avg = np.mean(max_pfs[:len(max_pfs)//3])
        mid_avg = np.mean(max_pfs[len(max_pfs)//3:2*len(max_pfs)//3])
        late_avg = np.mean(max_pfs[2*len(max_pfs)//3:])
        
        print(f"前1/3周期平均最高PF: {early_avg:,.2f}")
        print(f"中1/3周期平均最高PF: {mid_avg:,.2f}")
        print(f"后1/3周期平均最高PF: {late_avg:,.2f}")
        
        if late_avg > mid_avg > early_avg:
            print(f"\n✅ 持续改进！系统在不断学习")
        elif late_avg > early_avg:
            print(f"\n⚠️ 有改进，但中期可能有波动")
        else:
            print(f"\n❌ 未见明显改进，可能已达瓶颈或参数不当")
    
    conn.close()
    print("")


def analyze_convergence_direction():
    """分析2：收敛方向 - 是否匹配市场特征？"""
    print("\n" + "="*80)
    print("分析2：收敛方向正确性 - 策略是否匹配市场？")
    print("="*80 + "\n")
    
    # 加载市场数据
    try:
        market_data = pd.read_csv('data/stage1_1_training_market.csv')
        
        # 计算每个结构的特征
        print("【市场结构分析】")
        print(f"{'结构类型':<15} {'占比':>8} {'价格变化':>12} {'理想策略':>15}")
        print("-"*80)
        
        if 'structure_type' in market_data.columns:
            structures = market_data['structure_type'].unique()
            
            structure_impact = {}
            for structure in structures:
                structure_data = market_data[market_data['structure_type'] == structure]
                start_price = structure_data.iloc[0]['close']
                end_price = structure_data.iloc[-1]['close']
                roi = (end_price / start_price - 1) * 100
                weight = len(structure_data) / len(market_data)
                
                structure_impact[structure] = {
                    'weight': weight,
                    'roi': roi
                }
                
                ideal_strategy = ""
                if 'up' in structure:
                    ideal_strategy = "做多(bias>0.6)"
                elif 'down' in structure:
                    ideal_strategy = "做空(bias<0.4)"
                elif 'range' in structure:
                    ideal_strategy = "中性(bias≈0.5)"
                elif 'fake' in structure:
                    ideal_strategy = "快进快出"
                
                print(f"{structure:<15} {weight*100:>7.1f}% {roi:>+11.2f}% {ideal_strategy:>15}")
        else:
            print("⚠️ 市场数据缺少structure_type字段")
            return
        
        # 计算加权最优方向
        print(f"\n【加权最优策略计算】")
        
        # 简化计算：哪个方向的加权收益最高？
        weighted_up_roi = sum(
            info['weight'] * info['roi']
            for struct, info in structure_impact.items()
            if 'up' in struct
        )
        weighted_down_roi = sum(
            info['weight'] * abs(info['roi'])  # 做空时，下跌是盈利
            for struct, info in structure_impact.items()
            if 'down' in struct
        )
        
        print(f"做多加权收益: {weighted_up_roi:+.2f}%")
        print(f"做空加权收益: {weighted_down_roi:+.2f}%")
        
        optimal_bias = "做空(bias<0.4)" if weighted_down_roi > weighted_up_roi else "做多(bias>0.6)"
        print(f"\n理论最优策略: {optimal_bias}")
        
        # 对比实际收敛结果
        print(f"\n【实际收敛结果】")
        
        conn = sqlite3.connect('experience/stage1_1_full_training.db')
        cursor = conn.execute("""
            SELECT genome 
            FROM best_genomes
            WHERE profit_factor >= 2.0
        """)
        
        excellent_genes = []
        for row in cursor:
            genome = json.loads(row[0])
            excellent_genes.append(genome)
        
        if excellent_genes:
            avg_bias = np.mean([g['directional_bias'] for g in excellent_genes])
            print(f"优秀基因平均bias: {avg_bias:.3f}")
            
            actual_strategy = ""
            if avg_bias < 0.4:
                actual_strategy = "做空(bias<0.4)"
            elif avg_bias > 0.6:
                actual_strategy = "做多(bias>0.6)"
            else:
                actual_strategy = "中性(bias≈0.5)"
            
            print(f"实际收敛策略: {actual_strategy}")
            
            print(f"\n💡 方向匹配度评估:")
            if (weighted_down_roi > weighted_up_roi and avg_bias < 0.4) or \
               (weighted_down_roi < weighted_up_roi and avg_bias > 0.6):
                print(f"   ✅ 完美匹配！系统正确识别了市场特征")
                print(f"   ✅ 收敛方向与理论最优一致")
            else:
                print(f"   ⚠️ 方向偏差！系统可能未充分学习")
                print(f"   ⚠️ 建议：延长训练或调整参数")
        else:
            print("⚠️ 未找到优秀基因（PF≥2.0）")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    
    print("")


def analyze_elimination_efficiency():
    """分析3：淘汰效率 - 劣质基因是否被快速清除？"""
    print("\n" + "="*80)
    print("分析3：淘汰效率 - 自然选择的有效性")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 按周期统计不同表现等级的基因数量
    cursor = conn.execute("""
        SELECT 
            run_id,
            SUM(CASE WHEN profit_factor >= 2.0 THEN 1 ELSE 0 END) as excellent_count,
            SUM(CASE WHEN profit_factor >= 1.0 AND profit_factor < 2.0 THEN 1 ELSE 0 END) as good_count,
            SUM(CASE WHEN profit_factor > 0 AND profit_factor < 1.0 THEN 1 ELSE 0 END) as losing_count,
            SUM(CASE WHEN profit_factor = 0 AND trade_count > 0 THEN 1 ELSE 0 END) as bad_count,
            SUM(CASE WHEN trade_count = 0 THEN 1 ELSE 0 END) as inactive_count
        FROM best_genomes
        GROUP BY run_id
        ORDER BY run_id
    """)
    
    records = list(cursor)
    
    if len(records) < 3:
        print("⚠️ 数据不足，无法分析趋势")
        conn.close()
        return
    
    print("【基因质量分布趋势】")
    print(f"{'周期':<10} {'优秀':>8} {'良好':>8} {'亏损':>8} {'劣质':>8} {'不活跃':>10}")
    print("-"*80)
    
    # 提取周期信息
    cycles_data = []
    for run_id, exc, good, losing, bad, inactive in records:
        if '_cycle' in run_id:
            cycle = int(run_id.split('_cycle')[-1])
            cycles_data.append((cycle, exc, good, losing, bad, inactive))
    
    # 显示关键周期
    if cycles_data:
        # 首轮
        cycle, exc, good, losing, bad, inactive = cycles_data[0]
        print(f"Cycle{cycle:<5} {exc:>8} {good:>8} {losing:>8} {bad:>8} {inactive:>10}")
        
        # 中间（如果有的话）
        if len(cycles_data) > 10:
            print("   ...")
            mid = len(cycles_data) // 2
            cycle, exc, good, losing, bad, inactive = cycles_data[mid]
            print(f"Cycle{cycle:<5} {exc:>8} {good:>8} {losing:>8} {bad:>8} {inactive:>10}")
            print("   ...")
        
        # 最后一轮
        cycle, exc, good, losing, bad, inactive = cycles_data[-1]
        print(f"Cycle{cycle:<5} {exc:>8} {good:>8} {losing:>8} {bad:>8} {inactive:>10}")
    
    print(f"\n💡 淘汰效率评估:")
    
    # 计算趋势
    if len(cycles_data) >= 3:
        early_inactive = np.mean([data[5] for data in cycles_data[:len(cycles_data)//3]])
        late_inactive = np.mean([data[5] for data in cycles_data[2*len(cycles_data)//3:]])
        
        early_excellent = np.mean([data[1] for data in cycles_data[:len(cycles_data)//3]])
        late_excellent = np.mean([data[1] for data in cycles_data[2*len(cycles_data)//3:]])
        
        print(f"   不活跃基因: 前期{early_inactive:.1f} → 后期{late_inactive:.1f}")
        print(f"   优秀基因:   前期{early_excellent:.1f} → 后期{late_excellent:.1f}")
        
        if late_inactive < early_inactive and late_excellent > early_excellent:
            print(f"\n   ✅ 淘汰有效！劣质基因↓，优秀基因↑")
        elif late_inactive < early_inactive:
            print(f"\n   ⚠️ 淘汰有效但优秀基因未增加")
            print(f"   建议：增加繁殖率或降低淘汰率")
        else:
            print(f"\n   ❌ 淘汰效率低！劣质基因未被有效清除")
            print(f"   建议：提高淘汰率或缩短进化间隔")
    
    conn.close()
    print("")


def analyze_inactive_agents():
    """分析4：不活跃Agent - 是参数问题还是进化问题？"""
    print("\n" + "="*80)
    print("分析4：不活跃Agent深度分析（57.2%不交易）")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 提取不活跃Agent的参数特征
    cursor = conn.execute("""
        SELECT genome FROM best_genomes
        WHERE trade_count = 0
    """)
    
    inactive_genomes = []
    for row in cursor:
        genome = json.loads(row[0])
        inactive_genomes.append(genome)
    
    if not inactive_genomes:
        print("✅ 没有不活跃Agent")
        conn.close()
        return
    
    # 对比活跃Agent
    cursor = conn.execute("""
        SELECT genome FROM best_genomes
        WHERE trade_count > 0
    """)
    
    active_genomes = []
    for row in cursor:
        genome = json.loads(row[0])
        active_genomes.append(genome)
    
    print(f"不活跃Agent数量: {len(inactive_genomes)}")
    print(f"活跃Agent数量: {len(active_genomes)}\n")
    
    # 统计参数差异
    print("【参数对比：不活跃 vs 活跃】")
    print(f"{'参数':<30} {'不活跃平均':>15} {'活跃平均':>15} {'差异':>10}")
    print("-"*80)
    
    param_keys = [k for k in inactive_genomes[0].keys() if k != 'generation']
    
    for key in param_keys:
        inactive_values = [g.get(key, 0) for g in inactive_genomes]
        active_values = [g.get(key, 0) for g in active_genomes]
        
        inactive_mean = np.mean(inactive_values)
        active_mean = np.mean(active_values)
        diff = active_mean - inactive_mean
        
        marker = ""
        if abs(diff) > 0.15:
            marker = " ⭐" if diff > 0 else " ⚠️"
        
        print(f"{key:<30} {inactive_mean:>15.3f} {active_mean:>15.3f} {diff:>+10.3f}{marker}")
    
    print(f"\n💡 不活跃原因分析:")
    
    # 检查关键参数
    inactive_bias = np.mean([g['directional_bias'] for g in inactive_genomes])
    active_bias = np.mean([g['directional_bias'] for g in active_genomes])
    
    if abs(inactive_bias - active_bias) < 0.1:
        print(f"   ⚠️ 方向偏好接近（inactive={inactive_bias:.3f}, active={active_bias:.3f}）")
        print(f"   可能原因：其他参数导致不交易")
    
    # 检查holding_preference
    inactive_hold = np.mean([g['holding_preference'] for g in inactive_genomes])
    active_hold = np.mean([g['holding_preference'] for g in active_genomes])
    
    if inactive_hold > active_hold + 0.1:
        print(f"   ⚠️ 不活跃Agent持仓偏好更高（{inactive_hold:.3f} vs {active_hold:.3f}）")
        print(f"   可能：持仓偏好过高导致从不开仓")
    
    # 检查stop_loss和take_profit
    inactive_sl = np.mean([g['stop_loss_threshold'] for g in inactive_genomes])
    active_sl = np.mean([g['stop_loss_threshold'] for g in active_genomes])
    
    if abs(inactive_sl - active_sl) > 0.15:
        print(f"   ⚠️ 止损阈值差异大（inactive={inactive_sl:.3f}, active={active_sl:.3f}）")
        print(f"   可能：阈值设置过严，永远不满足交易条件")
    
    print(f"\n💡 建议:")
    print(f"   1. 这些不活跃Agent应该被更快淘汰（当前可能存活过久）")
    print(f"   2. 检查交易信号生成逻辑（InnerCouncil._strategy_voice）")
    print(f"   3. 考虑添加'交易数惩罚'：trade_count=0的Agent fitness大幅降低")
    
    conn.close()
    print("")


def analyze_convergence_quality():
    """分析5：收敛质量 - 最终基因的竞争力"""
    print("\n" + "="*80)
    print("分析5：收敛质量 - 最终基因能否实战？")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 提取Top基因
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
        WHERE profit_factor >= 2.0
        ORDER BY profit_factor DESC
    """)
    
    top_genes = []
    for roi, pf, trade_count, genome_str in cursor:
        genome = json.loads(genome_str)
        top_genes.append({
            'roi': roi,
            'pf': pf,
            'trade_count': trade_count,
            'genome': genome
        })
    
    if not top_genes:
        print("❌ 未找到优秀基因（PF≥2.0）")
        print("   系统可能未成功收敛")
        conn.close()
        return
    
    print(f"找到 {len(top_genes)} 个优秀基因\n")
    
    print("【Top 5 基因详情】")
    for i, gene in enumerate(top_genes[:5]):
        print(f"\n基因 #{i+1}")
        print(f"  ROI: {gene['roi']*100:+.2f}%")
        print(f"  PF: {gene['pf']:,.2f}")
        print(f"  交易数: {gene['trade_count']}")
        print(f"  策略:")
        print(f"    方向偏好: {gene['genome']['directional_bias']:.3f}", end="")
        if gene['genome']['directional_bias'] < 0.4:
            print(" (偏空)")
        elif gene['genome']['directional_bias'] > 0.6:
            print(" (偏多)")
        else:
            print(" (中性)")
        print(f"    持仓偏好: {gene['genome']['holding_preference']:.3f}")
        print(f"    仓位大小: {gene['genome']['position_size_base']:.3f}")
        print(f"    止损阈值: {gene['genome']['stop_loss_threshold']:.3f}")
        print(f"    止盈阈值: {gene['genome']['take_profit_threshold']:.3f}")
    
    # 评估基因质量
    print(f"\n{'='*80}")
    print("【基因质量评估】")
    print(f"{'='*80}\n")
    
    avg_roi = np.mean([g['roi'] for g in top_genes])
    avg_pf = np.mean([g['pf'] for g in top_genes])
    avg_trades = np.mean([g['trade_count'] for g in top_genes])
    
    print(f"平均ROI: {avg_roi*100:+.2f}%")
    print(f"平均PF: {avg_pf:,.2f}")
    print(f"平均交易数: {avg_trades:.0f}")
    
    print(f"\n💡 质量评级:")
    
    score = 0
    feedback = []
    
    # ROI评分
    if avg_roi > 5.0:
        score += 3
        feedback.append("✅ ROI优秀 (+3分)")
    elif avg_roi > 1.0:
        score += 2
        feedback.append("⚠️ ROI良好 (+2分)")
    elif avg_roi > 0.5:
        score += 1
        feedback.append("⚠️ ROI一般 (+1分)")
    else:
        feedback.append("❌ ROI较低 (0分)")
    
    # PF评分
    if avg_pf > 2.0:
        score += 3
        feedback.append("✅ PF优秀 (+3分)")
    elif avg_pf > 1.5:
        score += 2
        feedback.append("⚠️ PF良好 (+2分)")
    elif avg_pf > 1.0:
        score += 1
        feedback.append("⚠️ PF一般 (+1分)")
    else:
        feedback.append("❌ PF不足 (0分)")
    
    # 交易活跃度评分
    if avg_trades > 100:
        score += 2
        feedback.append("✅ 交易活跃 (+2分)")
    elif avg_trades > 10:
        score += 1
        feedback.append("⚠️ 交易一般 (+1分)")
    else:
        feedback.append("❌ 交易过少 (0分)")
    
    # 基因多样性评分（看Top基因是否太相似）
    if len(top_genes) > 1:
        biases = [g['genome']['directional_bias'] for g in top_genes]
        bias_std = np.std(biases)
        
        if bias_std > 0.1:
            score += 2
            feedback.append("✅ 保持多样性 (+2分)")
        else:
            score += 1
            feedback.append("⚠️ 基因相似 (+1分)")
    
    for line in feedback:
        print(f"   {line}")
    
    print(f"\n   总分: {score}/10")
    
    if score >= 9:
        print(f"   评级: ⭐⭐⭐⭐⭐ 卓越！可直接用于实战")
    elif score >= 7:
        print(f"   评级: ⭐⭐⭐⭐ 优秀！适合进入下一阶段")
    elif score >= 5:
        print(f"   评级: ⭐⭐⭐ 良好，但需要改进")
    else:
        print(f"   评级: ⭐⭐ 一般，建议重新训练或调参")
    
    conn.close()
    print("")


if __name__ == '__main__':
    print("\n" + "🎯"*40)
    print("Stage 1.1 收敛质量分析（v6.0视角：快速收敛=快速响应）")
    print("🎯"*40)
    
    analyze_convergence_speed()
    analyze_convergence_direction()
    analyze_elimination_efficiency()
    analyze_inactive_agents()
    analyze_convergence_quality()
    
    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80 + "\n")

