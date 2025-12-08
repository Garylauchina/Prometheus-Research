#!/usr/bin/env python3
"""
分析ExperienceDB中的基因特征

目标：
1. 分析各市场下优秀基因的参数特征
2. 发现规律，指导种群调度设计
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.core.experience_db import ExperienceDB
import numpy as np

def analyze_market_genes(db_path: str, market_type: str):
    """分析特定市场的基因特征"""
    db = ExperienceDB(db_path)
    
    print(f"\n{'='*80}")
    print(f"📊 {market_type.upper()} 市场基因分析")
    print('='*80)
    
    # 直接查询数据库
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT world_signature, genome, roi, sharpe, max_drawdown
        FROM best_genomes
        WHERE market_type = ?
        ORDER BY roi DESC
        LIMIT 50
    """, (market_type,))
    
    rows = cursor.fetchall()
    
    # ✅ 直接使用StrategyParams字典，不转换成GenomeVector
    import json
    
    genes = []
    for row in rows:
        ws_json, genome_json, roi, sharpe, dd = row
        genome_dict = json.loads(genome_json)  # 这是StrategyParams字典
        genes.append((None, genome_dict, roi, sharpe, dd))
    
    if not genes:
        print(f"❌ 没有{market_type}市场的数据")
        db.close()
        return
    
    print(f"样本数: {len(genes)}")
    
    # 提取参数
    directional_bias = []
    position_size = []
    holding_pref = []
    stop_loss = []
    take_profit = []
    rois = []
    sharpes = []
    
    for ws, genome_dict, roi, sharpe, dd in genes:
        # 直接从StrategyParams字典读取
        directional_bias.append(genome_dict.get('directional_bias', 0.5))
        position_size.append(genome_dict.get('position_size_base', 0.3))
        holding_pref.append(genome_dict.get('holding_preference', 0.5))
        stop_loss.append(genome_dict.get('stop_loss_threshold', 0.05))
        take_profit.append(genome_dict.get('take_profit_threshold', 0.1))
        rois.append(roi)
        sharpes.append(sharpe)
    
    # 统计分析
    print(f"\n📈 绩效指标:")
    print(f"  平均ROI: {np.mean(rois)*100:+.2f}%")
    print(f"  ROI范围: {np.min(rois)*100:+.2f}% ~ {np.max(rois)*100:+.2f}%")
    print(f"  平均Sharpe: {np.mean(sharpes):.2f}")
    
    print(f"\n🧬 关键参数分析:")
    
    # directional_bias
    print(f"\n1. directional_bias (方向偏好):")
    print(f"   均值: {np.mean(directional_bias):.3f}")
    print(f"   中位数: {np.median(directional_bias):.3f}")
    print(f"   标准差: {np.std(directional_bias):.3f}")
    print(f"   范围: {np.min(directional_bias):.3f} ~ {np.max(directional_bias):.3f}")
    
    # 分布
    high_bias = [b for b in directional_bias if b > 0.6]
    low_bias = [b for b in directional_bias if b < 0.4]
    mid_bias = [b for b in directional_bias if 0.4 <= b <= 0.6]
    
    print(f"   做多型(>0.6): {len(high_bias)} ({len(high_bias)/len(directional_bias)*100:.1f}%)")
    print(f"   做空型(<0.4): {len(low_bias)} ({len(low_bias)/len(directional_bias)*100:.1f}%)")
    print(f"   中性型(0.4-0.6): {len(mid_bias)} ({len(mid_bias)/len(directional_bias)*100:.1f}%)")
    
    # position_size
    print(f"\n2. position_size_base (仓位大小):")
    print(f"   均值: {np.mean(position_size):.3f}")
    print(f"   中位数: {np.median(position_size):.3f}")
    print(f"   范围: {np.min(position_size):.3f} ~ {np.max(position_size):.3f}")
    
    # holding_preference
    print(f"\n3. holding_preference (持仓偏好):")
    print(f"   均值: {np.mean(holding_pref):.3f}")
    print(f"   中位数: {np.median(holding_pref):.3f}")
    print(f"   范围: {np.min(holding_pref):.3f} ~ {np.max(holding_pref):.3f}")
    
    # stop_loss
    print(f"\n4. stop_loss_threshold (止损阈值):")
    print(f"   均值: {np.mean(stop_loss):.3f}")
    print(f"   范围: {np.min(stop_loss):.3f} ~ {np.max(stop_loss):.3f}")
    
    # take_profit
    print(f"\n5. take_profit_threshold (止盈阈值):")
    print(f"   均值: {np.mean(take_profit):.3f}")
    print(f"   范围: {np.min(take_profit):.3f} ~ {np.max(take_profit):.3f}")
    
    # Top 5基因详情
    print(f"\n🏆 Top 5 基因详情:")
    for i, (ws, genome_dict, roi, sharpe, dd) in enumerate(genes[:5], 1):
        # genome_dict已经是StrategyParams字典
        print(f"\n  #{i} ROI: {roi*100:+.2f}% | Sharpe: {sharpe:.2f}")
        print(f"      directional_bias: {genome_dict.get('directional_bias', 0.5):.3f}")
        print(f"      position_size: {genome_dict.get('position_size_base', 0.3):.3f}")
        print(f"      holding_pref: {genome_dict.get('holding_preference', 0.5):.3f}")
    
    db.close()


def main():
    db_path = "experience/gene_collection_v6.db"
    
    print("="*80)
    print("🔬 基因特征分析报告")
    print("="*80)
    print(f"数据库: {db_path}")
    
    # 分析各市场
    analyze_market_genes(db_path, "bull")
    analyze_market_genes(db_path, "bear")
    analyze_market_genes(db_path, "sideways")
    
    # 总结建议
    print("\n" + "="*80)
    print("💡 种群调度设计建议")
    print("="*80)
    
    print("""
基于基因分析，建议的调度规则：

1. 牛市环境：
   - 激活 directional_bias > 0.6 的Agent（做多型）
   - 抑制 directional_bias < 0.4 的Agent（做空型）
   - activity_level = bias (线性映射)

2. 熊市环境：
   - 激活 directional_bias < 0.4 的Agent（做空型）
   - 抑制 directional_bias > 0.6 的Agent（做多型）
   - activity_level = (1 - bias) (反向映射)

3. 震荡环境：
   - 抑制所有Agent的交易频率
   - activity_level = 0.3 (统一降低)
   - 或者只激活中性型 (0.4 <= bias <= 0.6)

实现代码示例：
```python
def calculate_activity_level(agent_bias, market_type):
    if market_type == 'bull':
        # 牛市：bias越高越活跃
        return max(0.1, min(1.0, agent_bias))
    
    elif market_type == 'bear':
        # 熊市：bias越低越活跃
        return max(0.1, min(1.0, 1.0 - agent_bias))
    
    else:  # sideways
        # 震荡市：统一抑制
        return 0.3
```
""")
    
    print("="*80)


if __name__ == "__main__":
    main()

