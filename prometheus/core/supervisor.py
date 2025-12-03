"""
监督者 (Supervisor) - Prometheus v4.0
系统的观察者和评估者,负责监控 Agent 和施加环境压力
v4.0: 集成奖章制度 + 市场分析功能(整合MarketAnalyzer)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd

from .medal_system import MedalSystem
from .indicator_calculator import IndicatorCalculator, TechnicalIndicators
from .market_state_analyzer import MarketStateAnalyzer, MarketState
from .ledger_system import (
    PublicLedger, AgentAccountSystem, Role,
    LedgerReconciler, DiscrepancyType, ReconciliationAction
)
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
    1. 市场分析(整合MarketAnalyzer)⭐
       - 计算技术指标
       - 分析市场状态
       - 发布市场公告
    2. Agent监控
       - 健康检查
       - 权限管理
       - 奖章颁发
       - 极乐净土审核
    3. 环境分析
       - 环境压力计算
       - 风险警告
       - 系统公告发布
    4. 预警机制
    """
    
    def __init__(self, 
                 bulletin_board=None,
                 elysium=None,
                 trading_permission_system=None,
                 suicide_threshold: float = 0.8,
                 last_stand_threshold: float = 0.6,
                 indicator_config: Optional[Dict] = None):
        """
        初始化监督者
        
        Args:
            bulletin_board: 公告板系统
            elysium: 极乐净土系统
            trading_permission_system: 交易权限系统
            suicide_threshold: 自杀触发阈值 (0-1)
            last_stand_threshold: 拼死一搏触发阈值 (0-1)
            indicator_config: 技术指标配置
        """
        self.bulletin_board = bulletin_board
        self.elysium = elysium
        self.trading_permission_system = trading_permission_system
        
        self.suicide_threshold = suicide_threshold
        self.last_stand_threshold = last_stand_threshold
        
        # 市场分析模块(整合)⭐
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
        
        # 死亡历史(用于环境压力计算)
        self.death_history: List[Dict] = []
        
        # ===== 双账簿系统 =====
        self.public_ledger = PublicLedger()  # 公共账簿(只有一本)
        self.agent_accounts: Dict[str, AgentAccountSystem] = {}  # Agent账户系统
        self.ledger_reconciler = LedgerReconciler()  # 账簿调节器
        
        # ===== 兼容旧代码：模拟旧的agent_virtual_portfolios =====
        # 这是一个property,动态生成旧格式的portfolio数据
        self._legacy_mode = True
        
        # ===== 运营组件(用于主循环)=====
        self.okx_trading = None  # OKX交易接口
        self.mastermind = None  # Mastermind组件
        self.config = None  # 配置
        
        # ===== v4.1 进化系统 =====
        from prometheus.core.evolution_manager import EvolutionManager
        from prometheus.core.epiphany_system import EpiphanySystem
        
        self.evolution_manager = EvolutionManager(self)  # 进化管理器
        self.epiphany_system = EpiphanySystem()  # 顿悟系统
        self.next_agent_id = 1  # 用于生成新Agent ID
        
        logger.info("监督者已初始化(完整运营系统：市场分析 + Agent监控 + 双账簿系统 + 进化系统)")
    
    @property
    def agent_virtual_portfolios(self) -> Dict[str, Dict]:
        """兼容属性：动态生成旧格式的portfolio数据"""
        portfolios = {}
        for agent_id, account in self.agent_accounts.items():
            portfolios[agent_id] = self._get_legacy_portfolio(agent_id)
        return portfolios
    
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
        - 生存时长(太短或太长都可能增加绝望)
        - 环境压力
        
        Args:
            consecutive_losses: 连续亏损次数
            capital_ratio: 当前资金/初始资金
            fitness_score: 适应度得分 (0-1)
            days_alive: 存活天数
            environmental_pressure: 环境压力 (0-2)
            
        Returns:
            float: 绝望指数 (0-1),越高越绝望
        """
        # 1. 连续亏损因子 (0-1)
        loss_factor = min(consecutive_losses / 15.0, 1.0)  # 15次连亏 = 1.0
        
        # 2. 资金损失因子 (0-1)
        capital_loss = max(0, 1 - capital_ratio)  # 亏损越多越高
        capital_factor = min(capital_loss * 2, 1.0)  # 亏损50% = 1.0
        
        # 3. 适应度因子 (0-1)
        fitness_factor = 1 - fitness_score  # 适应度越低越高
        
        # 4. 生存时长因子 (0-1)
        # 太短(还没适应)或太长(长期表现差)都增加绝望
        if days_alive < 7:
            time_factor = 0.3  # 新生 Agent 不容易绝望
        elif days_alive < 30:
            time_factor = 0.5  # 成长期
        else:
            time_factor = 0.7  # 长期表现差增加绝望
        
        # 5. 环境压力因子
        pressure_factor = environmental_pressure / 2.0  # 归一化到 0-1
        
        # 综合计算(加权平均)
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
        
        濒危但尚未绝望,评估是否适合拼死一搏
        
        Args:
            capital_ratio: 当前资金/初始资金
            recent_trend: 近期趋势 (-1 to 1)
            market_opportunity: 市场机会评分 (0-1)
            survival_will: 生存意志 (0-1)
            personality_aggression: 性格激进度 (0-1)
            
        Returns:
            float: 濒危指数 (0-1),越高越适合拼搏
        """
        # 1. 资金危机因子
        if capital_ratio > 0.5:
            capital_crisis = 0.0  # 资金充足,不需要拼搏
        elif capital_ratio > 0.3:
            capital_crisis = (0.5 - capital_ratio) / 0.2  # 0.3-0.5 线性增长
        else:
            capital_crisis = 1.0  # 资金严重不足
        
        # 2. 趋势因子(下降趋势增加拼搏意愿)
        trend_factor = max(0, -recent_trend)  # 只有下降趋势才触发
        
        # 3. 机会因子(有好机会才值得拼搏)
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
        
        # 计算多样性(基因或策略的标准差)
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
    
    # ========== 市场分析模块(新增)==========
    
    def analyze_market_and_publish(self, market_data: pd.DataFrame):
        """
        分析市场并发布【原始市场数据】到公告板
        
        职责：只发布客观数据，不做预测/建议
        预测由Mastermind（先知）负责
        
        Args:
            market_data: 市场数据(OHLCV格式)
        """
        try:
            # 1. 计算技术指标(一次性)
            self.current_indicators = self.indicator_calculator.calculate_all(market_data)
            
            # 2. 分析市场状态（客观分析）
            self.current_market_state = self.market_state_analyzer.analyze(self.current_indicators)
            
            # 3. 获取当前价格
            current_price = float(market_data['close'].iloc[-1]) if len(market_data) > 0 else 0
            
            # 4. 发布【原始市场数据】到公告板（不含预测/建议）
            if self.bulletin_board:
                self.bulletin_board.post(
                    tier='market',
                    title='📊 市场实时数据',
                    content={
                        'type': 'MARKET_DATA',
                        'current_price': current_price,
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
                            'opportunity_score': self.current_market_state.opportunity_score
                            # 注意：不再包含recommendation，由Mastermind占卜
                        }
                    },
                    publisher='Supervisor',
                    priority='normal'
                )
            
        except Exception as e:
            logger.error(f"市场分析失败: {e}")
            raise
    
    def calculate_environment_pressure_comprehensive(self) -> float:
        """
        计算环境压力(综合版)
        
        现在可以同时使用：
        - 市场技术指标(market difficulty)
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
        
        # 彻夜运行：减少重复日志
        # logger.info(f"🌍 环境状态已发布: 压力={pressure:.2f}")
    
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
            return "⚠️ 极端环境,建议降低仓位,严控风险"
        elif pressure > 0.6:
            return "⚠️ 高压环境,建议谨慎交易"
        elif pressure > 0.4:
            return "正常环境,可正常交易"
        else:
            return "良好环境,可适当增加仓位"
    
    # ========== 综合监控(一次性完成所有工作)==========
    
    def comprehensive_monitoring(self, market_data: pd.DataFrame):
        """
        综合监控(核心方法)
        
        一次性完成：
        1. 市场分析 → 发布市场公告
        2. Agent监控 → 更新权限/奖章
        3. 环境分析 → 发布系统公告
        4. 风险警告(如需要)
        
        Args:
            market_data: 市场数据
        """
        # 彻夜运行模式：移除重复的监控日志
        # logger.info("=" * 50)
        # logger.info("开始综合监控...")
        
        # 1. 市场分析
        self.analyze_market_and_publish(market_data)
        
        # 2. Agent监控
        self._monitor_and_update_agents()
        
        # 3. 环境分析
        self.publish_environment_info()
        
        # 4. 风险警告
        if self.environment_pressure > 0.7:
            self._issue_risk_warning()
        
        # 5. 极乐净土审核
        self._review_for_elysium()
        
        # logger.info("综合监控完成")
        # logger.info("=" * 50)
    
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
            
            # 权限更新(如果有交易权限系统)
            if self.trading_permission_system and hasattr(agent, 'permission_level'):
                self._update_agent_permission(agent, health_report)
            
            # 奖章评估(已在evaluate_agent中完成)
    
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
                'message': f"环境压力过高({self.environment_pressure:.2f}),请注意风险控制",
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
    
    def _review_for_elysium(self):
        """审核Agent是否符合极乐净土入选条件"""
        if not self.elysium:
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
                if not self.elysium.is_inducted(agent_id):
                    logger.info(f"🏛️ Agent {agent_id} 符合极乐净土条件({medal_count}枚奖章)")
                    # 可以在这里触发入选,或等待Mastermind决策
    
    def register_agent(self, agent):
        """注册Agent到监督系统"""
        if agent not in self.agents:
            self.agents.append(agent)
            logger.info(f"Agent {getattr(agent, 'agent_id', 'unknown')} 已注册到监督系统")
    
    def unregister_agent(self, agent):
        """注销Agent(死亡时)"""
        if agent in self.agents:
            self.agents.remove(agent)
            
            # 记录死亡
            self.death_history.append({
                'agent_id': getattr(agent, 'agent_id', 'unknown'),
                'timestamp': datetime.now(),
                'capital': getattr(agent, 'capital', 0),
                'total_pnl': getattr(agent, 'total_pnl', 0)
            })
            
            logger.info(f"Agent {getattr(agent, 'agent_id', 'unknown')} 已从监督系统注销(死亡)")
    
    # ========== 虚拟账户管理系统(新增)==========
    
    def initialize_virtual_accounts(self, agents: List[Any], initial_capital_per_agent: float = 10000):
        """
        初始化Agent虚拟账户系统(兼容旧代码)
        
        新架构使用AgentAccountSystem,这个方法保留用于兼容性
        
        Args:
            agents: Agent列表
            initial_capital_per_agent: 每个Agent的初始虚拟资金
        """
        # 使用新的双账簿系统
        for agent in agents:
            agent_id = getattr(agent, 'agent_id', 'unknown')
            
            # 创建账户系统
            if agent_id not in self.agent_accounts:
                account_system = AgentAccountSystem(
                    agent_id=agent_id,
                    initial_capital=initial_capital_per_agent,
                    public_ledger=self.public_ledger
                )
                self.agent_accounts[agent_id] = account_system
                
                # 注入到Agent
                if hasattr(agent, 'account'):
                    agent.account = account_system
        
        logger.info(f"✅ 虚拟账户系统已初始化: {len(agents)}个Agent,每个{initial_capital_per_agent} USDT")
        
        # 保留旧的字典格式用于兼容(映射到新系统)
        # 这样旧代码调用agent_virtual_portfolios时不会报错
        # 注意：这是临时兼容方案,建议迁移到新API
        pass
    
    def _get_legacy_portfolio(self, agent_id: str) -> Dict:
        """获取旧格式的portfolio(用于兼容)"""
        account = self.agent_accounts.get(agent_id)
        if not account:
            return None
        
        status = account.private_ledger.get_summary(0, Role.SUPERVISOR, 'system')
        
        # 转换为旧格式
        return {
            'agent_id': agent_id,
            'virtual_capital': status['balance'],
            'initial_capital': account.private_ledger.initial_capital,
            'virtual_positions': [],  # 简化
            'total_pnl': status['total_pnl'],
            'trade_count': status['trade_count'],
            'win_rate': status['win_rate']
        }
    
    def record_virtual_trade(self, agent_id: str, trade_type: str, price: float, amount: float, confidence: float = 0.0):
        """
        记录Agent的虚拟交易(兼容旧代码)
        
        新架构使用AgentAccountSystem.record_trade,这个方法保留用于兼容性
        
        Args:
            agent_id: Agent ID
            trade_type: 交易类型 ('buy' or 'sell')
            price: 交易价格
            amount: 交易数量
            confidence: 交易信心度
        """
        account = self.agent_accounts.get(agent_id)
        if not account:
            logger.warning(f"Agent {agent_id} 未注册账户")
            return
        
        # 委托给新的账簿系统
        account.record_trade(
            trade_type=trade_type,
            amount=amount,
            price=price,
            confidence=confidence,
            is_real=False,  # 虚拟交易
            caller_role=Role.SUPERVISOR
        )
        
        logger.debug(f"Agent {agent_id} 虚拟交易已记录")
        
        # 旧代码已移除,由新账簿系统处理
        return
        
        # 以下是废弃代码,保留用于参考
        """
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
        """
    
    def calculate_unrealized_pnl(self, current_price: float):
        """
        计算所有Agent的未实现盈亏(兼容旧代码)
        
        新架构使用PrivateLedger.calculate_unrealized_pnl
        
        Args:
            current_price: 当前市场价格
        """
        for agent_id, account in self.agent_accounts.items():
            # 委托给账户系统
            try:
                account.private_ledger.calculate_unrealized_pnl(current_price)
            except Exception as e:
                logger.error(f"计算{agent_id}未实现盈亏失败: {e}")
    
    # ========== 账簿调节方法 ==========
    
    def reconcile_agent_ledgers(self, agent_id: str, okx_position: dict = None) -> List[ReconciliationAction]:
        """
        调节单个Agent的账簿
        
        Supervisor自动检测并修复账簿不一致
        优先级：OKX实际 > 公共账簿 > 私有账簿
        
        Args:
            agent_id: Agent ID
            okx_position: OKX实际持仓（可选）
        
        Returns:
            执行的修复动作列表
        """
        if agent_id not in self.agent_accounts:
            logger.warning(f"Agent {agent_id} 不存在")
            return []
        
        account = self.agent_accounts[agent_id]
        
        return self.ledger_reconciler.reconcile_all(
            agent_id=agent_id,
            private_ledger=account.private_ledger,
            public_ledger=self.public_ledger,
            okx_position=okx_position
        )
    
    def reconcile_all_agents(self, okx_positions: Dict[str, dict] = None) -> Dict[str, List[ReconciliationAction]]:
        """
        调节所有Agent的账簿
        
        Args:
            okx_positions: 所有Agent的OKX实际持仓 {agent_id: position_dict}
        
        Returns:
            {agent_id: [actions]}
        """
        results = {}
        okx_positions = okx_positions or {}
        
        for agent_id in self.agent_accounts:
            okx_pos = okx_positions.get(agent_id)
            actions = self.reconcile_agent_ledgers(agent_id, okx_pos)
            if actions and any(a != ReconciliationAction.NO_ACTION for a in actions):
                results[agent_id] = actions
        
        if results:
            logger.info(f"[账簿调节] 修复了{len(results)}个Agent的账簿不一致")
        
        return results
    
    def detect_unclaimed_positions(self) -> List[dict]:
        """
        检测OKX上无人认领的持仓
        
        无人认领 = OKX有持仓但所有Agent账簿都没有记录
        
        Returns:
            无人认领的持仓列表 [{'symbol': ..., 'amount': ..., 'side': ...}]
        """
        if not self.okx_trading:
            return []
        
        unclaimed = []
        
        try:
            # 获取OKX所有持仓
            okx_positions = self.okx_trading.get_all_positions()
            
            if not okx_positions:
                return []
            
            # 汇总所有Agent的账簿持仓
            total_ledger_amount = 0.0
            for agent_id, account in self.agent_accounts.items():
                if account.private_ledger.real_position:
                    total_ledger_amount += account.private_ledger.real_position.amount
            
            # 检查每个OKX持仓
            for pos in okx_positions:
                okx_amount = abs(float(pos.get('contracts', 0)))
                symbol = pos.get('symbol', '')
                side = pos.get('side', 'long')
                
                if okx_amount <= 0:
                    continue
                
                # 如果OKX持仓 > 账簿总持仓，说明有无人认领的部分
                unclaimed_amount = okx_amount - total_ledger_amount
                
                if unclaimed_amount > 0.0001:  # 超过容差
                    unclaimed.append({
                        'symbol': symbol,
                        'amount': unclaimed_amount,
                        'okx_total': okx_amount,
                        'ledger_total': total_ledger_amount,
                        'side': side,
                        'entry_price': float(pos.get('entryPrice', 0))
                    })
                    logger.warning(
                        f"[无人认领] {symbol}: OKX={okx_amount}, 账簿总计={total_ledger_amount}, "
                        f"无人认领={unclaimed_amount}"
                    )
            
        except Exception as e:
            logger.error(f"检测无人认领持仓失败: {e}")
        
        return unclaimed
    
    def close_unclaimed_positions(self) -> List[dict]:
        """
        平仓所有无人认领的持仓
        
        安全策略：无人认领的持仓 = 无人负责风险管理 -> 立即平仓
        
        Returns:
            平仓结果列表
        """
        unclaimed = self.detect_unclaimed_positions()
        
        if not unclaimed:
            return []
        
        results = []
        
        for pos in unclaimed:
            symbol = pos['symbol']
            amount = pos['amount']
            side = pos['side']
            
            logger.warning(f"[平仓无人认领] {symbol}: {amount} ({side})")
            
            try:
                # 执行平仓
                if self.okx_trading:
                    # 平多仓用sell，平空仓用buy
                    order_side = 'sell' if side == 'long' else 'buy'
                    
                    order = self.okx_trading.place_market_order(
                        symbol=symbol,
                        side=order_side,
                        amount=amount,
                        reduce_only=True,
                        pos_side=side
                    )
                    
                    results.append({
                        'symbol': symbol,
                        'amount': amount,
                        'side': side,
                        'action': 'closed',
                        'order': order,
                        'reason': 'unclaimed_position'
                    })
                    
                    logger.info(f"[平仓成功] {symbol}: {amount} @ 市价")
                    
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'amount': amount,
                    'side': side,
                    'action': 'failed',
                    'error': str(e),
                    'reason': 'unclaimed_position'
                })
                logger.error(f"[平仓失败] {symbol}: {e}")
        
        return results
    
    def reconcile_with_okx(self) -> dict:
        """
        与OKX进行完整对账
        
        步骤：
        1. 检测无人认领持仓 -> 平仓
        2. 调节所有Agent账簿
        
        Returns:
            对账结果
        """
        result = {
            'unclaimed_closed': [],
            'agents_reconciled': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 处理无人认领持仓
        unclaimed_results = self.close_unclaimed_positions()
        result['unclaimed_closed'] = unclaimed_results
        
        # 2. 调节Agent账簿
        agent_results = self.reconcile_all_agents()
        result['agents_reconciled'] = {
            agent_id: [a.value for a in actions]
            for agent_id, actions in agent_results.items()
        }
        
        if unclaimed_results:
            logger.info(f"[OKX对账] 平仓{len(unclaimed_results)}笔无人认领持仓")
        
        return result
    
    def get_reconciliation_report(self) -> dict:
        """获取账簿调节报告"""
        return self.ledger_reconciler.get_reconciliation_summary()
    
    def rank_agent_performance(self, current_price: float = 0) -> List[Tuple[str, Dict]]:
        """
        对Agent表现进行排名
        
        计算流程：
        0. 轻量级账簿调节（私有vs公共，不调用OKX API）
        1. 从私有账簿获取Agent持仓和已实现盈亏
        2. 从公共账簿验证交易记录
        3. 使用当前市价计算未实现盈亏
        4. 总PnL = 已实现盈亏 + 未实现盈亏
        5. 综合得分排名
        
        注意：完整OKX对账在主循环中定期执行（每10个周期）
        
        Args:
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            List[Tuple]: (agent_id, performance_data)按表现降序排列
        """
        # ========== 0. 轻量级账簿调节（不调用OKX API）==========
        reconciliation_results = self.reconcile_all_agents()  # 不传okx_positions
        if reconciliation_results:
            for agent_id, actions in reconciliation_results.items():
                action_names = [a.value for a in actions if a != ReconciliationAction.NO_ACTION]
                if action_names:
                    logger.warning(f"[调节] {agent_id}: {', '.join(action_names)}")
        
        rankings = []
        
        for agent_id, account in self.agent_accounts.items():
            try:
                # ========== 1. 从私有账簿获取Agent状态 ==========
                private_status = account.get_status_for_decision(
                    current_price,
                    caller_role=Role.SUPERVISOR,
                    caller_id='system'
                )
                
                initial_capital = private_status.get('initial_capital', 10000.0)
                realized_pnl = private_status.get('total_pnl', 0.0)  # 已实现盈亏
                private_trade_count = private_status.get('trade_count', 0)
                win_rate = private_status.get('win_rate', 0.0)
                
                # 双向持仓信息
                has_position = private_status.get('has_position', False)
                
                # 获取多空持仓
                long_position = private_status.get('long_position')
                short_position = private_status.get('short_position')
                
                long_amount = long_position.get('amount', 0) if long_position else 0
                long_entry = long_position.get('entry_price', 0) if long_position else 0
                short_amount = short_position.get('amount', 0) if short_position else 0
                short_entry = short_position.get('entry_price', 0) if short_position else 0
                
                # 兼容：主要持仓（多头优先）
                position_amount = long_amount if long_amount > 0 else short_amount
                entry_price = long_entry if long_amount > 0 else short_entry
                
                # ========== 2. 从公共账簿验证交易记录 ==========
                public_trades = self.public_ledger.get_agent_trades(agent_id)
                public_trade_count = len(public_trades)
                
                # 验证一致性
                if private_trade_count != public_trade_count:
                    logger.warning(
                        f"{agent_id}: 账簿不一致 - 私有{private_trade_count}笔/公共{public_trade_count}笔"
                    )
                
                # ========== 3. 获取未实现盈亏（已由PrivateLedger计算，包含交易费用） ==========
                # 直接从private_status获取，避免重复计算
                unrealized_pnl = private_status.get('unrealized_pnl', 0.0)
                
                # ========== 4. 计算总PnL ==========
                total_pnl = realized_pnl + unrealized_pnl
                
                # ROI计算
                total_roi_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
                
                # 持仓成本和收益率
                position_cost = position_amount * entry_price if entry_price > 0 else 0
                position_roi_pct = (unrealized_pnl / position_cost * 100) if position_cost > 0 else 0
                
                # ========== 5. 综合得分计算 ==========
                # 核心理念：总盈亏最重要，所有得分标准化到同一数量级
                
                # 1. 总PnL得分（70%权重）- 盈亏最重要，放大到合理范围
                # 假设正常PnL范围是-100~+100美元，标准化为-100~+100分
                pnl_score = total_pnl  # 直接使用美元值作为分数
                
                # 2. 持仓ROI得分（15%权重）- 有持仓时的收益率
                # position_roi_pct已经是百分比（如3.5表示3.5%）
                # 限制在合理范围-10~+10
                efficiency_score = max(-10, min(10, position_roi_pct)) if has_position else 0
                
                # 3. 胜率得分（10%权重）- 已平仓交易的胜率
                # win_rate是0~1，转换为0~10分
                win_rate_score = win_rate * 10
                
                # 4. 交易活跃度得分（5%权重）- 适度交易
                # 最多1分
                activity_score = min(private_trade_count, 10) / 10
                
                # 综合得分（确保PnL主导）
                performance_score = (
                    pnl_score * 1.0 +           # PnL直接作为主要得分
                    efficiency_score * 0.5 +     # ROI作为辅助
                    win_rate_score * 0.3 +       # 胜率作为参考
                    activity_score * 0.2         # 活跃度微调
                )
                
                performance_data = {
                    'agent_id': agent_id,
                    'score': performance_score,
                    'total_pnl': total_pnl,
                    'realized_pnl': realized_pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'total_roi_pct': total_roi_pct,
                    'position_roi_pct': position_roi_pct,
                    'win_rate': win_rate,
                    'trade_count': private_trade_count,
                    'has_position': has_position,
                    'position_amount': position_amount,  # 兼容：主要持仓量
                    'entry_price': entry_price,  # 兼容：主要入场价
                    # 双向持仓详细信息
                    'long_position_amount': long_amount,
                    'long_entry_price': long_entry,
                    'short_position_amount': short_amount,
                    'short_entry_price': short_entry,
                    'data_verified': (private_trade_count == public_trade_count)
                }
                
                rankings.append((agent_id, performance_data))
                
            except Exception as e:
                logger.error(f"计算{agent_id}排名失败: {e}", exc_info=True)
        
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
            logger.warning("没有Agent表现数据,跳过发布")
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
                recommendations.append(f"🌟 Agent {rankings[0][0]} 表现突出,建议重点关注其策略")
        
        # 检查是否有失败者
        bottom_performer = rankings[-1][1]
        if bottom_performer['capital_ratio'] < 0.5:
            recommendations.append(f"⚠️ Agent {rankings[-1][0]} 资金损失超50%,建议重新评估策略")
        
        # 整体表现评估
        avg_win_rate = np.mean([r[1]['win_rate'] for r in rankings])
        if avg_win_rate < 0.4:
            recommendations.append("⚠️ 整体胜率偏低,建议调整市场分析或入场条件")
        elif avg_win_rate > 0.6:
            recommendations.append("✅ 整体表现良好,可考虑适当增加仓位")
        
        return recommendations
    
    def get_agent_portfolio(self, agent_id: str) -> Optional[Dict]:
        """
        获取Agent的虚拟账户信息
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict: 虚拟账户信息,如果不存在则返回None
        """
        return self.agent_virtual_portfolios.get(agent_id)
    
    def get_all_portfolios(self) -> Dict[str, Dict]:
        """获取所有Agent的虚拟账户信息"""
        return self.agent_virtual_portfolios
    
    def print_performance_summary(self):
        """打印Agent表现摘要(用于日志)"""
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
    
    # ========== 实际持仓跟踪系统(新增)==========
    
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
            logger.error("OKX交易接口未注入,无法执行交易")
            return False
        
        # 1. 记录虚拟交易(所有请求都记录)
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
                logger.debug(f"{agent_id}: 已有持仓,拒绝开仓请求")
                return False
        
        elif signal == 'sell':
            if position['has_position']:
                return self._execute_sell(agent_id, current_price, confidence)
            else:
                logger.debug(f"{agent_id}: 无持仓,拒绝平仓请求")
                return False
        
        return False
    
    def _execute_buy(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行开多(Supervisor执行交易)"""
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
                    'side': 'long',  # 明确标记为多仓
                    'amount': amount,
                    'entry_price': current_price,
                    'entry_time': datetime.now(),
                    'symbol': 'BTC/USDT:USDT'
                }
                
                logger.info(f"✅ {agent_id}: 开多 {amount} BTC @ ${current_price:.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 开多失败 - {e}")
        
        return False
    
    def _execute_sell(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行平仓(Supervisor执行交易)"""
        position = self.agent_real_positions.get(agent_id, {})
        amount = position.get('amount', 0)
        
        if amount <= 0:
            logger.warning(f"{agent_id}: 没有持仓可平")
            return False
        
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
                
                pnl_emoji = "📈" if pnl > 0 else "📉"
                logger.info(f"✅ {agent_id}: 平多 {amount} BTC {pnl_emoji} 盈亏:${pnl:.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 平多失败 - {e}")
        
        return False
    
    def _execute_short(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行开空(Supervisor执行交易)"""
        amount = 0.01
        
        try:
            order = self.okx_trading.place_market_order(
                symbol='BTC/USDT:USDT',
                side='sell',
                amount=amount,
                reduce_only=False,
                pos_side='short'  # 开空仓
            )
            
            if order:
                # 更新实际持仓状态
                self.agent_real_positions[agent_id] = {
                    'has_position': True,
                    'side': 'short',
                    'amount': amount,
                    'entry_price': current_price,
                    'entry_time': datetime.now(),
                    'symbol': 'BTC/USDT:USDT'
                }
                
                logger.info(f"✅ {agent_id}: 开空 {amount} BTC @ ${current_price:.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 开空失败 - {e}")
        
        return False
    
    def _execute_cover(self, agent_id: str, current_price: float, confidence: float) -> bool:
        """执行平空(Supervisor执行交易)"""
        position = self.agent_real_positions.get(agent_id, {})
        amount = position.get('amount', 0)
        
        if amount <= 0:
            logger.warning(f"{agent_id}: 没有空仓可平")
            return False
        
        if position.get('side') != 'short':
            logger.warning(f"{agent_id}: 当前不是空仓，无法平空")
            return False
        
        try:
            order = self.okx_trading.place_market_order(
                symbol='BTC/USDT:USDT',
                side='buy',  # 平空用buy
                amount=amount,
                reduce_only=True,
                pos_side='short'
            )
            
            if order:
                # 计算盈亏（做空盈亏 = (入场价 - 平仓价) * 数量）
                pnl = (position['entry_price'] - current_price) * amount
                
                # 更新实际持仓状态
                self.agent_real_positions[agent_id] = {
                    'has_position': False,
                    'side': None,
                    'amount': 0.0,
                    'entry_price': 0.0,
                    'entry_time': None,
                    'symbol': ''
                }
                
                pnl_emoji = "📈" if pnl > 0 else "📉"
                logger.info(f"✅ {agent_id}: 平空 {amount} BTC {pnl_emoji} 盈亏:${pnl:.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ {agent_id}: 平空失败 - {e}")
        
        return False
    
    def get_agent_position_status(self, agent_id: str) -> Dict:
        """获取Agent持仓状态"""
        return self.agent_real_positions.get(agent_id, {'has_position': False})
    
    # ========== 完整运营系统(新增：主循环)==========
    
    def _log_print(self, message):
        """同时输出到控制台和日志文件（处理Windows编码问题）"""
        try:
            print(message)
        except UnicodeEncodeError:
            # Windows控制台编码问题：将无法编码的字符替换为?
            print(message.encode('gbk', errors='replace').decode('gbk'))
        
        if hasattr(self, 'log_handler') and self.log_handler:
            self.log_handler.write(message + '\n')
            self.log_handler.flush()
    
    def set_components(self, okx_trading, mastermind, agents, config):
        """
        注入运营所需组件（旧方法，建议使用genesis()）
        
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
    
    # ========== 创世方法 ==========
    
    def genesis(self, okx_trading, mastermind, bulletin_board, config, 
                agent_factory=None) -> dict:
        """
        创世方法 - 完整的世界初始化
        
        创世流程：
        ┌─────────────────────────────────────────────────────────────┐
        │  第一章：天地初开 - 连接交易所                               │
        │  ├── 1.1 连接OKX交易所                                      │
        │  ├── 1.2 获取账户资金状况                                   │
        │  └── 1.3 清空所有历史持仓（归零）                           │
        │                                                              │
        │  第二章：定立法则 - 资源分配                                 │
        │  ├── 2.1 根据总资金决定Agent数量                            │
        │  ├── 2.2 计算每个Agent分配的资金                            │
        │  └── 2.3 设定交易规则（最小交易量等）                       │
        │                                                              │
        │  第三章：观测天象 - 获取市场信息                             │
        │  ├── 3.1 获取历史K线数据（过去N天）                         │
        │  ├── 3.2 分析市场趋势                                       │
        │  └── 3.3 Supervisor发布市场公告                             │
        │                                                              │
        │  第四章：先知占卜 - 发布创世大预言                           │
        │  ├── 4.1 先知分析市场信息                                   │
        │  └── 4.2 发布创世大预言                                     │
        │                                                              │
        │  第五章：众生创造 - Agent诞生                                │
        │  ├── 5.1 生成Agent基因库                                    │
        │  ├── 5.2 创建Agent实体                                      │
        │  └── 5.3 分配私有账簿                                       │
        │                                                              │
        │  第六章：世界运转 - 系统启动                                 │
        │  ├── 6.1 与OKX对账验证                                      │
        │  └── 6.2 记录创世时间                                       │
        └─────────────────────────────────────────────────────────────┘
        
        Args:
            okx_trading: OKX交易接口
            mastermind: 先知/Mastermind组件
            bulletin_board: 公告板
            config: 创世配置 {
                'min_agent_count': 5,      # 最少Agent数量
                'max_agent_count': 20,     # 最多Agent数量
                'min_capital_per_agent': 5000,  # 每个Agent最低资金
                'capital_reserve_ratio': 0.1,   # 资金储备比例(10%)
                'history_days': 7,         # 获取历史数据天数
            }
            agent_factory: Agent工厂函数（可选）
        
        Returns:
            创世结果
        """
        result = {
            'success': False,
            'genesis_time': None,
            'total_capital': 0,
            'agent_count': 0,
            'capital_per_agent': 0,
            'positions_closed': 0,
            'market_analysis': None,
            'first_prophecy': None,
            'agents_created': [],
            'errors': []
        }
        
        try:
            logger.info("\n" + "="*60)
            logger.info("🌅 创世开始 - Prometheus Genesis")
            logger.info("="*60)
            
            # ==================== 第一章：天地初开 ====================
            logger.info("\n📜 第一章：天地初开 - 连接交易所")
            logger.info("-"*40)
            
            # 1.1 注入组件
            logger.info("   [1.1] 连接OKX交易所...")
            self.okx_trading = okx_trading
            self.mastermind = mastermind
            self.bulletin_board = bulletin_board
            self.config = config
            
            if not self.okx_trading:
                raise Exception("OKX交易接口未提供")
            logger.info("      ✅ OKX连接成功")
            
            # 1.2 获取账户资金状况
            logger.info("   [1.2] 获取账户资金状况...")
            total_capital = self._genesis_get_account_balance()
            result['total_capital'] = total_capital
            logger.info(f"      ✅ 账户总资金: ${total_capital:,.2f}")
            
            # 1.3 清空所有历史持仓
            logger.info("   [1.3] 清空所有历史持仓...")
            positions_closed = self._genesis_close_all_positions()
            result['positions_closed'] = positions_closed
            logger.info(f"      ✅ 已清空{positions_closed}个持仓")
            
            # ==================== 第二章：定立法则 ====================
            logger.info("\n📜 第二章：定立法则 - 资源分配")
            logger.info("-"*40)
            
            # 2.1 根据总资金决定Agent数量
            logger.info("   [2.1] 计算Agent数量...")
            agent_count, capital_per_agent = self._genesis_calculate_allocation(
                total_capital, config
            )
            result['agent_count'] = agent_count
            result['capital_per_agent'] = capital_per_agent
            logger.info(f"      ✅ Agent数量: {agent_count}")
            logger.info(f"      ✅ 每Agent资金: ${capital_per_agent:,.2f}")
            
            # 2.2 设定交易规则
            logger.info("   [2.2] 设定交易规则...")
            trading_rules = self._genesis_set_trading_rules(capital_per_agent)
            self.trading_rules = trading_rules
            logger.info(f"      ✅ 最小交易量: {trading_rules['min_trade_amount']} BTC")
            logger.info(f"      ✅ 单笔最大: {trading_rules['max_trade_ratio']*100}%资金")
            
            # ==================== 第三章：观测天象 ====================
            logger.info("\n📜 第三章：观测天象 - 获取市场信息")
            logger.info("-"*40)
            
            # 3.1 获取历史K线数据
            history_days = config.get('history_days', 7)
            logger.info(f"   [3.1] 获取过去{history_days}天K线数据...")
            market_data = self._genesis_fetch_market_history(history_days)
            
            # 3.2 分析市场趋势
            logger.info("   [3.2] 分析市场趋势...")
            market_analysis = self._genesis_analyze_market(market_data)
            result['market_analysis'] = market_analysis
            logger.info(f"      ✅ 当前价格: ${market_analysis['current_price']:,.2f}")
            logger.info(f"      ✅ 7日涨跌: {market_analysis['change_7d']:+.2f}%")
            logger.info(f"      ✅ 趋势判断: {market_analysis['trend']}")
            
            # 3.3 Supervisor发布市场公告
            logger.info("   [3.3] 发布市场公告...")
            self._genesis_publish_market_bulletin(market_analysis)
            logger.info("      ✅ 市场公告已发布")
            
            # ==================== 第四章：先知占卜 ====================
            logger.info("\n📜 第四章：先知占卜 - 发布第一条预言")
            logger.info("-"*40)
            
            # 4.1 先知分析并发布创世大预言
            logger.info("   [4.1] 先知分析市场...")
            first_prophecy = self._genesis_first_prophecy(market_data, market_analysis)
            result['first_prophecy'] = first_prophecy
            # 详细信息已在_genesis_first_prophecy内部输出，这里只记录状态
            logger.info(f"      ✅ 创世大预言已发布")
            
            # ==================== 第五章：众生创造 ====================
            logger.info("\n📜 第五章：众生创造 - Agent诞生")
            logger.info("-"*40)
            
            # 5.1 生成Agent基因库
            logger.info("   [5.1] 生成Agent基因库...")
            gene_pool = self._genesis_create_gene_pool(agent_count, market_analysis)
            logger.info(f"      ✅ 生成{len(gene_pool)}个独特基因")
            
            # 5.2 创建Agent实体
            logger.info("   [5.2] 创建Agent实体...")
            agents = self._genesis_create_agents(
                agent_count, gene_pool, capital_per_agent, agent_factory
            )
            self.agents = agents
            result['agents_created'] = [a.agent_id for a in agents]
            logger.info(f"      ✅ 创建{len(agents)}个Agent")
            
            # 5.3 分配私有账簿
            logger.info("   [5.3] 分配私有账簿...")
            self._genesis_setup_ledgers(agents, capital_per_agent)
            logger.info("      ✅ 私有账簿分配完成")
            
            # ==================== 第六章：世界运转 ====================
            logger.info("\n📜 第六章：世界运转 - 系统启动")
            logger.info("-"*40)
            
            # 6.1 与OKX对账验证
            logger.info("   [6.1] 与OKX对账验证...")
            try:
                reconcile_result = self.reconcile_with_okx()
                if reconcile_result.get('unclaimed_closed'):
                    logger.warning("      ⚠️  发现无人认领持仓已处理")
                else:
                    logger.info("      ✅ OKX对账通过")
            except Exception as e:
                logger.warning(f"      ⚠️  OKX对账: {e}")
            
            # 6.2 记录创世时间
            logger.info("   [6.2] 记录创世时间...")
            genesis_time = datetime.now()
            self.genesis_time = genesis_time
            result['genesis_time'] = genesis_time
            result['success'] = True
            
            # ==================== 创世完成 ====================
            logger.info("\n" + "="*60)
            logger.info("🌅 创世完成 - Prometheus世界已诞生")
            logger.info("="*60)
            logger.info(f"   创世时间: {genesis_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   总资金: ${total_capital:,.2f}")
            logger.info(f"   Agent数量: {agent_count}")
            logger.info(f"   每Agent资金: ${capital_per_agent:,.2f}")
            logger.info(f"   市场趋势: {market_analysis['trend']}")
            logger.info(f"   创世大预言: {first_prophecy.get('trend_forecast', 'N/A')}(信心:{first_prophecy.get('forecast_confidence', 0)*100:.0f}%)")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ 创世失败: {e}")
            result['errors'].append(str(e))
            import traceback
            traceback.print_exc()
        
        return result
    
    # ========== 创世辅助方法 ==========
    
    def _genesis_get_account_balance(self) -> float:
        """获取OKX账户余额"""
        try:
            balance = self.okx_trading.exchange.fetch_balance()
            # 获取USDT余额
            usdt_balance = balance.get('USDT', {})
            total = float(usdt_balance.get('total', 0))
            if total == 0:
                # 尝试其他方式
                total = float(balance.get('total', {}).get('USDT', 0))
            return total if total > 0 else 100000  # 默认10万模拟资金
        except Exception as e:
            logger.warning(f"获取余额失败: {e}, 使用默认值")
            return 100000  # 默认10万
    
    def _genesis_close_all_positions(self) -> int:
        """清空所有持仓"""
        closed = 0
        try:
            positions = self.okx_trading.get_all_positions()
            for pos in positions:
                if float(pos.get('contracts', 0)) > 0:
                    closed += 1
            self.okx_trading.close_all_positions()
        except Exception as e:
            logger.warning(f"清空持仓异常: {e}")
        return closed
    
    def _genesis_calculate_allocation(self, total_capital: float, config: dict) -> tuple:
        """
        计算Agent数量和资金分配
        
        规则：
        1. 保留10%储备金
        2. 每个Agent至少5000 USDT
        3. Agent数量在5-20之间
        """
        reserve_ratio = config.get('capital_reserve_ratio', 0.1)
        min_per_agent = config.get('min_capital_per_agent', 5000)
        min_agents = config.get('min_agent_count', 5)
        max_agents = config.get('max_agent_count', 20)
        
        # 可分配资金 = 总资金 * (1 - 储备比例)
        available_capital = total_capital * (1 - reserve_ratio)
        
        # 计算最大可支持的Agent数量
        max_possible = int(available_capital / min_per_agent)
        
        # 限制在配置范围内
        agent_count = max(min_agents, min(max_agents, max_possible))
        
        # 计算每个Agent的资金
        capital_per_agent = available_capital / agent_count
        
        return agent_count, capital_per_agent
    
    def _genesis_set_trading_rules(self, capital_per_agent: float) -> dict:
        """设定交易规则"""
        return {
            'min_trade_amount': 0.01,  # 最小交易量(BTC)
            'max_trade_ratio': 0.1,    # 单笔最大占资金比例
            'max_position_ratio': 0.5, # 最大持仓占资金比例
            'stop_loss_ratio': 0.05,   # 止损线(5%)
            'take_profit_ratio': 0.1,  # 止盈线(10%)
        }
    
    def _genesis_fetch_market_history(self, days: int = 7):
        """获取历史市场数据"""
        try:
            # 获取日K线
            ohlcv = self.okx_trading.exchange.fetch_ohlcv(
                'BTC/USDT:USDT',
                timeframe='1d',
                limit=days + 1
            )
            
            import pandas as pd
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.warning(f"获取历史数据失败: {e}")
            return None
    
    def _genesis_analyze_market(self, market_data) -> dict:
        """分析市场趋势"""
        analysis = {
            'current_price': 0,
            'change_7d': 0,
            'trend': '未知',
            'volatility': 'medium',
            'support': 0,
            'resistance': 0
        }
        
        try:
            if market_data is not None and len(market_data) > 0:
                current_price = market_data['close'].iloc[-1]
                price_7d_ago = market_data['close'].iloc[0]
                
                change_7d = (current_price - price_7d_ago) / price_7d_ago * 100
                
                # 判断趋势（统一使用MarketState命名）
                if change_7d > 5:
                    trend = '强上升趋势'
                elif change_7d > 2:
                    trend = '弱上升趋势'
                elif change_7d > -2:
                    trend = '震荡'
                elif change_7d > -5:
                    trend = '弱下降趋势'
                else:
                    trend = '强下降趋势'
                
                analysis['current_price'] = current_price
                analysis['change_7d'] = change_7d
                analysis['trend'] = trend
                analysis['support'] = market_data['low'].min()
                analysis['resistance'] = market_data['high'].max()
                
                # 波动率
                daily_returns = market_data['close'].pct_change().dropna()
                volatility = daily_returns.std() * 100
                if volatility > 5:
                    analysis['volatility'] = 'high'
                elif volatility > 2:
                    analysis['volatility'] = 'medium'
                else:
                    analysis['volatility'] = 'low'
        except Exception as e:
            logger.warning(f"市场分析异常: {e}")
        
        return analysis
    
    def _genesis_publish_market_bulletin(self, market_analysis: dict):
        """发布市场公告"""
        if self.bulletin_board:
            self.bulletin_board.post(
                tier='market',
                title='🌅 创世市场报告',
                content={
                    'type': 'genesis_market_report',
                    'current_price': market_analysis['current_price'],
                    'trend': market_analysis['trend'],
                    'change_7d': market_analysis['change_7d'],
                    'volatility': market_analysis['volatility'],
                    'support': market_analysis['support'],
                    'resistance': market_analysis['resistance']
                },
                publisher='Supervisor',
                priority='high'
            )
    
    def _genesis_first_prophecy(self, market_data, market_analysis: dict) -> dict:
        """
        先知发布创世大预言 (Grand Prophecy)
        
        创世时的占卜使用大预言，进行全面深度分析
        """
        # 获取市场分析数据
        trend = market_analysis.get('trend', '')
        change_7d = market_analysis.get('change_7d', 0)
        volatility = market_analysis.get('volatility', '正常')
        
        # 计算看涨得分（基于7日涨跌幅和趋势）
        if '强' in trend and '上涨' in trend:
            bullish_score = 0.8
            trend_forecast = '强烈看涨'
        elif '上涨' in trend:
            bullish_score = 0.65
            trend_forecast = '看涨'
        elif '强' in trend and '下跌' in trend:
            bullish_score = 0.2
            trend_forecast = '强烈看跌'
        elif '下跌' in trend:
            bullish_score = 0.35
            trend_forecast = '看跌'
        else:
            bullish_score = 0.5
            trend_forecast = '震荡'
        
        # 计算预测信心度
        forecast_confidence = abs(bullish_score - 0.5) * 2 + 0.5  # 0.5~1.0
        
        # 交易量预测（基于波动率）
        if volatility in ['高波动', '极高波动']:
            volume_forecast = '放量'
            volume_intensity = 'high'
        elif volatility == '低波动':
            volume_forecast = '缩量'
            volume_intensity = 'low'
        else:
            volume_forecast = '正常'
            volume_intensity = 'normal'
        
        # 风险评估
        risk_factors = []
        if volatility in ['高波动', '极高波动']:
            risk_factors.append('高波动风险')
        if abs(change_7d) > 10:
            risk_factors.append('近期波动剧烈')
        
        risk_level = 'high' if len(risk_factors) >= 2 else ('medium' if risk_factors else 'low')
        
        # 评估环境压力（v4.1 OGAE - 创世版本）
        # 创世时只基于市场数据，无Agent表现数据
        pressure_factors = []
        
        # 市场波动
        if volatility in ['极高波动']:
            pressure_factors.append(0.8)
        elif volatility in ['高波动']:
            pressure_factors.append(0.6)
        elif volatility in ['低波动']:
            pressure_factors.append(0.2)
        else:
            pressure_factors.append(0.3)
        
        # 价格剧变
        if abs(change_7d) > 15:
            pressure_factors.append(0.9)
        elif abs(change_7d) > 10:
            pressure_factors.append(0.7)
        elif abs(change_7d) > 5:
            pressure_factors.append(0.4)
        else:
            pressure_factors.append(0.2)
        
        environmental_pressure = sum(pressure_factors) / len(pressure_factors) if pressure_factors else 0.3
        
        # 压力描述
        if environmental_pressure < 0.3:
            pressure_level = "low"
            pressure_desc = "平静如水🌊"
        elif environmental_pressure < 0.6:
            pressure_level = "medium"
            pressure_desc = "波涛渐起⚡"
        elif environmental_pressure < 0.8:
            pressure_level = "high"
            pressure_desc = "狂风暴雨🌪️"
        else:
            pressure_level = "extreme"
            pressure_desc = "末日浩劫💀"
        
        # 构建创世大预言
        prophecy = {
            'type': 'prophecy',
            'prophecy_level': 'grand',  # 大预言
            
            # 走势预测
            'trend_forecast': trend_forecast,
            'forecast_confidence': forecast_confidence,
            'bullish_score': bullish_score,
            
            # 交易量预测
            'volume_forecast': volume_forecast,
            'volume_intensity': volume_intensity,
            
            # 市场状态
            'market_reading': {
                'trend': trend,
                'trend_strength': bullish_score,
                'momentum': '中性',
                'momentum_score': 0.5,
                'volatility': volatility,
            },
            
            # 历史分析（大预言特有）
            'historical_analysis': {
                'change_7d': change_7d,
                'change_24h': 0,
                'price_position': 0.5,
                'trend_consistency': 0.5
            },
            
            # 风险评估
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            
            # 环境压力（v4.1新增）
            'environmental_pressure': environmental_pressure,
            'pressure_level': pressure_level,
            'pressure_description': pressure_desc,
            
            # 优秀Agent参考（创世时为空）
            'top_performers': [],
            
            # 时间戳
            'timestamp': datetime.now().isoformat(),
            
            # 下次大预言时间
            'next_grand_prophecy': (datetime.now() + timedelta(hours=8)).isoformat()
        }
        
        # 记录大预言时间
        self.last_grand_prophecy_time = datetime.now()
        
        try:
            # 发布到公告板
            if self.bulletin_board:
                self.bulletin_board.post(
                    tier='strategic',
                    title=f"📜 创世大预言: {trend_forecast}",
                    content=prophecy,
                    publisher='Mastermind',
                    priority='high'
                )
            
            logger.info(f"📜 创世大预言: {trend_forecast}(信心:{forecast_confidence:.0%}) | 量能:{volume_forecast} | 风险:{risk_level} | 压力:{environmental_pressure:.2f}({pressure_desc})")
                
        except Exception as e:
            logger.warning(f"创世占卜异常: {e}")
        
        return prophecy
    
    def _genesis_create_gene_pool(self, count: int, market_analysis: dict) -> list:
        """
        生成Agent基因库（v4.1：使用简化的可进化基因）
        
        创世时只有3个核心参数，通过进化逐步增加复杂度
        """
        from prometheus.core.evolvable_gene import EvolvableGene
        
        gene_pool = []
        trend = market_analysis.get('trend', '')
        
        logger.info(f"      使用可进化基因系统（创世：3参数）")
        
        # 生成多样化的创世基因
        for i in range(count):
            gene = EvolvableGene.create_genesis()
            gene_pool.append(gene)
        
        # 根据市场趋势调整初始参数倾向（微调）
        if '上涨' in trend:
            # 上涨市场：提升risk_appetite和trend_pref
            aggressive_count = int(count * 0.6)
            balanced_count = int(count * 0.3)
            conservative_count = count - aggressive_count - balanced_count
        elif '下跌' in trend:
            # 下跌市场：降低risk_appetite
            aggressive_count = int(count * 0.1)
            balanced_count = int(count * 0.3)
            conservative_count = count - aggressive_count - balanced_count
        else:
            # 震荡市场：平衡分布
            aggressive_count = count // 3
            balanced_count = count // 3
            conservative_count = count - aggressive_count - balanced_count
        
        # v4.1: 创世基因已生成，轻微标记类型（保持多样性）
        import random
        
        # 只对激进型和保守型做非常轻微的标记，保持基因多样性
        # 激进型：轻微提升（只调整10%）
        for i in range(min(aggressive_count, len(gene_pool))):
            if random.random() < 0.1:  # 只有10%概率调整
                gene_pool[i].active_params['risk_appetite'] = min(1.0, gene_pool[i].active_params.get('risk_appetite', 0.5) * 1.1)
        
        # 平衡型：完全保持原样
        # （不做任何调整，保持基因原始多样性）
        
        # 保守型：轻微降低（只调整10%）
        for i in range(aggressive_count + balanced_count, count):
            if i < len(gene_pool) and random.random() < 0.1:  # 只有10%概率调整
                gene_pool[i].active_params['risk_appetite'] = max(0.0, gene_pool[i].active_params.get('risk_appetite', 0.5) * 0.9)
        
        logger.info(f"      激进型: {aggressive_count}, 平衡型: {balanced_count}, 保守型: {conservative_count}")
        
        return gene_pool
    
    def _genesis_create_agents(self, count: int, gene_pool: list, 
                               capital: float, agent_factory=None) -> list:
        """创建Agent实体（v4.1：支持EvolvableGene）"""
        from prometheus.core.agent_v4 import AgentV4
        from prometheus.core.evolvable_gene import EvolvableGene
        
        agents = []
        
        for i in range(count):
            agent_id = f"Agent_{i+1:02d}"
            gene = gene_pool[i] if i < len(gene_pool) else gene_pool[-1]
            
            if agent_factory:
                # 使用工厂函数
                agent = agent_factory(agent_id, gene, capital)
            else:
                # 默认创建（v4.1：直接传入EvolvableGene对象）
                agent = AgentV4(
                    agent_id=agent_id,
                    gene=gene,  # ← v4.1: 直接传入EvolvableGene对象
                    personality=None,
                    initial_capital=capital,
                    bulletin_board=self.bulletin_board
                )
                
                # 确保Agent有顿悟计数器
                if not hasattr(agent, 'epiphany_count'):
                    agent.epiphany_count = 0
            
            agents.append(agent)
            
            # 更新next_agent_id
            self.next_agent_id = max(self.next_agent_id, i + 2)
        
        return agents
    
    def _genesis_setup_ledgers(self, agents: list, capital: float):
        """为Agent设置账簿系统"""
        self.public_ledger = PublicLedger()
        self.ledger_reconciler = LedgerReconciler()
        self.agent_accounts.clear()
        
        for agent in agents:
            agent_id = getattr(agent, 'agent_id', 'unknown')
            account_system = AgentAccountSystem(
                agent_id=agent_id,
                initial_capital=capital,
                public_ledger=self.public_ledger
            )
            self.agent_accounts[agent_id] = account_system
            agent.account = account_system
    
    def run(self, duration_minutes=None, check_interval=60, log_file=None):
        """
        Supervisor主循环(完整运营系统)
        
        这是Supervisor作为"完整运营系统"的核心方法
        
        Args:
            duration_minutes: 运行时长(分钟),None表示不限时
            check_interval: 检查间隔(秒)
            log_file: 日志文件路径
        """
        from datetime import timedelta
        import ccxt
        import sys
        
        # 设置日志输出
        self.log_file = log_file
        if log_file:
            # 同时输出到文件和控制台
            self.log_handler = open(log_file, 'w', encoding='utf-8', buffering=1)
            logger.info(f"📝 日志文件: {log_file}")
        else:
            self.log_handler = None
        
        # 彻夜运行：简化启动日志
        logger.info(f"Supervisor启动: {len(self.agents)}个Agent, 间隔{check_interval}秒")
        
        # 输出到控制台和日志文件
        self._log_print(f"\n{'='*70}")
        self._log_print(f"🏃 Supervisor完整运营系统启动")
        self._log_print(f"   Agent数量: {len(self.agents)}")
        self._log_print(f"   检查间隔: {check_interval}秒")
        if duration_minutes:
            self._log_print(f"   运行时长: {duration_minutes}分钟")
        else:
            self._log_print(f"   运行时长: 不限时 (按Ctrl+C停止)")
        if log_file:
            self._log_print(f"   日志文件: {log_file}")
        self._log_print(f"{'='*70}\n")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        cycle_count = 0
        
        # ========== 启动时对账检查（如果未经过创世则执行）==========
        if not hasattr(self, 'genesis_time') or self.genesis_time is None:
            self._log_print(f"\n🔍 启动对账检查（未经创世）...")
            try:
                reconcile_result = self.reconcile_with_okx()
                unclaimed = reconcile_result.get('unclaimed_closed', [])
                if unclaimed:
                    self._log_print(f"   ⚠️  平仓{len(unclaimed)}笔无人认领持仓")
                    for item in unclaimed:
                        self._log_print(f"      - {item['symbol']}: {item['amount']} ({item['action']})")
                else:
                    self._log_print(f"   ✅ 无人认领持仓检查通过")
            except Exception as e:
                self._log_print(f"   ⚠️  对账检查失败: {e}")
        else:
            self._log_print(f"\n✅ 已通过创世初始化 @ {self.genesis_time.strftime('%H:%M:%S')}")
        
        try:
            while True:
                # 检查是否超时
                if end_time and datetime.now() >= end_time:
                    self._log_print("\n⏰ 运行时间已到,正常结束")
                    break
                
                cycle_count += 1
                current_time = datetime.now()
                
                self._log_print(f"\n{'='*70}")
                self._log_print(f"  🔄 周期 {cycle_count} | {current_time.strftime('%H:%M:%S')}")
                self._log_print(f"{'='*70}")
                
                try:
                    # 1. 获取市场数据
                    market_data = self._fetch_market_data_from_okx()
                    if market_data is None or len(market_data) < 25:
                        self._log_print("⚠️  市场数据不足,等待下一周期...")
                        time.sleep(check_interval)
                        continue
                    
                    current_price = market_data['close'].iloc[-1]
                    self._log_print(f"\n📊 当前价格: ${current_price:.2f}")
                    
                    # 2. Supervisor分析市场并发布
                    self.comprehensive_monitoring(market_data)
                    
                    # 3. Mastermind占卜（区分大小预言）
                    if self.mastermind:
                        # 检查是否需要执行大预言（创世后首次、每8小时、固定时间点）
                        if self._should_execute_grand_prophecy():
                            self._log_print("\n📜 【大预言】 Grand Prophecy")
                            self._execute_mastermind_strategy(market_data, prophecy_type='grand')
                        # 小预言：每个周期都执行（实时性最强）
                        else:
                            self._execute_mastermind_strategy(market_data, prophecy_type='minor')
                    
                    # 4. 收集Agent决策（传入持仓状态）
                    self._log_print(f"\n🤖 【Agents】自主决策模式")
                    agent_decisions = []
                    for agent in self.agents:
                        try:
                            # 获取Agent的持仓状态
                            agent_id = agent.agent_id
                            account = self.agent_accounts.get(agent_id)
                            
                            has_position = False
                            unrealized_pnl_pct = 0.0
                            
                            # 获取Agent的完整状态
                            position_amount = 0.0
                            balance = 10000.0
                            initial_capital = 10000.0
                            trade_count = 0
                            
                            if account:
                                status = account.get_status_for_decision(
                                    current_price,
                                    caller_role=Role.SUPERVISOR,
                                    caller_id='system'
                                )
                                has_position = status.get('has_position', False)
                                position_side = status.get('position_side')  # 'long', 'short', or None
                                balance = status.get('balance', 10000.0)
                                initial_capital = status.get('initial_capital', 10000.0)
                                trade_count = status.get('trade_count', 0)
                                
                                # 计算未实现盈亏百分比和持仓量（entry_price在position_info里）
                                if has_position:
                                    position_info = status.get('position_info', {})
                                    if position_info:
                                        entry_price = position_info.get('entry_price', 0)
                                        position_amount = position_info.get('amount', 0)
                                        if entry_price > 0:
                                            # 根据持仓方向计算盈亏
                                            if position_side == 'short':
                                                unrealized_pnl_pct = (entry_price - current_price) / entry_price
                                            else:
                                                unrealized_pnl_pct = (current_price - entry_price) / entry_price
                            
                            # 传入完整状态给Agent决策（包含持仓方向）
                            decision = agent.decide(
                                current_price=current_price,
                                has_position=has_position,
                                unrealized_pnl_pct=unrealized_pnl_pct,
                                position_amount=position_amount,
                                balance=balance,
                                initial_capital=initial_capital,
                                trade_count=trade_count,
                                position_side=position_side
                            )
                            
                            if decision and isinstance(decision, dict):
                                agent_decisions.append({
                                    'agent_id': agent_id,
                                    'signal': decision.get('signal'),
                                    'confidence': decision.get('confidence', 0.5),
                                    'reason': decision.get('reason', ''),
                                    'has_position': has_position,
                                    'suggested_amount': decision.get('suggested_amount', 0.01)  # Agent自主建议的交易量
                                })
                        except Exception as e:
                            logger.error(f"Agent {agent.agent_id} 决策失败: {e}")
                    
                    # 统计决策（包括做空信号）
                    buy_count = sum(1 for d in agent_decisions if d['signal'] == 'buy')
                    add_count = sum(1 for d in agent_decisions if d['signal'] == 'add')
                    sell_count = sum(1 for d in agent_decisions if d['signal'] == 'sell')
                    short_count = sum(1 for d in agent_decisions if d['signal'] == 'short')
                    add_short_count = sum(1 for d in agent_decisions if d['signal'] == 'add_short')
                    cover_count = sum(1 for d in agent_decisions if d['signal'] == 'cover')
                    wait_count = len(agent_decisions) - buy_count - add_count - sell_count - short_count - add_short_count - cover_count
                    
                    self._log_print(f"\n   📊 Agent决策分布:")
                    self._log_print(f"      🟢 开多: {buy_count}个 | 加多: {add_count}个 | 平多: {sell_count}个")
                    self._log_print(f"      🔴 开空: {short_count}个 | 加空: {add_short_count}个 | 平空: {cover_count}个")
                    self._log_print(f"      ⚪ 观望: {wait_count}个Agent")
                    
                    # 5. Supervisor接收并执行交易请求
                    self._log_print(f"\n💼 【交易执行】Supervisor接收Agent请求")
                    executed_count = 0
                    for decision in agent_decisions:
                        if decision['signal']:
                            success = self._receive_and_execute_trade(
                                agent_id=decision['agent_id'],
                                signal=decision['signal'],
                                confidence=decision['confidence'],
                                current_price=current_price,
                                suggested_amount=decision.get('suggested_amount', 0.01)  # 使用Agent建议量
                            )
                            if success:
                                executed_count += 1
                    
                    if executed_count == 0:
                        self._log_print(f"   ⏸️  本周期无交易执行")
                    else:
                        self._log_print(f"   ✅ 执行了{executed_count}笔交易")
                    
                    # 6. 更新虚拟盈亏
                    self._update_unrealized_pnl(current_price)
                    
                    # 6.5 检查顿悟触发（v4.1进化系统）
                    if hasattr(self, 'epiphany_system'):
                        for agent in self.agents:
                            try:
                                # 准备市场状态
                                market_state_dict = {
                                    'price_change_pct': (current_price - market_data['close'].iloc[-2]) / market_data['close'].iloc[-2] * 100 if len(market_data) > 1 else 0,
                                    'volatility': market_data['close'].pct_change().std() if len(market_data) > 1 else 0
                                }
                                
                                # 获取最近交易记录
                                recent_trades = []
                                if agent.agent_id in self.agent_accounts:
                                    account = self.agent_accounts[agent.agent_id]
                                    trade_history = account.private_ledger.get_trade_history(caller_role=Role.SUPERVISOR, caller_id='system')
                                    recent_trades = [{'pnl': t.pnl, 'profit_pct': getattr(t, 'profit_pct', 0)} for t in trade_history[-10:]]
                                
                                # 检查顿悟
                                self.epiphany_system.check_and_trigger(agent, market_state_dict, recent_trades)
                            except Exception as e:
                                logger.error(f"顿悟检查失败 {agent.agent_id}: {e}")
                    
                    # 7. 发布Agent表现报告(每5个周期，包含浮动盈亏)
                    if cycle_count % 5 == 0:
                        self._publish_performance_report(current_price)
                    
                    # 8. 定期OKX对账(每10个周期，完整三方校验)
                    if cycle_count % 10 == 0:
                        self._log_print(f"\n🔍 定期OKX对账检查...")
                        try:
                            okx_result = self.reconcile_with_okx()
                            unclaimed = okx_result.get('unclaimed_closed', [])
                            if unclaimed:
                                self._log_print(f"   ⚠️  平仓{len(unclaimed)}笔无人认领持仓")
                            else:
                                self._log_print(f"   ✅ OKX对账通过")
                        except Exception as e:
                            self._log_print(f"   ⚠️  OKX对账失败: {e}")
                    
                    # 8.5 进化周期（v4.2动态智能调度）
                    if self.evolution_manager and self.evolution_manager.should_run_evolution(cycle_count):
                        self._log_print(f"\n{'='*70}")
                        self._log_print(f"🧬 周期{cycle_count}：触发进化...")
                        self._log_print(f"{'='*70}")
                        
                        try:
                            self._log_print(f"   🧬 开始执行进化周期...")
                            self.evolution_manager.run_evolution_cycle(current_price)
                            self._log_print(f"   ✅ 进化周期完成")
                        except Exception as e:
                            logger.error(f"进化周期失败: {e}", exc_info=True)
                            self._log_print(f"   ⚠️  进化周期失败: {e}")
                        
                        self._log_print(f"{'='*70}\n")
                    
                    # 9. 等待下一周期
                    self._log_print(f"\n⏸️  等待 {check_interval}秒...")
                    time.sleep(check_interval)
                
                except KeyboardInterrupt:
                    raise  # 向外抛出,由外层捕获
                except Exception as e:
                    logger.error(f"周期 {cycle_count} 执行失败: {e}", exc_info=True)
                    self._log_print(f"⚠️  周期执行失败: {e}")
                    time.sleep(check_interval)
        
        except KeyboardInterrupt:
            self._log_print("\n\n⚠️  运营被用户中断")
        
        # 最终总结
        self._log_print(f"\n{'='*70}")
        self._log_print(f"🏁 Supervisor运营结束")
        self._log_print(f"{'='*70}")
        self._print_final_summary()
        
        # 关闭日志文件
        if hasattr(self, 'log_handler') and self.log_handler:
            self.log_handler.close()
            logger.info(f"📝 日志已保存: {self.log_file}")
    
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
    
    def _execute_mastermind_strategy(self, market_data, prophecy_type='minor'):
        """
        执行Mastermind占卜
        
        Args:
            market_data: 市场数据
            prophecy_type: 'grand'(大预言) 或 'minor'(小预言)
        """
        if not self.mastermind or not self.bulletin_board:
            logger.warning("Mastermind或BulletinBoard未初始化，跳过预言")
            return
        
        try:
            # Mastermind读取公共账簿(只读权限)
            top_performers = self.public_ledger.get_top_performers(
                limit=5, 
                caller_role=Role.MASTERMIND
            )
            
            # 准备Agent表现统计（v4.1 OGAE）
            agent_performance_stats = self._calculate_agent_performance_stats()
            
            # 执行占卜（区分大小预言）
            if prophecy_type == 'grand':
                # 大预言：需要历史数据
                historical_data = self._get_historical_data(days=7)
                prophecy = self.mastermind.grand_prophecy(
                    market_data=market_data,
                    current_market_state=self.current_market_state,
                    top_performers=top_performers,
                    historical_data=historical_data,
                    agent_performance_stats=agent_performance_stats
                )
                self.last_grand_prophecy_time = datetime.now()
                title_prefix = "📜 大预言"
            else:
                # 小预言：轻量级
                prophecy = self.mastermind.minor_prophecy(
                    market_data=market_data,
                    current_market_state=self.current_market_state,
                    top_performers=top_performers,
                    agent_performance_stats=agent_performance_stats
                )
                title_prefix = "🔮 小预言"
            
            # 发布占卜公告
            if prophecy:
                trend_forecast = prophecy.get('trend_forecast', '震荡')
                self.bulletin_board.post(
                    tier='strategic',
                    title=f"{title_prefix}: {trend_forecast}",
                    content=prophecy,
                    publisher='Mastermind',
                    priority='high' if prophecy_type == 'grand' else 'normal'
                )
                
                # Mastermind已经输出完整预言信息，这里不需要重复输出
                # 如果需要，可以在这里添加额外的监控日志
                
        except Exception as e:
            logger.error(f"Mastermind占卜失败: {e}")
    
    def _calculate_agent_performance_stats(self) -> Dict:
        """
        计算Agent集体表现统计（v4.1 OGAE）
        
        Returns:
            Dict: {
                'avg_pnl': 平均盈亏,
                'losing_ratio': 亏损Agent比例,
                'avg_drawdown': 平均回撤
            }
        """
        if not self.agents:
            return {'avg_pnl': 0, 'losing_ratio': 0, 'avg_drawdown': 0}
        
        try:
            total_pnl = 0
            losing_count = 0
            total_drawdown = 0
            valid_agents = 0
            
            for agent_id, account in self.agent_accounts.items():
                try:
                    status = account.get_status_for_decision()
                    pnl = status.get('realized_pnl', 0) + status.get('unrealized_pnl', 0)
                    total_pnl += pnl
                    
                    if pnl < 0:
                        losing_count += 1
                    
                    # 计算回撤
                    initial_capital = account.private_ledger.initial_capital
                    current_capital = account.private_ledger.current_capital
                    if initial_capital > 0:
                        drawdown = (current_capital - initial_capital) / initial_capital
                        total_drawdown += drawdown
                    
                    valid_agents += 1
                    
                except Exception as e:
                    logger.debug(f"计算Agent {agent_id} 统计失败: {e}")
                    continue
            
            if valid_agents == 0:
                return {'avg_pnl': 0, 'losing_ratio': 0, 'avg_drawdown': 0}
            
            return {
                'avg_pnl': total_pnl / valid_agents,
                'losing_ratio': losing_count / valid_agents,
                'avg_drawdown': total_drawdown / valid_agents
            }
            
        except Exception as e:
            logger.error(f"计算Agent表现统计失败: {e}")
            return {'avg_pnl': 0, 'losing_ratio': 0, 'avg_drawdown': 0}
    
    def _should_execute_grand_prophecy(self) -> bool:
        """
        判断是否应该执行大预言
        
        执行时机：
        1. 从未执行过大预言
        2. 距离上次大预言超过8小时
        3. 到达固定时间点（00:00, 08:00, 16:00）
        """
        if not hasattr(self, 'last_grand_prophecy_time') or self.last_grand_prophecy_time is None:
            return True
        
        now = datetime.now()
        hours_since_last = (now - self.last_grand_prophecy_time).total_seconds() / 3600
        
        # 超过8小时
        if hours_since_last >= 8:
            return True
        
        # 到达固定时间点（00:00, 08:00, 16:00）
        current_hour = now.hour
        if current_hour in [0, 8, 16]:
            # 检查这个时间点是否已经执行过
            last_hour = self.last_grand_prophecy_time.hour
            if current_hour != last_hour:
                return True
        
        return False
    
    def _get_historical_data(self, days=7):
        """获取历史市场数据"""
        try:
            if self.okx_trading:
                # 获取过去N天的K线数据
                since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
                ohlcv = self.okx_trading.exchange.fetch_ohlcv(
                    'BTC/USDT:USDT', 
                    timeframe='1h',
                    since=since,
                    limit=days * 24
                )
                if ohlcv:
                    import pandas as pd
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    return df
        except Exception as e:
            logger.warning(f"获取历史数据失败: {e}")
        return None
    
    def _receive_and_execute_trade(self, agent_id, signal, confidence, current_price, suggested_amount=0.01):
        """
        接收并执行Agent的交易请求
        
        支持的信号：
        - 'buy': 开多（无持仓时）
        - 'add': 加多（有多仓时）
        - 'sell': 平多
        - 'short': 开空（无持仓时）
        - 'add_short': 加空（有空仓时）
        - 'cover': 平空
        
        Args:
            suggested_amount: Agent建议的交易量（BTC），由Agent根据性格和信心自主决定
        """
        account = self.agent_accounts.get(agent_id)
        if not account:
            logger.error(f"{agent_id}: 账户不存在")
            return False
        
        # 检查持仓状态(从私有账簿)
        status = account.get_status_for_decision(
            current_price,
            caller_role=Role.SUPERVISOR,
            caller_id='system'
        )
        
        has_position = status.get('has_position', False)
        position_side = status.get('position_side')  # 'long', 'short', or None
        
        # 校验并限制交易量（Supervisor把关）
        trade_amount = max(0.01, min(0.1, suggested_amount))  # 限制在0.01~0.1 BTC
        trade_amount = round(trade_amount, 2)  # 保留2位小数
        
        try:
            # ========== 开多（双向持仓：可与空仓并存）==========
            if signal == 'buy':
                # 双向持仓模式：检查是否已有多头持仓
                long_pos = status.get('long_position')
                if long_pos and long_pos.get('amount', 0) > 0:
                    logger.debug(f"{agent_id}: 已有多仓，请使用add加多")
                    return False
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='buy',
                    amount=trade_amount,
                    reduce_only=False,
                    pos_side='long'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='buy',
                        amount=trade_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 开多 {trade_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
                    return True
            
            # ========== 加多（双向持仓：只检查多仓）==========
            elif signal == 'add':
                # 双向持仓模式：只检查多头持仓
                long_pos = status.get('long_position')
                if not long_pos or long_pos.get('amount', 0) == 0:
                    logger.debug(f"{agent_id}: 无多仓,无法加多")
                    return False
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='buy',
                    amount=trade_amount,
                    reduce_only=False,
                    pos_side='long'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='buy',
                        amount=trade_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 加多 {trade_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
                    return True
            
            # ========== 平多 ==========
            elif signal == 'sell':
                if not has_position:
                    logger.debug(f"{agent_id}: 无持仓,拒绝平多")
                    return False
                
                if position_side != 'long':
                    logger.debug(f"{agent_id}: 当前是空仓,请使用cover平空")
                    return False
                
                position_info = status.get('position_info', {})
                position_amount = position_info.get('amount', 0.01) if position_info else 0.01
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='sell',
                    amount=position_amount,
                    reduce_only=True,
                    pos_side='long'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='sell',
                        amount=position_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 平多 {position_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
                    return True
            
            # ========== 开空（双向持仓：可与多仓并存）==========
            elif signal == 'short':
                # 双向持仓模式：检查是否已有空头持仓
                short_pos = status.get('short_position')
                if short_pos and short_pos.get('amount', 0) > 0:
                    logger.debug(f"{agent_id}: 已有空仓，请使用add_short加空")
                    return False
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='sell',
                    amount=trade_amount,
                    reduce_only=False,
                    pos_side='short'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='short',
                        amount=trade_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 开空 {trade_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
                    return True
            
            # ========== 加空（双向持仓：只检查空仓）==========
            elif signal == 'add_short':
                # 双向持仓模式：只检查空头持仓
                short_pos = status.get('short_position')
                if not short_pos or short_pos.get('amount', 0) == 0:
                    logger.debug(f"{agent_id}: 无空仓,无法加空")
                    return False
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='sell',
                    amount=trade_amount,
                    reduce_only=False,
                    pos_side='short'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='short',
                        amount=trade_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 加空 {trade_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
                    return True
            
            # ========== 平空 ==========
            elif signal == 'cover':
                if not has_position:
                    logger.debug(f"{agent_id}: 无持仓,拒绝平空")
                    return False
                
                if position_side != 'short':
                    logger.debug(f"{agent_id}: 当前是多仓,请使用sell平多")
                    return False
                
                position_info = status.get('position_info', {})
                position_amount = position_info.get('amount', 0.01) if position_info else 0.01
                
                order = self.okx_trading.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='buy',  # 平空用buy
                    amount=position_amount,
                    reduce_only=True,
                    pos_side='short'
                )
                
                if order and order.get('status') in ['closed', 'filled', None]:
                    # 提取OKX实际成交信息
                    actual_price = order.get('average') or order.get('price') or current_price
                    okx_order_id = order.get('id', '')
                    
                    account.record_trade(
                        trade_type='cover',
                        amount=position_amount,
                        price=actual_price,  # ✅ 使用实际成交价
                        confidence=confidence,
                        is_real=True,
                        caller_role=Role.SUPERVISOR,
                        okx_order_id=okx_order_id  # ✅ 传递订单ID
                    )
                    logger.info(f"✅ {agent_id}: 平空 {position_amount} BTC @ ${actual_price:.2f} (OKX:{okx_order_id[:8]})")
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
    
    def _publish_performance_report(self, current_price: float = 0):
        """发布Agent表现报告（包含未实现盈亏）并发布到公告板"""
        try:
            # 使用新的排名方法（包含未实现盈亏）
            rankings = self.rank_agent_performance(current_price)
            
            if not rankings:
                return
            
            # ========== 1. 控制台输出 ==========
            self._log_print(f"\n{'='*70}")
            self._log_print(f"📊 Agent表现排名 (含浮动盈亏)")
            self._log_print(f"{'='*70}")
            
            # 显示所有Agent（最多显示前20）
            for i, (agent_id, data) in enumerate(rankings[:20], 1):
                total_pnl = data.get('total_pnl', 0)
                realized_pnl = data.get('realized_pnl', 0)      # 实盈
                unrealized_pnl = data.get('unrealized_pnl', 0)  # 浮盈
                trade_count = data.get('trade_count', 0)
                
                # 双向持仓：分别显示多空持仓
                long_amount = data.get('long_position_amount', 0)
                short_amount = data.get('short_position_amount', 0)
                
                # 构建持仓显示字符串
                position_parts = []
                if long_amount > 0:
                    position_parts.append(f"多{long_amount:.2f}")
                if short_amount > 0:
                    position_parts.append(f"空{short_amount:.2f}")
                
                if position_parts:
                    position_str = " | ".join(position_parts) + "BTC"
                elif trade_count > 0:
                    position_str = "已平仓"  # 有交易记录但无持仓 = 已平仓
                else:
                    position_str = "未交易"  # 无交易记录 = 从未交易
                
                # 构建PnL显示字符串（包含实盈和浮盈分解）
                pnl_str = f"PnL=${total_pnl:+.2f} (实${realized_pnl:+.2f}|浮${unrealized_pnl:+.2f})"
                
                self._log_print(
                    f"  {i:2d}. {agent_id}: {pnl_str} | {position_str} | {trade_count}笔"
                )
            
            self._log_print(f"{'='*70}")
            
            # ========== 2. 发布到公告板（为未来功能预留） ==========
            if self.bulletin_board:
                self._publish_rankings_to_bulletin(rankings, current_price)
        
        except Exception as e:
            logger.error(f"发布表现报告失败: {e}")
    
    def _publish_rankings_to_bulletin(self, rankings: List[Tuple], current_price: float):
        """
        发布排名数据到公告板
        
        为以下未来功能预留接口：
        1. Mastermind策略参考：根据Agent群体表现调整预言
        2. Agent学习机制：Agent可参考优秀同伴策略
        3. 进化系统：淘汰表现差的Agent，繁殖优秀Agent
        4. 历史分析：追溯排名变化趋势
        """
        try:
            # 计算群体统计
            total_agents = len(rankings)
            all_pnl = [r[1].get('total_pnl', 0) for r in rankings]
            all_win_rates = [r[1].get('win_rate', 0) for r in rankings]
            
            # 持仓分布（双向持仓：可同时持有多空）
            long_count = sum(1 for r in rankings if r[1].get('long_position_amount', 0) > 0)
            short_count = sum(1 for r in rankings if r[1].get('short_position_amount', 0) > 0)
            both_count = sum(1 for r in rankings if r[1].get('long_position_amount', 0) > 0 and r[1].get('short_position_amount', 0) > 0)
            empty_count = sum(1 for r in rankings if r[1].get('long_position_amount', 0) == 0 and r[1].get('short_position_amount', 0) == 0)
            
            # 盈亏分布
            profitable_count = sum(1 for pnl in all_pnl if pnl > 0)
            losing_count = sum(1 for pnl in all_pnl if pnl < 0)
            breakeven_count = total_agents - profitable_count - losing_count
            
            # 构建完整排名数据
            full_rankings = []
            for rank, (agent_id, data) in enumerate(rankings, 1):
                full_rankings.append({
                    'rank': rank,
                    'agent_id': agent_id,
                    'score': data.get('score', 0),
                    # 盈亏信息（实盈+浮盈）
                    'total_pnl': data.get('total_pnl', 0),
                    'realized_pnl': data.get('realized_pnl', 0),      # 实盈
                    'unrealized_pnl': data.get('unrealized_pnl', 0),  # 浮盈
                    'roi_pct': data.get('total_roi_pct', 0),
                    'win_rate': data.get('win_rate', 0),
                    'trade_count': data.get('trade_count', 0),
                    # 兼容：主要持仓
                    'has_position': data.get('has_position', False),
                    'position_amount': data.get('position_amount', 0),
                    'entry_price': data.get('entry_price', 0),
                    # 双向持仓详细信息
                    'long_position': {
                        'amount': data.get('long_position_amount', 0),
                        'entry_price': data.get('long_entry_price', 0),
                    },
                    'short_position': {
                        'amount': data.get('short_position_amount', 0),
                        'entry_price': data.get('short_entry_price', 0),
                    },
                })
            
            # 进化信号（为未来功能预留）
            evolution_signals = {
                # 繁殖候选：前20%表现优异的Agent
                'breed_candidates': [r['agent_id'] for r in full_rankings[:max(1, total_agents // 5)]],
                # 淘汰候选：后20%表现最差的Agent
                'eliminate_candidates': [r['agent_id'] for r in full_rankings[-max(1, total_agents // 5):]],
                # 观察名单：连续亏损或长期不交易
                'watch_list': [r['agent_id'] for r in full_rankings if r['total_pnl'] < -10 or r['trade_count'] == 0],
            }
            
            # 发布到公告板
            self.bulletin_board.post(
                tier='system',
                title='📊 Agent排名报告',
                content={
                    'type': 'AGENT_RANKINGS',
                    'timestamp': datetime.now().isoformat(),
                    'current_price': current_price,
                    
                    # 完整排名（供Agent和Mastermind参考）
                    'rankings': full_rankings,
                    
                    # 前3名详情（供快速参考）
                    'top_performers': full_rankings[:3],
                    
                    # 后3名详情（供淘汰决策）
                    'bottom_performers': full_rankings[-3:] if len(full_rankings) >= 3 else full_rankings,
                    
                    # 群体统计（供Mastermind宏观决策）
                    'population_stats': {
                        'total_agents': total_agents,
                        'avg_pnl': sum(all_pnl) / total_agents if total_agents > 0 else 0,
                        'total_pnl': sum(all_pnl),
                        'max_pnl': max(all_pnl) if all_pnl else 0,
                        'min_pnl': min(all_pnl) if all_pnl else 0,
                        'avg_win_rate': sum(all_win_rates) / total_agents if total_agents > 0 else 0,
                        'profitable_agents': profitable_count,
                        'losing_agents': losing_count,
                        'breakeven_agents': breakeven_count,
                    },
                    
                    # 持仓分布（供市场情绪分析，支持双向持仓）
                    'position_distribution': {
                        'long_count': long_count,           # 持有多仓的Agent数
                        'short_count': short_count,         # 持有空仓的Agent数
                        'both_count': both_count,           # 同时持有多空的Agent数
                        'empty_count': empty_count,         # 空仓Agent数
                        'long_ratio': long_count / total_agents if total_agents > 0 else 0,
                        'short_ratio': short_count / total_agents if total_agents > 0 else 0,
                        'both_ratio': both_count / total_agents if total_agents > 0 else 0,
                    },
                    
                    # 进化信号（供未来进化系统使用）
                    'evolution_signals': evolution_signals,
                },
                publisher='Supervisor',
                priority='normal'
            )
            
            logger.debug(f"排名报告已发布到公告板: {total_agents}个Agent, 盈利{profitable_count}个")
            
        except Exception as e:
            logger.error(f"发布排名到公告板失败: {e}")
    
    def _print_final_summary(self):
        """打印最终总结"""
        try:
            all_stats = self.public_ledger.get_all_agent_stats(
                caller_role=Role.SUPERVISOR
            )
            
            self._log_print(f"\n{'='*70}")
            self._log_print(f"📊 最终统计")
            self._log_print(f"{'='*70}")
            self._log_print(f"活跃Agent: {len(all_stats)}")
            
            if all_stats:
                total_pnl = sum(stats.get('total_pnl', 0) for stats in all_stats.values())
                avg_pnl = total_pnl / len(all_stats)
                self._log_print(f"总盈亏: ${total_pnl:.2f}")
                self._log_print(f"平均盈亏: ${avg_pnl:.2f}")
            
            self._log_print(f"{'='*70}")
        except Exception as e:
            logger.error(f"打印最终总结失败: {e}")

