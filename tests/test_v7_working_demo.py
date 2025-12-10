"""
Prometheus v7.0 - 工作演示测试⭐⭐⭐

目标：今晚跑出第一个v7.0实际成绩！

测试内容：
  1. Prophet三维监控
  2. Moirai双周期机制（轻量级+重量级）
  3. 完整运行50个周期
  4. 验证三种市场场景（牛/熊/震荡）

不使用v6 Facade（明天再集成）
但使用真实的v6.0组件验证功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time
from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.three_dimension_monitor import ThreeDimensionMonitor
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
import numpy as np


class SimpleMockAgent:
    """简化的Mock Agent（用于测试）"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.initial_capital = 10000.0
        self.total_roi = 0.0
        self.current_capital = 10000.0
        self.allocated_capital = 10000.0
        self.generation = 0
        self.awards = 0
        self.profit_factor = 1.0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleBulletinBoard:
    """简单公告板（用于测试）"""
    def __init__(self):
        self.data = {}
    
    def publish(self, key: str, value: dict):
        self.data[key] = value
    
    def get(self, key: str):
        return self.data.get(key)


class SimpleMoiraiWrapper:
    """简化的Moirai包装（用于EvolutionManagerV5）"""
    def __init__(self):
        self.agents = []
        self.generation = 0
        self.TARGET_RESERVE_RATIO = 0.3  # 资金池生死线30%
    
    def retire_agent(self, agent, reason, current_price, awards=0):
        """简化的退休方法"""
        if agent in self.agents:
            self.agents.remove(agent)
            logger.info(f"   🏆 {agent.agent_id}退休: {reason}, {awards}枚奖章")
    
    def terminate_agent(self, agent, current_price, reason=None):
        """简化的淘汰方法"""
        if agent in self.agents:
            self.agents.remove(agent)


def run_v7_demo(
    total_cycles: int = 50,
    market_scenario: str = "mixed"  # "bull"/"bear"/"mixed"
):
    """
    运行v7.0演示⭐⭐⭐
    
    Args:
        total_cycles: 总周期数
        market_scenario: 市场场景
    """
    
    logger.info("="*80)
    logger.info("🚀 Prometheus v7.0 - 工作演示")
    logger.info("="*80)
    logger.info(f"   总周期: {total_cycles}")
    logger.info(f"   市场场景: {market_scenario}")
    logger.info("="*80)
    
    # ===== 1. 初始化组件 =====
    
    run_id = f"v7_demo_{market_scenario}_{int(time.time())}"
    
    # 数据库
    import tempfile
    import os
    db_path = os.path.join(tempfile.gettempdir(), f"{run_id}.db")
    exp_db = ExperienceDB(db_path=db_path)
    
    # 公告板
    bb = SimpleBulletinBoard()
    
    # Prophet
    prophet = ProphetV7(
        bulletin_board=bb,
        experience_db=exp_db,
        run_id=run_id
    )
    
    # Moirai包装器
    moirai_wrapper = SimpleMoiraiWrapper()
    
    # EvolutionManager（需要先有Agent列表）
    # 注意：EvolutionManagerV5不存储agents，而是通过moirai.agents访问
    
    # Moirai（先创建，EvolutionManager会通过它访问agents）
    # 但我们需要先创建EvolutionManager...
    # 这里有个循环依赖，让我们先给moirai_wrapper添加agents
    
    # 先创建Agent列表（使用简化的Mock Agent）
    initial_agents = []
    for i in range(100):
        agent = SimpleMockAgent(f"v7_agent_{i}")
        initial_agents.append(agent)
    
    moirai_wrapper.agents = initial_agents
    
    # 然后创建EvolutionManager
    evolution_mgr = EvolutionManagerV5(
        moirai=moirai_wrapper,
        elite_ratio=0.2,
        elimination_ratio=0.3,
        capital_pool=None,
        fitness_mode='profit_factor',
        retirement_enabled=True,
        medal_system_enabled=True,
        immigration_enabled=False
    )
    
    # Moirai
    moirai = MoiraiV7(bb, evolution_mgr)
    
    logger.info(f"\n✅ 组件初始化完成，创建了{len(moirai_wrapper.agents)}个Agent")
    
    # ===== 3. 运行周期 =====
    
    logger.info(f"\n🔄 开始运行{total_cycles}个周期...")
    
    # 历史记录
    history = {
        'cycle': [],
        'scale': [],
        'agent_count': [],
        'risk_level': [],
        'S': [],
        'E': []
    }
    
    current_price = 50000.0
    
    for cycle in range(1, total_cycles + 1):
        
        if cycle % 10 == 1:
            logger.info(f"\n{'='*60}")
            logger.info(f"📅 周期 {cycle}/{total_cycles}")
            logger.info("="*60)
        
        # ----- 模拟市场数据 -----
        market_data = generate_market_data(cycle, market_scenario, current_price)
        current_price = market_data['price']
        
        # ----- 模拟Agent交易（简化版）-----
        simulate_agent_trading(moirai_wrapper.agents, market_data, market_scenario)
        
        # ----- 模拟摩擦数据 -----
        friction_data = generate_friction_data(market_scenario, cycle)
        
        # ----- 模拟死亡统计 -----
        death_stats = calculate_death_stats(moirai_wrapper.agents, market_scenario)
        
        # ----- 发布到BulletinBoard -----
        bb.publish('world_signature', market_data)
        bb.publish('friction_data', friction_data)
        bb.publish('death_stats', death_stats)
        
        # ----- Prophet决策周期 -----
        prophet.run_decision_cycle()
        
        # ----- Moirai执行周期 -----
        moirai.run_cycle(cycle=cycle, current_price=current_price)
        
        # ----- 记录历史 -----
        announcement = bb.get('prophet_announcement')
        history['cycle'].append(cycle)
        history['scale'].append(moirai.current_scale)
        history['agent_count'].append(len(moirai_wrapper.agents))
        history['risk_level'].append(announcement.get('risk_level', 'safe'))
        history['S'].append(announcement.get('S', 0.5))
        history['E'].append(announcement.get('E', 0.0))
        
        # ----- 周期性日志 -----
        if cycle % 10 == 0:
            logger.info(f"\n📊 周期{cycle}状态:")
            logger.info(f"   Agent数量: {len(moirai_wrapper.agents)}")
            logger.info(f"   系统规模: {moirai.current_scale:.0%}")
            logger.info(f"   风险等级: {announcement.get('risk_level', 'safe')}")
            logger.info(f"   价格: ${current_price:.2f}")
    
    # ===== 4. 测试结果 =====
    
    logger.info(f"\n" + "="*80)
    logger.info("📊 测试结果汇总")
    logger.info("="*80)
    
    logger.info(f"\n系统规模变化:")
    logger.info(f"   初始: {history['scale'][0]:.0%}")
    logger.info(f"   最终: {history['scale'][-1]:.0%}")
    logger.info(f"   变化: {(history['scale'][-1] - history['scale'][0]):.0%}")
    
    logger.info(f"\nAgent数量变化:")
    logger.info(f"   初始: {history['agent_count'][0]}")
    logger.info(f"   最终: {history['agent_count'][-1]}")
    logger.info(f"   变化: {history['agent_count'][-1] - history['agent_count'][0]:+d}")
    
    logger.info(f"\n风险分布:")
    risk_counts = {}
    for r in history['risk_level']:
        risk_counts[r] = risk_counts.get(r, 0) + 1
    for risk, count in sorted(risk_counts.items()):
        logger.info(f"   {risk}: {count}次 ({count/len(history['risk_level'])*100:.1f}%)")
    
    # 查询数据库统计
    if exp_db:
        risk_summary = exp_db.get_risk_summary(run_id)
        logger.info(f"\n数据库统计:")
        logger.info(f"   总记录: {risk_summary['total']}")
        logger.info(f"   safe: {risk_summary['safe']}")
        logger.info(f"   warning: {risk_summary['warning']}")
        logger.info(f"   danger: {risk_summary['danger']}")
        logger.info(f"   critical: {risk_summary['critical']}")
    
    logger.info(f"\n✅ 测试完成！数据库: {db_path}")
    
    return history, exp_db, db_path


def generate_market_data(cycle: int, scenario: str, current_price: float) -> dict:
    """生成模拟市场数据"""
    import random
    
    if scenario == "bull":
        # 牛市：价格上涨
        price_change = random.uniform(0.01, 0.03)
        current_price *= (1 + price_change)
        return {
            'price': current_price,
            'price_change_24h': price_change * 12,
            'volatility_24h': random.uniform(0.02, 0.04),
            'volume_ratio': random.uniform(1.2, 1.8)
        }
    
    elif scenario == "bear":
        # 熊市：价格下跌
        price_change = random.uniform(-0.03, -0.01)
        current_price *= (1 + price_change)
        return {
            'price': current_price,
            'price_change_24h': price_change * 12,
            'volatility_24h': random.uniform(0.04, 0.08),
            'volume_ratio': random.uniform(0.5, 0.8)
        }
    
    else:  # mixed
        # 混合：前15周期牛市，中15周期熊市，后20周期震荡
        if cycle <= 15:
            price_change = random.uniform(0.01, 0.02)
        elif cycle <= 30:
            price_change = random.uniform(-0.02, -0.01)
        else:
            price_change = random.uniform(-0.005, 0.005)
        
        current_price *= (1 + price_change)
        
        # 周期35注入黑天鹅
        if cycle == 35:
            price_change = -0.15  # 暴跌15%
            current_price *= (1 + price_change)
            logger.warning(f"🚨 黑天鹅事件！价格暴跌{price_change:.0%}")
        
        return {
            'price': current_price,
            'price_change_24h': price_change * 12,
            'volatility_24h': abs(price_change) * 2,
            'volume_ratio': 1.0 + random.uniform(-0.2, 0.2)
        }


def generate_friction_data(scenario: str, cycle: int) -> dict:
    """生成摩擦数据"""
    import random
    
    base_slippage = 0.001
    base_latency = 0.02
    base_fill_rate = 0.98
    
    # 周期35黑天鹅：摩擦激增
    if cycle == 35:
        return {
            'slippage': base_slippage * 10,
            'latency_norm': base_latency * 5,
            'fill_rate': 0.5
        }
    
    return {
        'slippage': base_slippage * random.uniform(0.8, 1.2),
        'latency_norm': base_latency * random.uniform(0.8, 1.2),
        'fill_rate': base_fill_rate * random.uniform(0.98, 1.0)
    }


def calculate_death_stats(agents, scenario: str) -> dict:
    """计算死亡统计"""
    # 简化：基于Agent的ROI判断"非正常死亡"
    if not agents:
        return {'abnormal_deaths': 0, 'total_agents': 1}
    
    # 非正常死亡：ROI < -20%的Agent
    abnormal_deaths = sum(1 for a in agents if a.total_roi < -0.2)
    
    return {
        'abnormal_deaths': abnormal_deaths,
        'total_agents': len(agents)
    }


def simulate_agent_trading(agents, market_data, scenario):
    """模拟Agent交易（简化版）"""
    import random
    
    price_change = market_data['price_change_24h'] / 12  # 单周期变化
    
    for agent in agents:
        if random.random() < 0.3:  # 30%概率交易
            # 简化：随机方向，但有市场偏向
            if scenario == "bull" or (scenario == "mixed" and price_change > 0):
                direction_bias = 0.7  # 偏多
            elif scenario == "bear" or (scenario == "mixed" and price_change < 0):
                direction_bias = 0.3  # 偏空
            else:
                direction_bias = 0.5
            
            is_long = random.random() < direction_bias
            
            # 计算盈亏（简化）
            if is_long:
                pnl = price_change * 100  # 假设交易100单位
            else:
                pnl = -price_change * 100
            
            # 更新Agent ROI
            agent.total_roi += pnl / agent.current_capital
            agent.current_capital += pnl


if __name__ == "__main__":
    """
    运行v7.0演示测试
    """
    
    print("\n" + "🚀 " + "="*58)
    print("🚀 Prometheus v7.0 - 工作演示测试")
    print("🚀 目标：今晚跑出第一个v7.0实际成绩！")
    print("🚀 " + "="*58 + "\n")
    
    # 运行测试
    history, exp_db, db_path = run_v7_demo(
        total_cycles=50,
        market_scenario="mixed"  # 包含牛市、熊市、黑天鹅
    )
    
    print("\n" + "🏆 " + "="*58)
    print("🏆 v7.0演示测试完成！")
    print("🏆 " + "="*58 + "\n")
    
    print(f"📊 关键数据:")
    print(f"   数据库路径: {db_path}")
    print(f"   系统规模: {history['scale'][0]:.0%} → {history['scale'][-1]:.0%}")
    print(f"   Agent数量: {history['agent_count'][0]} → {history['agent_count'][-1]}")
    print()
    
    # 清理
    exp_db.close()

