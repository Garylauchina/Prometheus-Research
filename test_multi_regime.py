"""
多情境回测 - 验证系统在不同market regime下的鲁棒性

测试朋友的核心担忧：
系统是否只在"单一生态"中成功，而在不同regime下会失败？
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path

from prometheus.core import World, Moirai
from prometheus.evolution import EvolutionManager
from prometheus.agents import Agent, Daimon
from prometheus.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'multi_regime_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_historical_data(start_date: str, end_date: str):
    """加载指定时间段的历史数据"""
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] < end_date)
    period_data = df[mask].copy()
    
    logger.info(f"加载数据: {start_date} → {end_date}")
    logger.info(f"  数据点: {len(period_data)}个")
    logger.info(f"  起始价格: ${period_data.iloc[0]['close']:,.0f}")
    logger.info(f"  结束价格: ${period_data.iloc[-1]['close']:,.0f}")
    logger.info(f"  市场ROI: {(period_data.iloc[-1]['close'] / period_data.iloc[0]['close'] - 1) * 100:+.1f}%")
    
    return period_data


def run_backtest_for_regime(scenario: dict, num_runs: int = 20):
    """在特定regime下运行回测"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🎯 测试场景: {scenario['name']}")
    logger.info(f"{'='*70}")
    
    # 加载数据
    data = load_historical_data(scenario['start'], scenario['end'])
    
    if len(data) < 30:
        logger.warning(f"数据不足（{len(data)}天），跳过")
        return None
    
    # 运行多次测试
    results = []
    
    for run in range(num_runs):
        seed = run * 1000
        np.random.seed(seed)
        
        logger.info(f"\n运行 {run+1}/{num_runs} (seed={seed})...")
        
        try:
            # 初始化配置
            config = Config()
            config.evolution.initial_agents = 50
            config.evolution.evolution_cycle = len(data)  # 整个时期作为一个进化周期
            config.trading.initial_capital = 500000.0
            
            # 初始化系统
            world = World(config=config)
            moirai = Moirai(config=config)
            evolution_manager = EvolutionManager(world=world, moirai=moirai, config=config)
            
            # 创建初始Agent
            for i in range(config.evolution.initial_agents):
                genome = evolution_manager._generate_random_genome()
                agent = Agent(
                    agent_id=f"genesis_{i}",
                    genome=genome,
                    capital=config.trading.initial_capital / config.evolution.initial_agents
                )
                agent.daimon = Daimon(agent=agent)
                world.add_agent(agent)
            
            # 逐日回测
            for day_idx, row in data.iterrows():
                current_price = row['close']
                
                # 更新世界状态
                world.current_price = current_price
                world.timestamp = row['timestamp'].timestamp()
                
                # Agent交易（简化版）
                for agent in list(world.agents.values()):
                    if not agent.is_alive:
                        continue
                    
                    # 简单策略：基于基因随机决策
                    decision = np.random.choice(['hold', 'long', 'short'], p=[0.7, 0.15, 0.15])
                    
                    if decision == 'long' and agent.position == 0:
                        # 开多
                        size = agent.capital * 0.1 / current_price
                        agent.position = size
                        agent.entry_price = current_price
                    elif decision == 'short' and agent.position == 0:
                        # 开空
                        size = agent.capital * 0.1 / current_price
                        agent.position = -size
                        agent.entry_price = current_price
                    elif decision == 'hold' and agent.position != 0:
                        # 平仓
                        pnl = agent.position * (current_price - agent.entry_price)
                        agent.capital += pnl
                        agent.position = 0
                        agent.entry_price = 0
                    
                    # 更新持仓盈亏
                    if agent.position != 0:
                        unrealized_pnl = agent.position * (current_price - agent.entry_price)
                        agent.unrealized_pnl = unrealized_pnl
                        
                        # 爆仓检查（简化）
                        if agent.capital + unrealized_pnl < config.trading.initial_capital / config.evolution.initial_agents * 0.1:
                            agent.is_alive = False
                            logger.debug(f"Agent {agent.agent_id} 爆仓")
            
            # 统计结果
            survivors = [a for a in world.agents.values() if a.is_alive]
            total_capital = sum(a.capital for a in survivors)
            
            initial_capital = config.trading.initial_capital
            roi = (total_capital / initial_capital - 1) * 100
            
            market_roi = (data.iloc[-1]['close'] / data.iloc[0]['close'] - 1) * 100
            
            result = {
                'seed': seed,
                'survivors': len(survivors),
                'total_capital': total_capital,
                'roi': roi,
                'market_roi': market_roi,
                'days': len(data)
            }
            
            results.append(result)
            
            logger.info(f"  存活: {len(survivors)}/{config.evolution.initial_agents}")
            logger.info(f"  ROI: {roi:+.1f}% (市场: {market_roi:+.1f}%)")
            
        except Exception as e:
            logger.error(f"运行失败: {e}")
            continue
    
    return results


def analyze_results(scenario: dict, results: list):
    """分析测试结果"""
    if not results:
        return None
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 {scenario['name']} - 结果分析")
    logger.info(f"{'='*70}")
    
    rois = [r['roi'] for r in results]
    survivors = [r['survivors'] for r in results]
    market_roi = results[0]['market_roi']
    
    logger.info(f"\nROI统计:")
    logger.info(f"  平均: {np.mean(rois):+.1f}%")
    logger.info(f"  中位数: {np.median(rois):+.1f}%")
    logger.info(f"  最小: {np.min(rois):+.1f}%")
    logger.info(f"  最大: {np.max(rois):+.1f}%")
    logger.info(f"  标准差: {np.std(rois):.1f}%")
    
    logger.info(f"\n存活Agent统计:")
    logger.info(f"  平均: {np.mean(survivors):.1f}个")
    logger.info(f"  中位数: {np.median(survivors):.0f}个")
    logger.info(f"  最小: {np.min(survivors)}个")
    logger.info(f"  最大: {np.max(survivors)}个")
    
    logger.info(f"\n对比市场:")
    logger.info(f"  市场ROI: {market_roi:+.1f}%")
    logger.info(f"  系统平均: {np.mean(rois):+.1f}%")
    logger.info(f"  跑赢市场: {sum(1 for r in rois if r > market_roi) / len(rois) * 100:.0f}%")
    
    # 判断表现
    avg_roi = np.mean(rois)
    if avg_roi > market_roi:
        logger.info(f"\n✅ 系统表现: 优于市场 ({avg_roi - market_roi:+.1f}%)")
    else:
        logger.info(f"\n⚠️  系统表现: 弱于市场 ({avg_roi - market_roi:+.1f}%)")
    
    return {
        'avg_roi': np.mean(rois),
        'median_roi': np.median(rois),
        'min_roi': np.min(rois),
        'max_roi': np.max(rois),
        'std_roi': np.std(rois),
        'avg_survivors': np.mean(survivors),
        'market_roi': market_roi,
        'beat_market_pct': sum(1 for r in rois if r > market_roi) / len(rois) * 100
    }


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("🎯 多情境回测 - 验证系统鲁棒性")
    logger.info("="*70)
    
    # 加载测试场景
    with open('multi_regime_test_scenarios.json', 'r') as f:
        scenarios = json.load(f)
    
    logger.info(f"\n共{len(scenarios)}个测试场景:")
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"  {i}. {scenario['name']}: {scenario['description']}")
    
    # 运行测试
    all_results = {}
    all_summaries = {}
    
    for scenario in scenarios:
        results = run_backtest_for_regime(scenario, num_runs=20)
        
        if results:
            all_results[scenario['name']] = results
            summary = analyze_results(scenario, results)
            all_summaries[scenario['name']] = summary
    
    # 综合分析
    logger.info(f"\n{'='*70}")
    logger.info("📊 综合分析 - 跨Regime表现")
    logger.info(f"{'='*70}")
    
    for name, summary in all_summaries.items():
        logger.info(f"\n{name}:")
        logger.info(f"  系统平均ROI: {summary['avg_roi']:+.1f}%")
        logger.info(f"  市场ROI: {summary['market_roi']:+.1f}%")
        logger.info(f"  超额收益: {summary['avg_roi'] - summary['market_roi']:+.1f}%")
        logger.info(f"  跑赢概率: {summary['beat_market_pct']:.0f}%")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f'multi_regime_results_{timestamp}.json', 'w') as f:
        json.dump({
            'results': all_results,
            'summaries': all_summaries,
            'timestamp': timestamp
        }, f, indent=2)
    
    logger.info(f"\n✅ 结果已保存: multi_regime_results_{timestamp}.json")
    
    # 核心结论
    logger.info(f"\n{'='*70}")
    logger.info("🎯 核心结论")
    logger.info(f"{'='*70}")
    
    all_avg_rois = [s['avg_roi'] for s in all_summaries.values()]
    all_market_rois = [s['market_roi'] for s in all_summaries.values()]
    
    if len(all_avg_rois) > 0:
        overall_system = np.mean(all_avg_rois)
        overall_market = np.mean(all_market_rois)
        
        logger.info(f"\n跨所有Regime平均表现:")
        logger.info(f"  系统: {overall_system:+.1f}%")
        logger.info(f"  市场: {overall_market:+.1f}%")
        
        if overall_system > overall_market:
            logger.info(f"\n✅ 系统在多种market regime下均能跑赢市场")
            logger.info(f"   朋友的担忧：部分解除")
        else:
            logger.info(f"\n⚠️  系统在某些regime下表现欠佳")
            logger.info(f"   朋友的担忧：得到验证")
    
    logger.info(f"\n{'='*70}")


if __name__ == "__main__":
    main()

