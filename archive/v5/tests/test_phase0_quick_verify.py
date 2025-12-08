#!/usr/bin/env python3
"""
Phase 0: 快速验证 - AlphaZero式简化后系统稳定性测试

目标：
1. 验证full_genome_unlock后系统不崩溃
2. 验证简化Fitness后演化能正常进行
3. 验证关闭Immigration后种群不会灭绝

测试规模：10 seeds × 50 cycles = 500次实验（约30-60分钟）
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from prometheus.facade.v6_facade import run_scenario
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('test_phase0.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_quick_verify(num_seeds: int = 10, cycles_per_seed: int = 50):
    """
    快速验证测试
    
    Args:
        num_seeds: 测试的seed数量
        cycles_per_seed: 每个seed运行的周期数
    """
    logger.info("=" * 80)
    logger.info("🚀 Phase 0: 快速验证测试开始")
    logger.info(f"配置: {num_seeds} seeds × {cycles_per_seed} cycles")
    logger.info("=" * 80)
    
    # 加载市场数据
    logger.info("📊 加载历史数据...")
    try:
        df_btc = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
        if df_btc.empty:
            logger.error("❌ 数据文件为空")
            return
        logger.info(f"✅ 数据加载成功: {len(df_btc)} 条记录")
    except FileNotFoundError:
        logger.error("❌ 数据文件不存在: data/okx/BTC_USDT_1d_20251206.csv")
        logger.error("💡 请先下载数据: python3 tools/download_okx_data.py")
        return
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return
    
    # 构造market_feed函数
    prices = df_btc['close'].tolist()
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    # 测试配置
    results = []
    crashes = []
    
    for seed_idx in range(num_seeds):
        seed = 8000 + seed_idx
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 测试 {seed_idx+1}/{num_seeds}: seed={seed}")
        logger.info(f"{'='*60}")
        
        try:
            # ⭐ 关键配置：AlphaZero式简化
            result = run_scenario(
                mode="backtest",
                total_cycles=cycles_per_seed,
                market_feed=make_market_feed(),
                
                # 种群配置
                num_families=50,
                agent_count=50,
                capital_per_agent=10000.0,
                
                # 演化配置
                evo_interval=10,  # 每10周期进化一次
                
                # Seed配置
                seed=None,  # 主seed为None（数据加载用）
                genesis_seed=seed,  # 创世seed固定
                evolution_seed=None,  # 演化seed真随机
                
                # ⭐ AlphaZero式简化：全开基因
                full_genome_unlock=True  # 50个参数全开
            )
            
            # 提取结果
            facade = result
            moirai = facade.moirai
            
            # 统计（使用state判断存活）
            from prometheus.core.agent_v5 import AgentState
            alive_agents = len([a for a in moirai.agents if a.state != AgentState.DEAD])
            total_trades = sum(len(a.account.private_ledger.trade_history) 
                             for a in moirai.agents if hasattr(a, 'account') and a.account)
            
            # 计算系统收益
            agent_count = len(moirai.agents)
            system_initial = agent_count * 10000.0
            current_price = prices[min(cycles_per_seed - 1, len(prices) - 1)]
            system_current = sum(
                a.account.private_ledger.virtual_capital + a.calculate_unrealized_pnl(current_price)
                for a in moirai.agents if hasattr(a, 'account') and a.account
            )
            system_return = (system_current - system_initial) / system_initial * 100
            
            # 记录结果
            result_entry = {
                'seed': seed,
                'cycles': cycles_per_seed,
                'alive_agents': alive_agents,
                'total_trades': total_trades,
                'system_return': system_return,
                'avg_trades_per_agent': total_trades / agent_count if agent_count > 0 else 0,
                'status': 'success'
            }
            results.append(result_entry)
            
            logger.info(f"✅ Seed {seed} 完成:")
            logger.info(f"   存活Agent: {alive_agents}/{agent_count}")
            logger.info(f"   总交易数: {total_trades}")
            logger.info(f"   系统收益: {system_return:+.2f}%")
            logger.info(f"   人均交易: {result_entry['avg_trades_per_agent']:.1f}笔")
            
        except Exception as e:
            logger.error(f"❌ Seed {seed} 崩溃: {e}")
            crashes.append({
                'seed': seed,
                'error': str(e)
            })
            results.append({
                'seed': seed,
                'status': 'crashed',
                'error': str(e)
            })
    
    # ========== 汇总分析 ==========
    logger.info("\n" + "=" * 80)
    logger.info("📊 Phase 0 测试汇总")
    logger.info("=" * 80)
    
    success_results = [r for r in results if r['status'] == 'success']
    
    if len(success_results) == 0:
        logger.error("❌ 所有测试都失败了！系统无法运行！")
        return
    
    # 统计
    avg_alive = sum(r['alive_agents'] for r in success_results) / len(success_results)
    avg_trades = sum(r['total_trades'] for r in success_results) / len(success_results)
    avg_return = sum(r['system_return'] for r in success_results) / len(success_results)
    avg_trades_per_agent = sum(r['avg_trades_per_agent'] for r in success_results) / len(success_results)
    
    # 获取agent数量（从第一个成功的结果）
    agent_count = 50  # 默认值
    
    logger.info(f"✅ 成功率: {len(success_results)}/{num_seeds} ({len(success_results)/num_seeds*100:.1f}%)")
    logger.info(f"📈 平均存活Agent: {avg_alive:.1f}/{agent_count}")
    logger.info(f"💰 平均系统收益: {avg_return:+.2f}%")
    logger.info(f"📊 平均总交易数: {avg_trades:.0f}笔")
    logger.info(f"👤 平均每Agent交易: {avg_trades_per_agent:.1f}笔")
    
    if len(crashes) > 0:
        logger.warning(f"\n⚠️ {len(crashes)}个seed崩溃:")
        for crash in crashes:
            logger.warning(f"   Seed {crash['seed']}: {crash['error']}")
    
    # ========== 判断是否通过 ==========
    logger.info("\n" + "=" * 80)
    logger.info("🎯 验证结果判定")
    logger.info("=" * 80)
    
    passed = True
    
    # 检查1：稳定性
    if len(success_results) < num_seeds * 0.8:  # 至少80%成功
        logger.error(f"❌ 稳定性不足: 成功率 {len(success_results)/num_seeds*100:.1f}% < 80%")
        passed = False
    else:
        logger.info(f"✅ 稳定性: {len(success_results)/num_seeds*100:.1f}% ≥ 80%")
    
    # 检查2：种群存活
    if avg_alive < agent_count * 0.5:  # 至少50% Agent存活
        logger.error(f"❌ 种群灭绝风险: 平均存活 {avg_alive:.1f}/{agent_count} < 50%")
        passed = False
    else:
        logger.info(f"✅ 种群健康: {avg_alive:.1f}/{agent_count} ≥ 50%")
    
    # 检查3：交易活跃度
    if avg_trades < 10:  # 至少有10笔交易
        logger.warning(f"⚠️ 交易过少: {avg_trades:.0f}笔 < 10笔（可能过于保守）")
    else:
        logger.info(f"✅ 交易活跃: {avg_trades:.0f}笔 ≥ 10笔")
    
    # 检查4：不要求盈利（现阶段）
    logger.info(f"ℹ️ 系统收益: {avg_return:+.2f}%（Phase 0不要求盈利）")
    
    # ========== 最终判定 ==========
    if passed:
        logger.info("\n🎉 Phase 0 快速验证通过！")
        logger.info("✅ 系统稳定，可以进入Phase 1（同seed大规模训练）")
    else:
        logger.error("\n❌ Phase 0 快速验证失败！")
        logger.error("🛠️ 需要先修复稳定性问题，再进行大规模训练")
    
    # ========== 保存结果 ==========
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/phase0_verify_{timestamp}.json"
    Path("results").mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'config': {
                'num_seeds': num_seeds,
                'cycles_per_seed': cycles_per_seed,
                'full_genome_unlock': True
            },
            'summary': {
                'success_rate': len(success_results) / num_seeds,
                'avg_alive_agents': avg_alive,
                'avg_system_return': avg_return,
                'avg_trades': avg_trades,
                'avg_trades_per_agent': avg_trades_per_agent
            },
            'results': results,
            'crashes': crashes,
            'passed': passed
        }, f, indent=2)
    
    logger.info(f"\n💾 结果已保存: {output_file}")
    
    return passed


if __name__ == "__main__":
    passed = run_quick_verify(num_seeds=10, cycles_per_seed=50)
    sys.exit(0 if passed else 1)

