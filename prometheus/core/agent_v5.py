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
# from prometheus.core.instinct import Instinct  # 已移除，使用StrategyParams替代
from prometheus.core.strategy_params import StrategyParams  # AlphaZero式极简
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
        strategy_params: StrategyParams,  # AlphaZero式：直接替换instinct
        generation: int = 0,
        meta_genome: Optional['MetaGenome'] = None,
    ):
        """
        初始化Agent - AlphaZero式极简版
        
        Args:
            agent_id: Agent唯一标识
            initial_capital: 初始资金
            lineage: 血统向量
            genome: 基因组向量
            strategy_params: 策略参数（替代instinct）
            generation: 代数
            meta_genome: 元基因组（控制决策风格）
        """
        # ==================== 身份与血统 ====================
        self.agent_id = agent_id
        self.generation = generation
        self.lineage = lineage  # 固定，不变
        self.genome = genome    # 缓慢进化
        self.strategy_params = strategy_params  # AlphaZero式：纯理性策略参数
        
        # ==================== 元基因组（v5.1新增）====================
        if meta_genome is None:
            from prometheus.core.meta_genome import MetaGenome
            meta_genome = MetaGenome.create_genesis()
        self.meta_genome = meta_genome  # 可遗传，控制决策风格
        
        # ==================== 财务状态 ====================
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.capital_history: List[float] = [initial_capital]
        # 账簿占位：由上层（Supervisor/Moirai）挂载 AgentAccountSystem
        self.account = None
        
        # ==================== 交易状态 ====================
        # ⚠️ DEPRECATED: current_position 已废弃
        # 请使用 self._get_position_from_ledger() 获取实时持仓
        self.current_position: Dict = {'amount': 0, 'side': None, 'entry_price': 0}  # 保留兼容
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.total_pnl = 0.0
        
        # ==================== 统计追踪（v5.2新增）====================
        self.cycles_survived = 0  # 存活周期数
        self.cycles_with_position = 0  # 有持仓的周期数
        self.max_drawdown = 0.0  # 最大回撤
        self.pnl_history: List[float] = []  # 盈亏历史
        self.peak_capital = initial_capital  # 历史最高资金
        
        # ==================== 策略系统 ====================
        self.strategy_pool: List[Strategy] = []
        self.active_strategies: List[Strategy] = []
        self.current_strategy_name: Optional[str] = None
        self._initialize_strategies()
        
        # ==================== 记忆与经验 ====================
        self.personal_insights = PersonalInsights()
        
        # ==================== 情绪状态 ====================
        # AlphaZero式：移除情绪系统，纯理性决策
        # self.emotion = EmotionalState()  # 已移除
        
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
            f"策略:{self.strategy_params.get_display_string()}"
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
        # TODO: 回测模式下暂时禁用保护期，实盘应该开启
        protection_period = 0  # 原值: 3
        if self.cycles_alive < protection_period:
            self.cycles_alive += 1
            return None
        
        # 确保cycles_alive增长
        self.cycles_alive += 1
        
        # 2. 更新情绪（AlphaZero式：已移除）
        # self._update_emotional_state()  # 不再需要
        
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
        
        # 6. 合理性检查 ✅ 防止不合理决策
        if not self._validate_decision(guidance.action):
            logger.debug(
                f"Agent {self.agent_id} | "
                f"拒绝不合理决策: {guidance.action} (持仓不匹配)"
            )
            return None  # 拒绝不合理决策
        
        # 7. 生成交易请求
        if guidance.action in ['buy', 'sell', 'short', 'cover', 'close']:
            return self._create_trade_request(guidance, market_data)
        else:
            return None  # hold
    
    def _convert_position_for_daimon(self, real_position: Dict) -> Dict:
        """
        将双向持仓格式转换为Daimon兼容的旧格式
        
        新格式（双向持仓）:
            {'long': {'amount': 0.5, 'price': 90000}, 'short': None, 'has_position': True}
        
        旧格式（Daimon兼容）:
            {'amount': 0.5, 'side': 'long', 'entry_price': 90000}
        
        策略：优先返回多头，如果没有多头就返回空头
        
        Args:
            real_position: 实时双向持仓
        
        Returns:
            Dict: Daimon兼容的持仓格式
        """
        long_pos = real_position.get('long')
        short_pos = real_position.get('short')
        
        # 优先多头
        if long_pos:
            return {
                'amount': long_pos['amount'],
                'side': 'long',
                'entry_price': long_pos['price']
            }
        
        # 其次空头
        if short_pos:
            return {
                'amount': short_pos['amount'],
                'side': 'short',
                'entry_price': short_pos['price']
            }
        
        # 无持仓
        return {
            'amount': 0,
            'side': None,
            'entry_price': 0
        }
    
    def _validate_decision(self, action: str) -> bool:
        """
        验证决策的合理性
        
        防止Agent做出不可能的交易：
        - sell: 需要有多头持仓
        - cover: 需要有空头持仓
        - buy/short: 总是合理（开仓操作）
        
        Args:
            action: 交易动作 (buy/sell/short/cover/close/hold)
        
        Returns:
            bool: 决策是否合理
        """
        if action in ['buy', 'short', 'hold', 'close']:
            return True  # 开仓和持有总是合理的
        
        # 获取实时持仓
        position = self._get_position_from_ledger()
        
        # sell需要有多头持仓
        if action == 'sell':
            has_long = position.get('long') is not None
            if not has_long:
                logger.debug(f"{self.agent_id}: Daimon建议sell但无多头持仓，拒绝")
                return False
        
        # cover需要有空头持仓
        elif action == 'cover':
            has_short = position.get('short') is not None
            if not has_short:
                logger.debug(f"{self.agent_id}: Daimon建议cover但无空头持仓，拒绝")
                return False
        
        return True
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        计算未实现盈亏（v6新增）
        
        Args:
            current_price: 当前市场价格
        
        Returns:
            float: 未实现盈亏金额（美元）
        """
        if not hasattr(self, 'account') or not self.account:
            return 0.0
        
        ledger = self.account.private_ledger
        unrealized_pnl = 0.0
        
        # 多头未实现盈亏
        if ledger.long_position and ledger.long_position.amount > 0:
            unrealized_pnl += (current_price - ledger.long_position.entry_price) * ledger.long_position.amount
        
        # 空头未实现盈亏
        if ledger.short_position and ledger.short_position.amount > 0:
            unrealized_pnl += (ledger.short_position.entry_price - current_price) * ledger.short_position.amount
        
        return unrealized_pnl

    def _get_position_from_ledger(self) -> Dict:
        """
        从账簿系统获取实时持仓状态
        
        ⚠️ 这是唯一可信的持仓来源！
        不再使用 self.current_position (已废弃)
        
        Returns:
            Dict: {
                'long': {'amount': float, 'price': float} or None,
                'short': {'amount': float, 'price': float} or None,
                'has_position': bool
            }
        """
        # 如果没有账簿系统，返回空持仓
        if not hasattr(self, 'account') or not self.account:
            return {
                'long': None,
                'short': None,
                'has_position': False
            }
        
        ledger = self.account.private_ledger
        
        # 获取多头持仓
        long_pos = None
        if ledger.long_position and ledger.long_position.amount > 0:
            long_pos = {
                'amount': ledger.long_position.amount,
                'price': ledger.long_position.entry_price,
                'side': 'long'
            }
        
        # 获取空头持仓
        short_pos = None
        if ledger.short_position and ledger.short_position.amount > 0:
            short_pos = {
                'amount': ledger.short_position.amount,
                'price': ledger.short_position.entry_price,
                'side': 'short'
            }
        
        return {
            'long': long_pos,
            'short': short_pos,
            'has_position': long_pos is not None or short_pos is not None
        }
    
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
        # 获取实时持仓（新格式：双向持仓）
        real_position = self._get_position_from_ledger()
        
        # 转换为Daimon兼容格式（旧格式：单一持仓）
        position_for_daimon = self._convert_position_for_daimon(real_position)
        
        return {
            # 市场数据
            'market_data': market_data,
            'bulletins': bulletins,
            
            # Agent状态
            'capital': self.current_capital,
            'capital_ratio': self.current_capital / self.initial_capital,
            'position': position_for_daimon,  # ✅ Daimon兼容格式
            
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
        
        # ✅ 将Daimon的'close'转换成具体的平仓动作
        if action == 'close':
            position = self._get_position_from_ledger()
            if position.get('long') is not None:
                action = 'sell'  # 平多头
            elif position.get('short') is not None:
                action = 'cover'  # 平空头
            else:
                # 无持仓，忽略close请求
                return None
        
        # 计算仓位大小（基于genome和confidence）
        # ✨ V6修复：提高默认仓位到80%（原来10%太保守！）
        max_position_pct = self.genome.active_params.get('max_position_pct', 0.8)
        position_size = self.current_capital * max_position_pct * guidance.confidence
        amount = position_size / current_price if current_price > 0 else 0
        
        return {
            'agent_id': self.agent_id,
            'action': action,
            'amount': amount,
            'confidence': guidance.confidence,
            'reasoning': guidance.reasoning,
            'strategy': self.current_strategy_name,
            'leverage': guidance.leverage,  # ✨ 从Daimon决策中获取杠杆
        }
    
    # ==================== 状态更新 ====================
    
    def _update_emotional_state(self):
        """AlphaZero式：已移除情绪系统"""
        pass  # 纯理性Agent不需要情绪更新
    
    def _get_recent_pnl(self, last_n: int = 5) -> float:
        """获取最近N笔交易的平均盈亏率"""
        if len(self.capital_history) < 2:
            return 0.0
        
        recent = self.capital_history[-last_n:]
        if len(recent) < 2:
            return 0.0
        
        pnl_pct = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
        return pnl_pct
    
    # AlphaZero式：移除学习与冥思
    # 理由：
    # 1. 过度设计，增加复杂度
    # 2. AlphaZero没有"冥思"、"顿悟"等心理活动
    # 3. 学习应该通过进化实现，不需要个体学习
    #
    # def meditate(self, recent_trades: List[Dict]):
    #     """已移除"""
    #     pass
    #
    # def try_epiphany(self) -> bool:
    #     """已移除"""
    #     return False
    
    # ==================== 生命周期 ====================
    
    def age_one_day(self):
        """老化一天"""
        self.days_alive += 1
        
        # 状态转换
        if self.days_alive > 30:
            self.state = AgentState.MATURE
        elif self.days_alive > 7:
            self.state = AgentState.ACTIVE
    
    # AlphaZero式：移除自杀机制
    # 理由：
    # 1. Agent不应该主动自杀，应该由EvolutionManager强制淘汰
    # 2. 违背"死亡有价值"的理念
    # 3. AlphaZero的棋子不会"自杀"，只会被判定输赢
    #
    # def should_commit_suicide(self) -> bool:
    #     """已移除"""
    #     return False
    #
    # def commit_suicide(self):
    #     """已移除"""
    #     pass
    
    # ==================== 统计更新（v5.2新增）====================
    
    def update_cycle_statistics(self, has_position: bool):
        """
        更新每周期的统计数据（v5.2新增）
        
        Args:
            has_position: 本周期是否有持仓
        """
        self.cycles_survived += 1
        
        if has_position:
            self.cycles_with_position += 1
        
        # 更新最高资金
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # 计算回撤
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def get_avg_pnl(self) -> float:
        """计算平均盈亏"""
        if len(self.pnl_history) == 0:
            return 0.0
        return sum(self.pnl_history) / len(self.pnl_history)
    
    def get_pnl_std(self) -> float:
        """计算盈亏标准差"""
        if len(self.pnl_history) < 2:
            return 0.0
        import numpy as np
        return float(np.std(self.pnl_history))
    
    def get_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        avg_pnl = self.get_avg_pnl()
        pnl_std = self.get_pnl_std()
        if pnl_std == 0:
            return 0.0
        return avg_pnl / pnl_std
    
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
            # AlphaZero式：移除emotion字段
            'strategy_params': self.strategy_params.to_dict() if hasattr(self, 'strategy_params') else {},
        }
    
    @classmethod
    def create_genesis(cls, agent_id: str, initial_capital: float, family_id: int = 0, num_families: int = 50, 
                      full_genome_unlock: bool = False) -> 'AgentV5':
        """
        创建创世Agent - AlphaZero式极简版
        
        Args:
            agent_id: Agent ID
            initial_capital: 初始资金
            family_id: 家族ID
            num_families: 家族总数
            full_genome_unlock: 是否解锁所有50个基因参数（激进模式）
        
        Returns:
            AgentV5: 创世Agent
        """
        lineage = LineageVector.create_genesis(family_id=family_id, num_families=num_families)
        lineage.family_id = family_id  # 显式记录家族ID，供多样性/移民使用
        genome = GenomeVector.create_genesis(full_unlock=full_genome_unlock)
        strategy_params = StrategyParams.create_genesis()  # AlphaZero式
        
        return cls(
            agent_id=agent_id,
            initial_capital=initial_capital,
            lineage=lineage,
            genome=genome,
            strategy_params=strategy_params,  # 直接使用strategy_params
            generation=0,
        )

