"""
Agent (智能体) v4.0 - Prometheus v4.0
完全自主的交易执行者，拥有情绪和极端行为能力
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import numpy as np
from .bulletin_board import AgentBulletinProcessor
from .trading_permissions import PermissionLevel, TradingProduct, TradingPermissionSystem

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
    """
    Agent 性格特质（扩展版）
    
    多维度性格系统，防止性格趋同，增加群体多样性
    """
    # 核心性格
    aggression: float = 0.5      # 激进度 (0-1) - 影响仓位大小和交易频率
    risk_tolerance: float = 0.5  # 风险承受度 (0-1) - 影响止损止盈
    survival_will: float = 0.7   # 生存意志 (0-1) - 影响自杀和拼搏决策
    adaptability: float = 0.5    # 适应能力 (0-1) - 影响策略调整速度
    patience: float = 0.5        # 耐心程度 (0-1) - 影响持仓时间
    
    # 交易风格
    trend_following: float = 0.5  # 趋势跟随倾向 (0-1)
    contrarian: float = 0.5       # 逆向思维倾向 (0-1)
    momentum_seeking: float = 0.5  # 动量追逐倾向 (0-1)
    mean_reversion: float = 0.5   # 均值回归倾向 (0-1)
    
    # 情绪特质
    optimism: float = 0.5        # 乐观程度 (0-1)
    fear_sensitivity: float = 0.5  # 恐惧敏感度 (0-1)
    greed_level: float = 0.5     # 贪婪程度 (0-1)
    discipline: float = 0.5      # 纪律性 (0-1)
    
    # 学习特质
    learning_rate: float = 0.5   # 学习速度 (0-1)
    memory_decay: float = 0.5    # 记忆衰减 (0-1)
    exploration: float = 0.5     # 探索倾向 (0-1)
    exploitation: float = 0.5    # 利用倾向 (0-1)
    
    # 社交特质（群体行为）
    herd_mentality: float = 0.5  # 从众心理 (0-1)
    independence: float = 0.5    # 独立性 (0-1)
    competitiveness: float = 0.5  # 竞争性 (0-1)
    cooperation: float = 0.5     # 合作性 (0-1)
    
    def get_personality_vector(self) -> List[float]:
        """获取性格向量（用于计算多样性）"""
        return [
            self.aggression, self.risk_tolerance, self.survival_will,
            self.adaptability, self.patience, self.trend_following,
            self.contrarian, self.momentum_seeking, self.mean_reversion,
            self.optimism, self.fear_sensitivity, self.greed_level,
            self.discipline, self.learning_rate, self.memory_decay,
            self.exploration, self.exploitation, self.herd_mentality,
            self.independence, self.competitiveness, self.cooperation
        ]
    
    def calculate_diversity_score(self, other: 'AgentPersonality') -> float:
        """
        计算与另一个性格的差异度
        
        Args:
            other: 另一个Agent的性格
            
        Returns:
            float: 差异度分数 (0-1)，越高越不同
        """
        vec1 = np.array(self.get_personality_vector())
        vec2 = np.array(other.get_personality_vector())
        
        # 使用欧式距离
        distance = np.linalg.norm(vec1 - vec2)
        max_distance = np.sqrt(len(vec1))  # 最大可能距离
        
        return min(distance / max_distance, 1.0)


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
                 personality: Optional[AgentPersonality] = None,
                 parent_permission: Optional[PermissionLevel] = None,
                 bulletin_board=None,
                 permission_system=None):
        """
        初始化 Agent
        
        Args:
            agent_id: Agent 唯一标识
            initial_capital: 初始资金
            gene: 交易基因（策略参数）
            personality: 性格特质
            parent_permission: 父母的权限级别（用于继承）
            bulletin_board: 公告板系统（v4）
            permission_system: 交易权限系统
        """
        self.agent_id = agent_id
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 基因和性格
        self.gene = gene if gene else self._generate_random_gene()
        self.personality = personality if personality else self._generate_random_personality()
        
        # v4.0 系统集成
        self.bulletin_board = bulletin_board
        self.permission_system = permission_system or TradingPermissionSystem()
        
        # 权限系统
        if parent_permission and parent_permission != PermissionLevel.NOVICE:
            # 继承父母权限，但降一级
            self.permission_level = self.permission_system.get_inherited_level(parent_permission)
        else:
            # 创世Agent从新手开始
            self.permission_level = PermissionLevel.NOVICE
        
        # 生命周期
        self.state = AgentState.NEWBORN
        self.birth_time = datetime.now()
        self.death_time: Optional[datetime] = None
        self.death_reason: Optional[DeathReason] = None
        self.days_alive = 0
        
        # 公告阅读历史
        self.bulletin_read_count = 0
        self.last_bulletins_read = []
        
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
        
        # 公告板处理器（新增）
        self.bulletin_processor = AgentBulletinProcessor(self)
        
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
            },
            
            # 信号融合权重（新增）
            'signal_weights': {
                'technical': np.random.uniform(0.3, 0.7),   # 技术分析
                'opponent': np.random.uniform(0.2, 0.6),    # 对手分析
                'bulletin': np.random.uniform(0.0, 0.5),    # 公告板信号
                'emotion': np.random.uniform(0.1, 0.4)      # 情绪状态
            },
            
            # 公告板敏感度
            'bulletin_sensitivity': {
                'global': np.random.uniform(0.0, 1.0),      # 主脑战略
                'market': np.random.uniform(0.0, 1.0),      # 市场事件
                'system': np.random.uniform(0.0, 1.0),      # 系统风险
                'social': np.random.uniform(0.0, 1.0)       # 社交信号
            },
            
            # 交易品种偏好（新增）
            'product_preference': {
                'spot': np.random.uniform(0.0, 1.0),        # 现货偏好
                'margin': np.random.uniform(0.0, 1.0),      # 杠杆交易偏好
                'perpetual': np.random.uniform(0.0, 1.0),   # 永续合约偏好
                'futures': np.random.uniform(0.0, 1.0),     # 交割合约偏好
                'options': np.random.uniform(0.0, 1.0)      # 期权偏好
            },
            
            # 杠杆倾向（新增）
            'leverage_appetite': np.random.uniform(0.0, 1.0)  # 0=保守 1=激进
        }
    
    def _generate_random_personality(self) -> AgentPersonality:
        """
        生成随机性格（多样化）
        
        使用不同的分布函数生成各个维度，确保性格多样性
        """
        return AgentPersonality(
            # 核心性格 - 使用均匀分布
            aggression=np.random.uniform(0.2, 0.9),
            risk_tolerance=np.random.uniform(0.2, 0.9),
            survival_will=np.random.uniform(0.4, 0.95),
            adaptability=np.random.uniform(0.3, 0.9),
            patience=np.random.uniform(0.2, 0.9),
            
            # 交易风格 - 使用Beta分布（更自然）
            trend_following=np.random.beta(2, 2),
            contrarian=np.random.beta(2, 2),
            momentum_seeking=np.random.beta(2, 2),
            mean_reversion=np.random.beta(2, 2),
            
            # 情绪特质 - 使用正态分布截断
            optimism=np.clip(np.random.normal(0.5, 0.2), 0, 1),
            fear_sensitivity=np.clip(np.random.normal(0.5, 0.2), 0, 1),
            greed_level=np.clip(np.random.normal(0.5, 0.2), 0, 1),
            discipline=np.clip(np.random.normal(0.6, 0.2), 0, 1),  # 偏向高纪律性
            
            # 学习特质 - 使用对数正态分布
            learning_rate=np.clip(np.random.lognormal(-0.5, 0.5), 0, 1),
            memory_decay=np.random.uniform(0.3, 0.8),
            exploration=np.random.beta(2, 2),
            exploitation=np.random.beta(2, 2),
            
            # 社交特质 - 使用混合分布
            herd_mentality=np.random.choice([
                np.random.uniform(0.1, 0.3),  # 低从众
                np.random.uniform(0.7, 0.9)   # 高从众
            ]),
            independence=np.random.uniform(0.3, 0.9),
            competitiveness=np.random.beta(2, 2),
            cooperation=np.random.beta(2, 2)
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
        根据市场数据生成交易信号（多信号融合）
        
        Args:
            market_data: 市场数据
            
        Returns:
            Optional[Dict]: 交易信号
        """
        # 收集所有信号源
        signals = {}
        
        # 1. 技术分析信号
        signals['technical'] = self._analyze_technical(market_data)
        
        # 2. 对手分析信号
        signals['opponent'] = self._analyze_opponent(market_data)
        
        # 3. 公告板信号（新增）
        bulletins = market_data.get('bulletins', [])
        signals['bulletin'] = self.bulletin_processor.process_bulletins(bulletins)
        
        # 4. 情绪偏差
        signals['emotion'] = self._get_emotional_bias()
        
        # 多信号融合
        final_signal = self._integrate_signals(signals)
        
        # 根据信号强度决策
        if final_signal > 0.5:
            return self._create_buy_signal(final_signal, market_data)
        elif final_signal < -0.5:
            return self._create_sell_signal(final_signal, market_data)
        else:
            return None  # 不交易
    
    def _integrate_signals(self, signals: Dict[str, float]) -> float:
        """
        多信号融合
        
        Args:
            signals: 各种信号字典
            
        Returns:
            float: 综合信号 (-1到1)
        """
        weights = self.gene.get('signal_weights', {
            'technical': 0.5,
            'opponent': 0.3,
            'bulletin': 0.1,
            'emotion': 0.1
        })
        
        # 加权平均
        final_signal = (
            signals.get('technical', 0.0) * weights.get('technical', 0.5) +
            signals.get('opponent', 0.0) * weights.get('opponent', 0.3) +
            signals.get('bulletin', 0.0) * weights.get('bulletin', 0.1) +
            signals.get('emotion', 0.0) * weights.get('emotion', 0.1)
        )
        
        # 归一化
        total_weight = sum(weights.values())
        if total_weight > 0:
            final_signal /= total_weight
        
        # 限制范围
        return max(-1.0, min(1.0, final_signal))
    
    def _analyze_technical(self, market_data: Dict) -> float:
        """
        技术分析（简化版）
        
        Returns:
            float: -1到1的信号
        """
        # TODO: 实现真实的技术分析
        # 这里返回随机信号作为占位
        return np.random.uniform(-1.0, 1.0)
    
    def _analyze_opponent(self, market_data: Dict) -> float:
        """
        对手分析（简化版）
        
        Returns:
            float: -1到1的信号
        """
        # TODO: 实现真实的对手分析
        # 这里返回随机信号作为占位
        return np.random.uniform(-1.0, 1.0)
    
    def _get_emotional_bias(self) -> float:
        """
        获取情绪偏差
        
        Returns:
            float: -1到1的偏差
        """
        # 情绪对交易的影响
        fear_impact = -self.emotion.fear * 0.5
        confidence_impact = self.emotion.confidence * 0.3
        despair_impact = -self.emotion.despair * 0.7
        
        return fear_impact + confidence_impact + despair_impact
    
    def _create_buy_signal(self, signal_strength: float, market_data: Dict) -> Dict:
        """创建买入信号"""
        # 根据情绪调整仓位
        position_size = self.gene['max_position_size']
        if self.emotion.confidence > 0.7:
            position_size *= 1.2  # 信心强时加仓
        if self.emotion.fear > 0.6:
            position_size *= 0.5  # 恐惧时减仓
        
        return {
            'action': 'BUY',
            'signal_strength': signal_strength,
            'position_size': min(position_size, 1.0),
            'stop_loss': self.gene.get('stop_loss', 0.05),
            'take_profit': self.gene.get('take_profit', 0.10)
        }
    
    def _create_sell_signal(self, signal_strength: float, market_data: Dict) -> Dict:
        """创建卖出信号"""
        position_size = self.gene['max_position_size']
        if self.emotion.fear > 0.7:
            position_size *= 1.5  # 恐惧时加大卖出
        
        return {
            'action': 'SELL',
            'signal_strength': abs(signal_strength),
            'position_size': min(position_size, 1.0),
            'stop_loss': self.gene.get('stop_loss', 0.05),
            'take_profit': self.gene.get('take_profit', 0.10)
        }
    
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
    
    def select_trading_product(self, market_data: Dict) -> TradingProduct:
        """
        选择交易品种
        
        过程：
        1. 基因决定偏好
        2. 权限系统过滤
        3. 市场环境影响
        
        Args:
            market_data: 市场数据
            
        Returns:
            TradingProduct: 选择的交易品种
        """
        # 获取允许的品种
        config = self.permission_system.permissions[self.permission_level]
        allowed_products = config.allowed_products
        
        # 基因偏好（只考虑允许的）
        preferences = {}
        for product in allowed_products:
            product_key = product.value  # 'spot', 'margin', etc.
            preferences[product] = self.gene['product_preference'].get(product_key, 0.5)
        
        # 市场环境调整
        volatility = market_data.get('volatility', 0.03)
        
        # 高波动时倾向现货（风险规避）
        if volatility > 0.05:
            if TradingProduct.SPOT in preferences:
                preferences[TradingProduct.SPOT] *= 1.5
        
        # 低波动时可以用杠杆
        elif volatility < 0.02:
            if TradingProduct.PERPETUAL in preferences:
                preferences[TradingProduct.PERPETUAL] *= 1.3
        
        # 情绪影响
        if self.emotion.fear > 0.7:
            # 恐惧时倾向现货
            if TradingProduct.SPOT in preferences:
                preferences[TradingProduct.SPOT] *= 2.0
        elif self.emotion.confidence > 0.8:
            # 自信时倾向高风险品种
            for product in [TradingProduct.PERPETUAL, TradingProduct.FUTURES]:
                if product in preferences:
                    preferences[product] *= 1.5
        
        # 选择最高偏好的
        if preferences:
            selected = max(preferences.items(), key=lambda x: x[1])[0]
            return selected
        else:
            # 如果没有允许的品种（不应该发生），返回SPOT
            return TradingProduct.SPOT
    
    def calculate_leverage(self, market_data: Dict) -> float:
        """
        计算实际使用的杠杆
        
        过程：
        1. 基因决定杠杆偏好（0-1）
        2. 权限系统限制上限
        3. 市场环境和情绪调整
        
        Args:
            market_data: 市场数据
            
        Returns:
            float: 实际杠杆倍数
        """
        # 权限允许的最大杠杆
        max_allowed = self.permission_system.get_max_leverage(self.permission_level)
        
        # 基因偏好杠杆（线性映射到允许范围）
        leverage_appetite = self.gene.get('leverage_appetite', 0.5)
        gene_leverage = 1.0 + (max_allowed - 1.0) * leverage_appetite
        
        # 情绪调整
        if self.emotion.fear > 0.7:
            gene_leverage *= 0.5  # 恐惧时大幅降低杠杆
        elif self.emotion.fear > 0.5:
            gene_leverage *= 0.7
        
        if self.emotion.confidence > 0.8:
            gene_leverage *= 1.2  # 自信时小幅提高杠杆
        elif self.emotion.confidence > 0.6:
            gene_leverage *= 1.1
        
        if self.emotion.despair > 0.8:
            gene_leverage *= 0.3  # 绝望时极度保守
        
        # 市场波动调整
        volatility = market_data.get('volatility', 0.03)
        if volatility > 0.08:      # 极高波动
            gene_leverage *= 0.5
        elif volatility > 0.05:    # 高波动
            gene_leverage *= 0.7
        elif volatility < 0.02:    # 低波动
            gene_leverage *= 1.2
        
        # 性格影响
        if self.personality.risk_tolerance > 0.7:
            gene_leverage *= 1.1  # 风险偏好高
        elif self.personality.risk_tolerance < 0.3:
            gene_leverage *= 0.8  # 风险厌恶
        
        # 最终杠杆（确保在合理范围内）
        final_leverage = min(gene_leverage, max_allowed)
        final_leverage = max(1.0, final_leverage)  # 最低1x
        
        return final_leverage
    
    def update_permission_level(self):
        """
        更新权限等级（由Supervisor定期调用）
        """
        # 计算统计数据
        stats = {
            'days_alive': self.days_alive,
            'total_return': self.total_pnl / max(self.initial_capital, 1.0),
            'win_rate': self.win_count / max(self.trade_count, 1),
            'max_drawdown': self.calculate_max_drawdown()
        }
        
        # 评估新级别
        new_level = self.permission_system.evaluate_agent_level(stats)
        
        # 如果级别变化
        if new_level != self.permission_level:
            old_level = self.permission_level
            self.permission_level = new_level
            
            # 计算升级奖励
            bonus_ratio = self.permission_system.get_upgrade_bonus(old_level, new_level)
            if bonus_ratio > 0:
                bonus = self.current_capital * bonus_ratio
                self.current_capital += bonus
                logger.info(
                    f"🎉 Agent {self.agent_id} 权限升级: {old_level.value} → {new_level.value}, "
                    f"奖励: {bonus:.2f}"
                )
            else:
                logger.warning(
                    f"⚠️ Agent {self.agent_id} 权限降级: {old_level.value} → {new_level.value}"
                )
    
    def calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            float: 最大回撤比例 (0-1)
        """
        if len(self.capital_history) < 2:
            return 0.0
        
        peak = self.capital_history[0]
        max_dd = 0.0
        
        for capital in self.capital_history:
            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def get_stats(self) -> Dict:
        """
        获取Agent统计数据（用于权限评估）
        
        Returns:
            Dict: 统计数据
        """
        return {
            'agent_id': self.agent_id,
            'days_alive': self.days_alive,
            'total_return': self.total_pnl / max(self.initial_capital, 1.0),
            'win_rate': self.win_count / max(self.trade_count, 1),
            'max_drawdown': self.calculate_max_drawdown(),
            'current_capital': self.current_capital,
            'trade_count': self.trade_count,
            'permission_level': self.permission_level
        }
    
    def calculate_inheritance(self, inheritance_ratio: float = 0.3) -> Tuple[float, float]:
        """
        计算遗产分配
        
        死亡Agent的资产分配：
        - 一部分传给子代（作为奖励）
        - 一部分归还资金池
        
        Args:
            inheritance_ratio: 继承比例（传给子代的比例）
            
        Returns:
            Tuple[float, float]: (传给子代的金额, 归还资金池的金额)
        """
        # 如果是自杀或拼搏失败，降低继承比例（惩罚）
        if self.death_reason in [DeathReason.SUICIDE, DeathReason.FAILED_LAST_STAND]:
            inheritance_ratio *= 0.5  # 减半
        
        # 根据表现调整继承比例
        capital_ratio = self.current_capital / self.initial_capital
        if capital_ratio > 1.5:  # 表现优秀，增加继承
            inheritance_ratio *= 1.5
        elif capital_ratio < 0.5:  # 表现很差，减少继承
            inheritance_ratio *= 0.5
        
        # 计算分配
        to_offspring = self.current_capital * inheritance_ratio
        to_pool = self.current_capital - to_offspring
        
        logger.info(f"Agent {self.agent_id} 遗产分配: 子代={to_offspring:.2f}, 资金池={to_pool:.2f}")
        
        return to_offspring, to_pool
    
    def prepare_for_breeding(self) -> Dict:
        """
        准备繁殖数据
        
        Returns:
            Dict: 包含基因、性格和表现指标的完整数据
        """
        return {
            'gene': self.gene.copy(),
            'personality': self.personality.__dict__.copy(),
            'performance_metrics': {
                'total_trades': self.trade_count,
                'win_rate': self.win_count / max(self.trade_count, 1),
                'total_return': (self.current_capital - self.initial_capital) / self.initial_capital,
                'sharpe_ratio': self._calculate_sharpe_ratio(),
                'max_drawdown': self._calculate_max_drawdown(),
                'survival_days': self.days_alive,
                'birth_time': self.birth_time,
                'death_time': self.death_time,
                'death_reason': self.death_reason.value if self.death_reason else 'alive',
                'generation': 0,  # 会由基因库更新
                'parent_genes': []  # 会由基因库更新
            }
        }
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率
        
        Returns:
            float: 夏普比率
        """
        if len(self.capital_history) < 2:
            return 0.0
        
        # 计算每日收益率
        returns = np.diff(self.capital_history) / self.capital_history[:-1]
        
        if len(returns) == 0:
            return 0.0
        
        # 夏普比率 = 平均收益 / 收益标准差
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = mean_return / std_return * np.sqrt(252)  # 年化
        return sharpe
    
    def _calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            float: 最大回撤比例
        """
        if len(self.capital_history) < 2:
            return 0.0
        
        capital_array = np.array(self.capital_history)
        running_max = np.maximum.accumulate(capital_array)
        drawdown = (capital_array - running_max) / running_max
        
        return abs(np.min(drawdown))
    
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
    
    # ========== v4.0 公告板集成 ==========
    
    def read_bulletins(self, tier: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        读取公告板
        
        Args:
            tier: 层级过滤 ('strategic', 'market', 'system', None=all)
            limit: 最大数量
        
        Returns:
            List[Dict]: 公告列表（已转换为字典）
        """
        if not self.bulletin_board:
            logger.warning(f"{self.agent_id}: 公告板未初始化")
            return []
        
        # 读取公告
        bulletins = self.bulletin_board.read(self.agent_id, tier=tier, limit=limit)
        
        # 记录
        self.bulletin_read_count += len(bulletins)
        self.last_bulletins_read = bulletins
        
        logger.debug(f"{self.agent_id} 读取了 {len(bulletins)} 条公告")
        
        # 转换为字典方便处理
        return [b.to_dict() for b in bulletins]
    
    def interpret_bulletin(self, bulletin: Dict) -> Dict:
        """
        解读公告（基于基因和性格）
        
        Args:
            bulletin: 公告数据
        
        Returns:
            Dict: 解读结果
                - accept: 是否接受公告建议
                - confidence: 信心度 (0-1)
                - action: 拟采取的行动
        """
        content = bulletin.get('content', {})
        tier = bulletin.get('tier', '')
        
        # 基础信心度（基于性格）
        base_confidence = self.personality.confidence
        
        # 战略公告（主脑）- 权威性高
        if tier == 'strategic':
            # 更倾向接受权威指令，但性格会影响
            accept_threshold = 0.3  # 较低，容易接受
            confidence_boost = 0.2
        
        # 市场公告（监督者）- 信息性
        elif tier == 'market':
            # 根据市场敏感度决定
            market_sensitivity = self.gene.get('market_sensitivity', 0.5)
            accept_threshold = 1 - market_sensitivity
            confidence_boost = 0.1
        
        # 系统公告（监督者）- 警告性
        elif tier == 'system':
            # 根据风险偏好决定
            risk_aversion = 1 - self.personality.risk_appetite
            accept_threshold = 1 - risk_aversion
            confidence_boost = 0.15
        
        else:
            accept_threshold = 0.5
            confidence_boost = 0
        
        # 计算最终信心度
        final_confidence = min(base_confidence + confidence_boost, 1.0)
        
        # 决定是否接受
        accept = final_confidence > accept_threshold
        
        # 决定行动
        if accept:
            if tier == 'strategic':
                action = 'adjust_strategy'
            elif tier == 'market':
                action = 'analyze_opportunity'
            elif tier == 'system':
                action = 'reduce_risk'
            else:
                action = 'monitor'
        else:
            action = 'ignore'
        
        return {
            'accept': accept,
            'confidence': final_confidence,
            'action': action,
            'reason': f"基于性格({self.personality.confidence:.2f})和基因决策"
        }
    
    def process_bulletins_and_decide(self) -> Dict:
        """
        读取并处理所有公告，做出综合决策
        
        Returns:
            Dict: 决策结果
        """
        # 1. 读取公告
        bulletins = self.read_bulletins(limit=10)
        
        if not bulletins:
            return {
                'decision': 'no_info',
                'action': 'hold',
                'reason': '无公告信息'
            }
        
        # 2. 解读每条公告
        interpretations = []
        for bulletin in bulletins:
            interp = self.interpret_bulletin(bulletin)
            interpretations.append({
                'bulletin_id': bulletin.get('bulletin_id'),
                'tier': bulletin.get('tier'),
                'title': bulletin.get('title'),
                **interp
            })
        
        # 3. 综合决策
        accepted_bulletins = [i for i in interpretations if i['accept']]
        
        if not accepted_bulletins:
            return {
                'decision': 'all_rejected',
                'action': 'hold',
                'reason': '所有公告均未接受'
            }
        
        # 4. 根据接受的公告做出决策
        # 优先级：战略 > 系统 > 市场
        strategic = [b for b in accepted_bulletins if b['tier'] == 'strategic']
        system = [b for b in accepted_bulletins if b['tier'] == 'system']
        market = [b for b in accepted_bulletins if b['tier'] == 'market']
        
        if strategic:
            primary = strategic[0]
        elif system:
            primary = system[0]
        elif market:
            primary = market[0]
        else:
            primary = accepted_bulletins[0]
        
        return {
            'decision': 'bulletin_guided',
            'action': primary['action'],
            'primary_bulletin': primary['bulletin_id'],
            'accepted_count': len(accepted_bulletins),
            'total_count': len(bulletins),
            'confidence': primary['confidence'],
            'reason': f"接受了 {len(accepted_bulletins)}/{len(bulletins)} 条公告，主要依据: {primary['title']}"
        }

