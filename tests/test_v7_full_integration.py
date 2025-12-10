"""
Prometheus v7.0 - 完整系统集成测试⭐⭐⭐

从创世开始，运行完整的交易周期
验证Prophet + Moirai + EvolutionManagerV5 + Agent的完整协作

测试场景：
  1. 创世 → 10周期（牛市）→ 验证扩张
  2. 创世 → 10周期（熊市）→ 验证收缩
  3. 创世 → 50周期（牛→熊转换）→ 验证自适应
"""

import sys
import time
from pathlib import Path
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.meta_genome import MetaGenome
from prometheus.core.agent_v5 import AgentV5
import logging

logger = logging.getLogger(__name__)


class SimpleBulletinBoard:
    """简单的公告板（兼容Prophet和Moirai）"""
    
    def __init__(self):
        self.data = {}
    
    def publish(self, key: str, value: dict):
        """发布数据"""
        self.data[key] = value
    
    def get(self, key: str):
        """获取数据"""
        return self.data.get(key)


class MockExchange:
    """模拟交易所（用于测试）"""
    
    def __init__(self, market_scenario: str = "bull"):
        self.market_scenario = market_scenario  # "bull"/"bear"/"sideways"
        self.current_price = 50000.0
        self.cycle_count = 0
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        return self.current_price
    
    def get_market_data(self) -> dict:
        """获取市场数据"""
        self.cycle_count += 1
        
        if self.market_scenario == "bull":
            # 牛市：价格上涨，成交量增加
            price_change = 0.02  # +2% per cycle
            self.current_price *= (1 + price_change)
            return {
                'price': self.current_price,
                'price_change_24h': price_change * 12,  # 假设每周期2小时
                'volume_ratio': 1.5,
                'volatility_24h': 0.03,
                'volatility_change': 0.01,
            }
        
        elif self.market_scenario == "bear":
            # 熊市：价格下跌，成交量减少
            price_change = -0.02  # -2% per cycle
            self.current_price *= (1 + price_change)
            return {
                'price': self.current_price,
                'price_change_24h': price_change * 12,
                'volume_ratio': 0.6,
                'volatility_24h': 0.06,
                'volatility_change': 0.02,
            }
        
        else:  # sideways
            # 震荡市：价格小幅波动
            import random
            price_change = random.uniform(-0.005, 0.005)
            self.current_price *= (1 + price_change)
            return {
                'price': self.current_price,
                'price_change_24h': price_change * 12,
                'volume_ratio': 1.0,
                'volatility_24h': 0.02,
                'volatility_change': 0.0,
            }
    
    def execute_order(self, agent_id: str, direction: str, amount: float, **kwargs) -> dict:
        """执行订单（简化版）"""
        price = self.current_price
        
        # 模拟盈亏（基于市场场景）
        if self.market_scenario == "bull" and direction == "long":
            pnl_rate = 0.02  # 牛市做多盈利
        elif self.market_scenario == "bear" and direction == "short":
            pnl_rate = 0.02  # 熊市做空盈利
        elif self.market_scenario == "bull" and direction == "short":
            pnl_rate = -0.02  # 牛市做空亏损
        elif self.market_scenario == "bear" and direction == "long":
            pnl_rate = -0.02  # 熊市做多亏损
        else:
            pnl_rate = 0.0  # 震荡市
        
        return {
            'success': True,
            'executed_price': price,
            'executed_amount': amount,
            'pnl': amount * pnl_rate,
            'fee': amount * 0.001,  # 0.1% fee
        }


def test_full_integration_bull_market():
    """
    完整集成测试1：牛市场景⭐⭐⭐
    
    流程：
      1. 创世（从基因库创建100个Agent）
      2. 运行10个交易周期
      3. 每个周期：
         - Prophet发布公告
         - Moirai执行调整
         - Agents交易
         - Moirai报告结果
      4. 验证系统扩张
    """
    
    logger.info("="*60)
    logger.info("🧪 测试：完整集成 - 牛市场景")
    logger.info("="*60)
    
    # ===== 1. 初始化组件 =====
    
    bb = SimpleBulletinBoard()
    exchange = MockExchange(market_scenario="bull")
    
    # 创建ExperienceDB（使用测试数据库）
    import tempfile
    import os
    test_db_path = os.path.join(tempfile.gettempdir(), "test_v7_experience.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)  # 清理旧测试数据
    
    exp_db = ExperienceDB(db_path=test_db_path)
    
    # 创建EvolutionManagerV5
    evolution_mgr = EvolutionManagerV5(
        experience_db=exp_db,
        initial_population=100,
        enable_immigration=False,  # 暂时关闭移民
        enable_diversity_protection=False,
    )
    
    # 创建Prophet和Moirai
    prophet = ProphetV7(bb)
    moirai = MoiraiV7(bb, evolution_mgr)
    
    logger.info(f"\n📊 初始状态:")
    logger.info(f"   Agent数量: {len(evolution_mgr.agents)}")
    logger.info(f"   系统规模: {moirai.current_scale:.0%}")
    logger.info(f"   市场场景: 牛市")
    
    # ===== 2. 创世（如果数据库为空） =====
    
    if len(evolution_mgr.agents) == 0:
        logger.info(f"\n🌱 开始创世...")
        
        # 创建初始Agent（简化版，实际应该从基因库）
        for i in range(100):
            genome = MetaGenome()
            agent = AgentV5(
                agent_id=f"genesis_{i}",
                genome=genome,
                generation=0,
            )
            evolution_mgr.agents.append(agent)
        
        logger.info(f"   ✅ 创世完成，创建了{len(evolution_mgr.agents)}个Agent")
    
    # ===== 3. 运行10个交易周期 =====
    
    logger.info(f"\n🔄 开始运行10个交易周期...")
    
    scale_history = [moirai.current_scale]
    agent_count_history = [len(evolution_mgr.agents)]
    
    for cycle in range(1, 11):
        logger.info(f"\n" + "="*60)
        logger.info(f"📅 周期 {cycle}/10")
        logger.info("="*60)
        
        # ----- 步骤1：模拟交易（简化版） -----
        
        market_data = exchange.get_market_data()
        
        for agent in evolution_mgr.agents:
            # 简化：随机交易
            import random
            if random.random() < 0.5:
                direction = "long" if random.random() < 0.7 else "short"  # 牛市偏多
                result = exchange.execute_order(
                    agent_id=agent.agent_id,
                    direction=direction,
                    amount=100.0,
                )
                
                # 更新Agent ROI（简化）
                if result['success']:
                    agent.total_roi += result['pnl'] / 100.0
        
        # ----- 步骤2：Moirai计算种群状态并报告 -----
        
        moirai._report_to_prophet()
        
        # ----- 步骤3：发布市场数据到BulletinBoard -----
        
        bb.publish('world_signature', market_data)
        
        # ----- 步骤4：Prophet发布公告 -----
        
        prophet.run_decision_cycle()
        
        # ----- 步骤5：Moirai执行调整 -----
        
        moirai.run_cycle()
        
        # ----- 记录历史 -----
        
        scale_history.append(moirai.current_scale)
        agent_count_history.append(len(evolution_mgr.agents))
        
        logger.info(f"\n📊 周期{cycle}汇总:")
        logger.info(f"   Agent数量: {len(evolution_mgr.agents)}")
        logger.info(f"   系统规模: {moirai.current_scale:.0%}")
        logger.info(f"   价格: ${market_data['price']:.2f}")
    
    # ===== 4. 验证结果 =====
    
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 测试结果汇总")
    logger.info("="*60)
    
    logger.info(f"\n系统规模变化:")
    logger.info(f"   初始: {scale_history[0]:.0%}")
    logger.info(f"   最终: {scale_history[-1]:.0%}")
    logger.info(f"   变化: {(scale_history[-1] - scale_history[0]):.0%}")
    
    logger.info(f"\nAgent数量变化:")
    logger.info(f"   初始: {agent_count_history[0]}")
    logger.info(f"   最终: {agent_count_history[-1]}")
    logger.info(f"   变化: {agent_count_history[-1] - agent_count_history[0]:+d}")
    
    # 验证：牛市应该扩张
    assert scale_history[-1] > scale_history[0], "❌ 牛市应该扩张系统"
    logger.info(f"\n✅ 测试通过：牛市系统正确扩张！")
    
    return {
        'scale_history': scale_history,
        'agent_count_history': agent_count_history,
        'final_scale': scale_history[-1],
        'final_agent_count': agent_count_history[-1],
    }


def test_full_integration_bear_market():
    """
    完整集成测试2：熊市场景⭐⭐⭐
    
    验证系统在熊市中正确收缩
    """
    
    logger.info("\n\n" + "="*60)
    logger.info("🧪 测试：完整集成 - 熊市场景")
    logger.info("="*60)
    
    # ===== 初始化（与牛市测试类似）=====
    
    bb = SimpleBulletinBoard()
    exchange = MockExchange(market_scenario="bear")  # 熊市
    
    # 使用测试数据库
    import tempfile
    import os
    test_db_path = os.path.join(tempfile.gettempdir(), "test_v7_experience_bear.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    exp_db = ExperienceDB(db_path=test_db_path)
    
    evolution_mgr = EvolutionManagerV5(
        experience_db=exp_db,
        initial_population=100,
        enable_immigration=False,
        enable_diversity_protection=False,
    )
    
    prophet = ProphetV7(bb)
    moirai = MoiraiV7(bb, evolution_mgr)
    
    # 创世
    if len(evolution_mgr.agents) == 0:
        for i in range(100):
            genome = MetaGenome()
            agent = AgentV5(
                agent_id=f"genesis_{i}",
                genome=genome,
                generation=0,
            )
            evolution_mgr.agents.append(agent)
    
    logger.info(f"\n📊 初始状态:")
    logger.info(f"   Agent数量: {len(evolution_mgr.agents)}")
    logger.info(f"   系统规模: {moirai.current_scale:.0%}")
    logger.info(f"   市场场景: 熊市")
    
    # ===== 运行10个周期 =====
    
    scale_history = [moirai.current_scale]
    agent_count_history = [len(evolution_mgr.agents)]
    
    for cycle in range(1, 11):
        logger.info(f"\n📅 周期 {cycle}/10")
        
        # 模拟交易
        market_data = exchange.get_market_data()
        
        for agent in evolution_mgr.agents:
            import random
            if random.random() < 0.5:
                direction = "short" if random.random() < 0.7 else "long"  # 熊市偏空
                result = exchange.execute_order(
                    agent_id=agent.agent_id,
                    direction=direction,
                    amount=100.0,
                )
                if result['success']:
                    agent.total_roi += result['pnl'] / 100.0
        
        # Prophet + Moirai循环
        moirai._report_to_prophet()
        bb.publish('world_signature', market_data)
        prophet.run_decision_cycle()
        moirai.run_cycle()
        
        scale_history.append(moirai.current_scale)
        agent_count_history.append(len(evolution_mgr.agents))
    
    # ===== 验证结果 =====
    
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 测试结果汇总")
    logger.info("="*60)
    
    logger.info(f"\n系统规模变化:")
    logger.info(f"   初始: {scale_history[0]:.0%}")
    logger.info(f"   最终: {scale_history[-1]:.0%}")
    logger.info(f"   变化: {(scale_history[-1] - scale_history[0]):.0%}")
    
    # 验证：熊市应该收缩
    assert scale_history[-1] < scale_history[0], "❌ 熊市应该收缩系统"
    logger.info(f"\n✅ 测试通过：熊市系统正确收缩！")
    
    return {
        'scale_history': scale_history,
        'agent_count_history': agent_count_history,
        'final_scale': scale_history[-1],
        'final_agent_count': agent_count_history[-1],
    }


def test_market_regime_change():
    """
    完整集成测试3：市场切换场景⭐⭐⭐
    
    牛市（15周期）→ 熊市（15周期）→ 震荡（20周期）
    验证系统自适应能力
    """
    
    logger.info("\n\n" + "="*60)
    logger.info("🧪 测试：市场切换场景（自适应）")
    logger.info("="*60)
    
    # ===== 初始化 =====
    
    bb = SimpleBulletinBoard()
    exchange = MockExchange(market_scenario="bull")
    
    # 使用测试数据库
    import tempfile
    import os
    test_db_path = os.path.join(tempfile.gettempdir(), "test_v7_experience_regime.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    exp_db = ExperienceDB(db_path=test_db_path)
    
    evolution_mgr = EvolutionManagerV5(
        experience_db=exp_db,
        initial_population=100,
        enable_immigration=False,
        enable_diversity_protection=False,
    )
    
    prophet = ProphetV7(bb)
    moirai = MoiraiV7(bb, evolution_mgr)
    
    # 创世
    if len(evolution_mgr.agents) == 0:
        for i in range(100):
            genome = MetaGenome()
            agent = AgentV5(
                agent_id=f"genesis_{i}",
                genome=genome,
                generation=0,
            )
            evolution_mgr.agents.append(agent)
    
    logger.info(f"\n📊 初始状态:")
    logger.info(f"   Agent数量: {len(evolution_mgr.agents)}")
    logger.info(f"   系统规模: {moirai.current_scale:.0%}")
    
    # ===== 运行50个周期（3个阶段）=====
    
    scale_history = [moirai.current_scale]
    market_regime_history = []
    
    for cycle in range(1, 51):
        # 切换市场场景
        if cycle <= 15:
            regime = "bull"
        elif cycle <= 30:
            regime = "bear"
        else:
            regime = "sideways"
        
        if exchange.market_scenario != regime:
            logger.info(f"\n🔄 市场切换: {exchange.market_scenario} → {regime}")
            exchange.market_scenario = regime
        
        market_regime_history.append(regime)
        
        if cycle % 10 == 1:
            logger.info(f"\n📅 周期 {cycle}/50 - {regime.upper()}")
        
        # 模拟交易
        market_data = exchange.get_market_data()
        
        for agent in evolution_mgr.agents:
            import random
            if random.random() < 0.5:
                if regime == "bull":
                    direction = "long" if random.random() < 0.7 else "short"
                elif regime == "bear":
                    direction = "short" if random.random() < 0.7 else "long"
                else:
                    direction = "long" if random.random() < 0.5 else "short"
                
                result = exchange.execute_order(
                    agent_id=agent.agent_id,
                    direction=direction,
                    amount=100.0,
                )
                if result['success']:
                    agent.total_roi += result['pnl'] / 100.0
        
        # Prophet + Moirai循环
        moirai._report_to_prophet()
        bb.publish('world_signature', market_data)
        prophet.run_decision_cycle()
        moirai.run_cycle()
        
        scale_history.append(moirai.current_scale)
    
    # ===== 验证结果 =====
    
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 测试结果汇总")
    logger.info("="*60)
    
    logger.info(f"\n系统规模变化:")
    logger.info(f"   初始: {scale_history[0]:.0%}")
    logger.info(f"   牛市末（周期15）: {scale_history[15]:.0%}")
    logger.info(f"   熊市末（周期30）: {scale_history[30]:.0%}")
    logger.info(f"   震荡末（周期50）: {scale_history[50]:.0%}")
    
    # 验证：系统应该自适应
    bull_growth = scale_history[15] - scale_history[0]
    bear_decline = scale_history[30] - scale_history[15]
    
    logger.info(f"\n市场适应性:")
    logger.info(f"   牛市阶段: {bull_growth:+.0%}")
    logger.info(f"   熊市阶段: {bear_decline:+.0%}")
    
    assert bull_growth > 0, "❌ 牛市阶段应该扩张"
    assert bear_decline < 0, "❌ 熊市阶段应该收缩"
    
    logger.info(f"\n✅ 测试通过：系统成功适应市场切换！")
    
    return {
        'scale_history': scale_history,
        'market_regime_history': market_regime_history,
    }


if __name__ == "__main__":
    """
    运行完整集成测试
    """
    
    # 配置logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "🚀 " + "="*58)
    print("🚀 Prometheus v7.0 - 完整系统集成测试")
    print("🚀 从创世到多周期运行的完整验证")
    print("🚀 " + "="*58 + "\n")
    
    # 测试1：牛市
    result1 = test_full_integration_bull_market()
    
    # 测试2：熊市
    result2 = test_full_integration_bear_market()
    
    # 测试3：市场切换
    result3 = test_market_regime_change()
    
    print("\n" + "🏆 " + "="*58)
    print("🏆 所有完整集成测试通过！⭐⭐⭐")
    print("🏆 v7.0系统验证完成！")
    print("🏆 " + "="*58 + "\n")
    
    print("📊 最终结果:")
    print(f"   测试1（牛市10周期）: {result1['final_scale']:.0%} 规模")
    print(f"   测试2（熊市10周期）: {result2['final_scale']:.0%} 规模")
    print(f"   测试3（市场切换50周期）: {result3['scale_history'][-1]:.0%} 规模")
    print()

