"""
测试v7.0的自适应资金管理⭐⭐⭐

目标：验证系统能否根据市场表现自动调整资金分配

测试场景：
- 阶段1 (周期1-10)：牛市 → 预期：Agent盈利，S上升，资金增加
- 阶段2 (周期11-20)：熊市 → 预期：Agent亏损，S下降，资金减少
- 阶段3 (周期21-30)：震荡 → 预期：表现分化，S稳定，资金适度

观察指标：
1. Prophet的S值变化
2. 系统规模(current_scale)变化
3. Agent的allocated_capital变化
4. 平均ROI变化

2025-12-11 03:15创建
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time
import numpy as np
from datetime import datetime
import tempfile
import os

from prometheus.core.agent_v5 import AgentV5, LineageVector, GenomeVector
from prometheus.core.strategy_params import StrategyParams
from prometheus.core.meta_genome import MetaGenome
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.bulletin_board import BulletinBoard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_real_agent(agent_id: str) -> AgentV5:
    """创建真实AgentV5"""
    initial_capital = 10000.0
    lineage = LineageVector(np.random.rand(10))
    genome = GenomeVector(np.random.rand(50))
    strategy_params = StrategyParams.create_genesis()
    
    agent = AgentV5(
        agent_id=agent_id,
        initial_capital=initial_capital,
        lineage=lineage,
        genome=genome,
        strategy_params=strategy_params,
        generation=0,
        meta_genome=MetaGenome()
    )
    
    # 初始化属性
    agent.total_roi = 0.0
    agent.current_capital = initial_capital
    agent.allocated_capital = initial_capital  # 初始分配
    agent.age = 0
    agent.profit_factor = 1.0
    agent.winning_trades = 0
    agent.losing_trades = 0
    
    return agent


def simulate_agent_trading(agent, market_data):
    """
    模拟Agent交易（简化版）
    
    关键：使用allocated_capital而不是current_capital
    """
    current_price = market_data['price']
    price_change = market_data['price_change']
    
    # 使用allocated_capital（Prophet的指挥棒）⭐⭐⭐
    available_capital = getattr(agent, 'allocated_capital', agent.current_capital)
    
    # 简单策略：10%仓位
    position_size = available_capital * 0.1
    amount = position_size / current_price if current_price > 0 else 0
    
    # 计算盈亏（简化：完全跟随价格变化）
    pnl = position_size * price_change
    
    # 更新capital和roi
    agent.current_capital += pnl
    agent.total_roi = (agent.current_capital - agent.initial_capital) / agent.initial_capital
    
    # 更新交易统计
    if pnl > 0:
        agent.winning_trades += 1
    else:
        agent.losing_trades += 1
    
    # 更新年龄
    agent.age += 1
    
    return pnl


def generate_market_data(cycle: int, base_price: float) -> dict:
    """
    生成3阶段市场数据
    
    阶段1 (1-10)：牛市，价格稳定上涨
    阶段2 (11-20)：熊市，价格稳定下跌
    阶段3 (21-30)：震荡，价格随机波动
    """
    import random
    
    if 1 <= cycle <= 10:
        # 牛市：+1%到+2%
        price_change = random.uniform(0.01, 0.02)
        phase = "牛市"
    elif 11 <= cycle <= 20:
        # 熊市：-2%到-1%
        price_change = random.uniform(-0.02, -0.01)
        phase = "熊市"
    else:
        # 震荡：-0.5%到+0.5%
        price_change = random.uniform(-0.005, 0.005)
        phase = "震荡"
    
    new_price = base_price * (1 + price_change)
    
    return {
        'price': new_price,
        'price_change': price_change,
        'phase': phase,
        'timestamp': time.time()
    }


def run_adaptive_test():
    """运行自适应性测试"""
    
    logger.info("="*80)
    logger.info("🧪 测试v7.0自适应资金管理")
    logger.info("="*80)
    logger.info("测试目标：验证资金分配随市场表现动态调整")
    logger.info("测试周期：30周期（3个阶段）")
    logger.info("="*80)
    
    # 初始化
    db_path = tempfile.mktemp(suffix='.db')
    experience_db = ExperienceDB(db_path)
    bulletin_board = BulletinBoard("test_adaptive")
    
    # 创建初始Agent
    logger.info("创建20个初始Agent...")
    agents = []
    for i in range(20):
        agent = create_real_agent(f"agent_{i}")
        agents.append(agent)
    
    # 创建Moirai（传入初始agents）
    moirai = MoiraiV7(
        bulletin_board=bulletin_board,
        evolution_manager=None,  # 稍后注入
        initial_agents=agents
    )
    
    # 创建Prophet
    prophet = ProphetV7(
        bulletin_board=bulletin_board,
        experience_db=experience_db,
        run_id="test_adaptive"
    )
    
    # 创建EvolutionManager
    evolution_manager = EvolutionManagerV5(
        moirai=moirai,
        elite_ratio=0.2,
        elimination_ratio=0.3,
        capital_pool=None,
        fitness_mode='profit_factor',
        experience_db=experience_db
    )
    
    # 注入EvolutionManager到Moirai
    moirai.evolution_manager = evolution_manager
    
    # 运行测试
    current_price = 50000.0
    history = {
        'cycle': [],
        'phase': [],
        'S': [],
        'E': [],
        'scale': [],
        'avg_roi': [],
        'agent_count': [],
        'avg_allocated': []
    }
    
    logger.info("\n开始测试...\n")
    logger.info(f"{'周期':<6} {'阶段':<6} {'价格':<10} {'S值':<8} {'规模':<8} {'平均ROI':<10} {'Agent数':<8} {'平均分配':<10}")
    logger.info("-" * 80)
    
    for cycle in range(1, 31):
        # 生成市场数据
        market_data = generate_market_data(cycle, current_price)
        current_price = market_data['price']
        
        # 发布市场数据
        bulletin_board.publish('market_data', market_data)
        
        # Agent交易
        for agent in moirai.agents:
            simulate_agent_trading(agent, market_data)
        
        # Moirai报告
        moirai._report_to_prophet()
        
        # Prophet决策
        prophet.run_decision_cycle()
        announcement = bulletin_board.get('prophet_announcement')
        if announcement is None:
            announcement = {}
        S = announcement.get('reproduction_target', 0.5)
        E = announcement.get('pressure_level', 0.5)
        
        # Moirai执行
        moirai.run_cycle(cycle)
        
        # 收集统计
        avg_roi = sum(getattr(a, 'total_roi', 0) for a in moirai.agents) / len(moirai.agents) if moirai.agents else 0
        avg_allocated = sum(getattr(a, 'allocated_capital', 0) for a in moirai.agents) / len(moirai.agents) if moirai.agents else 0
        
        history['cycle'].append(cycle)
        history['phase'].append(market_data['phase'])
        history['S'].append(S)
        history['E'].append(E)
        history['scale'].append(moirai.current_scale)
        history['avg_roi'].append(avg_roi)
        history['agent_count'].append(len(moirai.agents))
        history['avg_allocated'].append(avg_allocated)
        
        # 打印进度
        logger.info(
            f"{cycle:<6} {market_data['phase']:<6} "
            f"{current_price:<10.0f} {S:<8.2%} {moirai.current_scale:<8.2%} "
            f"{avg_roi:<10.2%} {len(moirai.agents):<8} {avg_allocated:<10.0f}"
        )
    
    # 分析结果
    logger.info("\n" + "="*80)
    logger.info("📊 测试结果分析")
    logger.info("="*80)
    
    # 阶段1：牛市 (1-10)
    phase1_S = np.mean(history['S'][:10])
    phase1_scale = np.mean(history['scale'][:10])
    phase1_roi = np.mean(history['avg_roi'][:10])
    
    # 阶段2：熊市 (11-20)
    phase2_S = np.mean(history['S'][10:20])
    phase2_scale = np.mean(history['scale'][10:20])
    phase2_roi = np.mean(history['avg_roi'][10:20])
    
    # 阶段3：震荡 (21-30)
    phase3_S = np.mean(history['S'][20:30])
    phase3_scale = np.mean(history['scale'][20:30])
    phase3_roi = np.mean(history['avg_roi'][20:30])
    
    logger.info(f"\n阶段1（牛市，周期1-10）：")
    logger.info(f"  平均S值：{phase1_S:.2%}")
    logger.info(f"  平均规模：{phase1_scale:.2%}")
    logger.info(f"  平均ROI：{phase1_roi:.2%}")
    
    logger.info(f"\n阶段2（熊市，周期11-20）：")
    logger.info(f"  平均S值：{phase2_S:.2%}")
    logger.info(f"  平均规模：{phase2_scale:.2%}")
    logger.info(f"  平均ROI：{phase2_roi:.2%}")
    
    logger.info(f"\n阶段3（震荡，周期21-30）：")
    logger.info(f"  平均S值：{phase3_S:.2%}")
    logger.info(f"  平均规模：{phase3_scale:.2%}")
    logger.info(f"  平均ROI：{phase3_roi:.2%}")
    
    # 判断自适应性
    logger.info("\n" + "="*80)
    logger.info("🎯 自适应性验证")
    logger.info("="*80)
    
    # 预期：牛市S最高，熊市S最低
    s_adaptive = phase1_S > phase2_S
    logger.info(f"S值响应：{'✅ 通过' if s_adaptive else '❌ 失败'}")
    logger.info(f"  牛市S ({phase1_S:.2%}) > 熊市S ({phase2_S:.2%}): {s_adaptive}")
    
    # 预期：牛市规模最大，熊市规模最小
    scale_adaptive = phase1_scale > phase2_scale
    logger.info(f"规模响应：{'✅ 通过' if scale_adaptive else '❌ 失败'}")
    logger.info(f"  牛市规模 ({phase1_scale:.2%}) > 熊市规模 ({phase2_scale:.2%}): {scale_adaptive}")
    
    # 预期：牛市ROI为正，熊市ROI为负
    roi_adaptive = phase1_roi > 0 and phase2_roi < 0
    logger.info(f"ROI响应：{'✅ 通过' if roi_adaptive else '❌ 失败'}")
    logger.info(f"  牛市ROI ({phase1_roi:.2%}) > 0: {phase1_roi > 0}")
    logger.info(f"  熊市ROI ({phase2_roi:.2%}) < 0: {phase2_roi < 0}")
    
    # 总结
    if s_adaptive and scale_adaptive and roi_adaptive:
        logger.info("\n🎉 自适应性验证成功！系统能够根据市场表现动态调整资金！")
    else:
        logger.warning("\n⚠️ 自适应性验证部分失败，需要检查Prophet的计算逻辑")
    
    logger.info("\n" + "="*80)
    
    # 清理
    os.unlink(db_path)
    
    return history


if __name__ == "__main__":
    history = run_adaptive_test()

