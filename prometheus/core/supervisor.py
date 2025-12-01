"""
监督者 (Supervisor) - Prometheus v4.0
系统的观察者和评估者，负责监控 Agent 和施加环境压力
v4.0: 集成奖章制度 + 市场分析功能（整合MarketAnalyzer）
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import numpy as np
import pandas as pd

from .medal_system import MedalSystem
from .indicator_calculator import IndicatorCalculator, TechnicalIndicators
from .market_state_analyzer import MarketStateAnalyzer, MarketState

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
    1. 市场分析（整合MarketAnalyzer）⭐
       - 计算技术指标
       - 分析市场状态
       - 发布市场公告
    2. Agent监控
       - 健康检查
       - 权限管理
       - 奖章颁发
       - 英灵殿审核
    3. 环境分析
       - 环境压力计算
       - 风险警告
       - 系统公告发布
    4. 预警机制
    """
    
    def __init__(self, 
                 bulletin_board=None,
                 valhalla=None,
                 trading_permission_system=None,
                 suicide_threshold: float = 0.8,
                 last_stand_threshold: float = 0.6,
                 indicator_config: Optional[Dict] = None):
        """
        初始化监督者
        
        Args:
            bulletin_board: 公告板系统
            valhalla: 英灵殿系统
            trading_permission_system: 交易权限系统
            suicide_threshold: 自杀触发阈值 (0-1)
            last_stand_threshold: 拼死一搏触发阈值 (0-1)
            indicator_config: 技术指标配置
        """
        self.bulletin_board = bulletin_board
        self.valhalla = valhalla
        self.trading_permission_system = trading_permission_system
        
        self.suicide_threshold = suicide_threshold
        self.last_stand_threshold = last_stand_threshold
        
        # 市场分析模块（整合）⭐
        self.indicator_calculator = IndicatorCalculator(indicator_config)
        self.market_state_analyzer = MarketStateAnalyzer()
        
        # 当前市场数据
        self.current_indicators: Optional[TechnicalIndicators] = None
        self.current_market_state: Optional[MarketState] = None
        self.environment_pressure: float = 0.0
        
        # Agent监控数据
        self.agent_reports: Dict[str, List[AgentHealthReport]] = {}
        self.population_statistics: List[Dict] = []
        self.agents: List[Any] = []  # Agent列表
        
        # 奖章系统
        self.medal_system = MedalSystem()
        
        # 死亡历史（用于环境压力计算）
        self.death_history: List[Dict] = []
        
        logger.info("监督者已初始化（完整版：市场分析 + Agent监控 + 风险管理）")
    
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
        
        # 评估并颁发奖章
        newly_awarded = self.medal_system.evaluate_and_award(agent_data)
        if newly_awarded:
            logger.info(f"🏅 Agent {agent_data['agent_id']} 获得 {len(newly_awarded)} 个新奖章")
        
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
    
    # ========== 市场分析模块（新增）==========
    
    def analyze_market_and_publish(self, market_data: pd.DataFrame):
        """
        分析市场并发布到公告板
        
        整合原MarketAnalyzer的功能
        
        Args:
            market_data: 市场数据（OHLCV格式）
        """
        try:
            # 1. 计算技术指标（一次性）
            self.current_indicators = self.indicator_calculator.calculate_all(market_data)
            
            # 2. 分析市场状态
            self.current_market_state = self.market_state_analyzer.analyze(self.current_indicators)
            
            # 3. 发布到公告板
            if self.bulletin_board:
                self.bulletin_board.post(
                    tier='market',
                    title='市场技术指标',
                    content={
                        'type': 'MARKET_INDICATORS',
                        'indicators': {
                            'trend': self.current_indicators.trend,
                            'momentum': self.current_indicators.momentum,
                            'volatility': self.current_indicators.volatility,
                            'volume': self.current_indicators.volume,
                            'price': self.current_indicators.price
                        },
                        'market_state': {
                            'trend': self.current_market_state.trend.value,
                            'trend_strength': self.current_market_state.trend_strength,
                            'momentum': self.current_market_state.momentum.value,
                            'momentum_score': self.current_market_state.momentum_score,
                            'volatility': self.current_market_state.volatility.value,
                            'volatility_score': self.current_market_state.volatility_score,
                            'market_difficulty': self.current_market_state.market_difficulty,
                            'opportunity_score': self.current_market_state.opportunity_score,
                            'recommendation': self.current_market_state.recommendation
                        }
                    },
                    publisher='Supervisor',
                    priority='normal'
                )
                logger.info(f"📊 市场分析已发布: {self.current_market_state.trend.value}")
            
        except Exception as e:
            logger.error(f"市场分析失败: {e}")
            raise
    
    def calculate_environment_pressure_comprehensive(self) -> float:
        """
        计算环境压力（综合版）
        
        现在可以同时使用：
        - 市场技术指标（market difficulty）
        - Agent群体表现
        - 死亡率
        
        Returns:
            float: 环境压力 (0-1)
        """
        # 1. 市场难度因素
        if self.current_market_state:
            market_difficulty = self.current_market_state.market_difficulty
        else:
            market_difficulty = 0.5
        
        # 2. Agent群体表现
        if self.agents:
            avg_pnl = np.mean([getattr(agent, 'total_pnl', 0) for agent in self.agents])
            performance_factor = max(0, -avg_pnl / 10000)  # 亏损越多压力越大
        else:
            performance_factor = 0.5
        
        # 3. 死亡率因素
        recent_deaths = len([d for d in self.death_history[-24:] if d])  # 最近24小时
        total_agents = len(self.agents) if self.agents else 1
        death_rate = min(recent_deaths / max(total_agents, 1), 1.0)
        
        # 综合计算
        pressure = (
            market_difficulty * 0.5 +
            performance_factor * 0.3 +
            death_rate * 0.2
        )
        
        self.environment_pressure = min(max(pressure, 0), 1)
        return self.environment_pressure
    
    def publish_environment_info(self):
        """发布环境信息到公告板"""
        if not self.bulletin_board:
            return
        
        # 计算环境压力
        pressure = self.calculate_environment_pressure_comprehensive()
        
        # 群体统计
        if self.agents:
            total_agents = len(self.agents)
            avg_capital = np.mean([getattr(agent, 'capital', 0) for agent in self.agents])
        else:
            total_agents = 0
            avg_capital = 0
        
        # 发布
        self.bulletin_board.post(
            tier='system',
            title='环境状态报告',
            content={
                'type': 'ENVIRONMENT',
                'pressure': pressure,
                'pressure_level': self._get_pressure_level(pressure),
                'total_agents': total_agents,
                'avg_capital': avg_capital,
                'recent_deaths': len(self.death_history[-24:]),
                'recommendation': self._get_environment_recommendation(pressure)
            },
            publisher='Supervisor',
            priority='high' if pressure > 0.7 else 'normal'
        )
        
        logger.info(f"🌍 环境状态已发布: 压力={pressure:.2f}")
    
    def _get_pressure_level(self, pressure: float) -> str:
        """获取压力等级描述"""
        if pressure > 0.8:
            return "极高压力"
        elif pressure > 0.6:
            return "高压力"
        elif pressure > 0.4:
            return "中等压力"
        elif pressure > 0.2:
            return "低压力"
        else:
            return "极低压力"
    
    def _get_environment_recommendation(self, pressure: float) -> str:
        """获取环境建议"""
        if pressure > 0.8:
            return "⚠️ 极端环境，建议降低仓位，严控风险"
        elif pressure > 0.6:
            return "⚠️ 高压环境，建议谨慎交易"
        elif pressure > 0.4:
            return "正常环境，可正常交易"
        else:
            return "良好环境，可适当增加仓位"
    
    # ========== 综合监控（一次性完成所有工作）==========
    
    def comprehensive_monitoring(self, market_data: pd.DataFrame):
        """
        综合监控（核心方法）
        
        一次性完成：
        1. 市场分析 → 发布市场公告
        2. Agent监控 → 更新权限/奖章
        3. 环境分析 → 发布系统公告
        4. 风险警告（如需要）
        
        Args:
            market_data: 市场数据
        """
        logger.info("=" * 50)
        logger.info("开始综合监控...")
        
        # 1. 市场分析
        self.analyze_market_and_publish(market_data)
        
        # 2. Agent监控
        self._monitor_and_update_agents()
        
        # 3. 环境分析
        self.publish_environment_info()
        
        # 4. 风险警告
        if self.environment_pressure > 0.7:
            self._issue_risk_warning()
        
        # 5. 英灵殿审核
        self._review_for_valhalla()
        
        logger.info("综合监控完成")
        logger.info("=" * 50)
    
    def _monitor_and_update_agents(self):
        """监控并更新所有Agent"""
        for agent in self.agents:
            # 健康检查
            agent_data = {
                'agent_id': getattr(agent, 'agent_id', 'unknown'),
                'current_capital': getattr(agent, 'capital', 0),
                'initial_capital': getattr(agent, 'initial_capital', 10000),
                'total_pnl': getattr(agent, 'total_pnl', 0),
                'win_rate': getattr(agent, 'win_rate', 0),
                'trade_count': getattr(agent, 'trade_count', 0),
                'consecutive_losses': getattr(agent, 'consecutive_losses', 0),
                'consecutive_wins': getattr(agent, 'consecutive_wins', 0),
                'days_alive': getattr(agent, 'days_alive', 0),
                'fitness_score': getattr(agent, 'fitness_score', 0.5),
                'market_adaptation': getattr(agent, 'market_adaptation', 0.5),
                'recent_trend': getattr(agent, 'recent_trend', 0),
                'market_opportunity': self.current_market_state.opportunity_score if self.current_market_state else 0.5,
                'survival_will': getattr(agent, 'survival_will', 0.7),
                'personality_aggression': getattr(agent.personality, 'risk_appetite', 0.5) if hasattr(agent, 'personality') else 0.5
            }
            
            health_report = self.evaluate_agent(agent_data, self.environment_pressure)
            
            # 权限更新（如果有交易权限系统）
            if self.trading_permission_system and hasattr(agent, 'permission_level'):
                self._update_agent_permission(agent, health_report)
            
            # 奖章评估（已在evaluate_agent中完成）
    
    def _update_agent_permission(self, agent, health_report):
        """更新Agent交易权限"""
        # 根据表现晋升或降级
        if health_report.health_status == 'healthy' and health_report.win_rate > 0.6:
            # 可能晋升
            pass  # 由TradingPermissionSystem处理
        elif health_report.health_status in ['critical', 'dying']:
            # 可能降级
            pass
    
    def _issue_risk_warning(self):
        """发布风险警告"""
        if not self.bulletin_board:
            return
        
        self.bulletin_board.post(
            tier='system',
            title='⚠️ 系统风险警告',
            content={
                'type': 'RISK_WARNING',
                'level': 'HIGH',
                'pressure': self.environment_pressure,
                'message': f"环境压力过高（{self.environment_pressure:.2f}），请注意风险控制",
                'recommendations': [
                    "降低仓位至50%以下",
                    "收紧止损位",
                    "避免高杠杆交易",
                    "优先保护本金"
                ]
            },
            publisher='Supervisor',
            priority='urgent'
        )
        
        logger.warning(f"⚠️ 风险警告已发布: 环境压力={self.environment_pressure:.2f}")
    
    def _review_for_valhalla(self):
        """审核Agent是否符合英灵殿入选条件"""
        if not self.valhalla:
            return
        
        for agent in self.agents:
            # 获取奖章数量
            agent_id = getattr(agent, 'agent_id', None)
            if not agent_id:
                continue
            
            medals = self.medal_system.get_agent_medals(agent_id)
            medal_count = len(medals)
            
            # 入选条件：奖章数量 >= 5
            if medal_count >= 5 and hasattr(agent, 'prepare_for_breeding'):
                breeding_data = agent.prepare_for_breeding()
                
                # 检查是否已入选
                if not self.valhalla.is_inducted(agent_id):
                    logger.info(f"🏛️ Agent {agent_id} 符合英灵殿条件（{medal_count}枚奖章）")
                    # 可以在这里触发入选，或等待Mastermind决策
    
    def register_agent(self, agent):
        """注册Agent到监督系统"""
        if agent not in self.agents:
            self.agents.append(agent)
            logger.info(f"Agent {getattr(agent, 'agent_id', 'unknown')} 已注册到监督系统")
    
    def unregister_agent(self, agent):
        """注销Agent（死亡时）"""
        if agent in self.agents:
            self.agents.remove(agent)
            
            # 记录死亡
            self.death_history.append({
                'agent_id': getattr(agent, 'agent_id', 'unknown'),
                'timestamp': datetime.now(),
                'capital': getattr(agent, 'capital', 0),
                'total_pnl': getattr(agent, 'total_pnl', 0)
            })
            
            logger.info(f"Agent {getattr(agent, 'agent_id', 'unknown')} 已从监督系统注销（死亡）")

