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
from .ledger_system import PublicLedger, AgentAccountSystem, Role
import time

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
        
        # ===== 双账簿系统 =====
        self.public_ledger = PublicLedger()  # 公共账簿（只有一本）
        self.agent_accounts: Dict[str, AgentAccountSystem] = {}  # Agent账户系统
        
        # ===== 运营组件（用于主循环）=====
        self.okx_trading = None  # OKX交易接口
        self.mastermind = None  # Mastermind组件
        self.config = None  # 配置
        
        logger.info("监督者已初始化（完整运营系统：市场分析 + Agent监控 + 双账簿系统）")
    
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
    
    # ========== 虚拟账户管理系统（新增）==========
    
    def initialize_virtual_accounts(self, agents: List[Any], initial_capital_per_agent: float = 10000):
        """
        初始化Agent虚拟账户系统
        
        Args:
            agents: Agent列表
            initial_capital_per_agent: 每个Agent的初始虚拟资金
        """
        for agent in agents:
            agent_id = getattr(agent, 'agent_id', 'unknown')
            
            self.agent_virtual_portfolios[agent_id] = {
                'agent_id': agent_id,
                'virtual_capital': initial_capital_per_agent,
                'initial_capital': initial_capital_per_agent,
                'virtual_positions': [],  # 虚拟持仓列表
                'virtual_trades': [],     # 虚拟交易历史
                'total_pnl': 0.0,
                'realized_pnl': 0.0,
                'unrealized_pnl': 0.0,
                'trade_count': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'personality': {
                    'aggression': getattr(agent.personality, 'aggression', 0.5) if hasattr(agent, 'personality') else 0.5,
                    'risk_tolerance': getattr(agent.personality, 'risk_tolerance', 0.5) if hasattr(agent, 'personality') else 0.5,
                    'adaptability': getattr(agent.personality, 'adaptability', 0.5) if hasattr(agent, 'personality') else 0.5
                },
                'created_at': datetime.now()
            }
        
        logger.info(f"✅ 虚拟账户系统已初始化: {len(agents)}个Agent，每个{initial_capital_per_agent} USDT")
    
    def record_virtual_trade(self, agent_id: str, trade_type: str, price: float, amount: float, confidence: float = 0.0):
        """
        记录Agent的虚拟交易
        
        Args:
            agent_id: Agent ID
            trade_type: 交易类型 ('buy' or 'sell')
            price: 交易价格
            amount: 交易数量
            confidence: 交易信心度
        """
        if agent_id not in self.agent_virtual_portfolios:
            logger.warning(f"Agent {agent_id} 未注册虚拟账户")
            return
        
        portfolio = self.agent_virtual_portfolios[agent_id]
        
        # 检查是否有持仓
        has_position = len(portfolio['virtual_positions']) > 0
        
        if trade_type == 'buy' and not has_position:
            # 虚拟开多
            portfolio['virtual_positions'].append({
                'side': 'long',
                'entry_price': price,
                'amount': amount,
                'entry_time': datetime.now(),
                'confidence': confidence
            })
            portfolio['trade_count'] += 1
            logger.debug(f"Agent {agent_id} 虚拟开多: {amount} @ ${price}")
            
        elif trade_type == 'sell' and has_position:
            # 虚拟平仓
            for pos in portfolio['virtual_positions']:
                if pos['side'] == 'long':
                    # 计算盈亏
                    pnl = (price - pos['entry_price']) * pos['amount']
                    portfolio['realized_pnl'] += pnl
                    portfolio['total_pnl'] += pnl
                    portfolio['virtual_capital'] += pnl
                    
                    if pnl > 0:
                        portfolio['win_count'] += 1
                    else:
                        portfolio['loss_count'] += 1
                    
                    # 更新胜率
                    if portfolio['trade_count'] > 0:
                        portfolio['win_rate'] = portfolio['win_count'] / portfolio['trade_count']
                    
                    # 计算持仓时间
                    holding_time = (datetime.now() - pos['entry_time']).total_seconds() / 60
                    
                    # 记录交易
                    portfolio['virtual_trades'].append({
                        'entry_price': pos['entry_price'],
                        'exit_price': price,
                        'amount': pos['amount'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (pos['entry_price'] * pos['amount'])) * 100,
                        'holding_time_minutes': holding_time,
                        'entry_confidence': pos['confidence'],
                        'entry_time': pos['entry_time'],
                        'exit_time': datetime.now()
                    })
                    
                    logger.debug(f"Agent {agent_id} 虚拟平仓: PnL=${pnl:.2f}")
            
            # 清空持仓
            portfolio['virtual_positions'] = []
    
    def calculate_unrealized_pnl(self, current_price: float):
        """
        计算所有Agent的未实现盈亏
        
        Args:
            current_price: 当前市场价格
        """
        for agent_id, portfolio in self.agent_virtual_portfolios.items():
            unrealized = 0.0
            for pos in portfolio['virtual_positions']:
                if pos['side'] == 'long':
                    unrealized += (current_price - pos['entry_price']) * pos['amount']
            
            portfolio['unrealized_pnl'] = unrealized
    
    def rank_agent_performance(self) -> List[Tuple[str, Dict]]:
        """
        对Agent表现进行排名
        
        Returns:
            List[Tuple]: (agent_id, performance_data)按表现降序排列
        """
        rankings = []
        
        for agent_id, portfolio in self.agent_virtual_portfolios.items():
            # 计算综合表现得分
            capital_ratio = portfolio['virtual_capital'] / portfolio['initial_capital']
            win_rate = portfolio['win_rate']
            trade_count = portfolio['trade_count']
            
            # 综合得分：资金增长 * 0.6 + 胜率 * 0.3 + 交易活跃度 * 0.1
            performance_score = (
                (capital_ratio - 1) * 0.6 +
                win_rate * 0.3 +
                min(trade_count / 10, 1.0) * 0.1
            )
            
            performance_data = {
                'agent_id': agent_id,
                'score': performance_score,
                'capital': portfolio['virtual_capital'],
                'capital_ratio': capital_ratio,
                'total_pnl': portfolio['total_pnl'],
                'win_rate': win_rate,
                'trade_count': trade_count,
                'win_count': portfolio['win_count'],
                'loss_count': portfolio['loss_count'],
                'personality': portfolio['personality']
            }
            
            rankings.append((agent_id, performance_data))
        
        # 按综合得分降序排列
        rankings.sort(key=lambda x: x[1]['score'], reverse=True)
        
        self.agent_performance_rankings = rankings
        logger.info(f"Agent表现排名已更新: {len(rankings)}个Agent")
        
        return rankings
    
    def publish_agent_performance_report(self):
        """发布Agent表现报告到公告板"""
        if not self.bulletin_board:
            return
        
        # 更新排名
        rankings = self.rank_agent_performance()
        
        if not rankings:
            logger.warning("没有Agent表现数据，跳过发布")
            return
        
        # 提取前3名和后3名
        top_3 = rankings[:3]
        bottom_3 = rankings[-3:] if len(rankings) > 3 else []
        
        # 计算平均表现
        avg_win_rate = np.mean([r[1]['win_rate'] for r in rankings])
        avg_pnl = np.mean([r[1]['total_pnl'] for r in rankings])
        avg_capital_ratio = np.mean([r[1]['capital_ratio'] for r in rankings])
        
        # 发布公告
        self.bulletin_board.post(
            tier='system',
            title='📊 Agent表现报告',
            content={
                'type': 'AGENT_PERFORMANCE',
                'timestamp': datetime.now().isoformat(),
                'total_agents': len(rankings),
                'top_performers': [
                    {
                        'agent_id': r[0],
                        'rank': i + 1,
                        'capital': r[1]['capital'],
                        'pnl': r[1]['total_pnl'],
                        'win_rate': r[1]['win_rate'],
                        'trade_count': r[1]['trade_count']
                    }
                    for i, r in enumerate(top_3)
                ],
                'bottom_performers': [
                    {
                        'agent_id': r[0],
                        'rank': len(rankings) - bottom_3.index(r),
                        'capital': r[1]['capital'],
                        'pnl': r[1]['total_pnl'],
                        'win_rate': r[1]['win_rate'],
                        'trade_count': r[1]['trade_count']
                    }
                    for r in bottom_3
                ] if bottom_3 else [],
                'population_stats': {
                    'avg_win_rate': avg_win_rate,
                    'avg_pnl': avg_pnl,
                    'avg_capital_ratio': avg_capital_ratio
                },
                'recommendations': self._generate_performance_recommendations(rankings)
            },
            publisher='Supervisor',
            priority='normal'
        )
        
        logger.info(f"📊 Agent表现报告已发布: Top1={top_3[0][0] if top_3 else 'N/A'}, "
                   f"Avg胜率={avg_win_rate:.2%}")
    
    def _generate_performance_recommendations(self, rankings: List[Tuple]) -> List[str]:
        """生成表现建议"""
        recommendations = []
        
        if not rankings:
            return recommendations
        
        # 检查是否有明显的优胜者
        if len(rankings) >= 3:
            top_performer = rankings[0][1]
            avg_score = np.mean([r[1]['score'] for r in rankings])
            
            if top_performer['score'] > avg_score * 1.5:
                recommendations.append(f"🌟 Agent {rankings[0][0]} 表现突出，建议重点关注其策略")
        
        # 检查是否有失败者
        bottom_performer = rankings[-1][1]
        if bottom_performer['capital_ratio'] < 0.5:
            recommendations.append(f"⚠️ Agent {rankings[-1][0]} 资金损失超50%，建议重新评估策略")
        
        # 整体表现评估
        avg_win_rate = np.mean([r[1]['win_rate'] for r in rankings])
        if avg_win_rate < 0.4:
            recommendations.append("⚠️ 整体胜率偏低，建议调整市场分析或入场条件")
        elif avg_win_rate > 0.6:
            recommendations.append("✅ 整体表现良好，可考虑适当增加仓位")
        
        return recommendations
    
    def get_agent_portfolio(self, agent_id: str) -> Optional[Dict]:
        """
        获取Agent的虚拟账户信息
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict: 虚拟账户信息，如果不存在则返回None
        """
        return self.agent_virtual_portfolios.get(agent_id)
    
    def get_all_portfolios(self) -> Dict[str, Dict]:
        """获取所有Agent的虚拟账户信息"""
        return self.agent_virtual_portfolios
    
    def print_performance_summary(self):
        """打印Agent表现摘要（用于日志）"""
        rankings = self.rank_agent_performance()
        
        if not rankings:
            logger.info("暂无Agent表现数据")
            return
        
        logger.info("\n" + "="*60)
        logger.info("📊 Agent表现排名")
        logger.info("="*60)
        
        for i, (agent_id, data) in enumerate(rankings[:10], 1):  # 只显示前10名
            capital_change = (data['capital_ratio'] - 1) * 100
            logger.info(
                f"  {i:2d}. {agent_id}: "
                f"资金${data['capital']:.2f} ({capital_change:+.1f}%), "
                f"胜率{data['win_rate']:.1%}, "
                f"交易{data['trade_count']}笔"
            )
        
        if len(rankings) > 10:
            logger.info(f"  ... 还有{len(rankings)-10}个Agent")
        
        logger.info("="*60)
    
    # ========== 实际持仓跟踪系统（新增）==========
    
    def set_okx_trading(self, okx_trading):
        """注入OKX交易接口"""
        self.okx_trading = okx_trading
        logger.info("OKX交易接口已注入到Supervisor")
    
    def initialize_agent_real_positions(self, agents: List[Any]):
        """
        初始化Agent实际持仓跟踪
        
        Args:
            agents: Agent列表
        """
        for agent in agents:
            agent_id = getattr(agent, 'agent_id', 'unknown')
            self.agent_real_positions[agent_id] = {
                'has_position': False,
                'amount': 0.0,
                'entry_price': 0.0,
                'entry_time': None,
                'symbol': 'BTC/USDT:USDT'
            }
        
        logger.info(f"✅ 实际持仓跟踪已初始化: {len(agents)}个Agent")
    
    def receive_trade_request(self, agent_id: str, signal: str, confidence: float, current_price: float) -> bool:
        """
        接收Agent的交易请求并执行
        
        这是Supervisor作为"运营者"的核心方法
        
        Args:
            agent_id: Agent ID
            signal: 交易信号 ('buy' or 'sell')
            confidence: 信心度
            current_price: 当前价格
            
        Returns:
            bool: 是否执行成功
        """
        if not self.okx_trading:
            logger.error("OKX交易接口未注入，无法执行交易")
            return False
        
        # 1. 记录虚拟交易（所有请求都记录）
        self.record_virtual_trade(
            agent_id=agent_id,
            trade_type=signal,
            price=current_price,
            amount=0.01,
            confidence=confidence
        )
        
        # 2. 检查是否可以执行实际交易
        position = self.agent_real_positions.get(agent_id, {'has_position': False})
        
        if signal == 'buy':
            if not position['has_position']:
                return self._execute_buy(agent_id, current_price, confidence)
            else:
                logger.debug(f"{agent_id}: 已有持仓，拒绝开仓请求")
                return False
        
        elif signal == 'sell':
            if position['has_position']:
                return self._execute_sell(agent_id, current_price, confidence)
            else:
                logger.debug(f"{agent_id}: 无持仓，拒绝平仓请求")
                return False
        
        return False
    
    def _execute_buy(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行开仓（Supervisor执行交易）"""
        amount = 0.01
        
        try:
            order = self.okx_trading.place_market_order(
                symbol='BTC/USDT:USDT',
                side='buy',
                amount=amount,
                reduce_only=False,
                pos_side='long'
            )
            
            if order:
                # 更新实际持仓状态
                self.agent_real_positions[agent_id] = {
                    'has_position': True,
                    'amount': amount,
                    'entry_price': current_price,
                    'entry_time': datetime.now(),
                    'symbol': 'BTC/USDT:USDT'
                }
                
                logger.info(f"✅ {agent_id}: Supervisor执行开多 {amount} BTC (信心:{confidence:.2f})")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 开仓失败 - {e}")
        
        return False
    
    def _execute_sell(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行平仓（Supervisor执行交易）"""
        position = self.agent_real_positions[agent_id]
        amount = position['amount']
        
        try:
            order = self.okx_trading.place_market_order(
                symbol='BTC/USDT:USDT',
                side='sell',
                amount=amount,
                reduce_only=True,
                pos_side='long'
            )
            
            if order:
                # 计算盈亏
                pnl = (current_price - position['entry_price']) * amount
                
                # 更新实际持仓状态
                self.agent_real_positions[agent_id] = {
                    'has_position': False,
                    'amount': 0.0,
                    'entry_price': 0.0,
                    'entry_time': None,
                    'symbol': ''
                }
                
                logger.info(f"✅ {agent_id}: Supervisor执行平仓 {amount} BTC (盈亏:${pnl:.2f})")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 平仓失败 - {e}")
        
        return False
    
    def get_agent_position_status(self, agent_id: str) -> Dict:
        """获取Agent持仓状态"""
        return self.agent_real_positions.get(agent_id, {'has_position': False})
    
    # ========== 完整运营系统（新增：主循环）==========
    
    def set_components(self, okx_trading, mastermind, agents, config):
        """
        注入运营所需组件
        
        Args:
            okx_trading: OKX交易接口
            mastermind: Mastermind组件
            agents: Agent列表
            config: 配置
        """
        self.okx_trading = okx_trading
        self.mastermind = mastermind
        self.agents = agents
        self.config = config
        
        # 为每个Agent创建账户系统
        initial_capital = config.get('initial_capital_per_agent', 10000)
        for agent in agents:
            agent_id = getattr(agent, 'agent_id', 'unknown')
            account_system = AgentAccountSystem(
                agent_id=agent_id,
                initial_capital=initial_capital,
                public_ledger=self.public_ledger
            )
            self.agent_accounts[agent_id] = account_system
            
            # 将账户系统注入Agent
            agent.account = account_system
        
        logger.info(f"✅ Supervisor完整运营系统已配置：{len(agents)}个Agent")
    
    def run(self, duration_minutes=None, check_interval=60):
        """
        Supervisor主循环（完整运营系统）
        
        这是Supervisor作为"完整运营系统"的核心方法
        
        Args:
            duration_minutes: 运行时长（分钟），None表示不限时
            check_interval: 检查间隔（秒）
        """
        from datetime import timedelta
        import ccxt
        
        logger.info("="*70)
        logger.info("🏃 Supervisor完整运营系统启动")
        logger.info(f"   - Agent数量: {len(self.agents)}")
        logger.info(f"   - 检查间隔: {check_interval}秒")
        logger.info(f"   - 运行时长: {'不限时' if duration_minutes is None else f'{duration_minutes}分钟'}")
        logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"🏃 Supervisor完整运营系统启动")
        print(f"   Agent数量: {len(self.agents)}")
        print(f"   检查间隔: {check_interval}秒")
        if duration_minutes:
            print(f"   运行时长: {duration_minutes}分钟")
        else:
            print(f"   运行时长: 不限时 (按Ctrl+C停止)")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        cycle_count = 0
        
        try:
            while True:
                # 检查是否超时
                if end_time and datetime.now() >= end_time:
                    print("\n⏰ 运行时间已到，正常结束")
                    break
                
                cycle_count += 1
                current_time = datetime.now()
                
                print(f"\n{'='*70}")
                print(f"  🔄 周期 {cycle_count} | {current_time.strftime('%H:%M:%S')}")
                print(f"{'='*70}")
                
                try:
                    # 1. 获取市场数据
                    market_data = self._fetch_market_data_from_okx()
                    if market_data is None or len(market_data) < 25:
                        print("⚠️  市场数据不足，等待下一周期...")
                        time.sleep(check_interval)
                        continue
                    
                    current_price = market_data['close'].iloc[-1]
                    print(f"\n📊 当前价格: ${current_price:.2f}")
                    
                    # 2. Supervisor分析市场并发布
                    self.comprehensive_monitoring(market_data)
                    
                    # 3. Mastermind战略决策（每5个周期）
                    if cycle_count % 5 == 0 and self.mastermind:
                        self._execute_mastermind_strategy(market_data)
                    
                    # 4. 收集Agent决策
                    print(f"\n🤖 【Agents】自主决策模式")
                    agent_decisions = []
                    for agent in self.agents:
                        try:
                            decision = agent.decide()
                            if decision and isinstance(decision, dict):
                                agent_decisions.append({
                                    'agent_id': agent.agent_id,
                                    'signal': decision.get('signal'),
                                    'confidence': decision.get('confidence', 0.5),
                                    'reason': decision.get('reason', '')
                                })
                        except Exception as e:
                            logger.error(f"Agent {agent.agent_id} 决策失败: {e}")
                    
                    # 统计决策
                    buy_count = sum(1 for d in agent_decisions if d['signal'] == 'buy')
                    sell_count = sum(1 for d in agent_decisions if d['signal'] == 'sell')
                    wait_count = len(agent_decisions) - buy_count - sell_count
                    
                    print(f"\n   📊 Agent决策分布:")
                    print(f"      🟢 做多: {buy_count}个Agent")
                    print(f"      🔴 做空/平仓: {sell_count}个Agent")
                    print(f"      ⚪ 观望: {wait_count}个Agent")
                    
                    # 5. Supervisor接收并执行交易请求
                    print(f"\n💼 【交易执行】Supervisor接收Agent请求")
                    executed_count = 0
                    for decision in agent_decisions:
                        if decision['signal']:
                            success = self._receive_and_execute_trade(
                                agent_id=decision['agent_id'],
                                signal=decision['signal'],
                                confidence=decision['confidence'],
                                current_price=current_price
                            )
                            if success:
                                executed_count += 1
                    
                    if executed_count == 0:
                        print(f"   ⏸️  本周期无交易执行")
                    else:
                        print(f"   ✅ 执行了{executed_count}笔交易")
                    
                    # 6. 更新虚拟盈亏
                    self._update_unrealized_pnl(current_price)
                    
                    # 7. 发布Agent表现报告（每5个周期）
                    if cycle_count % 5 == 0:
                        self._publish_performance_report()
                    
                    # 8. 等待下一周期
                    print(f"\n⏸️  等待 {check_interval}秒...")
                    time.sleep(check_interval)
                
                except KeyboardInterrupt:
                    raise  # 向外抛出，由外层捕获
                except Exception as e:
                    logger.error(f"周期 {cycle_count} 执行失败: {e}", exc_info=True)
                    print(f"⚠️  周期执行失败: {e}")
                    time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  运营被用户中断")
        
        # 最终总结
        print(f"\n{'='*70}")
        print(f"🏁 Supervisor运营结束")
        print(f"{'='*70}")
        self._print_final_summary()
    
    def _fetch_market_data_from_okx(self):
        """从OKX获取市场数据"""
        try:
            # 获取K线数据
            ohlcv = self.okx_trading.exchange.fetch_ohlcv(
                'BTC/USDT:USDT',
                timeframe='15m',
                limit=100
            )
            
            # 转换为DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def _execute_mastermind_strategy(self, market_data):
        """执行Mastermind战略决策"""
        if not self.mastermind or not self.bulletin_board:
            return
        
        try:
            # Mastermind读取公共账簿（只读权限）
            top_performers = self.public_ledger.get_top_performers(
                limit=5, 
                caller_role=Role.MASTERMIND
            )
            
            # Mastermind制定战略
            strategy = self.mastermind.make_decision(
                market_data=market_data,
                current_market_state=self.current_market_state,
                top_performers=top_performers
            )
            
            # 发布战略公告
            if strategy:
                self.bulletin_board.publish('mastermind', strategy)
                logger.info(f"🧠 Mastermind发布战略: {strategy.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Mastermind战略决策失败: {e}")
    
    def _receive_and_execute_trade(self, agent_id, signal, confidence, current_price):
        """接收并执行Agent的交易请求"""
        account = self.agent_accounts.get(agent_id)
        if not account:
            logger.error(f"{agent_id}: 账户不存在")
            return False
        
        # 检查持仓状态（从私有账簿）
        status = account.get_status_for_decision(
            current_price,
            caller_role=Role.SUPERVISOR,
            caller_id='system'
        )
        
        try:
            if signal == 'buy':
                if status['has_position']:
                    logger.debug(f"{agent_id}: 已有持仓，拒绝买入")
                    return False
                
                # 执行买入
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='buy',
                    amount=0.01,
                    reduce_only=False,
                    pos_side='long'
                )
                
                if order:
                    # 更新账簿（同时更新私有和公共）
                    account.record_trade(
                        trade_type='buy',
                        amount=0.01,
                        price=current_price,
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR
                    )
                    logger.info(f"✅ {agent_id}: 开多 0.01 BTC @ ${current_price:.2f}")
                    return True
            
            elif signal == 'sell':
                if not status['has_position']:
                    logger.debug(f"{agent_id}: 无持仓，拒绝卖出")
                    return False
                
                # 执行卖出
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='sell',
                    amount=0.01,
                    reduce_only=True,
                    pos_side='long'
                )
                
                if order:
                    # 更新账簿
                    account.record_trade(
                        trade_type='sell',
                        amount=0.01,
                        price=current_price,
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR
                    )
                    logger.info(f"✅ {agent_id}: 平仓 0.01 BTC @ ${current_price:.2f}")
                    return True
        
        except Exception as e:
            logger.error(f"{agent_id}: 交易执行失败 - {e}")
        
        return False
    
    def _update_unrealized_pnl(self, current_price):
        """更新所有Agent的未实现盈亏"""
        for agent_id, account in self.agent_accounts.items():
            try:
                account.private_ledger.calculate_unrealized_pnl(current_price)
            except Exception as e:
                logger.error(f"更新{agent_id}未实现盈亏失败: {e}")
    
    def _publish_performance_report(self):
        """发布Agent表现报告"""
        try:
            # 从公共账簿获取统计
            top_performers = self.public_ledger.get_top_performers(
                limit=10,
                caller_role=Role.SUPERVISOR
            )
            
            print(f"\n{'='*60}")
            print(f"📊 Agent表现排名 (Top 5)")
            print(f"{'='*60}")
            
            for i, (agent_id, stats) in enumerate(top_performers[:5], 1):
                pnl = stats.get('total_pnl', 0)
                win_rate = stats.get('win_rate', 0)
                trade_count = stats.get('trade_count', 0)
                print(f"  {i}. {agent_id}: PnL=${pnl:.2f}, 胜率{win_rate:.1%}, {trade_count}笔")
            
            print(f"{'='*60}")
        
        except Exception as e:
            logger.error(f"发布表现报告失败: {e}")
    
    def _print_final_summary(self):
        """打印最终总结"""
        try:
            all_stats = self.public_ledger.get_all_agent_stats(
                caller_role=Role.SUPERVISOR
            )
            
            print(f"\n{'='*70}")
            print(f"📊 最终统计")
            print(f"{'='*70}")
            print(f"活跃Agent: {len(all_stats)}")
            
            if all_stats:
                total_pnl = sum(stats.get('total_pnl', 0) for stats in all_stats.values())
                avg_pnl = total_pnl / len(all_stats)
                print(f"总盈亏: ${total_pnl:.2f}")
                print(f"平均盈亏: ${avg_pnl:.2f}")
            
            print(f"{'='*70}")
        except Exception as e:
            logger.error(f"打印最终总结失败: {e}")

