"""
Prometheus v7.0 - Moirai核心模块

🎯 Moirai = 种群管理者⭐⭐⭐

职责：
  1. 读取Prophet的公告（S + E）
  2. 根据终极公式自主决策
  3. 执行繁殖/淘汰

核心公式：
  delta = (S - current) × |E|
  
  S = 目标（繁殖指数）
  |E| = 速度（压力指数）

代码：5行核心代码⭐⭐⭐
"""

import time
import logging
from typing import Dict, List
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 使用标准logging
logger = logging.getLogger(__name__)


class MoiraiV7:
    """
    Moirai v7.0 - 种群管理者⭐⭐⭐
    
    读取Prophet信息，自主决策
    """
    
    def __init__(
        self, 
        bulletin_board: BulletinBoard,
        evolution_manager: EvolutionManagerV5
    ):
        """
        初始化Moirai
        
        Args:
            bulletin_board: 公告板
            evolution_manager: 进化管理器（v6.0）
        """
        self.bulletin_board = bulletin_board
        self.evolution_manager = evolution_manager
        
        # 当前系统规模（0-1）
        self.current_scale = 0.5
        
        logger.info("⚖️ Moirai v7.0 已初始化")
        logger.info("   职责：繁殖/淘汰")
        logger.info("   公式：delta = (S - current) × |E|")
    
    def run_cycle(self):
        """
        Moirai的工作流程⭐⭐⭐
        
        1. 读取Prophet公告
        2. 自主决策（5行公式）
        3. 执行调整
        """
        
        # ===== 1. 读取Prophet公告⭐ =====
        announcement = self.bulletin_board.get('prophet_announcement')
        
        if not announcement:
            logger.warning("⚠️ 未找到Prophet公告，跳过本周期")
            return
        
        S = announcement['reproduction_target']  # 繁殖指数目标
        E_raw = announcement.get('E', 0.0)       # 原始E值
        pressure = announcement['pressure_level']  # 压力指数
        
        logger.info(f"📖 Moirai读取Prophet公告:")
        logger.info(f"   繁殖指数目标: {S:.2f} ({S:.0%})")
        logger.info(f"   压力指数: {pressure:.2f} ({pressure:.0%})")
        
        # ===== 2. 自主决策（5行核心代码）⭐⭐⭐ =====
        new_scale = self.decide(S, E_raw)
        
        # ===== 3. 执行调整 =====
        self._adjust_population(new_scale)
        
        # ===== 4. 上报执行结果 =====
        self._report_to_prophet()
    
    def decide(self, S: float, E: float) -> float:
        """
        终极公式⭐⭐⭐
        
        Args:
            S: 繁殖指数目标（0-1）
            E: 趋势值（-1 to +1）
        
        Returns:
            新的系统规模（0-1）
        """
        
        # ===== 5行核心代码⭐⭐⭐ =====
        
        target = S                              # 1. 目标 = S
        speed = abs(E)                          # 2. 速度 = |E|
        delta = (target - self.current_scale) * speed  # 3. 调整量
        self.current_scale += delta             # 4. 执行调整
        self.current_scale = max(0, min(1, self.current_scale))  # 5. 限制范围
        
        logger.info(f"💡 Moirai自主决策:")
        logger.info(f"   目标规模: {target:.2f} ({target:.0%})")
        logger.info(f"   调整速度: {speed:.2f} ({speed:.0%})")
        logger.info(f"   调整量: {delta:+.2f} ({delta:+.0%})")
        logger.info(f"   → 新规模: {self.current_scale:.2f} ({self.current_scale:.0%})")
        
        return self.current_scale
    
    def _adjust_population(self, target_scale: float):
        """
        执行种群规模调整
        
        根据target_scale调整Agent数量
        
        Args:
            target_scale: 目标规模（0-1）
        """
        
        # 获取当前Agent数量
        current_agents = len(self.evolution_manager.agents)
        
        # 假设最大Agent数量为2000
        max_agents = 2000
        
        # 计算目标Agent数量
        target_agents = int(max_agents * target_scale)
        
        # 计算需要调整的数量
        delta_agents = target_agents - current_agents
        
        logger.info(f"🔧 种群调整:")
        logger.info(f"   当前Agent: {current_agents}")
        logger.info(f"   目标Agent: {target_agents}")
        logger.info(f"   调整量: {delta_agents:+d}")
        
        if delta_agents > 0:
            # 需要增加Agent（繁殖）⭐
            logger.info(f"   → 繁殖{delta_agents}个Agent")
            self._breed_agents(delta_agents)
        
        elif delta_agents < 0:
            # 需要减少Agent（淘汰）⭐
            logger.info(f"   → 淘汰{abs(delta_agents)}个Agent")
            self._eliminate_agents(abs(delta_agents))
        
        else:
            # 维持不变
            logger.info(f"   → 维持当前规模")
    
    def _breed_agents(self, count: int):
        """
        繁殖Agent⭐
        
        从当前表现好的Agent中选择父母，繁殖新Agent
        
        Args:
            count: 需要繁殖的数量
        """
        
        # 调用EvolutionManagerV5的繁殖逻辑
        # （这里复用v6.0的繁殖机制）
        
        agents = self.evolution_manager.agents
        
        if not agents:
            logger.warning("⚠️ 没有Agent可以繁殖")
            return
        
        # 按ROI排序，选择表现好的Agent作为父母
        sorted_agents = sorted(agents, key=lambda a: a.total_roi, reverse=True)
        
        for i in range(count):
            # 选择父母（从top 30%中随机选择）
            top_agents = sorted_agents[:max(1, len(sorted_agents) // 3)]
            
            if len(top_agents) >= 2:
                from random import choice
                parent1 = choice(top_agents)
                parent2 = choice(top_agents)
                
                # 繁殖（调用v6.0的繁殖逻辑）
                child = self.evolution_manager._breed_single_agent(parent1, parent2)
                self.evolution_manager.agents.append(child)
                
                logger.debug(f"   👶 繁殖Agent #{child.agent_id}")
            else:
                # 如果Agent不够，就克隆
                parent = top_agents[0]
                child = self.evolution_manager._breed_single_agent(parent, parent)
                self.evolution_manager.agents.append(child)
    
    def _eliminate_agents(self, count: int):
        """
        淘汰Agent⭐
        
        淘汰表现差的Agent
        
        Args:
            count: 需要淘汰的数量
        """
        
        agents = self.evolution_manager.agents
        
        if not agents:
            logger.warning("⚠️ 没有Agent可以淘汰")
            return
        
        # 按ROI排序，淘汰表现差的Agent
        sorted_agents = sorted(agents, key=lambda a: a.total_roi)
        
        # 淘汰bottom N个Agent
        to_eliminate = sorted_agents[:min(count, len(sorted_agents))]
        
        for agent in to_eliminate:
            self.evolution_manager.agents.remove(agent)
            logger.debug(f"   ⚰️ 淘汰Agent #{agent.agent_id} (ROI: {agent.total_roi:.2%})")
    
    def _report_to_prophet(self):
        """
        向Prophet报告执行结果⭐
        
        报告当前种群状态，供Prophet下次计算S使用
        """
        
        agents = self.evolution_manager.agents
        
        if not agents:
            return
        
        # 计算关键指标
        total_agents = len(agents)
        
        # 存活率（简化版，基于ROI）
        profitable_agents = [a for a in agents if a.total_roi > 0]
        survival_rate = len(profitable_agents) / total_agents if total_agents > 0 else 0
        
        # 平均ROI
        avg_roi = sum(a.total_roi for a in agents) / total_agents if total_agents > 0 else 0
        
        # 多样性（简化版，基于基因方差）
        # TODO: 实现更精确的多样性计算
        diversity = 0.6  # 暂时使用固定值
        
        # 发布报告
        self.bulletin_board.publish('moirai_report', {
            'total_agents': total_agents,
            'profitable_agents': len(profitable_agents),
            'survival_rate': survival_rate,
            'avg_roi': avg_roi,
            'diversity': diversity,
            'current_scale': self.current_scale,
            'timestamp': time.time(),
        })
        
        logger.debug(f"📊 Moirai报告:")
        logger.debug(f"   总Agent: {total_agents}")
        logger.debug(f"   盈利Agent: {len(profitable_agents)}")
        logger.debug(f"   存活率: {survival_rate:.2%}")
        logger.debug(f"   平均ROI: {avg_roi:.2%}")
        logger.debug(f"   当前规模: {self.current_scale:.0%}")


if __name__ == "__main__":
    """
    简单测试
    """
    from prometheus.core.bulletin_board import BulletinBoard
    
    # 创建BulletinBoard
    bb = BulletinBoard()
    
    # 模拟Prophet公告
    bb.publish('prophet_announcement', {
        'reproduction_target': 0.75,
        'pressure_level': 0.20,
        'E': 0.20,
    })
    
    # 创建Moirai（需要EvolutionManager，这里暂时跳过）
    # moirai = MoiraiV7(bb, evolution_manager)
    
    # 测试决策公式
    moirai = MoiraiV7.__new__(MoiraiV7)
    moirai.current_scale = 0.5
    
    new_scale = moirai.decide(S=0.75, E=0.20)
    
    print(f"\n{'='*50}")
    print(f"测试Moirai决策公式:")
    print(f"{'='*50}")
    print(f"当前规模: 50%")
    print(f"繁殖指数目标: 75%")
    print(f"压力指数: 20%")
    print(f"→ 新规模: {new_scale:.0%}")
    print(f"{'='*50}")

