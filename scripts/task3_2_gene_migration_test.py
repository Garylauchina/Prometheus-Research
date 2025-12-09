"""
Task 3.2: 基因迁移性测试
=========================

核心问题：
  在市场A训练的基因，在市场B是否仍然有效？
  
这是v7.0架构的基础假设验证！

测试方法：
  1. 提取Top 4基因（在switching market训练）
  2. 在3种新市场中测试：
     - 新的switching market（不同随机种子）
     - 纯熊市（验证做空基因）
     - 纯牛市（验证是否过度特化）
  3. 对比表现，评估迁移性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
import numpy as np
import pandas as pd
from prometheus.facade.v6_facade import V6Facade
from prometheus.config.mock_training_config import MockTrainingConfig
from prometheus.core.strategy_params import StrategyParams
from prometheus.utils.market_generator import MarketStructureGenerator


def load_top_genes_from_db(db_path: str = 'experience/stage1_1_full_training.db', top_k: int = 4):
    """从数据库加载Top基因"""
    print("\n" + "="*80)
    print("Step 1: 加载Top基因")
    print("="*80 + "\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("""
        SELECT roi, profit_factor, trade_count, genome
        FROM best_genomes
        WHERE profit_factor >= 2.0
        ORDER BY profit_factor DESC
        LIMIT ?
    """, (top_k,))
    
    genes = []
    for i, (roi, pf, trade_count, genome_str) in enumerate(cursor):
        genome = json.loads(genome_str)
        genes.append({
            'id': i + 1,
            'roi': roi,
            'pf': pf,
            'trade_count': trade_count,
            'genome': genome
        })
        print(f"基因 #{i+1}:")
        print(f"  原始ROI: {roi*100:+.2f}%")
        print(f"  原始PF: {pf:,.2f}")
        print(f"  交易数: {trade_count}")
        print(f"  方向偏好: {genome['directional_bias']:.3f}")
        print(f"  持仓偏好: {genome['holding_preference']:.3f}")
        print("")
    
    conn.close()
    
    if not genes:
        print("❌ 未找到优质基因（PF≥2.0）")
        return []
    
    print(f"✅ 加载了 {len(genes)} 个优质基因\n")
    return genes


def generate_test_markets():
    """生成3种测试市场"""
    print("\n" + "="*80)
    print("Step 2: 生成测试市场")
    print("="*80 + "\n")
    
    markets = {}
    
    # 测试市场1: 新的switching market（不同随机种子）
    print("生成测试市场1: Switching Market (新随机种子)")
    generator = MarketStructureGenerator(random_seed=999)  # 不同的种子
    markets['switching_new'] = generator.generate_switching_market(
        structures=['trend_up', 'range', 'trend_down', 'fake_breakout'],
        bars_per_structure=300,
        total_bars=5000,
        structure_cycle=True
    )
    print(f"  ✅ 生成了 {len(markets['switching_new'])} bars")
    
    # 测试市场2: 纯熊市（验证做空基因）
    print("\n生成测试市场2: 纯熊市")
    bear_data, _ = generator._generate_trend_down(
        bars=5000,
        start_price=150000.0  # 从高位开始
    )
    markets['pure_bear'] = pd.DataFrame(
        bear_data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    markets['pure_bear']['timestamp'] = range(len(markets['pure_bear']))
    start = markets['pure_bear'].iloc[0]['close']
    end = markets['pure_bear'].iloc[-1]['close']
    print(f"  ✅ 生成了 {len(markets['pure_bear'])} bars")
    print(f"  价格: ${start:,.2f} → ${end:,.2f} ({(end/start-1)*100:+.2f}%)")
    
    # 测试市场3: 纯牛市（验证是否过度特化）
    print("\n生成测试市场3: 纯牛市")
    bull_data, _ = generator._generate_trend_up(
        bars=5000,
        start_price=40000.0  # 从低位开始
    )
    markets['pure_bull'] = pd.DataFrame(
        bull_data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    markets['pure_bull']['timestamp'] = range(len(markets['pure_bull']))
    start = markets['pure_bull'].iloc[0]['close']
    end = markets['pure_bull'].iloc[-1]['close']
    print(f"  ✅ 生成了 {len(markets['pure_bull'])} bars")
    print(f"  价格: ${start:,.2f} → ${end:,.2f} ({(end/start-1)*100:+.2f}%)")
    
    return markets


def test_gene_in_market(gene, market_data, market_name, facade):
    """测试单个基因在指定市场的表现"""
    
    # 创建配置
    config = MockTrainingConfig(
        total_cycles=len(market_data),
        initial_capital=500000,
        initial_agent_count=1,  # 只测试一个Agent
        genesis_strategy='smart',  # 使用智能创世
        evolution_interval=999999,  # 不进化
        elimination_rate=0.0,  # 不淘汰
        elite_ratio=1.0,
        mutation_rate=0.0,  # 不突变
        fitness_mode='profit_factor',
        market_type='test',
        save_experience=False,  # 不保存
        save_experience_interval=999999,
        top_k_to_save=0,
        log_interval=1000
    )
    
    # 运行测试
    try:
        result = facade.run_mock_training(
            market_data=market_data,
            config=config
        )
        
        return {
            'success': True,
            'system_roi': result.system_roi,
            'agent_best_roi': result.agent_best_roi,
            'agent_avg_roi': result.agent_avg_roi,
            'final_capital': result.final_capital
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def run_migration_test():
    """主测试流程"""
    print("\n" + "🧪"*40)
    print("Task 3.2: 基因迁移性测试")
    print("🧪"*40)
    
    # Step 1: 加载基因
    genes = load_top_genes_from_db()
    if not genes:
        return
    
    # Step 2: 生成测试市场
    markets = generate_test_markets()
    
    # Step 3: 测试每个基因在每个市场的表现
    print("\n" + "="*80)
    print("Step 3: 执行迁移性测试")
    print("="*80 + "\n")
    
    facade = V6Facade()
    
    results = {}
    
    for market_name, market_data in markets.items():
        print(f"\n{'─'*80}")
        print(f"测试市场: {market_name}")
        print(f"{'─'*80}\n")
        
        results[market_name] = []
        
        for gene in genes:
            print(f"  测试基因 #{gene['id']} (原始ROI: {gene['roi']*100:+.2f}%)...")
            
            # TODO: 实际测试需要实现"智能创世加载指定基因"功能
            # 这里暂时用placeholder
            result = {
                'gene_id': gene['id'],
                'original_roi': gene['roi'],
                'original_pf': gene['pf'],
                'test_roi': None,  # TODO: 实际测试
                'test_pf': None,
                'migration_score': None
            }
            
            results[market_name].append(result)
            
            print(f"    ⚠️ TODO: 需要实现'加载指定基因创世'功能")
    
    # Step 4: 分析结果
    print("\n" + "="*80)
    print("Step 4: 迁移性分析")
    print("="*80 + "\n")
    
    print("⚠️ 当前为框架代码，需要实现以下功能：")
    print("  1. V6Facade支持'加载指定基因创世'")
    print("  2. MockTrainingSchool支持单Agent测试模式")
    print("  3. 完整的迁移性评分计算")
    
    print("\n💡 预期输出格式：")
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │ 基因迁移性测试结果                                            │
    ├─────────────────────────────────────────────────────────────┤
    │ 基因ID │ 原始ROI  │ Switching │ 纯熊市  │ 纯牛市  │ 平均迁移性 │
    ├────────┼──────────┼───────────┼─────────┼─────────┼───────────┤
    │   1    │ +69229%  │   +45000% │ +60000% │  -20%   │    73%    │
    │   2    │ +69229%  │   +50000% │ +65000% │  -15%   │    76%    │
    │   3    │ +69229%  │   +48000% │ +62000% │  -18%   │    74%    │
    │   4    │   +41%   │     +30%  │   +25%  │  +15%   │    68%    │
    └────────┴──────────┴───────────┴─────────┴─────────┴───────────┘
    
    ✅ 结论：
       - 平均迁移性: 72.8% (优秀)
       - 做空基因在熊市表现稳定（~90%迁移性）
       - 在牛市亏损正常（说明基因特化，不是万能）
       - 基因库策略可行！可以继续v6.5/v7.0开发
    """)
    
    return results


if __name__ == '__main__':
    results = run_migration_test()
    
    print("\n" + "="*80)
    print("✅ Task 3.2 框架完成")
    print("="*80)
    print("\n下一步：")
    print("  1. 实现V6Facade.run_mock_training_with_genes()方法")
    print("  2. 运行完整测试")
    print("  3. 根据迁移性结果决定下一步")
    print("")

