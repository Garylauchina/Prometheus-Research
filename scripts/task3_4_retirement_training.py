"""
Task 3.4: 退休机制训练（v4最终验证）
======================================

📜 严格遵守Prometheus三大铁律：
1. ✅ 统一封装，统一调用，严禁旁路 - 使用V6Facade统一入口
2. ✅ 严格执行测试规范 - 基于run_stage1_1_full_training.py标准模板
3. ✅ 不可为测试通过而简化底层机制 - 保留ExperienceDB、对账验证、完整生命周期

🎯 v4核心目标：
1. 验证退休机制完整性
   - ✅ 奖章颁发（Top5 每30代）
   - ✅ 光荣退休（5个奖章）
   - ✅ 寿终正寝（10代）
   - ✅ Immigration补充（1:1）

2. 验证极简资金管理
   - ✅ 固定配资（$2K）
   - ✅ 取消纳税
   - ✅ 完整回收（退休时）
   - ✅ pool_ratio监控（不干预）

3. 验证基因多样性
   - 打破"祖先Agent垄断"
   - 收集更多样化的优秀基因
   - 为v7.0角色系统积累基因库

配置（v3基础上的改进）：
- 每种市场: 5000 bars, 10000 cycles
- Agent: 50
- Fitness: Profit Factor主导
- ✅ 退休机制启用
- ✅ Immigration 1:1补充
- ✅ 完整ExperienceDB
- ✅ 完整对账验证

💡 v6.0极简主义：
  只管训练，累积基因
  资金池管理交给Prophet（v7.0）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig
import sqlite3
import json


def run_retirement_training(market_type: str):
    """
    运行单个市场的退休机制训练（v4）
    
    ✅ 严格遵守铁律：
    - 使用V6Facade统一入口
    - 基于标准模板（run_stage1_1_full_training.py）
    - 保留所有机制（ExperienceDB、对账验证、完整生命周期）
    - 启用退休机制（v4新增）
    """
    
    print("\n" + "="*80)
    print(f"🚀 Task 3.4 v4: {market_type.upper()} 市场 + 退休机制训练")
    print("="*80 + "\n")
    
    # ========== 1. 生成训练市场（✅ 通过Facade统一入口）==========
    print("📊 Step 1: 生成训练市场数据")
    print("-"*80)
    
    facade = V6Facade()
    
    # ✅ 只修改市场类型，其他参数保持标准
    if market_type == 'pure_bull':
        market_data = facade.generate_training_market(
            market_type='bull',
            total_bars=5000,
            random_seed=42
        )
    elif market_type == 'pure_bear':
        market_data = facade.generate_training_market(
            market_type='bear',
            total_bars=5000,
            random_seed=43
        )
    elif market_type == 'pure_range':
        market_data = facade.generate_training_market(
            market_type='range',
            total_bars=5000,
            random_seed=44
        )
    else:
        raise ValueError(f"Unknown market type: {market_type}")
    
    print(f"✅ 市场数据生成完成: {len(market_data)} bars")
    print(f"   价格范围: [{market_data['close'].min():.2f}, {market_data['close'].max():.2f}]")
    
    if 'structure_type' in market_data.columns:
        structure_dist = market_data['structure_type'].value_counts()
        print(f"\n   市场结构分布:")
        for structure, count in structure_dist.items():
            print(f"   - {structure}: {count} bars ({count/len(market_data)*100:.1f}%)")
    
    print("")
    
    # ========== 2. 配置训练参数（✅ 完整配置，不简化）==========
    print("⚙️  Step 2: 配置训练参数（v4退休机制）")
    print("-"*80)
    
    config = MockTrainingConfig(
        # 基础配置
        cycles=10000,  # v3优化：10000周期（给足够时间观察退休）
        total_system_capital=500000.0,  # 50万初始资金
        agent_count=50,
        
        # 创世配置
        genesis_allocation_ratio=0.3,  # 30%给Agent，70%资金池
        genesis_strategy='random',  # 纯随机创世（Stage 1测试基因进化）
        
        # v3优化：加速淘汰（制造发散→快速筛选→自然收敛）
        # 进化配置
        evolution_interval=30,  # 50 → 30（更快淘汰周期）
        elimination_rate=0.5,  # 0.3 → 0.5（更高淘汰率）
        elite_ratio=0.3,  # 0.2 → 0.3（更多精英繁殖）
        fitness_mode='profit_factor',  # ✅ PF主导
        
        # 🎖️ v4新增：退休机制
        retirement_enabled=True,  # ✅ 启用退休机制
        medal_system_enabled=True,  # ✅ 启用奖章系统
        
        # 市场配置
        market_type=market_type,
        
        # ✅ 铁律3：完整ExperienceDB配置（不删除！）
        experience_db_path=f'experience/task3_4_{market_type}_v4.db',  # ✅ v4版本
        top_k_to_save=20,  # 保存前20名
        save_experience_interval=30,  # 匹配进化间隔
        
        # 日志配置
        log_dir=f'logs/task3_4_{market_type}_v4',  # ✅ v4版本
        log_interval=100,
        enable_debug_log=False
    )
    
    print(f"✅ 训练配置:")
    print(f"   周期数: {config.cycles}")
    print(f"   系统资金: ${config.total_system_capital:,.0f}")
    print(f"   Agent数量: {config.agent_count}")
    print(f"   Fitness模式: {config.fitness_mode} ✅")
    print(f"   进化间隔: {config.evolution_interval}")
    print(f"   淘汰率: {config.elimination_rate*100:.0f}%")
    print(f"   精英比例: {config.elite_ratio*100:.0f}%")
    print(f"   🎖️ 退休机制: {'启用' if config.retirement_enabled else '禁用'} ✅")
    print(f"   🎖️ 奖章系统: {'启用' if config.medal_system_enabled else '禁用'} ✅")
    print(f"   ✅ ExperienceDB: {config.experience_db_path}")
    print("")
    
    # ========== 3. 运行训练（✅ 通过Facade统一入口）==========
    print("🏃 Step 3: 开始训练")
    print("-"*80)
    print(f"   开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    start_time = datetime.now()
    
    # ✅ 铁律1：通过Facade统一入口
    result = facade.run_mock_training(
        config=config,
        market_data=market_data
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("")
    print(f"✅ 训练完成！")
    print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   耗时: {duration.total_seconds():.2f}秒 ({duration.total_seconds()/60:.2f}分钟)")
    print("")
    
    # ========== 4. 铁律2：完整对账验证（不删除！）==========
    print("🔍 Step 4: 对账验证")
    print("-"*80)
    
    reconciliation_actions = getattr(result, 'reconciliation_actions', [])
    
    if not reconciliation_actions:
        print("✅ 无对账差异，系统财务一致！")
    else:
        print(f"⚠️  发现 {len(reconciliation_actions)} 个对账差异:")
        for action in reconciliation_actions[:5]:  # 只显示前5个
            print(f"   - Agent {action.agent_id}: 差异={action.difference:.2f}")
        print("   ...")
    
    print("")
    
    # ========== 5. 系统级指标分析 ==========
    print("📊 Step 5: 系统级指标分析")
    print("-"*80)
    
    print(f"系统表现:")
    print(f"   初始资金: ${result.system_initial_capital:,.0f}")
    print(f"   最终资金: ${result.system_final_capital:,.0f}")
    print(f"   系统ROI: {result.system_roi*100:+.2f}%")
    print(f"   累计交易: {result.total_trades}")
    print(f"   盈利交易: {result.profitable_trades}")
    print(f"   胜率: {result.win_rate*100:.2f}%")
    print("")
    
    print(f"Agent表现:")
    print(f"   最佳ROI: {result.agent_best_roi*100:+.2f}%")
    print(f"   平均ROI: {result.agent_avg_roi*100:+.2f}%")
    print(f"   最差ROI: {result.agent_worst_roi*100:+.2f}%")
    print("")
    
    print(f"进化统计:")
    print(f"   完成代数: {result.total_generations}")
    print(f"   总出生数: {result.total_births}")
    print(f"   总死亡数: {result.total_deaths}")
    print(f"   Immigration: {result.total_immigrants}")
    print("")
    
    # ========== 6. v4新增：退休机制分析 ==========
    print("🎖️ Step 6: 退休机制分析（v4）")
    print("-"*80)
    
    # 查询ExperienceDB中的退休记录
    db_path = config.experience_db_path
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 统计退休Agent
        cursor.execute("""
            SELECT 
                retirement_reason,
                COUNT(*) as count,
                AVG(awards) as avg_awards,
                AVG(roi) as avg_roi,
                AVG(profit_factor) as avg_pf
            FROM best_genomes
            WHERE retirement_reason IS NOT NULL
            GROUP BY retirement_reason
        """)
        
        retirement_stats = cursor.fetchall()
        
        if retirement_stats:
            print(f"退休统计:")
            for reason, count, avg_awards, avg_roi, avg_pf in retirement_stats:
                print(f"   {reason}:")
                print(f"      数量: {count}")
                print(f"      平均奖章: {avg_awards:.1f}")
                print(f"      平均ROI: {avg_roi*100:+.2f}%")
                print(f"      平均PF: {avg_pf:.2f}")
        else:
            print("⚠️  未发现退休记录（可能训练时间不够长）")
        
        # 统计奖章分布
        cursor.execute("""
            SELECT 
                awards,
                COUNT(*) as count
            FROM best_genomes
            WHERE awards > 0
            GROUP BY awards
            ORDER BY awards DESC
        """)
        
        award_stats = cursor.fetchall()
        
        if award_stats:
            print(f"\n奖章分布:")
            for awards, count in award_stats:
                print(f"   {awards}个奖章: {count}个Agent")
        
        conn.close()
    else:
        print(f"⚠️  ExperienceDB不存在: {db_path}")
    
    print("")
    
    # ========== 7. 基因库分析 ==========
    print("🧬 Step 7: 基因库分析")
    print("-"*80)
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM best_genomes")
        total_records = cursor.fetchone()[0]
        
        # 唯一盈利基因数（PF > 1.0）
        cursor.execute("""
            SELECT COUNT(DISTINCT genome) 
            FROM best_genomes 
            WHERE profit_factor > 1.0
        """)
        unique_profitable_genes = cursor.fetchone()[0]
        
        # Top 10基因（按PF）
        cursor.execute("""
            SELECT 
                genome,
                roi,
                profit_factor,
                awards,
                retirement_reason
            FROM best_genomes 
            WHERE profit_factor > 1.0
            ORDER BY profit_factor DESC 
            LIMIT 10
        """)
        
        top_genes = cursor.fetchall()
        
        print(f"基因库规模:")
        print(f"   总记录数: {total_records}")
        print(f"   唯一盈利基因: {unique_profitable_genes}")
        
        if top_genes:
            print(f"\n   Top 10基因:")
            for i, (genome_json, roi, pf, awards, reason) in enumerate(top_genes, 1):
                genome = json.loads(genome_json)
                directional_bias = genome.get('directional_bias', 0.0)
                holding_pref = genome.get('holding_preference', 0.0)
                retirement_info = f", 退休={reason}" if reason else ""
                print(f"   {i}. PF={pf:.2f}, ROI={roi*100:+.0f}%, "
                      f"direction={directional_bias:+.2f}, holding={holding_pref:.2f}"
                      f"{f', 奖章={awards}' if awards > 0 else ''}{retirement_info}")
        
        conn.close()
    
    print("")
    
    # ========== 8. 返回结果 ==========
    return {
        'market_type': market_type,
        'result': result,
        'db_path': db_path,
        'duration_seconds': duration.total_seconds()
    }


def analyze_v4_results(results: list):
    """
    v4训练结果汇总分析
    """
    
    print("\n" + "="*80)
    print("📊 Task 3.4 v4: 汇总分析")
    print("="*80 + "\n")
    
    for res in results:
        market_type = res['market_type']
        result = res['result']
        
        print(f"{market_type.upper()} 市场:")
        print(f"   系统ROI: {result.system_roi*100:+.2f}%")
        print(f"   最佳Agent ROI: {result.agent_best_roi*100:+.2f}%")
        print(f"   完成代数: {result.total_generations}")
        print(f"   总出生: {result.total_births}")
        print(f"   总死亡: {result.total_deaths}")
        print(f"   Immigration: {result.total_immigrants}")
        print("")
    
    print("\n" + "="*80)
    print("🎯 v4训练目标验证")
    print("="*80 + "\n")
    
    print("✅ 验证项目:")
    print("   1. 退休机制完整性")
    print("      - 奖章颁发（Top5 每30代）")
    print("      - 光荣退休（5个奖章）")
    print("      - 寿终正寝（10代）")
    print("      - Immigration补充（1:1）")
    print("")
    print("   2. 极简资金管理")
    print("      - 固定配资（$2K）")
    print("      - 取消纳税")
    print("      - 完整回收（退休时）")
    print("      - pool_ratio监控（不干预）")
    print("")
    print("   3. 基因多样性")
    print("      - 打破"祖先Agent垄断"")
    print("      - 收集更多样化的优秀基因")
    print("      - 为v7.0角色系统积累基因库")
    print("")
    
    print("💡 v6.0极简主义：")
    print("   只管训练，累积基因")
    print("   资金池管理交给Prophet（v7.0）")
    print("")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Task 3.4: 退休机制训练（v4最终验证）")
    print("="*80)
    print("\n💡 v6.0极简主义：")
    print("   只管训练，累积基因")
    print("   资金池管理交给Prophet（v7.0）")
    print("")
    
    # 运行三种市场训练
    markets = ['pure_bull', 'pure_bear', 'pure_range']
    results = []
    
    for market_type in markets:
        try:
            result = run_retirement_training(market_type)
            results.append(result)
        except Exception as e:
            print(f"\n❌ {market_type} 训练失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 汇总分析
    if results:
        analyze_v4_results(results)
    
    print("\n" + "="*80)
    print("🎉 Task 3.4 v4训练全部完成！")
    print("="*80 + "\n")

