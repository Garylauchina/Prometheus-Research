"""
主脑 (Mastermind) - Prometheus v4.0
系统的最高决策层，负责战略规划和全局调控
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from .llm_oracle import LLMOracle, HumanOracle

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态枚举"""
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    RANGING = "ranging"     # 震荡
    VOLATILE = "volatile"   # 高波动
    UNKNOWN = "unknown"     # 未知


@dataclass
class GlobalStrategy:
    """全局策略配置"""
    # 资金管理
    total_capital_utilization: float = 0.7  # 总资金利用率
    max_agents: int = 100                    # 最大 Agent 数量
    min_agents: int = 10                     # 最小 Agent 数量
    capital_per_agent: float = 1000.0       # 每个 Agent 初始资金
    
    # 风险控制
    max_system_drawdown: float = 0.3        # 系统最大回撤
    max_position_concentration: float = 0.2  # 单一仓位最大占比
    risk_level: int = 3                     # 风险等级 1-5
    
    # 进化参数
    mutation_rate: float = 0.1              # 基因突变率
    selection_pressure: float = 0.5         # 淘汰压力
    diversity_target: float = 0.7           # 多样性目标
    
    # 环境压力
    environmental_pressure: float = 1.0      # 环境压力系数


class Mastermind:
    """
    主脑 - 系统的最高决策层
    
    职责：
    1. 宏观市场分析
    2. 资源分配策略
    3. 进化方向引导
    4. 生态平衡控制
    
    决策模式：
    - LLM先知模式：使用AI辅助决策
    - 人工干预模式：人类操作员直接决策
    - 混合模式：LLM提供建议，人工最终决策
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 decision_mode: str = "llm",
                 llm_model: Optional[str] = None):
        """
        初始化主脑
        
        Args:
            initial_capital: 系统初始总资金
            decision_mode: 决策模式 ("llm"[默认], "human", "hybrid")
            llm_model: LLM模型名称（用于LLM模式）
            
        Note:
            v4.0 以LLM先知为主要决策模式，人工基本不参与
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.strategy = GlobalStrategy()
        self.market_regime = MarketRegime.UNKNOWN
        self.decision_mode = decision_mode
        
        # 决策历史
        self.decision_history: List[Dict] = []
        
        # 初始化决策系统
        self.llm_oracle = LLMOracle(model=llm_model or "gpt-4") if decision_mode in ["llm", "hybrid"] else None
        self.human_oracle = HumanOracle() if decision_mode in ["human", "hybrid"] else None
        
        logger.info(f"主脑已初始化，总资金: {initial_capital}, 决策模式: {decision_mode}")
    
    def analyze_market_regime(self, market_data: Dict) -> MarketRegime:
        """
        分析当前市场状态
        
        Args:
            market_data: 市场数据
            
        Returns:
            MarketRegime: 市场状态
        """
        # TODO: 实现市场状态分析逻辑
        # 可以使用：
        # - 趋势指标 (MA, EMA)
        # - 波动率指标 (ATR, Bollinger Bands)
        # - 成交量分析
        # - 多时间周期确认
        
        logger.info("正在分析市场状态...")
        return MarketRegime.UNKNOWN
    
    def adjust_global_strategy(self, 
                               agent_statistics: Dict,
                               market_regime: MarketRegime) -> GlobalStrategy:
        """
        根据市场状态和 Agent 表现调整全局策略
        
        Args:
            agent_statistics: Agent 群体统计数据
            market_regime: 当前市场状态
            
        Returns:
            GlobalStrategy: 更新后的全局策略
        """
        # 根据市场状态调整策略
        if market_regime == MarketRegime.BULL:
            # 牛市：提高资金利用率，降低淘汰压力
            self.strategy.total_capital_utilization = 0.8
            self.strategy.selection_pressure = 0.3
            self.strategy.risk_level = 4
            
        elif market_regime == MarketRegime.BEAR:
            # 熊市：降低资金利用率，提高淘汰压力
            self.strategy.total_capital_utilization = 0.5
            self.strategy.selection_pressure = 0.7
            self.strategy.risk_level = 2
            
        elif market_regime == MarketRegime.VOLATILE:
            # 高波动：中等资金利用率，高淘汰压力
            self.strategy.total_capital_utilization = 0.6
            self.strategy.selection_pressure = 0.6
            self.strategy.risk_level = 3
        
        # 根据 Agent 表现调整
        avg_performance = agent_statistics.get('avg_performance', 0)
        if avg_performance < -0.2:  # 整体表现差
            self.strategy.environmental_pressure *= 1.2  # 增加压力
            self.strategy.mutation_rate *= 1.3  # 增加变异
        elif avg_performance > 0.3:  # 整体表现好
            self.strategy.environmental_pressure *= 0.9  # 减少压力
            self.strategy.mutation_rate *= 0.9  # 减少变异
        
        logger.info(f"全局策略已调整: {self.strategy}")
        return self.strategy
    
    def allocate_capital(self, agent_count: int) -> Dict[str, float]:
        """
        分配资金给 Agent 群体
        
        Args:
            agent_count: Agent 数量
            
        Returns:
            Dict: 资金分配方案
        """
        available_capital = self.current_capital * self.strategy.total_capital_utilization
        capital_per_agent = available_capital / max(agent_count, self.strategy.min_agents)
        
        allocation = {
            'total_available': available_capital,
            'per_agent': capital_per_agent,
            'reserved': self.current_capital - available_capital
        }
        
        logger.info(f"资金分配方案: {allocation}")
        return allocation
    
    def should_spawn_new_agent(self, current_agent_count: int) -> bool:
        """
        决定是否应该创建新的 Agent
        
        Args:
            current_agent_count: 当前 Agent 数量
            
        Returns:
            bool: 是否创建新 Agent
        """
        if current_agent_count < self.strategy.min_agents:
            return True
        
        if current_agent_count >= self.strategy.max_agents:
            return False
        
        # 根据系统表现决定是否扩充
        # TODO: 可以根据资金池盈利情况、Agent 平均表现等决定
        return False
    
    def evaluate_system_health(self, system_metrics: Dict) -> Dict:
        """
        评估系统整体健康状况
        
        Args:
            system_metrics: 系统指标
            
        Returns:
            Dict: 健康评估报告
        """
        current_drawdown = system_metrics.get('drawdown', 0)
        agent_diversity = system_metrics.get('diversity', 1.0)
        
        health_report = {
            'overall_health': 'healthy',
            'warnings': [],
            'critical_issues': []
        }
        
        # 检查回撤
        if current_drawdown > self.strategy.max_system_drawdown:
            health_report['critical_issues'].append(
                f"系统回撤 {current_drawdown:.2%} 超过限制 {self.strategy.max_system_drawdown:.2%}"
            )
            health_report['overall_health'] = 'critical'
        
        # 检查多样性
        if agent_diversity < self.strategy.diversity_target:
            health_report['warnings'].append(
                f"Agent 多样性 {agent_diversity:.2f} 低于目标 {self.strategy.diversity_target:.2f}"
            )
        
        logger.info(f"系统健康评估: {health_report['overall_health']}")
        return health_report
    
    def make_strategic_decision(self,
                               market_data: Dict,
                               agent_statistics: Dict,
                               system_metrics: Dict,
                               human_override: Optional[Dict] = None) -> Dict:
        """
        做出战略决策（主脑的主要决策入口）
        
        根据决策模式选择决策方式：
        - llm: 完全使用LLM决策
        - human: 等待人工输入
        - hybrid: LLM提供建议，人工可以覆盖
        
        Args:
            market_data: 市场数据
            agent_statistics: Agent 统计数据
            system_metrics: 系统指标
            human_override: 人工覆盖参数（可选）
            
        Returns:
            Dict: 决策结果
        """
        # 1. 基础分析
        self.market_regime = self.analyze_market_regime(market_data)
        health = self.evaluate_system_health(system_metrics)
        
        # 2. 根据决策模式获取策略建议
        if self.decision_mode == "llm":
            # 纯LLM决策
            llm_analysis = self.llm_oracle.analyze_market_situation(
                market_data, agent_statistics, system_metrics
            )
            strategy = self._apply_llm_suggestions(llm_analysis)
            decision_source = "llm"
            
        elif self.decision_mode == "human":
            # 纯人工决策
            if human_override:
                strategy = self._apply_human_adjustments(human_override)
                decision_source = "human"
            else:
                # 使用默认策略
                strategy = self.adjust_global_strategy(agent_statistics, self.market_regime)
                decision_source = "default"
                
        else:  # hybrid
            # 混合决策：LLM提供建议，人工可覆盖
            llm_analysis = self.llm_oracle.analyze_market_situation(
                market_data, agent_statistics, system_metrics
            )
            
            if human_override:
                # 人工覆盖LLM建议
                strategy = self._apply_human_adjustments(human_override)
                decision_source = "human_override"
                logger.info("人工覆盖LLM建议")
            else:
                # 采用LLM建议
                strategy = self._apply_llm_suggestions(llm_analysis)
                decision_source = "llm_suggestion"
        
        # 3. 构建决策结果
        decision = {
            'timestamp': market_data.get('timestamp'),
            'decision_mode': self.decision_mode,
            'decision_source': decision_source,
            'market_regime': self.market_regime.value,
            'strategy': strategy,
            'health': health,
            'actions': []
        }
        
        # 根据健康状况决定行动
        if health['overall_health'] == 'critical':
            decision['actions'].append('REDUCE_RISK')
            decision['actions'].append('INCREASE_SELECTION_PRESSURE')
        
        # 记录决策
        self.decision_history.append(decision)
        
        logger.info(f"战略决策完成 [{decision_source}]: {decision}")
        return decision
    
    def _apply_llm_suggestions(self, llm_analysis: Dict) -> GlobalStrategy:
        """
        应用LLM的策略建议
        
        Args:
            llm_analysis: LLM分析结果
            
        Returns:
            GlobalStrategy: 更新后的策略
        """
        adjustments = llm_analysis.get('strategy_adjustments', {})
        
        self.strategy.total_capital_utilization = adjustments.get('capital_utilization', 0.7)
        self.strategy.risk_level = adjustments.get('risk_level', 3)
        self.strategy.selection_pressure = adjustments.get('selection_pressure', 0.5)
        self.strategy.environmental_pressure = adjustments.get('environmental_pressure', 1.0)
        
        logger.info(f"应用LLM建议: {adjustments}")
        return self.strategy
    
    def _apply_human_adjustments(self, adjustments: Dict) -> GlobalStrategy:
        """
        应用人工调整
        
        Args:
            adjustments: 人工调整参数
            
        Returns:
            GlobalStrategy: 更新后的策略
        """
        if 'capital_utilization' in adjustments:
            self.strategy.total_capital_utilization = adjustments['capital_utilization']
        if 'risk_level' in adjustments:
            self.strategy.risk_level = adjustments['risk_level']
        if 'selection_pressure' in adjustments:
            self.strategy.selection_pressure = adjustments['selection_pressure']
        if 'environmental_pressure' in adjustments:
            self.strategy.environmental_pressure = adjustments['environmental_pressure']
        if 'max_agents' in adjustments:
            self.strategy.max_agents = adjustments['max_agents']
        if 'min_agents' in adjustments:
            self.strategy.min_agents = adjustments['min_agents']
        
        logger.info(f"应用人工调整: {adjustments}")
        return self.strategy
    
    def get_statistics(self) -> Dict:
        """
        获取主脑统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'market_regime': self.market_regime.value,
            'strategy': self.strategy.__dict__,
            'decision_count': len(self.decision_history)
        }

