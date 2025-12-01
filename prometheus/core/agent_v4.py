"""
Agent (智能体) v4.0 - Prometheus v4.0
完全自主的交易执行者，拥有情绪和极端行为能力
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent 生命状态"""
    NEWBORN = "newborn"         # 新生
    GROWING = "growing"         # 成长中
    MATURE = "mature"           # 成熟
    STRUGGLING = "struggling"   # 挣扎中
    LAST_STAND = "last_stand"   # 拼死一搏
    DYING = "dying"             # 濒死
    DEAD = "dead"               # 已死亡


class DeathReason(Enum):
    """死亡原因"""
    NATURAL = "natural"         # 自然淘汰
    SUICIDE = "suicide"         # 绝望自杀
    FAILED_LAST_STAND = "failed_last_stand"  # 拼搏失败
    SYSTEM_SHUTDOWN = "system_shutdown"       # 系统关闭


@dataclass
class AgentPersonality:
    """Agent 性格特质"""
    aggression: float = 0.5      # 激进度 (0-1)
    risk_tolerance: float = 0.5  # 风险承受度 (0-1)
    survival_will: float = 0.7   # 生存意志 (0-1)
    adaptability: float = 0.5    # 适应能力 (0-1)
    patience: float = 0.5        # 耐心程度 (0-1)


@dataclass
class EmotionalState:
    """Agent 情绪状态"""
    despair: float = 0.0         # 绝望值 (0-1)
    fear: float = 0.0            # 恐惧值 (0-1)
    confidence: float = 0.5      # 信心值 (0-1)
    stress: float = 0.0          # 压力值 (0-1)


class AgentV4:
    """
    Agent v4.0 - 完全自主的智能交易体
    
    核心特性：
    1. 完全自主决策，不受外部干预
    2. 拥有性格和情绪
    3. 具备"绝望自杀"和"拼死一搏"能力
    4. 完整的生命周期管理
    """
    
    def __init__(self,
                 agent_id: str,
                 initial_capital: float,
                 gene: Optional[Dict] = None,
                 personality: Optional[AgentPersonality] = None):
        """
        初始化 Agent
        
        Args:
            agent_id: Agent 唯一标识
            initial_capital: 初始资金
            gene: 交易基因（策略参数）
            personality: 性格特质
        """
        self.agent_id = agent_id
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 基因和性格
        self.gene = gene if gene else self._generate_random_gene()
        self.personality = personality if personality else self._generate_random_personality()
        
        # 生命周期
        self.state = AgentState.NEWBORN
        self.birth_time = datetime.now()
        self.death_time: Optional[datetime] = None
        self.death_reason: Optional[DeathReason] = None
        self.days_alive = 0
        
        # 情绪状态
        self.emotion = EmotionalState()
        
        # 交易数据
        self.positions: Dict = {}
        self.trade_history: List[Dict] = []
        self.capital_history: List[float] = [initial_capital]
        
        # 统计指标
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 0
        self.total_pnl = 0.0
        self.best_trade = 0.0
        self.worst_trade = 0.0
        
        # 特殊状态标记
        self.is_in_last_stand = False
        self.last_stand_start_time: Optional[datetime] = None
        self.last_stand_initial_capital: Optional[float] = None
        
        logger.info(f"Agent {agent_id} 诞生，初始资金: {initial_capital}, 性格: {self.personality}")
    
    def _generate_random_gene(self) -> Dict:
        """生成随机交易基因"""
        return {
            # 交易信号阈值
            'long_threshold': np.random.uniform(0.5, 0.8),
            'short_threshold': np.random.uniform(0.5, 0.8),
            
            # 风险管理
            'max_position_size': np.random.uniform(0.1, 0.3),
            'stop_loss': np.random.uniform(0.02, 0.10),
            'take_profit': np.random.uniform(0.05, 0.20),
            
            # 时间周期
            'holding_period': np.random.randint(1, 48),  # 小时
            
            # 技术指标权重
            'indicator_weights': {
                'trend': np.random.uniform(0.1, 0.4),
                'momentum': np.random.uniform(0.1, 0.4),
                'volatility': np.random.uniform(0.1, 0.4),
                'volume': np.random.uniform(0.1, 0.3)
            }
        }
    
    def _generate_random_personality(self) -> AgentPersonality:
        """生成随机性格"""
        return AgentPersonality(
            aggression=np.random.uniform(0.2, 0.8),
            risk_tolerance=np.random.uniform(0.2, 0.8),
            survival_will=np.random.uniform(0.5, 0.9),
            adaptability=np.random.uniform(0.3, 0.8),
            patience=np.random.uniform(0.3, 0.8)
        )
    
    def update_emotional_state(self):
        """更新情绪状态"""
        capital_ratio = self.current_capital / self.initial_capital
        
        # 更新绝望值
        if capital_ratio < 0.5:
            self.emotion.despair = (0.5 - capital_ratio) * 2  # 0-1
        else:
            self.emotion.despair = 0
        
        # 连续亏损增加绝望
        self.emotion.despair += self.consecutive_losses * 0.05
        self.emotion.despair = min(self.emotion.despair, 1.0)
        
        # 更新信心
        if capital_ratio > 1.0:
            self.emotion.confidence = min(capital_ratio - 1.0 + 0.5, 1.0)
        else:
            self.emotion.confidence = capital_ratio * 0.5
        
        # 更新恐惧
        self.emotion.fear = self.emotion.despair * 0.8
        
        # 更新压力
        self.emotion.stress = (self.emotion.despair + self.emotion.fear) / 2
    
    def should_commit_suicide(self) -> bool:
        """
        判断是否应该自杀
        
        完全由 Agent 自主决定，外部无法干预
        
        Returns:
            bool: 是否自杀
        """
        if self.state == AgentState.DEAD:
            return False
        
        # 新生 Agent 有保护期
        if self.days_alive < 3:
            return False
        
        capital_ratio = self.current_capital / self.initial_capital
        
        # 综合评估
        suicide_factors = {
            '资金严重亏损': capital_ratio < 0.3,
            '连续大量亏损': self.consecutive_losses > 10,
            '累计亏损巨大': capital_ratio < 0.2,
            '长期表现差': self.days_alive > 30 and capital_ratio < 0.5,
            '情绪绝望': self.emotion.despair > 0.8,
        }
        
        # 统计满足的条件数
        triggered_factors = sum(suicide_factors.values())
        
        # 满足3个或以上条件，考虑自杀
        if triggered_factors >= 3:
            # 性格影响最终决定
            suicide_probability = triggered_factors / len(suicide_factors)
            suicide_probability *= (1 - self.personality.survival_will)  # 生存意志降低自杀概率
            
            if np.random.random() < suicide_probability:
                logger.warning(f"Agent {self.agent_id} 决定自杀，触发因素: {[k for k, v in suicide_factors.items() if v]}")
                return True
        
        return False
    
    def commit_suicide(self):
        """
        执行自杀
        
        完全由 Agent 自主决定和执行
        """
        logger.warning(f"Agent {self.agent_id} 执行自杀，资金: {self.current_capital:.2f}, 绝望值: {self.emotion.despair:.2f}")
        
        # 平掉所有持仓
        self.close_all_positions()
        
        # 标记死亡
        self.state = AgentState.DEAD
        self.death_time = datetime.now()
        self.death_reason = DeathReason.SUICIDE
        
        # 记录死亡信息
        self._record_death()
    
    def should_enter_last_stand(self) -> bool:
        """
        判断是否应该进入拼死一搏状态
        
        Returns:
            bool: 是否进入拼搏状态
        """
        if self.state == AgentState.DEAD or self.is_in_last_stand:
            return False
        
        # 已经很绝望的不拼搏了，直接自杀
        if self.emotion.despair > 0.8:
            return False
        
        capital_ratio = self.current_capital / self.initial_capital
        
        # 拼搏条件
        last_stand_conditions = {
            '资金濒危': 0.2 < capital_ratio < 0.5,
            '连续亏损但未绝望': 5 < self.consecutive_losses < 10,
            '有翻盘意志': self.personality.survival_will > 0.6,
            '性格激进': self.personality.aggression > 0.5,
        }
        
        triggered = sum(last_stand_conditions.values())
        
        # 满足3个或以上条件
        if triggered >= 3:
            logger.warning(f"Agent {self.agent_id} 准备拼死一搏，资金: {self.current_capital:.2f}")
            return True
        
        return False
    
    def enter_last_stand(self):
        """进入拼死一搏模式"""
        if self.is_in_last_stand:
            return
        
        logger.warning(f"Agent {self.agent_id} 进入拼死一搏模式！")
        
        self.is_in_last_stand = True
        self.state = AgentState.LAST_STAND
        self.last_stand_start_time = datetime.now()
        self.last_stand_initial_capital = self.current_capital
        
        # 调整策略参数（更激进）
        self.gene['max_position_size'] *= 2.0  # 仓位翻倍
        self.gene['stop_loss'] *= 0.7  # 止损收紧
        self.gene['take_profit'] *= 1.5  # 止盈放宽
        
        logger.info(f"Agent {self.agent_id} 拼搏参数：仓位={self.gene['max_position_size']:.2f}, "
                   f"止损={self.gene['stop_loss']:.3f}, 止盈={self.gene['take_profit']:.3f}")
    
    def exit_last_stand(self, success: bool):
        """
        退出拼死一搏模式
        
        Args:
            success: 是否成功
        """
        if not self.is_in_last_stand:
            return
        
        duration = (datetime.now() - self.last_stand_start_time).total_seconds() / 3600
        capital_change = self.current_capital - self.last_stand_initial_capital
        
        if success:
            logger.info(f"Agent {self.agent_id} 拼搏成功！用时 {duration:.1f}h，资金增加 {capital_change:.2f}")
            self.state = AgentState.MATURE
        else:
            logger.warning(f"Agent {self.agent_id} 拼搏失败，用时 {duration:.1f}h，资金减少 {-capital_change:.2f}")
            self.death_reason = DeathReason.FAILED_LAST_STAND
            self.state = AgentState.DEAD
        
        self.is_in_last_stand = False
        
        # 恢复策略参数
        self.gene['max_position_size'] /= 2.0
        self.gene['stop_loss'] /= 0.7
        self.gene['take_profit'] /= 1.5
    
    def make_trading_decision(self, market_data: Dict) -> Optional[Dict]:
        """
        做出交易决策（核心方法）
        
        完全自主决策，不受外部干预
        
        Args:
            market_data: 市场数据
            
        Returns:
            Optional[Dict]: 交易信号，None 表示不交易
        """
        if self.state == AgentState.DEAD:
            return None
        
        # 1. 更新情绪状态
        self.update_emotional_state()
        
        # 2. 检查是否应该自杀
        if self.should_commit_suicide():
            self.commit_suicide()
            return None
        
        # 3. 检查是否应该拼死一搏
        if self.should_enter_last_stand():
            self.enter_last_stand()
        
        # 4. 拼搏状态检查
        if self.is_in_last_stand:
            capital_ratio = self.current_capital / self.last_stand_initial_capital
            if capital_ratio > 1.3:  # 拼搏成功
                self.exit_last_stand(success=True)
            elif capital_ratio < 0.5:  # 拼搏失败
                self.exit_last_stand(success=False)
                return None
        
        # 5. 基于基因和市场数据生成交易信号
        signal = self._generate_trading_signal(market_data)
        
        return signal
    
    def _generate_trading_signal(self, market_data: Dict) -> Optional[Dict]:
        """
        根据市场数据生成交易信号
        
        Args:
            market_data: 市场数据
            
        Returns:
            Optional[Dict]: 交易信号
        """
        # TODO: 实现具体的信号生成逻辑
        # 这里应该基于：
        # - self.gene（交易策略参数）
        # - market_data（市场数据）
        # - self.emotion（情绪状态）
        # - self.personality（性格特质）
        
        return None
    
    def close_all_positions(self):
        """平掉所有持仓"""
        if self.positions:
            logger.info(f"Agent {self.agent_id} 平掉所有持仓")
            self.positions = {}
    
    def _record_death(self):
        """记录死亡信息"""
        death_record = {
            'agent_id': self.agent_id,
            'birth_time': self.birth_time,
            'death_time': self.death_time,
            'death_reason': self.death_reason.value,
            'days_alive': self.days_alive,
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': self.total_pnl,
            'trade_count': self.trade_count,
            'win_rate': self.win_count / max(self.trade_count, 1),
            'gene': self.gene,
            'personality': self.personality.__dict__,
            'final_emotion': self.emotion.__dict__
        }
        
        logger.info(f"Agent {self.agent_id} 死亡记录: {death_record}")
        return death_record
    
    def get_status(self) -> Dict:
        """
        获取 Agent 当前状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'agent_id': self.agent_id,
            'state': self.state.value,
            'is_alive': self.state != AgentState.DEAD,
            'days_alive': self.days_alive,
            'current_capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'capital_ratio': self.current_capital / self.initial_capital,
            'total_pnl': self.total_pnl,
            'trade_count': self.trade_count,
            'win_rate': self.win_count / max(self.trade_count, 1),
            'consecutive_losses': self.consecutive_losses,
            'consecutive_wins': self.consecutive_wins,
            'emotion': self.emotion.__dict__,
            'personality': self.personality.__dict__,
            'is_in_last_stand': self.is_in_last_stand,
            'positions': len(self.positions)
        }

