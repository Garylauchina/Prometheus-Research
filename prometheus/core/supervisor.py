"""
监督者 (Supervisor) - Prometheus v4.0
系统的观察者和评估者，负责监控 Agent 和施加环境压力
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthReport:
    """Agent 健康报告"""
    agent_id: str
    timestamp: datetime
    
    # 财务指标
    current_capital: float
    initial_capital: float
    capital_ratio: float  # 当前资金/初始资金
    total_pnl: float
    win_rate: float
    
    # 行为指标
    trade_count: int
    consecutive_losses: int
    consecutive_wins: int
    days_alive: int
    
    # 适应度指标
    fitness_score: float
    market_adaptation: float
    
    # 情绪指标
    despair_index: float      # 绝望指数
    endangered_index: float   # 濒危指数
    
    # 状态判定
    health_status: str  # 'healthy', 'warning', 'critical', 'dying'
    recommended_action: str  # 'none', 'monitor', 'last_stand', 'suicide'


class Supervisor:
    """
    监督者 - 系统的观察者和评估者
    
    职责：
    1. 监控 Agent 状态
    2. 绩效评估
    3. 环境压力施加
    4. 数据收集与分析
    5. 预警机制
    """
    
    def __init__(self, 
                 suicide_threshold: float = 0.8,
                 last_stand_threshold: float = 0.6):
        """
        初始化监督者
        
        Args:
            suicide_threshold: 自杀触发阈值 (0-1)
            last_stand_threshold: 拼死一搏触发阈值 (0-1)
        """
        self.suicide_threshold = suicide_threshold
        self.last_stand_threshold = last_stand_threshold
        
        # 监控数据
        self.agent_reports: Dict[str, List[AgentHealthReport]] = {}
        self.population_statistics: List[Dict] = []
        
        logger.info("监督者已初始化")
    
    def calculate_despair_index(self,
                                consecutive_losses: int,
                                capital_ratio: float,
                                fitness_score: float,
                                days_alive: int,
                                environmental_pressure: float) -> float:
        """
        计算 Agent 的绝望指数
        
        绝望指数综合考虑：
        - 连续亏损情况
        - 资金损失程度
        - 市场适应能力
        - 生存时长（太短或太长都可能增加绝望）
        - 环境压力
        
        Args:
            consecutive_losses: 连续亏损次数
            capital_ratio: 当前资金/初始资金
            fitness_score: 适应度得分 (0-1)
            days_alive: 存活天数
            environmental_pressure: 环境压力 (0-2)
            
        Returns:
            float: 绝望指数 (0-1)，越高越绝望
        """
        # 1. 连续亏损因子 (0-1)
        loss_factor = min(consecutive_losses / 15.0, 1.0)  # 15次连亏 = 1.0
        
        # 2. 资金损失因子 (0-1)
        capital_loss = max(0, 1 - capital_ratio)  # 亏损越多越高
        capital_factor = min(capital_loss * 2, 1.0)  # 亏损50% = 1.0
        
        # 3. 适应度因子 (0-1)
        fitness_factor = 1 - fitness_score  # 适应度越低越高
        
        # 4. 生存时长因子 (0-1)
        # 太短（还没适应）或太长（长期表现差）都增加绝望
        if days_alive < 7:
            time_factor = 0.3  # 新生 Agent 不容易绝望
        elif days_alive < 30:
            time_factor = 0.5  # 成长期
        else:
            time_factor = 0.7  # 长期表现差增加绝望
        
        # 5. 环境压力因子
        pressure_factor = environmental_pressure / 2.0  # 归一化到 0-1
        
        # 综合计算（加权平均）
        despair_index = (
            loss_factor * 0.3 +
            capital_factor * 0.35 +
            fitness_factor * 0.2 +
            time_factor * 0.05 +
            pressure_factor * 0.1
        )
        
        return min(despair_index, 1.0)
    
    def calculate_endangered_index(self,
                                   capital_ratio: float,
                                   recent_trend: float,
                                   market_opportunity: float,
                                   survival_will: float,
                                   personality_aggression: float) -> float:
        """
        计算 Agent 的濒危指数
        
        濒危但尚未绝望，评估是否适合拼死一搏
        
        Args:
            capital_ratio: 当前资金/初始资金
            recent_trend: 近期趋势 (-1 to 1)
            market_opportunity: 市场机会评分 (0-1)
            survival_will: 生存意志 (0-1)
            personality_aggression: 性格激进度 (0-1)
            
        Returns:
            float: 濒危指数 (0-1)，越高越适合拼搏
        """
        # 1. 资金危机因子
        if capital_ratio > 0.5:
            capital_crisis = 0.0  # 资金充足，不需要拼搏
        elif capital_ratio > 0.3:
            capital_crisis = (0.5 - capital_ratio) / 0.2  # 0.3-0.5 线性增长
        else:
            capital_crisis = 1.0  # 资金严重不足
        
        # 2. 趋势因子（下降趋势增加拼搏意愿）
        trend_factor = max(0, -recent_trend)  # 只有下降趋势才触发
        
        # 3. 机会因子（有好机会才值得拼搏）
        opportunity_factor = market_opportunity
        
        # 4. 意志因子
        will_factor = survival_will
        
        # 5. 性格因子
        personality_factor = personality_aggression
        
        # 综合计算
        # 只有在资金危机 + 有机会 + 有意志的情况下才触发
        endangered_index = (
            capital_crisis * 0.4 +
            opportunity_factor * 0.3 +
            will_factor * 0.15 +
            personality_factor * 0.15
        ) * (1 + trend_factor * 0.2)  # 趋势作为增幅
        
        return min(endangered_index, 1.0)
    
    def evaluate_agent(self, agent_data: Dict, environmental_pressure: float) -> AgentHealthReport:
        """
        评估单个 Agent 的健康状况
        
        Args:
            agent_data: Agent 数据
            environmental_pressure: 当前环境压力
            
        Returns:
            AgentHealthReport: 健康报告
        """
        # 计算基础指标
        capital_ratio = agent_data['current_capital'] / agent_data['initial_capital']
        
        # 计算绝望指数
        despair_index = self.calculate_despair_index(
            consecutive_losses=agent_data.get('consecutive_losses', 0),
            capital_ratio=capital_ratio,
            fitness_score=agent_data.get('fitness_score', 0.5),
            days_alive=agent_data.get('days_alive', 0),
            environmental_pressure=environmental_pressure
        )
        
        # 计算濒危指数
        endangered_index = self.calculate_endangered_index(
            capital_ratio=capital_ratio,
            recent_trend=agent_data.get('recent_trend', 0),
            market_opportunity=agent_data.get('market_opportunity', 0.5),
            survival_will=agent_data.get('survival_will', 0.7),
            personality_aggression=agent_data.get('personality_aggression', 0.5)
        )
        
        # 判定健康状态
        if despair_index >= self.suicide_threshold:
            health_status = 'dying'
            recommended_action = 'suicide'
        elif endangered_index >= self.last_stand_threshold:
            health_status = 'critical'
            recommended_action = 'last_stand'
        elif capital_ratio < 0.7 or agent_data.get('consecutive_losses', 0) > 5:
            health_status = 'warning'
            recommended_action = 'monitor'
        else:
            health_status = 'healthy'
            recommended_action = 'none'
        
        # 生成报告
        report = AgentHealthReport(
            agent_id=agent_data['agent_id'],
            timestamp=datetime.now(),
            current_capital=agent_data['current_capital'],
            initial_capital=agent_data['initial_capital'],
            capital_ratio=capital_ratio,
            total_pnl=agent_data.get('total_pnl', 0),
            win_rate=agent_data.get('win_rate', 0),
            trade_count=agent_data.get('trade_count', 0),
            consecutive_losses=agent_data.get('consecutive_losses', 0),
            consecutive_wins=agent_data.get('consecutive_wins', 0),
            days_alive=agent_data.get('days_alive', 0),
            fitness_score=agent_data.get('fitness_score', 0.5),
            market_adaptation=agent_data.get('market_adaptation', 0.5),
            despair_index=despair_index,
            endangered_index=endangered_index,
            health_status=health_status,
            recommended_action=recommended_action
        )
        
        # 记录报告
        if agent_data['agent_id'] not in self.agent_reports:
            self.agent_reports[agent_data['agent_id']] = []
        self.agent_reports[agent_data['agent_id']].append(report)
        
        logger.debug(f"Agent {agent_data['agent_id']} 评估完成: {health_status}")
        return report
    
    def monitor_population(self, agents_data: List[Dict], environmental_pressure: float) -> Dict:
        """
        监控整个 Agent 群体
        
        Args:
            agents_data: 所有 Agent 的数据
            environmental_pressure: 环境压力
            
        Returns:
            Dict: 群体统计数据
        """
        if not agents_data:
            return {
                'total_agents': 0,
                'avg_performance': 0,
                'diversity': 0
            }
        
        # 评估每个 Agent
        reports = [self.evaluate_agent(agent, environmental_pressure) for agent in agents_data]
        
        # 计算群体统计
        health_counts = {
            'healthy': sum(1 for r in reports if r.health_status == 'healthy'),
            'warning': sum(1 for r in reports if r.health_status == 'warning'),
            'critical': sum(1 for r in reports if r.health_status == 'critical'),
            'dying': sum(1 for r in reports if r.health_status == 'dying')
        }
        
        avg_capital_ratio = np.mean([r.capital_ratio for r in reports])
        avg_fitness = np.mean([r.fitness_score for r in reports])
        avg_despair = np.mean([r.despair_index for r in reports])
        
        # 计算多样性（基因或策略的标准差）
        fitness_std = np.std([r.fitness_score for r in reports])
        diversity = min(fitness_std * 2, 1.0)  # 归一化到 0-1
        
        statistics = {
            'timestamp': datetime.now(),
            'total_agents': len(agents_data),
            'health_counts': health_counts,
            'avg_capital_ratio': avg_capital_ratio,
            'avg_fitness': avg_fitness,
            'avg_despair': avg_despair,
            'diversity': diversity,
            'avg_performance': avg_capital_ratio - 1.0,  # 平均盈亏
            'reports': reports
        }
        
        self.population_statistics.append(statistics)
        
        logger.info(f"群体监控完成: {len(agents_data)} 个 Agent, "
                   f"健康: {health_counts['healthy']}, "
                   f"警告: {health_counts['warning']}, "
                   f"危急: {health_counts['critical']}, "
                   f"濒死: {health_counts['dying']}")
        
        return statistics
    
    def detect_system_risks(self, population_stats: Dict) -> List[Dict]:
        """
        检测系统级风险
        
        Args:
            population_stats: 群体统计数据
            
        Returns:
            List[Dict]: 风险警报列表
        """
        alerts = []
        
        # 1. 检查 Agent 数量过低
        if population_stats['total_agents'] < 5:
            alerts.append({
                'level': 'critical',
                'type': 'population_low',
                'message': f"Agent 数量过低: {population_stats['total_agents']}"
            })
        
        # 2. 检查整体表现
        if population_stats['avg_performance'] < -0.3:
            alerts.append({
                'level': 'warning',
                'type': 'poor_performance',
                'message': f"整体表现差: {population_stats['avg_performance']:.2%}"
            })
        
        # 3. 检查多样性
        if population_stats['diversity'] < 0.3:
            alerts.append({
                'level': 'warning',
                'type': 'low_diversity',
                'message': f"策略多样性过低: {population_stats['diversity']:.2f}"
            })
        
        # 4. 检查群体健康
        health_counts = population_stats['health_counts']
        unhealthy_ratio = (health_counts['critical'] + health_counts['dying']) / max(population_stats['total_agents'], 1)
        if unhealthy_ratio > 0.5:
            alerts.append({
                'level': 'critical',
                'type': 'mass_extinction',
                'message': f"大量 Agent 濒临死亡: {unhealthy_ratio:.1%}"
            })
        
        if alerts:
            logger.warning(f"检测到 {len(alerts)} 个系统风险")
            for alert in alerts:
                logger.warning(f"  [{alert['level']}] {alert['type']}: {alert['message']}")
        
        return alerts
    
    def get_statistics(self) -> Dict:
        """
        获取监督者统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'monitored_agents': len(self.agent_reports),
            'total_evaluations': sum(len(reports) for reports in self.agent_reports.values()),
            'population_snapshots': len(self.population_statistics)
        }

