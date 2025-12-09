"""
Stage 1.1 训练结果深度分析
===========================

分析内容：
1. 超高PF的真实原因（total_profit vs total_loss）
2. 优秀基因的详细特征和共性
3. Agent表现不佳的原因
4. Immigration触发情况
5. 基因收敛速度和演化趋势
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
import pandas as pd
from collections import Counter


def analyze_super_genes():
    """分析1：超级基因（超高PF）的真实情况"""
    print("\n" + "="*80)
    print("分析1：超级基因（PF > 1000）深度剖析")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 查询超高PF的记录
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome, run_id
        FROM best_genomes
        WHERE profit_factor > 1000
        ORDER BY profit_factor DESC
    """)
    
    records = cursor.fetchall()
    
    if not records:
        print("⚠️ 没有找到PF>1000的记录")
        conn.close()
        return
    
    print(f"找到 {len(records)} 条超高PF记录\n")
    
    # 分析前3条
    for i, (roi, pf, trade_count, genome_str, run_id) in enumerate(records[:3]):
        print(f"{'='*80}")
        print(f"记录 #{i+1}")
        print(f"{'='*80}")
        
        genome = json.loads(genome_str)
        
        print(f"ROI: {roi*100:+.2f}%")
        print(f"Profit Factor: {pf:,.2f}")
        print(f"交易数: {trade_count}")
        print(f"Run ID: {run_id}")
        print(f"\n策略参数:")
        for key, value in genome.items():
            print(f"  {key:25s}: {value:.4f}")
        
        # 尝试从run_id推断是第几轮保存
        if '_cycle' in run_id:
            cycle = run_id.split('_cycle')[-1]
            print(f"\n保存周期: {cycle}")
        
        print("")
    
    # 检查是否是同一个Agent
    print(f"{'='*80}")
    print("重复性检查")
    print(f"{'='*80}\n")
    
    genomes = [json.loads(row[3]) for row in records]
    unique_genomes = []
    
    for genome in genomes:
        is_duplicate = False
        for unique in unique_genomes:
            # 检查是否完全相同（所有参数都一样）
            if all(abs(genome.get(k, 0) - unique.get(k, 0)) < 1e-6 for k in genome.keys()):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_genomes.append(genome)
    
    print(f"总记录数: {len(records)}")
    print(f"唯一基因数: {len(unique_genomes)}")
    print(f"重复率: {(len(records) - len(unique_genomes)) / len(records) * 100:.1f}%")
    
    if len(unique_genomes) < len(records):
        print(f"\n💡 这些记录是同一个Agent在不同周期的快照")
        print(f"   每50周期保存一次，所以同一个优秀Agent会被重复保存")
    
    conn.close()
    print("")


def analyze_excellent_genes():
    """分析2：所有优秀基因（PF≥2.0）的共性"""
    print("\n" + "="*80)
    print("分析2：优秀基因（PF≥2.0）共性分析")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
        WHERE profit_factor >= 2.0
        ORDER BY profit_factor DESC
    """)
    
    records = cursor.fetchall()
    
    if not records:
        print("⚠️ 没有找到PF≥2.0的记录")
        conn.close()
        return
    
    print(f"找到 {len(records)} 条优秀基因记录\n")
    
    # 提取所有参数
    params_list = []
    for roi, pf, trade_count, genome_str in records:
        genome = json.loads(genome_str)
        params_list.append(genome)
    
    # 统计每个参数的分布
    param_stats = {}
    for key in params_list[0].keys():
        if key == 'generation':
            continue
        values = [p.get(key, 0) for p in params_list]
        param_stats[key] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values)
        }
    
    print("参数分布:")
    print(f"{'参数':<30} {'平均值':>10} {'标准差':>10} {'范围':>20}")
    print("-"*80)
    
    for key, stats in param_stats.items():
        print(f"{key:<30} {stats['mean']:>10.3f} {stats['std']:>10.3f} [{stats['min']:>6.3f}, {stats['max']:>6.3f}]")
    
    conn.close()
    print("")


def analyze_poor_performance():
    """分析3：为什么99.8%的基因表现不佳？"""
    print("\n" + "="*80)
    print("分析3：表现不佳基因（PF<1.0）原因分析")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 统计不同trade_count区间的PF分布
    cursor = conn.execute("""
        SELECT 
            CASE 
                WHEN trade_count = 0 THEN '0 (不交易)'
                WHEN trade_count <= 10 THEN '1-10'
                WHEN trade_count <= 50 THEN '11-50'
                WHEN trade_count <= 100 THEN '51-100'
                WHEN trade_count <= 500 THEN '101-500'
                ELSE '500+'
            END as trade_range,
            COUNT(*) as count,
            AVG(profit_factor) as avg_pf,
            AVG(roi) as avg_roi
        FROM best_genomes
        WHERE profit_factor < 1.0
        GROUP BY trade_range
        ORDER BY 
            CASE 
                WHEN trade_count = 0 THEN 0
                WHEN trade_count <= 10 THEN 1
                WHEN trade_count <= 50 THEN 2
                WHEN trade_count <= 100 THEN 3
                WHEN trade_count <= 500 THEN 4
                ELSE 5
            END
    """)
    
    print("按交易次数分组:")
    print(f"{'交易区间':<15} {'数量':>10} {'平均PF':>12} {'平均ROI':>12}")
    print("-"*80)
    
    for row in cursor:
        trade_range, count, avg_pf, avg_roi = row
        print(f"{trade_range:<15} {count:>10} {avg_pf:>12.2f} {avg_roi*100:>11.2f}%")
    
    print(f"\n💡 分析:")
    print(f"   - trade_count=0: Agent从不交易（可能过于保守）")
    print(f"   - trade_count>0但PF<1.0: Agent交易但策略不佳（亏多赚少）")
    
    conn.close()
    print("")


def analyze_gene_evolution():
    """分析4：基因演化趋势（通过run_id时间序列）"""
    print("\n" + "="*80)
    print("分析4：基因演化趋势（收敛速度）")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    # 按run_id（包含周期信息）分组统计
    cursor = conn.execute("""
        SELECT 
            run_id,
            COUNT(*) as record_count,
            AVG(profit_factor) as avg_pf,
            MAX(profit_factor) as max_pf,
            AVG(roi) as avg_roi,
            MAX(roi) as max_roi
        FROM best_genomes
        GROUP BY run_id
        ORDER BY run_id
    """)
    
    records = list(cursor)
    
    print(f"总共 {len(records)} 轮保存\n")
    
    # 只显示前10轮和最后10轮
    print("【前10轮】")
    print(f"{'轮次':<10} {'记录数':>8} {'平均PF':>12} {'最高PF':>15} {'平均ROI':>12} {'最高ROI':>12}")
    print("-"*80)
    
    for i, (run_id, count, avg_pf, max_pf, avg_roi, max_roi) in enumerate(records[:10]):
        cycle = run_id.split('_cycle')[-1] if '_cycle' in run_id else '???'
        print(f"Cycle{cycle:<5} {count:>8} {avg_pf:>12.2f} {max_pf:>15.2f} {avg_roi*100:>11.2f}% {max_roi*100:>11.2f}%")
    
    print(f"\n{'... 省略中间轮次 ...':^80}\n")
    
    print("【最后10轮】")
    print(f"{'轮次':<10} {'记录数':>8} {'平均PF':>12} {'最高PF':>15} {'平均ROI':>12} {'最高ROI':>12}")
    print("-"*80)
    
    for i, (run_id, count, avg_pf, max_pf, avg_roi, max_roi) in enumerate(records[-10:]):
        cycle = run_id.split('_cycle')[-1] if '_cycle' in run_id else '???'
        print(f"Cycle{cycle:<5} {count:>8} {avg_pf:>12.2f} {max_pf:>15.2f} {avg_roi*100:>11.2f}% {max_roi*100:>11.2f}%")
    
    # 分析收敛速度
    print(f"\n{'='*80}")
    print("收敛速度分析")
    print(f"{'='*80}\n")
    
    # 计算每轮的最高PF
    max_pfs = [row[3] for row in records]
    
    # 找到第一次出现PF>2.0的轮次
    first_excellent = None
    for i, (run_id, count, avg_pf, max_pf, avg_roi, max_roi) in enumerate(records):
        if max_pf >= 2.0:
            first_excellent = i
            break
    
    if first_excellent is not None:
        cycle = records[first_excellent][0].split('_cycle')[-1] if '_cycle' in records[first_excellent][0] else '???'
        print(f"✅ 第一次出现优秀基因（PF≥2.0）: 第{first_excellent+1}轮（Cycle {cycle}）")
        print(f"   收敛速度: {int(cycle) if cycle.isdigit() else '???'} 周期")
    else:
        print(f"⚠️ 整个训练期间没有出现PF≥2.0的基因")
    
    conn.close()
    print("")


def analyze_directional_bias_impact():
    """分析5：directional_bias对表现的影响"""
    print("\n" + "="*80)
    print("分析5：方向偏好（directional_bias）对表现的影响")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
    """)
    
    # 按directional_bias分组统计
    bins = {
        '强空(<0.2)': [],
        '偏空(0.2-0.4)': [],
        '中性(0.4-0.6)': [],
        '偏多(0.6-0.8)': [],
        '强多(>0.8)': []
    }
    
    for roi, pf, trade_count, genome_str in cursor:
        genome = json.loads(genome_str)
        bias = genome.get('directional_bias', 0.5)
        
        if bias < 0.2:
            bins['强空(<0.2)'].append((roi, pf, trade_count))
        elif bias < 0.4:
            bins['偏空(0.2-0.4)'].append((roi, pf, trade_count))
        elif bias < 0.6:
            bins['中性(0.4-0.6)'].append((roi, pf, trade_count))
        elif bias < 0.8:
            bins['偏多(0.6-0.8)'].append((roi, pf, trade_count))
        else:
            bins['强多(>0.8)'].append((roi, pf, trade_count))
    
    print(f"{'方向偏好':<15} {'数量':>8} {'平均ROI':>12} {'平均PF':>12} {'平均交易':>10}")
    print("-"*80)
    
    for bin_name, records in bins.items():
        if not records:
            continue
        
        count = len(records)
        avg_roi = np.mean([r[0] for r in records])
        avg_pf = np.mean([r[1] for r in records])
        avg_trades = np.mean([r[2] for r in records])
        
        print(f"{bin_name:<15} {count:>8} {avg_roi*100:>11.2f}% {avg_pf:>12.2f} {avg_trades:>10.1f}")
    
    print(f"\n💡 分析:")
    print(f"   - 市场包含trend_up和trend_down，理论上多空策略都应该能盈利")
    print(f"   - 如果某个方向明显优于其他，说明市场结构不平衡或策略有偏")
    
    conn.close()
    print("")


def analyze_trade_activity():
    """分析6：交易活跃度分析"""
    print("\n" + "="*80)
    print("分析6：交易活跃度分析")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('experience/stage1_1_full_training.db')
    
    cursor = conn.execute("""
        SELECT trade_count FROM best_genomes
    """)
    
    trade_counts = [row[0] for row in cursor]
    
    zero_trades = sum(1 for t in trade_counts if t == 0)
    low_trades = sum(1 for t in trade_counts if 0 < t <= 10)
    medium_trades = sum(1 for t in trade_counts if 10 < t <= 100)
    high_trades = sum(1 for t in trade_counts if 100 < t <= 1000)
    very_high_trades = sum(1 for t in trade_counts if t > 1000)
    
    total = len(trade_counts)
    
    print(f"交易活跃度分布:")
    print(f"{'类别':<20} {'数量':>10} {'占比':>10}")
    print("-"*80)
    print(f"{'不交易(0)':<20} {zero_trades:>10} {zero_trades/total*100:>9.1f}%")
    print(f"{'低频(1-10)':<20} {low_trades:>10} {low_trades/total*100:>9.1f}%")
    print(f"{'中频(11-100)':<20} {medium_trades:>10} {medium_trades/total*100:>9.1f}%")
    print(f"{'高频(101-1000)':<20} {high_trades:>10} {high_trades/total*100:>9.1f}%")
    print(f"{'极高频(>1000)':<20} {very_high_trades:>10} {very_high_trades/total*100:>9.1f}%")
    
    print(f"\n平均交易数: {np.mean(trade_counts):.1f}")
    print(f"中位数交易数: {np.median(trade_counts):.1f}")
    print(f"最多交易数: {np.max(trade_counts)}")
    
    print(f"\n💡 分析:")
    if zero_trades / total > 0.5:
        print(f"   ⚠️ 超过50%的Agent不交易，可能是策略过于保守")
        print(f"   建议：调整交易阈值或增加激进型Agent")
    else:
        print(f"   ✅ 大部分Agent有交易活动")
    
    conn.close()
    print("")


def analyze_pf_calculation_detail():
    """分析7：PF计算细节（验证超高PF的合理性）"""
    print("\n" + "="*80)
    print("分析7：超高PF的计算细节验证")
    print("="*80 + "\n")
    
    print("💡 Profit Factor公式: PF = total_profit / total_loss")
    print("")
    print("如果 PF = 2,076,883.02，可能的情况:")
    print("")
    
    scenarios = [
        ("情况1：极少亏损", 2076883.02, 1.0, "total_profit=$2,076,883, total_loss=$1"),
        ("情况2：正常盈利，微小亏损", 100.0, 0.048, "total_profit=$100, total_loss=$0.048"),
        ("情况3：极大盈利", 2000000.0, 1.0, "total_profit=$2,000,000, total_loss=$1"),
    ]
    
    print(f"{'情况':<20} {'total_profit':>15} {'total_loss':>15} {'PF':>15}")
    print("-"*80)
    
    for name, profit, loss, _ in scenarios:
        pf = profit / loss if loss > 0 else profit
        print(f"{name:<20} ${profit:>14,.2f} ${loss:>14,.2f} {pf:>15,.2f}")
    
    print(f"\n💡 分析:")
    print(f"   PF = 2,076,883 说明:")
    print(f"   - 要么total_loss极小（比如只亏$1）")
    print(f"   - 要么total_profit极大（比如赚$2,076,883）")
    print(f"   - 或者两者都有")
    print(f"\n   如果Agent ROI = +69,229% (从$750→$520,000):")
    print(f"   - 总盈利约$519,250")
    print(f"   - 如果PF = 2,076,883，则total_loss ≈ $0.25")
    print(f"   - 说明这个Agent几乎只有盈利交易！")
    
    print("")


def analyze_market_structure_impact():
    """分析8：不同市场结构对Agent表现的影响"""
    print("\n" + "="*80)
    print("分析8：市场结构影响分析")
    print("="*80 + "\n")
    
    # 加载市场数据
    try:
        market_data = pd.read_csv('data/stage1_1_training_market.csv')
        
        if 'structure_type' in market_data.columns:
            structures = market_data['structure_type'].unique()
            print(f"市场包含的结构: {list(structures)}\n")
            
            for structure in structures:
                structure_data = market_data[market_data['structure_type'] == structure]
                start_price = structure_data.iloc[0]['close']
                end_price = structure_data.iloc[-1]['close']
                roi = (end_price / start_price - 1) * 100
                
                print(f"{structure:15s}: {len(structure_data):>5} bars, "
                      f"价格 ${start_price:>10,.2f} → ${end_price:>10,.2f}, "
                      f"ROI {roi:>+8.2f}%")
            
            print(f"\n💡 分析:")
            print(f"   - trend_up应该利好做多策略（bias>0.6）")
            print(f"   - trend_down应该利好做空策略（bias<0.4）")
            print(f"   - range应该利好均值回归（中性bias）")
            print(f"   - fake_breakout需要快速止损能力")
        else:
            print("⚠️ 市场数据缺少structure_type字段")
    
    except Exception as e:
        print(f"❌ 无法加载市场数据: {e}")
    
    print("")


if __name__ == '__main__':
    print("\n" + "🔬"*40)
    print("Stage 1.1 训练结果深度分析")
    print("🔬"*40)
    
    analyze_super_genes()
    analyze_excellent_genes()
    analyze_poor_performance()
    analyze_gene_evolution()
    analyze_pf_calculation_detail()
    analyze_market_structure_impact()
    
    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80 + "\n")

