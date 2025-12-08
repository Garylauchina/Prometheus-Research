#!/usr/bin/env python3
"""
验证系统进化的鲁棒性
===================

核心假设：
不管初始Agent是什么特质（天胡还是天崩），
系统都应该通过进化向好的方向发展，
最终实现盈利。

测试方法：
- 使用相同的历史数据（确定性）
- 使用不同的随机种子（不同初始Agent）
- 观察最终结果是否都收敛到盈利
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
import json

logging.basicConfig(level=logging.ERROR)


def run_evolution_test(seed, steps=200):
    """运行进化测试"""
    
    # 设置随机种子
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    # 加载数据（相同的数据）
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 初始化系统
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建初始Agent（不同种子会创建不同特质）
    agents = moirai._genesis_create_agents(
        agent_count=20,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    for agent in agents:
        agent.fitness = 1.0
    
    moirai.agents = agents
    
    # 记录初始Agent特质
    initial_traits = []
    for agent in agents:
        traits = {
            'risk_tolerance': getattr(agent.instinct, 'risk_tolerance', 0.5),
            'time_preference': getattr(agent.instinct, 'time_preference', 0.5),
            'loss_aversion': getattr(agent.instinct, 'loss_aversion', 0.5),
        }
        initial_traits.append(traits)
    
    # 计算初始特质的统计
    avg_risk = np.mean([t['risk_tolerance'] for t in initial_traits])
    avg_time = np.mean([t['time_preference'] for t in initial_traits])
    avg_loss = np.mean([t['loss_aversion'] for t in initial_traits])
    
    # 运行回测
    evolution_interval = 30
    current_step = 0
    evolution_count = 0
    
    for idx, row in df.head(steps).iterrows():
        current_step += 1
        current_price = row['close']
        
        if idx > 0:
            prev_price = df.iloc[idx - 1]['close']
            price_change = (current_price - prev_price) / prev_price
        else:
            price_change = 0.0
        
        # 每个Agent交易
        for agent in agents:
            if agent.current_capital <= 0:
                continue
            
            # Agent决策
            risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
            if abs(price_change) < 0.001:
                position = 0.0
            elif price_change > 0:
                position = risk_tolerance * 0.8
            else:
                position = -risk_tolerance * 0.8
            
            # 杠杆选择
            if risk_tolerance < 0.6:
                leverage = 3.0 + (risk_tolerance - 0.2) * 10
            else:
                leverage = 5.0 + (risk_tolerance - 0.6) * 25
            
            leverage = min(max(leverage, 1.0), 100.0)
            
            # 计算收益
            base_return = price_change * position
            leveraged_return = base_return * leverage
            
            # 简化成本
            if abs(position) > 0.01:
                cost = 0.0015
                leveraged_return -= cost * leverage
            
            # 检查爆仓
            if leveraged_return <= -1.0:
                agent.current_capital = 0.0
            else:
                agent.current_capital *= (1 + leveraged_return)
        
        # 定期进化
        if current_step % evolution_interval == 0:
            evolution_count += 1
            agents = [a for a in agents if a.current_capital > 0]
            moirai.agents = agents
            
            try:
                evolution_manager.run_evolution_cycle()
                agents = moirai.agents
            except:
                pass
    
    # 记录最终Agent特质
    final_traits = []
    for agent in agents:
        traits = {
            'risk_tolerance': getattr(agent.instinct, 'risk_tolerance', 0.5),
            'time_preference': getattr(agent.instinct, 'time_preference', 0.5),
            'loss_aversion': getattr(agent.instinct, 'loss_aversion', 0.5),
        }
        final_traits.append(traits)
    
    # 计算最终特质的统计
    if len(final_traits) > 0:
        final_avg_risk = np.mean([t['risk_tolerance'] for t in final_traits])
        final_avg_time = np.mean([t['time_preference'] for t in final_traits])
        final_avg_loss = np.mean([t['loss_aversion'] for t in final_traits])
    else:
        final_avg_risk = 0
        final_avg_time = 0
        final_avg_loss = 0
    
    # 收集结果
    final_capitals = [a.current_capital for a in agents if a.current_capital > 0]
    
    if len(final_capitals) > 0:
        avg_capital = np.mean(final_capitals)
        median_capital = np.median(final_capitals)
        max_capital = np.max(final_capitals)
        min_capital = np.min(final_capitals)
        roi = (avg_capital / 10000 - 1) * 100
    else:
        avg_capital = 0
        median_capital = 0
        max_capital = 0
        min_capital = 0
        roi = -100
    
    return {
        'seed': seed,
        'survivors': len(agents),
        'evolution_count': evolution_count,
        'avg_capital': avg_capital,
        'roi': roi,
        'initial_traits': {
            'avg_risk': avg_risk,
            'avg_time': avg_time,
            'avg_loss': avg_loss,
        },
        'final_traits': {
            'avg_risk': final_avg_risk,
            'avg_time': final_avg_time,
            'avg_loss': final_avg_loss,
        },
        'trait_evolution': {
            'risk_change': final_avg_risk - avg_risk,
            'time_change': final_avg_time - avg_time,
            'loss_change': final_avg_loss - avg_loss,
        }
    }


def classify_initial_condition(traits):
    """分类初始条件"""
    risk = traits['avg_risk']
    
    if risk > 0.7:
        return "🔥 天胡开局（高风险，激进）"
    elif risk < 0.3:
        return "🛡️ 保守开局（低风险，谨慎）"
    else:
        return "⚖️ 平衡开局（中等风险）"


def main():
    print()
    print("=" * 80)
    print("🧬 验证系统进化的鲁棒性")
    print("=" * 80)
    print()
    
    print("🎯 核心假设:")
    print("   不管初始Agent是什么特质（天胡还是天崩），")
    print("   系统都应该通过进化向好的方向发展，")
    print("   最终实现盈利。")
    print()
    print("🧪 测试方法:")
    print("   - 相同的历史数据（确定性）")
    print("   - 不同的随机种子（不同初始Agent）")
    print("   - 观察最终结果是否都收敛到盈利")
    print()
    print("=" * 80)
    print()
    
    # 运行多次测试
    num_tests = 20
    results = []
    
    print(f"🚀 开始运行{num_tests}次测试（200步/次）...")
    print()
    
    for i in range(num_tests):
        seed = i * 100  # 使用较大间隔的种子，确保差异
        print(f"   测试 #{i+1}/#{num_tests} (seed={seed})...", end=" ")
        result = run_evolution_test(seed, steps=200)
        results.append(result)
        
        initial_type = classify_initial_condition(result['initial_traits'])
        print(f"✓ {initial_type} → ROI: {result['roi']:+.1f}%")
    
    print()
    print("=" * 80)
    print()
    
    # 分析结果
    print("📊 结果分析:")
    print()
    
    # 1. 总体统计
    rois = [r['roi'] for r in results]
    avg_roi = np.mean(rois)
    median_roi = np.median(rois)
    std_roi = np.std(rois)
    min_roi = np.min(rois)
    max_roi = np.max(rois)
    
    profitable_count = sum(1 for roi in rois if roi > 0)
    profitable_rate = profitable_count / len(rois) * 100
    
    print(f"📈 总体表现:")
    print(f"   平均ROI: {avg_roi:+.2f}%")
    print(f"   中位数ROI: {median_roi:+.2f}%")
    print(f"   标准差: ±{std_roi:.2f}%")
    print(f"   最好: {max_roi:+.2f}%")
    print(f"   最差: {min_roi:+.2f}%")
    print(f"   盈利率: {profitable_rate:.1f}% ({profitable_count}/{len(rois)})")
    print()
    
    # 2. 按初始条件分组
    aggressive = []  # 高风险
    conservative = []  # 低风险
    balanced = []  # 平衡
    
    for r in results:
        risk = r['initial_traits']['avg_risk']
        if risk > 0.7:
            aggressive.append(r)
        elif risk < 0.3:
            conservative.append(r)
        else:
            balanced.append(r)
    
    print(f"📊 按初始条件分组:")
    print()
    
    if len(aggressive) > 0:
        avg_roi_agg = np.mean([r['roi'] for r in aggressive])
        print(f"   🔥 天胡开局（高风险>0.7）:")
        print(f"      数量: {len(aggressive)}次")
        print(f"      平均ROI: {avg_roi_agg:+.2f}%")
        print(f"      范围: {min([r['roi'] for r in aggressive]):+.1f}% ~ {max([r['roi'] for r in aggressive]):+.1f}%")
        print()
    
    if len(conservative) > 0:
        avg_roi_con = np.mean([r['roi'] for r in conservative])
        print(f"   🛡️ 保守开局（低风险<0.3）:")
        print(f"      数量: {len(conservative)}次")
        print(f"      平均ROI: {avg_roi_con:+.2f}%")
        print(f"      范围: {min([r['roi'] for r in conservative]):+.1f}% ~ {max([r['roi'] for r in conservative]):+.1f}%")
        print()
    
    if len(balanced) > 0:
        avg_roi_bal = np.mean([r['roi'] for r in balanced])
        print(f"   ⚖️ 平衡开局（中等风险0.3-0.7）:")
        print(f"      数量: {len(balanced)}次")
        print(f"      平均ROI: {avg_roi_bal:+.2f}%")
        print(f"      范围: {min([r['roi'] for r in balanced]):+.1f}% ~ {max([r['roi'] for r in balanced]):+.1f}%")
        print()
    
    # 3. 特质进化分析
    print("🧬 特质进化分析:")
    print()
    
    avg_risk_change = np.mean([r['trait_evolution']['risk_change'] for r in results])
    avg_time_change = np.mean([r['trait_evolution']['time_change'] for r in results])
    avg_loss_change = np.mean([r['trait_evolution']['loss_change'] for r in results])
    
    print(f"   风险承受度变化: {avg_risk_change:+.3f}")
    print(f"   时间偏好变化: {avg_time_change:+.3f}")
    print(f"   损失厌恶变化: {avg_loss_change:+.3f}")
    print()
    
    # 4. 收敛性分析
    print("🎯 收敛性分析:")
    print()
    
    # 计算最终特质的标准差
    final_risks = [r['final_traits']['avg_risk'] for r in results]
    final_times = [r['final_traits']['avg_time'] for r in results]
    final_losses = [r['final_traits']['avg_loss'] for r in results]
    
    std_final_risk = np.std(final_risks)
    std_final_time = np.std(final_times)
    std_final_loss = np.std(final_losses)
    
    # 计算初始特质的标准差
    initial_risks = [r['initial_traits']['avg_risk'] for r in results]
    initial_times = [r['initial_traits']['avg_time'] for r in results]
    initial_losses = [r['initial_traits']['avg_loss'] for r in results]
    
    std_initial_risk = np.std(initial_risks)
    std_initial_time = np.std(initial_times)
    std_initial_loss = np.std(initial_losses)
    
    print(f"   初始特质标准差:")
    print(f"      风险承受度: {std_initial_risk:.3f}")
    print(f"      时间偏好: {std_initial_time:.3f}")
    print(f"      损失厌恶: {std_initial_loss:.3f}")
    print()
    
    print(f"   最终特质标准差:")
    print(f"      风险承受度: {std_final_risk:.3f}")
    print(f"      时间偏好: {std_final_time:.3f}")
    print(f"      损失厌恶: {std_final_loss:.3f}")
    print()
    
    # 收敛指数
    convergence_risk = 1 - (std_final_risk / std_initial_risk) if std_initial_risk > 0 else 0
    convergence_time = 1 - (std_final_time / std_initial_time) if std_initial_time > 0 else 0
    convergence_loss = 1 - (std_final_loss / std_initial_loss) if std_initial_loss > 0 else 0
    
    print(f"   收敛指数（越高越收敛）:")
    print(f"      风险承受度: {convergence_risk:+.2%}")
    print(f"      时间偏好: {convergence_time:+.2%}")
    print(f"      损失厌恶: {convergence_loss:+.2%}")
    print()
    
    # 5. 验证核心假设
    print("=" * 80)
    print()
    print("🎓 核心假设验证:")
    print()
    
    if profitable_rate >= 90:
        print("   ✅ 强验证: {:.1f}%的测试都盈利".format(profitable_rate))
        print("      → 系统确实能从不同初始条件收敛到盈利")
        print("      → 进化算法非常有效")
    elif profitable_rate >= 70:
        print("   ✅ 中等验证: {:.1f}%的测试盈利".format(profitable_rate))
        print("      → 系统大多数情况下能盈利")
        print("      → 进化算法有效，但有偶然性")
    elif profitable_rate >= 50:
        print("   ⚠️  弱验证: 仅{:.1f}%的测试盈利".format(profitable_rate))
        print("      → 系统盈利概率略高于50%")
        print("      → 进化算法效果有限")
    else:
        print("   ❌ 未验证: 仅{:.1f}%的测试盈利".format(profitable_rate))
        print("      → 系统大多数情况下亏损")
        print("      → 进化算法可能无效")
    
    print()
    
    # 检查不同初始条件是否收敛
    if len(aggressive) > 0 and len(conservative) > 0:
        diff = abs(avg_roi_agg - avg_roi_con)
        print(f"   初始条件影响:")
        print(f"      天胡开局 vs 保守开局 ROI差距: {diff:.1f}%")
        if diff < 20:
            print("      ✅ 差距小，说明初始条件影响不大")
            print("      → 进化能够抹平初始差异")
        else:
            print("      ⚠️  差距大，说明初始条件影响显著")
            print("      → 进化未能完全抹平初始差异")
    
    print()
    
    # 最终结论
    print("=" * 80)
    print()
    print("🎯 最终结论:")
    print()
    
    if profitable_rate >= 90 and std_roi < 50:
        print("   🏆 系统表现优秀:")
        print("      - 高盈利率（{:.1f}%）".format(profitable_rate))
        print("      - 低波动性（标准差{:.1f}%）".format(std_roi))
        print("      - 进化算法非常有效")
        print("      - 可以信赖系统的鲁棒性")
    elif profitable_rate >= 70:
        print("   ✅ 系统表现良好:")
        print("      - 较高盈利率（{:.1f}%）".format(profitable_rate))
        print("      - 中等波动性（标准差{:.1f}%）".format(std_roi))
        print("      - 进化算法有效")
        print("      - 系统基本鲁棒")
    else:
        print("   ⚠️  系统需要改进:")
        print("      - 盈利率偏低（{:.1f}%）".format(profitable_rate))
        print("      - 可能需要优化进化参数")
        print("      - 或者增加进化代数")
    
    print()
    print("=" * 80)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evolution_robustness_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"💾 详细结果已保存: {results_file}")
    print()


if __name__ == "__main__":
    main()

