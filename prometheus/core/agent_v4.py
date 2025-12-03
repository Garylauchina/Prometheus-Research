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
        
        # 基因和性格（v4.1：支持EvolvableGene对象）
        from prometheus.core.evolvable_gene import EvolvableGene
        
        if gene is None:
            self.gene = self._generate_random_gene()
        elif isinstance(gene, EvolvableGene):
            # v4.1: 直接使用EvolvableGene对象
            self.gene = gene
        elif isinstance(gene, dict):
            # 兼容旧版：从字典转换为EvolvableGene对象
            # 检查是否是完整的EvolvableGene序列化字典
            if 'active_params' in gene and 'generation' in gene:
                # 完整的序列化字典，使用from_dict
                self.gene = EvolvableGene.from_dict(gene)
            else:
                # 简单的参数字典，作为active_params使用
                self.gene = EvolvableGene(active_params=gene, generation=0)
        else:
            # 未知类型，尝试作为EvolvableGene使用
            self.gene = gene
        
        # 将agent_id绑定到基因（用于追溯谱系）
        if hasattr(self.gene, 'agent_id') or isinstance(self.gene, EvolvableGene):
            self.gene.agent_id = agent_id
        
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
        
        # 止盈止损追踪变量
        self._max_profit_pct = 0.0      # 持仓期间最高盈利百分比（追踪止盈用）
        self._holding_periods = 0        # 持仓周期数（时间止损用）
        
        # 冷却期机制（防止频繁开平仓）
        self._cooldown_periods = 0       # 平仓后的冷却周期计数
        self._last_close_cycle = 0       # 上次平仓的周期号
        self._last_trade_pnl = 0.0       # 最后一笔交易的盈亏
        self._consecutive_losses = 0     # 连续亏损次数
        self._close_reason = ''          # 平仓原因
        
        # 公告板处理器（新增）
        self.bulletin_processor = AgentBulletinProcessor(self)
        
        logger.info(f"Agent {agent_id} 诞生，初始资金: {initial_capital}, 性格: {self.personality}")
    
    def _generate_random_gene(self):
        """生成随机交易基因（v4.1：返回EvolvableGene对象）"""
        from prometheus.core.evolvable_gene import EvolvableGene
        # v4.1: 返回EvolvableGene对象，而不是Dict
        # 旧版复杂的Dict基因已弃用，现在使用简化的可进化基因（3参数起步）
        return EvolvableGene.create_genesis()
    
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
    
    def interpret_bulletin(self, bulletin: Dict, has_position: bool = False, 
                           unrealized_pnl_pct: float = 0.0,
                           position_amount: float = 0.0,
                           balance: float = 10000.0,
                           initial_capital: float = 10000.0,
                           trade_count: int = 0,
                           position_side: str = None) -> Dict:
        """
        解读公告（基于基因、性格、持仓和资金状态）
        
        Args:
            bulletin: 公告数据
            has_position: 是否持有仓位
            unrealized_pnl_pct: 未实现盈亏百分比
            position_amount: 当前持仓量（BTC）
            balance: 当前余额
            initial_capital: 初始资金
            trade_count: 已交易笔数
            position_side: 持仓方向 'long'/'short'/None
        
        Returns:
            Dict: 解读结果
                - accept: 是否接受公告建议
                - confidence: 信心度 (0-1)
                - signal: 交易信号 'buy'/'sell'/'add'/'short'/'add_short'/'cover'/None
                - reason: 决策原因
        """
        # 计算资金使用率
        capital_usage = 1 - (balance / initial_capital) if initial_capital > 0 else 0
        # 设置最大持仓量限制（每个Agent最多持有0.05 BTC）
        max_position = 0.05
        # 设置最大资金使用率（最多使用初始资金的50%）
        max_capital_usage = 0.5
        content = bulletin.get('content', {})
        tier = bulletin.get('tier', '')
        
        # 基础信心度（基于性格：乐观度+纪律性）
        base_confidence = (self.personality.optimism + self.personality.discipline) / 2
        
        # 战略公告（先知占卜）- 权威性高
        if tier == 'strategic':
            accept_threshold = 0.3  # 较低，容易接受
            confidence_boost = 0.2
        
        # 市场公告（监督者）- 信息性
        elif tier == 'market':
            market_sensitivity = getattr(self.gene, 'market_sensitivity', 0.5)
            accept_threshold = 1 - market_sensitivity
            confidence_boost = 0.1
        
        # 系统公告（监督者）- 警告性
        elif tier == 'system':
            risk_aversion = 1 - self.personality.risk_tolerance
            accept_threshold = 1 - risk_aversion
            confidence_boost = 0.15
        else:
            accept_threshold = 0.5
            confidence_boost = 0
        
        # 计算最终信心度
        final_confidence = min(base_confidence + confidence_boost, 1.0)
        accept = final_confidence > accept_threshold
        
        signal = None
        reason = ""
        
        if accept:
            # ========== 先知占卜公告（strategic）- Agent自主解读 ==========
            if tier == 'strategic' and content.get('type') == 'prophecy':
                # 获取先知预测数据（纯预测，无建议）
                trend_forecast = content.get('trend_forecast', '震荡')
                forecast_confidence = content.get('forecast_confidence', 0.5)
                bullish_score = content.get('bullish_score', 0.5)
                volume_forecast = content.get('volume_forecast', '正常')
                risk_level = content.get('risk_level', 'medium')
                risk_factors = content.get('risk_factors', [])
                
                # ========== Agent自主解读预言 ==========
                # 根据自己的性格来理解市场信号
                
                # 解读走势：不同性格对"看涨/看跌"的阈值不同
                # 乐观派：bullish_score > 0.45 就觉得是看涨
                # 悲观派：bullish_score > 0.6 才觉得是看涨
                optimism_adjust = (self.personality.optimism - 0.5) * 0.15
                personal_bullish_threshold = 0.55 - optimism_adjust  # 乐观派阈值更低
                personal_bearish_threshold = 0.45 + optimism_adjust  # 悲观派阈值更高
                
                is_bullish = bullish_score >= personal_bullish_threshold
                is_bearish = bullish_score <= personal_bearish_threshold
                is_strong_bullish = bullish_score >= 0.7
                is_strong_bearish = bullish_score <= 0.3
                
                # 解读风险：不同风险承受度对风险的反应不同
                # 高风险承受：忽略medium风险
                # 低风险承受：medium风险就很敏感
                risk_sensitive = (risk_level == 'high') or (risk_level == 'medium' and self.personality.risk_tolerance < 0.4)
                
                # 解读交易量：激进派喜欢放量，保守派喜欢缩量
                volume_favorable = (volume_forecast == '放量' and self.personality.aggression > 0.5) or \
                                   (volume_forecast == '缩量' and self.personality.aggression < 0.5) or \
                                   (volume_forecast == '正常')
                
                # 优化C：动态开仓门槛（低信心/高风险时提高门槛，避免频繁被手续费吃掉）
                low_confidence_market = forecast_confidence < 0.60  # 信心不足市场
                if low_confidence_market and not has_position:
                    # 在不明朗市场提高开仓门槛：信心需>65%才开仓
                    min_confidence_to_open = 0.65
                else:
                    min_confidence_to_open = 0.50  # 正常阈值
                
                if has_position:
                    # === 已持仓：考虑加仓/减仓/清仓 ===
                    # 确定平仓和加仓信号（根据持仓方向）
                    is_long = position_side == 'long' or position_side is None  # 默认多仓
                    close_signal = 'sell' if is_long else 'cover'
                    add_signal = 'add' if is_long else 'add_short'
                    position_type = "多仓" if is_long else "空仓"
                    
                    # ========== 计算个性化止盈止损阈值 ==========
                    # 基础止盈线：保守派3%，激进派5%
                    base_take_profit = 0.03 + self.personality.aggression * 0.02
                    # 基础止损线：低风险承受2%，高风险承受4%
                    base_stop_loss = 0.02 + self.personality.risk_tolerance * 0.02
                    
                    # 追踪止盈：记录最高盈利（使用Agent属性）
                    if not hasattr(self, '_max_profit_pct'):
                        self._max_profit_pct = 0.0
                    if unrealized_pnl_pct > self._max_profit_pct:
                        self._max_profit_pct = unrealized_pnl_pct
                    
                    # 持仓周期计数已移至process_bulletins_and_decide，避免每条公告都计数
                    if not hasattr(self, '_holding_periods'):
                        self._holding_periods = 0
                    
                    # ========== 1. 止盈逻辑（Agent自主判断）==========
                    take_profit_triggered = False
                    
                    # 1.1 追踪止盈：曾经盈利超过5%，回撤40%则止盈
                    if self._max_profit_pct > 0.05:
                        trailing_threshold = self._max_profit_pct * 0.6
                        if unrealized_pnl_pct < trailing_threshold:
                            signal = close_signal
                            reason = f"追踪止盈(最高{self._max_profit_pct*100:.1f}%→当前{unrealized_pnl_pct*100:.1f}%)"
                            take_profit_triggered = True
                    
                    # 1.2 基础止盈：达到个性化止盈线
                    if not take_profit_triggered and unrealized_pnl_pct > base_take_profit:
                        adjusted_target = base_take_profit * (1 + self._holding_periods // 10 * 0.1)
                        if unrealized_pnl_pct > adjusted_target:
                            signal = close_signal
                            reason = f"止盈(盈利{unrealized_pnl_pct*100:.1f}%>目标{adjusted_target*100:.1f}%)"
                            take_profit_triggered = True
                    
                    # 1.3 趋势反向时主动止盈（Agent解读预言后判断）
                    # 注：止盈阈值必须>0.1%才能覆盖双向交易费(0.05%*2=0.1%)
                    adverse_trend = is_bearish if is_long else is_bullish
                    if not take_profit_triggered and adverse_trend and unrealized_pnl_pct > 0.025:  # 提高到2.5%
                        if self.personality.risk_tolerance < 0.5:  # 风险规避型主动止盈
                            signal = close_signal
                            reason = f"趋势{trend_forecast}+盈利{unrealized_pnl_pct*100:.1f}%，主动止盈"
                            take_profit_triggered = True
                    
                    # 1.4 超高盈利强制止盈（任何人盈利>8%）
                    if not take_profit_triggered and unrealized_pnl_pct > 0.08:
                        signal = close_signal
                        reason = f"超高盈利止盈({unrealized_pnl_pct*100:.1f}%)"
                        take_profit_triggered = True
                    
                    # ========== 2. 止损逻辑（Agent自主判断）==========
                    stop_loss_triggered = False
                    
                    if not take_profit_triggered:
                        # 趋势反向时收紧止损（Agent自己判断趋势是否对自己不利）
                        effective_stop_loss = base_stop_loss * 0.7 if adverse_trend else base_stop_loss
                        
                        # 风险敏感时进一步收紧止损
                        if risk_sensitive:
                            effective_stop_loss *= 0.8
                        
                        # 2.1 基础止损
                        if unrealized_pnl_pct < -effective_stop_loss:
                            signal = close_signal
                            reason = f"止损(亏损{abs(unrealized_pnl_pct)*100:.1f}%>阈值{effective_stop_loss*100:.1f}%)"
                            stop_loss_triggered = True
                        
                        # 2.2 强烈反向趋势快速止损（新增）
                        elif (is_strong_bearish if is_long else is_strong_bullish) and unrealized_pnl_pct < -0.005:
                            signal = close_signal
                            reason = f"强烈{trend_forecast}+亏损{abs(unrealized_pnl_pct)*100:.1f}%，快速止损"
                            stop_loss_triggered = True
                        
                        # 2.3 趋势反向+亏损（降低阈值）
                        elif adverse_trend and unrealized_pnl_pct < -0.008:  # 从-1.5%降到-0.8%
                            signal = close_signal
                            reason = f"趋势{trend_forecast}+亏损{abs(unrealized_pnl_pct)*100:.1f}%"
                            stop_loss_triggered = True
                        
                        # 2.4 高风险警告时止损
                        elif risk_sensitive and unrealized_pnl_pct < -0.008:  # 从-1.0%降到-0.8%
                            signal = close_signal
                            reason = f"风险{risk_level}+亏损{abs(unrealized_pnl_pct)*100:.1f}%"
                            stop_loss_triggered = True
                        
                        # 2.5 强制止损（任何人亏损>5%）
                        elif unrealized_pnl_pct < -0.05:
                            signal = close_signal
                            reason = f"强制止损(亏损{abs(unrealized_pnl_pct)*100:.1f}%)"
                            stop_loss_triggered = True
                        
                        # 2.6 时间止损
                        elif self._holding_periods > 30 and unrealized_pnl_pct < 0.005:
                            if self.personality.patience < 0.5:
                                signal = close_signal
                                reason = f"时间止损(持仓{self._holding_periods}周期)"
                                stop_loss_triggered = True
                    
                    # ========== 3. 加仓逻辑（Agent自主判断）==========
                    # 趋势有利时考虑加仓
                    favorable_trend = is_bullish if is_long else is_bearish
                    
                    if not take_profit_triggered and not stop_loss_triggered:
                        # 条件：趋势有利 + 量能配合 + 风险可控
                        if favorable_trend and volume_favorable and not risk_sensitive:
                            can_add = True
                            reject_reason = ""
                            
                            if position_amount >= max_position:
                                can_add = False
                                reject_reason = f"持仓已达上限"
                            elif capital_usage >= max_capital_usage:
                                can_add = False
                                reject_reason = f"资金使用率上限"
                            elif self.personality.aggression <= 0.5:
                                can_add = False
                                reject_reason = "性格不够激进"
                            elif forecast_confidence < 0.6:
                                can_add = False
                                reject_reason = "预测信心不足"
                            
                            if can_add:
                                signal = add_signal
                                reason = f"趋势{trend_forecast}+量能{volume_forecast}，加{position_type}"
                            else:
                                reason = f"放弃加仓: {reject_reason}"
                    
                    # 4. 趋势反向时悲观派减仓
                    if signal is None and not take_profit_triggered and not stop_loss_triggered:
                        if adverse_trend and self.personality.optimism < 0.4:
                            signal = close_signal
                            reason = f"趋势{trend_forecast}，悲观派平{position_type}"
                    
                    # 5. 持有
                    if signal is None and not take_profit_triggered and not stop_loss_triggered:
                        reason = f"维持{position_type}"
                
                else:
                    # === 无持仓：Agent自主决定开仓方向 ===
                    # 重置追踪变量
                    self._max_profit_pct = 0.0
                    self._holding_periods = 0
                    
                    # ========== Agent根据性格解读预言后自主决策 ==========
                    
                    # 风险过高时观望
                    if risk_sensitive and risk_level == 'high':
                        signal = None
                        reason = f"风险{risk_level}({','.join(risk_factors[:2])}),观望"
                    
                    # === 强烈信号：大多数Agent都会跟随 ===
                    elif is_strong_bullish:
                        # 强烈看涨：除了极度悲观派都开多
                        if self.personality.optimism >= 0.3:
                            signal = 'buy'
                            reason = f"强烈{trend_forecast}(信心{forecast_confidence:.0%})，开多"
                        else:
                            signal = None
                            reason = "极度悲观派观望"
                    
                    elif is_strong_bearish:
                        # 强烈看跌：除了极度乐观派都开空
                        if self.personality.optimism <= 0.7:
                            signal = 'short'
                            reason = f"强烈{trend_forecast}(信心{forecast_confidence:.0%})，开空"
                        else:
                            signal = None
                            reason = "极度乐观派观望"
                    
                    # === 普通信号：根据性格决定 ===
                    elif is_bullish:
                        # 优化C：检查是否满足开仓门槛
                        if forecast_confidence < min_confidence_to_open:
                            signal = None
                            reason = f"{trend_forecast}但信心不足({forecast_confidence:.0%}<{min_confidence_to_open:.0%})，观望"
                        # 看涨：乐观派和激进派开多
                        elif self.personality.optimism >= 0.5:
                            signal = 'buy'
                            reason = f"{trend_forecast}，乐观派开多"
                        elif self.personality.aggression > 0.6 and volume_favorable:
                            signal = 'buy'
                            reason = f"{trend_forecast}+{volume_forecast}，激进派开多"
                        else:
                            signal = None
                            reason = f"{trend_forecast}但性格不匹配，观望"
                    
                    elif is_bearish:
                        # 优化C：检查是否满足开仓门槛
                        if forecast_confidence < min_confidence_to_open:
                            signal = None
                            reason = f"{trend_forecast}但信心不足({forecast_confidence:.0%}<{min_confidence_to_open:.0%})，观望"
                        # 看跌：悲观派和激进派开空（降低门槛，与做多对称）
                        elif self.personality.optimism <= 0.5:
                            signal = 'short'
                            reason = f"{trend_forecast}，悲观派开空"
                        elif self.personality.aggression > 0.5 and volume_favorable:  # 从0.6降到0.5
                            signal = 'short'
                            reason = f"{trend_forecast}+{volume_forecast}，激进派开空"
                        elif forecast_confidence > 0.65:  # 新增：高信心时中性派也开空
                            signal = 'short'
                            reason = f"{trend_forecast}(高信心{forecast_confidence:.0%})，开空"
                        else:
                            signal = None
                            reason = f"{trend_forecast}但性格不匹配，观望"
                    
                    # === 震荡行情：只有激进派会操作 ===
                    else:
                        if self.personality.aggression > 0.7 and self.personality.patience < 0.4:
                            # 激进且没耐心的人可能会博方向
                            if self.personality.optimism > 0.5:
                                signal = 'buy'
                                reason = "震荡行情，激进乐观派博多"
                            else:
                                signal = 'short'
                                reason = "震荡行情，激进悲观派博空"
                        else:
                            signal = None
                            reason = f"震荡行情({trend_forecast})，观望"
            
            # ========== 市场数据公告（market）==========
            elif tier == 'market':
                market_state = content.get('market_state', {})
                trend = market_state.get('trend', '')
                momentum = market_state.get('momentum', '')
                
                if has_position:
                    # 已持仓时根据市场变化决定（区分多空）
                    is_long = position_side == 'long' or position_side is None
                    close_signal = 'sell' if is_long else 'cover'
                    position_type = "多仓" if is_long else "空仓"
                    
                    base_take_profit = 0.03 + self.personality.aggression * 0.02
                    base_stop_loss = 0.02 + self.personality.risk_tolerance * 0.02
                    
                    if is_long:
                        # 多仓：市场转跌触发止损
                        if '下降' in trend:
                            if self.personality.optimism < 0.4:
                                signal = close_signal
                                reason = "市场转跌，悲观派平多"
                            elif unrealized_pnl_pct < -base_stop_loss * 0.7:
                                signal = close_signal
                                reason = f"市场转跌+亏损{abs(unrealized_pnl_pct)*100:.1f}%"
                        # 超买触发止盈
                        elif '超买' in momentum:
                            if unrealized_pnl_pct > base_take_profit * 0.8:
                                signal = close_signal
                                reason = f"超买+盈利{unrealized_pnl_pct*100:.1f}%"
                            elif self.personality.aggression < 0.5:
                                signal = close_signal
                                reason = "超买，保守派止盈"
                    else:
                        # 空仓：市场转涨触发止损
                        if '上升' in trend:
                            if self.personality.optimism > 0.6:
                                signal = close_signal
                                reason = "市场转涨，乐观派平空"
                            elif unrealized_pnl_pct < -base_stop_loss * 0.7:
                                signal = close_signal
                                reason = f"市场转涨+亏损{abs(unrealized_pnl_pct)*100:.1f}%"
                        # 超卖触发止盈（空仓的止盈）
                        elif '超卖' in momentum:
                            if unrealized_pnl_pct > base_take_profit * 0.8:
                                signal = close_signal
                                reason = f"超卖+盈利{unrealized_pnl_pct*100:.1f}%"
                            elif self.personality.aggression < 0.5:
                                signal = close_signal
                                reason = "超卖，保守派止盈"
                else:
                    # 无持仓时根据趋势开仓（重置追踪变量）
                    self._max_profit_pct = 0.0
                    self._holding_periods = 0
                    
                    # 上涨趋势开多
                    if '上升' in trend:
                        if self.personality.optimism >= 0.5:
                            signal = 'buy'
                            reason = "市场上涨，乐观派开多"
                        elif self.personality.aggression > 0.7:
                            signal = 'buy'
                            reason = "市场上涨，激进派开多"
                    # 下跌趋势开空
                    elif '下降' in trend:
                        if self.personality.optimism <= 0.4:
                            signal = 'short'
                            reason = "市场下跌，悲观派开空"
                        elif self.personality.aggression > 0.7:
                            signal = 'short'
                            reason = "市场下跌，激进派开空"
                    # 超卖抄底
                    elif '超卖' in momentum and self.personality.aggression < 0.4:
                        signal = 'buy'
                        reason = "超卖抄底开多"
                    # 超买做空
                    elif '超买' in momentum and self.personality.aggression > 0.6:
                        signal = 'short'
                        reason = "超买做空"
            
            # ========== 系统警告公告（system）==========
            elif tier == 'system':
                if '风险' in str(content) and has_position:
                    if self.personality.risk_tolerance < 0.5:
                        signal = 'sell'
                        reason = "系统风险警告，减仓"
        
        if not reason:
            reason = f"性格(乐观{self.personality.optimism:.1f}/激进{self.personality.aggression:.1f})"
        
        return {
            'accept': accept,
            'confidence': final_confidence,
            'signal': signal,
            'reason': reason
        }
    
    def calculate_personal_cooldown(self, close_reason: str, last_trade_pnl: float,
                                    trend_forecast: str, risk_level: str) -> int:
        """
        Agent自主计算个性化冷却期（根据性格、经历、市场状态）
        
        Args:
            close_reason: 平仓原因 ('take_profit', 'stop_loss', 'time_stop', 'trend_reverse')
            last_trade_pnl: 最后一笔交易的盈亏
            trend_forecast: 市场趋势预测
            risk_level: 风险等级
            
        Returns:
            int: 冷却周期数（2~30）
        """
        # 基础冷却期：5个周期 = 100秒
        base_cooldown = 5
        
        # ========== 1. 性格因子 ==========
        # 激进度：激进派冷却短，保守派冷却长
        # aggression=1.0 → factor=0.5 (减半)
        # aggression=0.5 → factor=1.0 (标准)
        # aggression=0.0 → factor=1.5 (加长50%)
        aggression_factor = 1.5 - self.personality.aggression
        
        # 耐心度：没耐心想快速再战，有耐心愿意等待
        # patience=0.0 → factor=0.6
        # patience=0.5 → factor=0.85
        # patience=1.0 → factor=1.1
        patience_factor = 0.6 + self.personality.patience * 0.5
        
        # ========== 2. 盈亏状态因子 ==========
        if last_trade_pnl > 10:
            # 大赚(>$10)：判断正确，快速再入场
            pnl_factor = 0.5
            mood = "兴奋😊"
        elif last_trade_pnl > 0:
            # 小赚：适度冷却
            pnl_factor = 0.8
            mood = "满意😌"
        elif last_trade_pnl > -10:
            # 小亏(<$10)：延长冷却
            pnl_factor = 1.3
            mood = "沮丧😔"
        elif last_trade_pnl > -30:
            # 中等亏损($10~$30)：显著延长
            pnl_factor = 1.8
            mood = "懊恼😞"
        else:
            # 大亏(>$30)：长时间反思
            pnl_factor = 2.5
            mood = "痛苦😭"
        
        # ========== 3. 连续亏损惩罚（强制冷静）==========
        if self._consecutive_losses >= 5:
            # 连续5次亏损：可能策略失效，长时间暂停
            loss_penalty = 3.0
            mood = "迷茫😵"
        elif self._consecutive_losses >= 3:
            # 连续3次亏损：需要重新评估
            loss_penalty = 2.0
            mood = "困惑😕"
        else:
            loss_penalty = 1.0
        
        # ========== 4. 市场状态因子 ==========
        market_factor = 1.0
        
        # 震荡市最危险，容易来回打脸
        if trend_forecast in ['震荡', '盘整', '横盘']:
            market_factor = 2.5  # 震荡市：延长150%
        
        # 风险等级调整
        if risk_level == 'high':
            market_factor = max(market_factor, 2.0)  # 高风险：至少延长100%
        elif risk_level == 'medium':
            market_factor = max(market_factor, 1.3)
        
        # ========== 5. 平仓原因调整 ==========
        reason_factor = {
            'take_profit': 0.7,      # 主动止盈：判断正确，短冷却
            'stop_loss': 1.5,        # 止损：判断错误，延长冷却
            'time_stop': 1.2,        # 时间止损：耐心耗尽，适度延长
            'trend_reverse': 1.4,    # 趋势反转：需要重新观察
            'risk_alert': 1.6,       # 风险预警：谨慎行事
        }.get(close_reason, 1.0)
        
        # ========== 6. 综合计算 ==========
        cooldown = base_cooldown * (
            aggression_factor 
            * patience_factor 
            * pnl_factor 
            * loss_penalty 
            * market_factor 
            * reason_factor
        )
        
        # 限制范围：2~30个周期（40秒~10分钟）
        final_cooldown = int(max(2, min(30, cooldown)))
        
        logger.info(
            f"🕐 {self.agent_id}: 个性化冷却={final_cooldown}周期({final_cooldown*20}秒) "
            f"[盈亏${last_trade_pnl:+.1f} {mood}] "
            f"[激进{self.personality.aggression:.1f}×{aggression_factor:.1f}, "
            f"耐心{self.personality.patience:.1f}×{patience_factor:.1f}] "
            f"[市场{trend_forecast}×{market_factor:.1f}]"
        )
        
        return final_cooldown
    
    def calculate_position_size(self, current_price: float, balance: float, 
                                 initial_capital: float, confidence: float,
                                 risk_level: str = 'medium', 
                                 total_pnl_ratio: float = 0.0) -> float:
        """
        Agent自主计算交易量（基于性格和市场信息）
        
        Args:
            current_price: 当前BTC价格
            balance: 可用资金
            initial_capital: 初始资金
            confidence: 交易信心度 (0-1)
            risk_level: 风险等级 ('low', 'medium', 'high')
            total_pnl_ratio: 总盈亏占初始资金比例
            
        Returns:
            float: 建议交易量（BTC）
        """
        if current_price <= 0 or balance <= 0:
            return 0.01  # 默认最小量
        
        # ========== 简化计算：直接算BTC数量 ==========
        # 基础交易量：0.01 BTC
        base_amount = 0.01
        
        # 1. 激进度加成：激进派可以翻倍 (0→1x, 0.5→1.5x, 1→2x)
        aggression_multiplier = 1.0 + self.personality.aggression
        
        # 2. 风险承受度加成 (0→1x, 0.5→1.25x, 1→1.5x)
        risk_tolerance_multiplier = 1.0 + self.personality.risk_tolerance * 0.5
        
        # 3. 信心度加成 (0.5→1x, 0.8→1.3x, 1.0→1.5x)
        confidence_multiplier = 1.0 + (confidence - 0.5) * 1.0
        
        # 4. 风险等级调整
        risk_multiplier = {
            'low': 1.5,      # 低风险：+50%
            'medium': 1.0,   # 中风险：不变
            'high': 0.5      # 高风险：-50%
        }.get(risk_level, 1.0)
        
        # 5. 盈亏状态调整
        if total_pnl_ratio > 0.05:      # 盈利>5%，激进+30%
            pnl_multiplier = 1.3
        elif total_pnl_ratio > 0.02:    # 盈利>2%，+10%
            pnl_multiplier = 1.1
        elif total_pnl_ratio < -0.05:   # 亏损>5%，保守-40%
            pnl_multiplier = 0.6
        elif total_pnl_ratio < -0.02:   # 亏损>2%，-20%
            pnl_multiplier = 0.8
        else:
            pnl_multiplier = 1.0
        
        # 综合计算BTC数量
        btc_amount = (base_amount 
                      * aggression_multiplier 
                      * risk_tolerance_multiplier 
                      * confidence_multiplier 
                      * risk_multiplier 
                      * pnl_multiplier)
        
        # BTC数量限制：0.01~0.1 BTC
        btc_amount = max(0.01, min(0.1, btc_amount))
        
        # 四舍五入到0.01精度
        btc_amount = round(btc_amount, 2)
        
        logger.debug(f"{self.agent_id}: 计算仓位 amount={btc_amount} BTC "
                    f"(激进{self.personality.aggression:.1f}, 信心{confidence:.1%}, 风险{risk_level})")
        
        return btc_amount
    
    def decide(self, current_price: float = 0, has_position: bool = False, 
               unrealized_pnl_pct: float = 0.0, position_amount: float = 0.0,
               balance: float = 10000.0, initial_capital: float = 10000.0,
               trade_count: int = 0, position_side: str = None) -> Dict:
        """
        决策方法（Supervisor调用的统一接口）
        
        Args:
            current_price: 当前价格
            has_position: 是否已有持仓
            unrealized_pnl_pct: 未实现盈亏百分比
            position_amount: 当前持仓量（BTC）
            balance: 当前余额
            initial_capital: 初始资金
            trade_count: 已交易笔数
            position_side: 持仓方向 'long'/'short'/None
        
        Returns:
            Dict: 决策结果 {'signal', 'confidence', 'reason', 'suggested_amount'}
        """
        # 保存当前价格供仓位计算使用
        self._current_price = current_price
        self._balance = balance
        self._initial_capital = initial_capital
        
        return self.process_bulletins_and_decide(
            has_position, unrealized_pnl_pct, position_amount, 
            balance, initial_capital, trade_count, position_side
        )
    
    def process_bulletins_and_decide(self, has_position: bool = False, 
                                     unrealized_pnl_pct: float = 0.0,
                                     position_amount: float = 0.0,
                                     balance: float = 10000.0,
                                     initial_capital: float = 10000.0,
                                     trade_count: int = 0,
                                     position_side: str = None) -> Dict:
        """
        读取并处理所有公告，做出综合决策
        
        Args:
            has_position: 是否已有持仓
            unrealized_pnl_pct: 未实现盈亏百分比
            position_amount: 当前持仓量（BTC）
            balance: 当前余额
            initial_capital: 初始资金
            trade_count: 已交易笔数
            position_side: 持仓方向 'long'/'short'/None
        
        Returns:
            Dict: 决策结果 {'signal': 'buy'/'sell'/'add'/'short'/'cover'/None, 'confidence': float, 'reason': str}
        """
        # 0. 冷却期处理（防止频繁开平仓）
        # 注：个性化冷却期由calculate_personal_cooldown()动态计算
        
        # 冷却期递减
        if self._cooldown_periods > 0:
            self._cooldown_periods -= 1
        
        # 持仓周期递增（每个决策周期只增加一次，而不是每条公告都增加）
        if has_position:
            if not hasattr(self, '_holding_periods'):
                self._holding_periods = 0
            self._holding_periods += 1
        
        # 1. 读取公告
        bulletins = self.read_bulletins(limit=10)
        
        if not bulletins:
            return {
                'signal': None,
                'confidence': 0,
                'reason': '无公告信息'
            }
        
        # 2. 解读每条公告（传入持仓和资金状态）
        interpretations = []
        for bulletin in bulletins:
            interp = self.interpret_bulletin(
                bulletin, has_position, unrealized_pnl_pct,
                position_amount, balance, initial_capital, trade_count,
                position_side
            )
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
                'signal': None,
                'confidence': 0,
                'reason': '所有公告均未接受'
            }
        
        # 4. 根据接受的公告做出决策
        # 优先级：战略(先知占卜) > 系统 > 市场
        strategic = [b for b in accepted_bulletins if b['tier'] == 'strategic' and b.get('signal')]
        system = [b for b in accepted_bulletins if b['tier'] == 'system' and b.get('signal')]
        market = [b for b in accepted_bulletins if b['tier'] == 'market' and b.get('signal')]
        
        # 选择最高优先级且有交易信号的公告
        if strategic:
            primary = strategic[0]
        elif system:
            primary = system[0]
        elif market:
            primary = market[0]
        else:
            # 没有任何交易信号
            position_status = "持仓中" if has_position else "空仓"
            return {
                'signal': None,
                'confidence': 0,
                'reason': f"{position_status}，观望"
            }
        
        final_signal = primary['signal']
        final_reason = primary['reason']
        final_confidence = primary['confidence']
        
        # 冷却期检查：平仓后不能立即开仓
        is_close_signal = final_signal in ['sell', 'cover']
        is_open_signal = final_signal in ['buy', 'short']
        is_add_signal = final_signal in ['add', 'add_short']
        
        # ========== 如果是平仓信号，计算个性化冷却期 ==========
        if is_close_signal:
            # 提取市场信息（用于计算冷却期）
            trend_forecast = '正常'
            risk_level = 'medium'
            
            # 从战略公告（先知预言）中提取
            for b in strategic:
                content = b.get('content', {}) if isinstance(b.get('content'), dict) else {}
                trend_forecast = content.get('trend_forecast', '正常')
                risk_level = content.get('risk_level', 'medium')
                break
            
            # 分析平仓原因
            if '止盈' in final_reason or '盈利' in final_reason:
                close_reason = 'take_profit'
            elif '止损' in final_reason or '亏损' in final_reason:
                close_reason = 'stop_loss'
            elif '时间' in final_reason:
                close_reason = 'time_stop'
            elif '趋势' in final_reason or '反转' in final_reason or '反向' in final_reason:
                close_reason = 'trend_reverse'
            elif '风险' in final_reason:
                close_reason = 'risk_alert'
            else:
                close_reason = 'unknown'
            
            # 估算本次交易盈亏（基于未实现盈亏）
            # 注：实际盈亏会在Supervisor执行后更新，这里只是估算
            estimated_pnl = unrealized_pnl_pct * balance if 'has_position' in locals() and has_position else 0
            
            # 更新连续亏损计数器
            if estimated_pnl < 0:
                self._consecutive_losses += 1
            else:
                self._consecutive_losses = 0  # 盈利则重置
            
            # 调用个性化冷却期计算
            personal_cooldown = self.calculate_personal_cooldown(
                close_reason=close_reason,
                last_trade_pnl=estimated_pnl,
                trend_forecast=trend_forecast,
                risk_level=risk_level
            )
            
            self._cooldown_periods = personal_cooldown
            self._close_reason = close_reason
        
        # 如果是开仓信号且在冷却期内，阻止开仓
        if is_open_signal and self._cooldown_periods > 0:
            return {
                'signal': None,
                'confidence': 0,
                'reason': f"冷却期中({self._cooldown_periods}周期)，暂不开仓",
                'suggested_amount': 0
            }
        
        # ========== 计算建议交易量（Agent自主决定）==========
        suggested_amount = 0.01  # 默认最小量
        
        if is_open_signal or is_add_signal:
            # 从战略公告中获取风险等级
            risk_level = 'medium'
            for b in strategic:
                content = b.get('content', {}) if isinstance(b.get('content'), dict) else {}
                risk_level = content.get('risk_level', 'medium')
                break
            
            # 计算盈亏比例
            total_pnl_ratio = 0.0
            if hasattr(self, '_initial_capital') and self._initial_capital > 0:
                # 从账簿状态估算（简化版）
                if hasattr(self, '_balance'):
                    total_pnl_ratio = (self._balance - self._initial_capital) / self._initial_capital
            
            # 调用仓位计算方法
            if hasattr(self, '_current_price') and self._current_price > 0:
                suggested_amount = self.calculate_position_size(
                    current_price=self._current_price,
                    balance=getattr(self, '_balance', 10000),
                    initial_capital=getattr(self, '_initial_capital', 10000),
                    confidence=final_confidence,
                    risk_level=risk_level,
                    total_pnl_ratio=total_pnl_ratio
                )
        
        return {
            'signal': final_signal,
            'confidence': final_confidence,
            'reason': final_reason,
            'suggested_amount': suggested_amount
        }

