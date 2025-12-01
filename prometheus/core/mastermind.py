"""
主脑 (Mastermind) - Prometheus v4.0
系统的最高决策层，负责战略规划和全局调控
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

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
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化主脑
        
        Args:
            initial_capital: 系统初始总资金
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.strategy = GlobalStrategy()
        self.market_regime = MarketRegime.UNKNOWN
        
        # 决策历史
        self.decision_history: List[Dict] = []
        
        logger.info(f"主脑已初始化，总资金: {initial_capital}")
    
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
                               system_metrics: Dict) -> Dict:
        """
        做出战略决策（主脑的主要决策入口）
        
        Args:
            market_data: 市场数据
            agent_statistics: Agent 统计数据
            system_metrics: 系统指标
            
        Returns:
            Dict: 决策结果
        """
        # 1. 分析市场
        self.market_regime = self.analyze_market_regime(market_data)
        
        # 2. 调整全局策略
        strategy = self.adjust_global_strategy(agent_statistics, self.market_regime)
        
        # 3. 评估系统健康
        health = self.evaluate_system_health(system_metrics)
        
        # 4. 做出决策
        decision = {
            'timestamp': market_data.get('timestamp'),
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
        
        logger.info(f"战略决策完成: {decision}")
        return decision
    
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

