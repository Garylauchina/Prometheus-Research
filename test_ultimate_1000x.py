#!/usr/bin/env python3
"""
终极测试：1000次 × 2000步超长周期
=====================================

目标：
- 验证系统在极端长期下的表现
- 1000次不同随机种子，全面评估
- 发现所有可能的极端情况
- 得到最准确的统计结果

特性：
- 支持分批运行（每批100次）
- 支持断点续传（保存中间结果）
- 实时进度显示
- 自动生成统计报告
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from pathlib import Path

logging.basicConfig(level=logging.ERROR)


def run_single_test(seed, steps=2000, evolution_interval=30):
    """运行单次测试"""
    
    # 设置随机种子
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    try:
        # 加载数据
        df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 初始化系统
        moirai = Moirai()
        evolution_manager = EvolutionManagerV5(moirai=moirai)
        
        # 创建初始Agent
        agents = moirai._genesis_create_agents(
            agent_count=50,  # 使用50个Agent
            gene_pool=[],
            capital_per_agent=10000.0
        )
        
        for agent in agents:
            agent.fitness = 1.0
        
        moirai.agents = agents
        
        # 记录初始特质
        initial_traits = {
            'avg_risk': np.mean([getattr(a.instinct, 'risk_tolerance', 0.5) for a in agents]),
            'avg_time': np.mean([getattr(a.instinct, 'time_preference', 0.5) for a in agents]),
            'avg_loss': np.mean([getattr(a.instinct, 'loss_aversion', 0.5) for a in agents]),
        }
        
        # 运行回测
        current_step = 0
        evolution_count = 0
        total_trades = 0
        total_liquidations = 0
        
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
                time_preference = getattr(agent.instinct, 'time_preference', 0.5)
                
                # 简化决策逻辑
                if abs(price_change) < 0.001:
                    position = 0.0
                elif price_change > 0:
                    position = risk_tolerance * 0.8
                else:
                    position = -risk_tolerance * 0.8
                
                if position != 0:
                    total_trades += 1
                
                # 杠杆选择
                if risk_tolerance < 0.6:
                    leverage = 3.0 + (risk_tolerance - 0.2) * 10
                else:
                    leverage = 5.0 + (risk_tolerance - 0.6) * 25
                
                leverage = min(max(leverage, 1.0), 100.0)
                
                # 计算收益
                base_return = price_change * position
                leveraged_return = base_return * leverage
                
                # 交易成本
                if abs(position) > 0.01:
                    trading_fee = 0.001  # 0.10%
                    slippage = 0.0001     # 0.01%
                    funding_rate = 0.0003  # 0.03%
                    total_cost = trading_fee + slippage + funding_rate
                    leveraged_return -= total_cost * leverage
                
                # 检查爆仓
                if leveraged_return <= -1.0:
                    agent.current_capital = 0.0
                    total_liquidations += 1
                else:
                    agent.current_capital *= (1 + leveraged_return)
            
            # 定期进化
            if current_step % evolution_interval == 0:
                evolution_count += 1
                agents = [a for a in agents if a.current_capital > 0]
                moirai.agents = agents
                
                if len(agents) > 0:
                    try:
                        evolution_manager.run_evolution_cycle()
                        agents = moirai.agents
                    except:
                        pass
        
        # 记录最终特质
        if len(agents) > 0:
            final_traits = {
                'avg_risk': np.mean([getattr(a.instinct, 'risk_tolerance', 0.5) for a in agents]),
                'avg_time': np.mean([getattr(a.instinct, 'time_preference', 0.5) for a in agents]),
                'avg_loss': np.mean([getattr(a.instinct, 'loss_aversion', 0.5) for a in agents]),
            }
        else:
            final_traits = {'avg_risk': 0, 'avg_time': 0, 'avg_loss': 0}
        
        # 收集结果
        final_capitals = [a.current_capital for a in agents if a.current_capital > 0]
        
        # 计算所有Agent的平均（包括死亡的）
        all_agents_capital = [a.current_capital for a in moirai.agents]
        if len(all_agents_capital) == 0:
            all_agents_capital = [0] * 50
        
        # 补齐到50个（已死亡的为0）
        while len(all_agents_capital) < 50:
            all_agents_capital.append(0)
        
        avg_all_agents = np.mean(all_agents_capital)
        roi_all = (avg_all_agents / 10000 - 1) * 100
        
        if len(final_capitals) > 0:
            avg_survivors = np.mean(final_capitals)
            median_survivors = np.median(final_capitals)
            max_capital = np.max(final_capitals)
            min_capital = np.min(final_capitals)
            roi_survivors = (avg_survivors / 10000 - 1) * 100
        else:
            avg_survivors = 0
            median_survivors = 0
            max_capital = 0
            min_capital = 0
            roi_survivors = -100
        
        # 计算市场收益
        market_start = df.iloc[0]['close']
        market_end = df.iloc[steps - 1]['close']
        market_roi = (market_end / market_start - 1) * 100
        
        return {
            'seed': seed,
            'success': True,
            'survivors': len(agents),
            'evolution_count': evolution_count,
            'total_trades': total_trades,
            'total_liquidations': total_liquidations,
            'avg_all_agents': avg_all_agents,
            'roi_all': roi_all,
            'avg_survivors': avg_survivors,
            'roi_survivors': roi_survivors,
            'median_survivors': median_survivors,
            'max_capital': max_capital,
            'min_capital': min_capital,
            'market_roi': market_roi,
            'initial_traits': initial_traits,
            'final_traits': final_traits,
        }
    
    except Exception as e:
        return {
            'seed': seed,
            'success': False,
            'error': str(e),
            'roi_all': -100,
            'roi_survivors': -100,
        }


def load_progress(progress_file):
    """加载进度"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'completed': 0, 'results': []}


def save_progress(progress_file, progress):
    """保存进度"""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def generate_report(results, save_path):
    """生成统计报告"""
    
    # 过滤成功的结果
    successful = [r for r in results if r.get('success', True)]
    
    if len(successful) == 0:
        print("❌ 没有成功的测试结果")
        return
    
    # 基本统计
    rois_all = [r['roi_all'] for r in successful]
    rois_survivors = [r['roi_survivors'] for r in successful]
    survivors_counts = [r['survivors'] for r in successful]
    
    report = []
    report.append("=" * 80)
    report.append("📊 1000次超长周期测试统计报告")
    report.append("=" * 80)
    report.append("")
    report.append(f"测试次数: {len(successful)}")
    report.append(f"成功率: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    report.append("")
    
    # ROI统计（所有Agent）
    report.append("📈 ROI统计（包括所有Agent，消除幸存者偏差）:")
    report.append("")
    
    avg_roi = np.mean(rois_all)
    median_roi = np.median(rois_all)
    std_roi = np.std(rois_all)
    min_roi = np.min(rois_all)
    max_roi = np.max(rois_all)
    
    profitable_count = sum(1 for r in rois_all if r > 0)
    profitable_rate = profitable_count / len(rois_all) * 100
    
    report.append(f"   平均ROI: {avg_roi:+.2f}%")
    report.append(f"   中位数ROI: {median_roi:+.2f}%")
    report.append(f"   标准差: ±{std_roi:.2f}%")
    report.append(f"   最好: {max_roi:+.2f}%")
    report.append(f"   最差: {min_roi:+.2f}%")
    report.append(f"   盈利率: {profitable_rate:.1f}% ({profitable_count}/{len(rois_all)})")
    report.append("")
    
    # 变异系数
    if avg_roi != 0:
        cv = abs(std_roi / avg_roi) * 100
        report.append(f"   变异系数: {cv:.2f}%")
    report.append("")
    
    # 分位数
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    report.append("   分位数分布:")
    for p in percentiles:
        val = np.percentile(rois_all, p)
        report.append(f"      {p}%: {val:+.2f}%")
    report.append("")
    
    # 幸存者统计
    report.append("👥 幸存者统计:")
    report.append("")
    report.append(f"   平均幸存: {np.mean(survivors_counts):.1f}个")
    report.append(f"   中位数: {np.median(survivors_counts):.0f}个")
    report.append(f"   最多: {np.max(survivors_counts)}个")
    report.append(f"   最少: {np.min(survivors_counts)}个")
    report.append(f"   幸存率: {np.mean(survivors_counts)/50*100:.1f}%")
    report.append("")
    
    # 市场对比
    if successful[0].get('market_roi'):
        market_roi = successful[0]['market_roi']
        report.append(f"📊 市场对比:")
        report.append("")
        report.append(f"   市场收益: {market_roi:+.2f}%")
        report.append(f"   系统收益: {avg_roi:+.2f}%")
        report.append(f"   超额收益: {avg_roi - market_roi:+.2f}%")
        report.append(f"   倍数: {avg_roi / market_roi if market_roi > 0 else 0:.2f}x")
        report.append("")
    
    # 写入文件
    report_text = "\n".join(report)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # 打印到控制台
    print()
    print(report_text)
    print("=" * 80)
    print()
    print(f"💾 详细报告已保存: {save_path}")


def main():
    print()
    print("=" * 80)
    print("🚀 终极测试：1000次 × 2000步超长周期")
    print("=" * 80)
    print()
    
    # 配置
    total_tests = 1000
    batch_size = 100
    steps = 2000  # 5.5年完整数据
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    progress_file = f"ultimate_1000x_progress_{timestamp}.json"
    results_file = f"ultimate_1000x_results_{timestamp}.json"
    report_file = f"ULTIMATE_1000X_REPORT_{timestamp}.md"
    
    print(f"📋 测试配置:")
    print(f"   总测试次数: {total_tests}")
    print(f"   每次步数: {steps}步（约5.5年）")
    print(f"   批次大小: {batch_size}次/批")
    print(f"   总批次: {total_tests // batch_size}")
    print(f"   预计耗时: 3-5小时")
    print()
    print(f"💾 进度文件: {progress_file}")
    print(f"💾 结果文件: {results_file}")
    print(f"💾 报告文件: {report_file}")
    print()
    print("=" * 80)
    print()
    
    # 加载进度
    progress = load_progress(progress_file)
    completed = progress['completed']
    results = progress['results']
    
    if completed > 0:
        print(f"📂 检测到已完成 {completed} 次测试，继续执行...")
        print()
    
    # 运行测试
    start_time = datetime.now()
    
    for i in range(completed, total_tests):
        seed = i * 1000  # 使用较大间隔的种子
        
        # 显示进度
        batch_num = i // batch_size + 1
        batch_progress = (i % batch_size) + 1
        overall_progress = (i + 1) / total_tests * 100
        
        print(f"   [{batch_num}/{total_tests//batch_size}] 测试 #{i+1}/{total_tests} ({overall_progress:.1f}%) seed={seed}...", end=" ")
        
        # 运行测试
        result = run_single_test(seed, steps=steps)
        results.append(result)
        
        # 显示结果
        if result['success']:
            roi = result['roi_all']
            survivors = result['survivors']
            status = "✅盈利" if roi > 0 else "❌亏损"
            print(f"{status} ROI:{roi:+.1f}% 幸存:{survivors}个")
        else:
            print(f"❌失败: {result.get('error', '未知错误')}")
        
        # 更新进度
        progress['completed'] = i + 1
        progress['results'] = results
        
        # 每10次保存一次进度
        if (i + 1) % 10 == 0:
            save_progress(progress_file, progress)
        
        # 每批次结束生成阶段性报告
        if (i + 1) % batch_size == 0:
            print()
            print(f"   批次 #{batch_num} 完成！生成阶段性报告...")
            interim_report = report_file.replace('.md', f'_batch{batch_num}.md')
            generate_report(results, interim_report)
            print()
    
    # 最终保存
    save_progress(progress_file, progress)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 生成最终报告
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 80)
    print()
    print(f"🎉 测试完成！")
    print(f"   耗时: {duration}")
    print(f"   成功: {sum(1 for r in results if r.get('success', True))}/{len(results)}")
    print()
    
    # 生成最终报告
    generate_report(results, report_file)
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

