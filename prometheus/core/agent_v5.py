"""
Agent V5.0 - 完全重构的Agent系统
================================

v5.0设计理念：
- 模块化：清晰分离Lineage/Genome/Instinct/Strategy/Memory/Emotion/Daimon
- 自主性：Agent完全自主决策
- 可解释性：决策过程完全可追溯
- 可进化性：支持基因进化和策略学习

架构：
    Lineage（血统）- 固定，用于生殖隔离
    Genome（基因组）- 缓慢进化，决定能力
    Instinct（本能）- 可遗传，驱动生存
    Strategy Pool（策略组）- 灵活，可切换
    PersonalInsights（个体记忆）- 学习，可积累
    EmotionalState（情绪）- 动态，影响决策
    Daimon（守护神）- 决策中枢

与v4.0的区别：
- v4.0：单一决策方法，硬编码逻辑
- v5.0：Daimon投票机制，模块化设计
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import logging

# v5.0模块
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.instinct import Instinct
from prometheus.core.inner_council import Daimon, CouncilDecision
from prometheus.core.strategy import Strategy, StrategySignal, get_compatible_strategies
from prometheus.core.personal_insights import PersonalInsights

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent状态"""
    NEWBORN = "newborn"      # 新生（保护期）
    ACTIVE = "active"        # 活跃
    MATURE = "mature"        # 成熟
    STRUGGLING = "struggling"  # 挣扎
    DYING = "dying"          # 濒死
    DEAD = "dead"            # 死亡


class DeathReason(Enum):
    """死亡原因"""
    CAPITAL_DEPLETION = "capital_depletion"  # 资金耗尽
    SUICIDE = "suicide"                      # 自杀
    NATURAL_DEATH = "natural_death"          # 自然死亡（老age）
    SYSTEM_ELIMINATION = "system_elimination"  # 系统淘汰


@dataclass
class EmotionalState:
    """
    情绪状态
    
    Attributes:
        despair: 绝望 (0-1)
        fear: 恐惧 (0-1)
        confidence: 信心 (0-1)
        stress: 压力 (0-1)
    """
    despair: float = 0.0
    fear: float = 0.0
    confidence: float = 0.5
    stress: float = 0.0


class AgentV5:
    """
    Agent v5.0 - 完全重构版
    
    核心特性：
    1. 模块化设计：Lineage/Genome/Instinct/Strategy/Memory/Emotion/Daimon
    2. 自主决策：通过Daimon综合所有因素
    3. 可学习：通过PersonalInsights积累经验
    4. 可进化：Lineage/Genome/Instinct支持遗传
    """
    
    def __init__(
        self,
        agent_id: str,
        initial_capital: float,
        lineage: LineageVector,
        genome: GenomeVector,
        instinct: Instinct,
        generation: int = 0,
        meta_genome: Optional['MetaGenome'] = None,
    ):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识
            initial_capital: 初始资金
            lineage: 血统向量
            genome: 基因组向量
            instinct: 本能
            generation: 代数
            meta_genome: 元基因组（控制决策风格）
        """
        # ==================== 身份与血统 ====================
        self.agent_id = agent_id
        self.generation = generation
        self.lineage = lineage  # 固定，不变
        self.genome = genome    # 缓慢进化
        self.instinct = instinct  # 可遗传，可变
        
        # ==================== 元基因组（v5.1新增）====================
        if meta_genome is None:
            from prometheus.core.meta_genome import MetaGenome
            meta_genome = MetaGenome.create_genesis()
        self.meta_genome = meta_genome  # 可遗传，控制决策风格
        
        # ==================== 财务状态 ====================
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.capital_history: List[float] = [initial_capital]
        
        # ==================== 交易状态 ====================
        self.current_position: Dict = {'amount': 0, 'side': None, 'entry_price': 0}
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.total_pnl = 0.0
        
        # ==================== 策略系统 ====================
        self.strategy_pool: List[Strategy] = []
        self.active_strategies: List[Strategy] = []
        self.current_strategy_name: Optional[str] = None
        self._initialize_strategies()
        
        # ==================== 记忆与经验 ====================
        self.personal_insights = PersonalInsights()
        
        # ==================== 情绪状态 ====================
        self.emotion = EmotionalState()
        
        # ==================== 决策系统 ====================
        self.daimon = Daimon(self)  # 守护神 - 决策中枢
        
        # ==================== 状态管理 ====================
        self.state = AgentState.NEWBORN
        self.days_alive = 0
        self.cycles_alive = 0
        self.death_reason: Optional[DeathReason] = None
        
        logger.info(
            f"🆕 Agent {agent_id} 诞生 | "
            f"第{generation}代 | "
            f"资金${initial_capital:.2f} | "
            f"家族{self.lineage.get_dominant_families()[:3]} | "
            f"性格:{self.instinct.describe_personality()}"
        )
    
    # ==================== 策略管理 ====================
    
    def _initialize_strategies(self):
        """
        初始化策略池
        
        规则：
        1. 根据genome选择兼容的策略
        2. 最多5个策略
        3. 至少激活1个策略
        """
        # 获取与genome兼容的策略
        compatible = get_compatible_strategies(self.genome)
        
        # 限制最多5个
        self.strategy_pool = compatible[:5]
        
        # 激活第一个策略（后续可以动态切换）
        if self.strategy_pool:
            self.active_strategies = [self.strategy_pool[0]]
            self.current_strategy_name = self.strategy_pool[0].name
        
        logger.debug(
            f"Agent {self.agent_id} 策略池: "
            f"{[s.name for s in self.strategy_pool]} | "
            f"激活: {[s.name for s in self.active_strategies]}"
        )
    
    def switch_strategy(self, strategy_name: str) -> bool:
        """
        切换激活的策略
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            bool: 是否成功切换
        """
        # 查找策略
        for strategy in self.strategy_pool:
            if strategy.name == strategy_name:
                self.active_strategies = [strategy]
                self.current_strategy_name = strategy_name
                logger.info(f"Agent {self.agent_id} 切换策略: {strategy_name}")
                return True
        
        logger.warning(f"Agent {self.agent_id} 策略切换失败: {strategy_name} 不在策略池中")
        return False
    
    # ==================== 核心决策流程 ====================
    
    def make_trading_decision(
        self,
        market_data: Dict,
        bulletins: Dict,
        cycle_count: int
    ) -> Optional[Dict]:
        """
        做出交易决策 - v5.0完全自主
        
        决策流程：
        1. 检查Agent状态（死亡/新生保护）
        2. 更新情绪状态
        3. 激活策略，获取市场分析
        4. 准备决策上下文
        5. 咨询Daimon（守护神）
        6. 返回交易请求
        
        Args:
            market_data: 市场数据
            bulletins: 公告板信息
            cycle_count: 当前周期数
        
        Returns:
            Optional[Dict]: 交易请求，None表示不交易
        """
        # 1. 状态检查
        if self.state == AgentState.DEAD:
            return None
        
        # 新生保护期（前3个周期）
        if self.cycles_alive < 3:
            self.cycles_alive += 1
            return None
        
        # 2. 更新情绪
        self._update_emotional_state()
        
        # 3. 激活策略，获取市场分析
        strategy_signals = self._analyze_with_strategies(market_data)
        
        # 4. 准备决策上下文
        context = self._prepare_decision_context(
            market_data, bulletins, strategy_signals
        )
        
        # 5. 咨询Daimon
        guidance = self.daimon.guide(context)
        
        logger.debug(
            f"Agent {self.agent_id} | "
            f"Daimon建议: {guidance.action}({guidance.confidence:.1%}) | "
            f"推理: {guidance.reasoning}"
        )
        
        # 6. 生成交易请求
        if guidance.action in ['buy', 'sell', 'short', 'cover', 'close']:
            return self._create_trade_request(guidance, market_data)
        else:
            return None  # hold
    
    def _analyze_with_strategies(self, market_data: Dict) -> List[StrategySignal]:
        """
        使用激活的策略分析市场
        
        Args:
            market_data: 市场数据
        
        Returns:
            List[StrategySignal]: 策略信号列表
        """
        signals = []
        
        # 准备Agent上下文（策略需要）
        agent_context = {
            'genome': self.genome,
            'position': self.current_position,
            'capital_ratio': self.current_capital / self.initial_capital,
        }
        
        # 遍历激活的策略
        for strategy in self.active_strategies:
            try:
                signal = strategy.analyze(market_data, agent_context)
                signals.append(signal)
            except Exception as e:
                logger.error(f"策略{strategy.name}分析失败: {e}")
        
        return signals
    
    def _prepare_decision_context(
        self,
        market_data: Dict,
        bulletins: Dict,
        strategy_signals: List[StrategySignal]
    ) -> Dict:
        """
        准备决策上下文（给Daimon）
        
        Args:
            market_data: 市场数据
            bulletins: 公告板信息
            strategy_signals: 策略信号
        
        Returns:
            Dict: 决策上下文
        """
        return {
            # 市场数据
            'market_data': market_data,
            'bulletins': bulletins,
            
            # Agent状态
            'capital': self.current_capital,
            'capital_ratio': self.current_capital / self.initial_capital,
            'position': self.current_position,
            
            # 交易历史
            'recent_pnl': self._get_recent_pnl(),
            'consecutive_losses': self.consecutive_losses,
            'consecutive_wins': self.consecutive_wins,
            
            # 策略信号（⭐ v5.0新增）
            'strategy_signals': [
                {
                    'strategy_name': s.strategy_name,
                    'bullish_score': s.bullish_score,
                    'bearish_score': s.bearish_score,
                    'confidence': s.confidence,
                    'reasoning': s.reasoning,
                }
                for s in strategy_signals
            ],
            
            # 个人经验
            'personal_stats': self.personal_insights.get_quick_stats(),
        }
    
    def _create_trade_request(
        self,
        guidance: CouncilDecision,
        market_data: Dict
    ) -> Dict:
        """
        创建交易请求
        
        Args:
            guidance: Daimon的决策
            market_data: 市场数据
        
        Returns:
            Dict: 交易请求
        """
        action = guidance.action
        current_price = market_data.get('price', 0)
        
        # 计算仓位大小（基于genome和confidence）
        max_position_pct = self.genome.active_params.get('max_position_pct', 0.1)
        position_size = self.current_capital * max_position_pct * guidance.confidence
        amount = position_size / current_price if current_price > 0 else 0
        
        return {
            'agent_id': self.agent_id,
            'action': action,
            'amount': amount,
            'confidence': guidance.confidence,
            'reasoning': guidance.reasoning,
            'strategy': self.current_strategy_name,
        }
    
    # ==================== 状态更新 ====================
    
    def _update_emotional_state(self):
        """更新情绪状态"""
        capital_ratio = self.current_capital / self.initial_capital
        
        # 绝望
        if capital_ratio < 0.5:
            self.emotion.despair = (0.5 - capital_ratio) * 2
        else:
            self.emotion.despair = 0
        
        self.emotion.despair += self.consecutive_losses * 0.05
        self.emotion.despair = min(self.emotion.despair, 1.0)
        
        # 信心
        if capital_ratio > 1.0:
            self.emotion.confidence = min(capital_ratio - 1.0 + 0.5, 1.0)
        else:
            self.emotion.confidence = capital_ratio * 0.5
        
        # 恐惧
        self.emotion.fear = self.emotion.despair * 0.8
        
        # 压力
        self.emotion.stress = (self.emotion.despair + self.emotion.fear) / 2
    
    def _get_recent_pnl(self, last_n: int = 5) -> float:
        """获取最近N笔交易的平均盈亏率"""
        if len(self.capital_history) < 2:
            return 0.0
        
        recent = self.capital_history[-last_n:]
        if len(recent) < 2:
            return 0.0
        
        pnl_pct = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
        return pnl_pct
    
    # ==================== 学习与冥思 ====================
    
    def meditate(self, recent_trades: List[Dict]):
        """
        冥思：反思最近的交易
        
        Args:
            recent_trades: 最近的交易记录
        """
        record = self.personal_insights.meditate(recent_trades)
        
        if record.insights:
            logger.info(
                f"🧘 Agent {self.agent_id} 冥思 | "
                f"发现{record.patterns_discovered}个模式 | "
                f"洞察: {record.insights[:2]}"
            )
    
    def try_epiphany(self) -> bool:
        """
        尝试顿悟
        
        顿悟条件：
        - 连续盈利3次
        - 或资金翻倍
        - 或其他触发条件
        
        Returns:
            bool: 是否触发顿悟
        """
        capital_ratio = self.current_capital / self.initial_capital
        
        # 条件1: 资金翻倍
        if capital_ratio >= 2.0:
            epiphany = self.personal_insights.trigger_epiphany(
                trigger="资金翻倍",
                effect="解锁新策略",
                magnitude=0.8
            )
            logger.info(f"💡 Agent {self.agent_id} 顿悟! {epiphany.effect}")
            return True
        
        # 条件2: 连续盈利5次
        if self.consecutive_wins >= 5:
            epiphany = self.personal_insights.trigger_epiphany(
                trigger="连续盈利5次",
                effect="提升信心本能",
                magnitude=0.5
            )
            logger.info(f"💡 Agent {self.agent_id} 顿悟! {epiphany.effect}")
            return True
        
        return False
    
    # ==================== 生命周期 ====================
    
    def age_one_day(self):
        """老化一天"""
        self.days_alive += 1
        
        # 状态转换
        if self.days_alive > 30:
            self.state = AgentState.MATURE
        elif self.days_alive > 7:
            self.state = AgentState.ACTIVE
    
    def should_commit_suicide(self) -> bool:
        """
        判断是否应该自杀
        
        完全由Agent自主决定
        
        Returns:
            bool: 是否自杀
        """
        if self.state == AgentState.DEAD or self.days_alive < 3:
            return False
        
        capital_ratio = self.current_capital / self.initial_capital
        
        # 综合评估
        suicide_factors = {
            '资金严重亏损': capital_ratio < 0.3,
            '连续大量亏损': self.consecutive_losses > 10,
            '累计亏损巨大': capital_ratio < 0.2,
            '情绪绝望': self.emotion.despair > 0.8,
        }
        
        triggered = sum(suicide_factors.values())
        
        if triggered >= 3:
            # 性格影响最终决定
            suicide_probability = triggered / len(suicide_factors)
            will_to_live = self.instinct.fear_of_death * (1 - self.emotion.despair)
            
            if suicide_probability > will_to_live:
                return True
        
        return False
    
    def commit_suicide(self):
        """自杀"""
        logger.warning(
            f"💀 Agent {self.agent_id} 自杀 | "
            f"资金剩余{self.current_capital:.2f} | "
            f"绝望{self.emotion.despair:.1%}"
        )
        self.state = AgentState.DEAD
        self.death_reason = DeathReason.SUICIDE
    
    # ==================== 工具方法 ====================
    
    def get_summary(self) -> Dict:
        """获取Agent摘要信息"""
        return {
            'agent_id': self.agent_id,
            'generation': self.generation,
            'state': self.state.value,
            'capital': self.current_capital,
            'capital_ratio': self.current_capital / self.initial_capital,
            'total_pnl': self.total_pnl,
            'trade_count': self.trade_count,
            'win_rate': self.win_count / self.trade_count if self.trade_count > 0 else 0,
            'current_strategy': self.current_strategy_name,
            'emotion': {
                'despair': self.emotion.despair,
                'fear': self.emotion.fear,
                'confidence': self.emotion.confidence,
                'stress': self.emotion.stress,
            },
        }
    
    @classmethod
    def create_genesis(cls, agent_id: str, initial_capital: float, family_id: int = 0, num_families: int = 50) -> 'AgentV5':
        """
        创建创世Agent
        
        Args:
            agent_id: Agent ID
            initial_capital: 初始资金
            family_id: 家族ID
            num_families: 家族总数
        
        Returns:
            AgentV5: 创世Agent
        """
        lineage = LineageVector.create_genesis(family_id=family_id, num_families=num_families)
        genome = GenomeVector.create_genesis()
        instinct = Instinct.create_genesis()
        
        return cls(
            agent_id=agent_id,
            initial_capital=initial_capital,
            lineage=lineage,
            genome=genome,
            instinct=instinct,
            generation=0,
        )

