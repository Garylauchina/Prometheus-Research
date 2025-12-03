"""
主脑 (Mastermind) - Prometheus v4.0
系统的最高决策层，负责战略规划和全局调控
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
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
                 llm_model: Optional[str] = None,
                 bulletin_board=None,
                 nirvana_system=None):
        """
        初始化主脑
        
        Args:
            initial_capital: 系统初始总资金
            decision_mode: 决策模式 ("llm"[默认], "human", "hybrid")
            llm_model: LLM模型名称（用于LLM模式）
            bulletin_board: 公告板系统（v4）
            nirvana_system: 涅槃系统
            
        Note:
            v4.0 以LLM先知为主要决策模式，人工基本不参与
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.strategy = GlobalStrategy()
        self.market_regime = MarketRegime.UNKNOWN
        self.decision_mode = decision_mode
        
        # v4.0 系统集成
        self.bulletin_board = bulletin_board
        self.nirvana_system = nirvana_system
        
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
    
    def make_decision(self, market_data=None, current_market_state=None, 
                      top_performers=None, prophecy_type='minor') -> Optional[Dict]:
        """
        先知占卜统一接口（供Supervisor调用）
        
        Args:
            market_data: 市场数据
            current_market_state: 当前市场状态
            top_performers: 表现最好的Agent列表
            prophecy_type: 'grand'(大预言) 或 'minor'(小预言)
            
        Returns:
            Dict: 占卜结果
        """
        if prophecy_type == 'grand':
            return self.grand_prophecy(market_data, current_market_state, top_performers)
        else:
            return self.minor_prophecy(market_data, current_market_state, top_performers)
    
    def evaluate_environmental_pressure(self, market_data=None, current_market_state=None,
                                       agent_performance_stats=None) -> float:
        """
        评估环境压力指数（v4.1 OGAE系统）
        
        环境压力指数用于触发进化系统的自适应调整。
        压力越高，进化系统变异率越高，淘汰率越低，以快速适应环境变化。
        
        Args:
            market_data: 市场历史数据
            current_market_state: 当前市场状态
            agent_performance_stats: Agent表现统计 {avg_pnl, losing_ratio, avg_drawdown, etc.}
        
        Returns:
            float: 环境压力指数（0-1）
                0.0-0.3: 低压力（平静如水🌊）
                0.3-0.6: 中压力（波涛渐起⚡）
                0.6-0.8: 高压力（狂风暴雨🌪️）
                0.8-1.0: 极端压力（末日浩劫💀）
        """
        import numpy as np
        
        pressure_factors = {}
        
        try:
            # ========== 因素1：市场波动率（30%权重）==========
            if market_data is not None and hasattr(market_data, 'close'):
                # 计算最近的价格波动率
                returns = market_data['close'].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std()
                    # 归一化：5%以上视为高波动
                    volatility_score = min(1.0, volatility / 0.05)
                    pressure_factors['volatility'] = volatility_score
                else:
                    pressure_factors['volatility'] = 0.2
            elif current_market_state and hasattr(current_market_state, 'volatility'):
                # 使用MarketState中的volatility
                vol_str = str(current_market_state.volatility).lower()
                if 'high' in vol_str or '高' in vol_str:
                    pressure_factors['volatility'] = 0.8
                elif 'low' in vol_str or '低' in vol_str:
                    pressure_factors['volatility'] = 0.2
                else:
                    pressure_factors['volatility'] = 0.4
            else:
                pressure_factors['volatility'] = 0.3
            
            # ========== 因素2：价格剧烈变化（25%权重）==========
            if market_data is not None and hasattr(market_data, 'close') and len(market_data) > 1:
                # 最近一次价格变化
                recent_change = abs(market_data['close'].pct_change().iloc[-1])
                # 归一化：10%以上视为剧烈变化
                price_shock_score = min(1.0, recent_change / 0.10)
                pressure_factors['price_shock'] = price_shock_score
            else:
                pressure_factors['price_shock'] = 0.2
            
            # ========== 因素3：趋势反转（20%权重）==========
            trend_reversal_detected = False
            if market_data is not None and hasattr(market_data, 'close') and len(market_data) > 10:
                # 简单趋势反转检测：短期MA穿越长期MA
                short_ma = market_data['close'].rolling(5).mean()
                long_ma = market_data['close'].rolling(20).mean()
                
                if len(short_ma) >= 2 and len(long_ma) >= 2:
                    # 检查最近是否发生穿越
                    prev_above = short_ma.iloc[-2] > long_ma.iloc[-2]
                    curr_above = short_ma.iloc[-1] > long_ma.iloc[-1]
                    trend_reversal_detected = (prev_above != curr_above)
            
            pressure_factors['trend_reversal'] = 0.8 if trend_reversal_detected else 0.2
            
            # ========== 因素4：Agent集体表现（25%权重）==========
            if agent_performance_stats:
                avg_pnl = agent_performance_stats.get('avg_pnl', 0)
                losing_ratio = agent_performance_stats.get('losing_ratio', 0)
                avg_drawdown = agent_performance_stats.get('avg_drawdown', 0)
                
                # 多个负面指标叠加
                collective_stress = 0
                
                # 平均盈亏严重负值
                if avg_pnl < -5000:
                    collective_stress += 0.4
                elif avg_pnl < -2000:
                    collective_stress += 0.2
                
                # 大部分Agent亏损
                if losing_ratio > 0.8:
                    collective_stress += 0.4
                elif losing_ratio > 0.6:
                    collective_stress += 0.2
                
                # 平均回撤严重
                if avg_drawdown and avg_drawdown < -0.3:
                    collective_stress += 0.3
                elif avg_drawdown and avg_drawdown < -0.2:
                    collective_stress += 0.15
                
                pressure_factors['collective_failure'] = min(1.0, collective_stress)
            else:
                pressure_factors['collective_failure'] = 0.3
            
            # ========== 综合压力指数 ==========
            pressure = (
                0.30 * pressure_factors.get('volatility', 0.3) +
                0.25 * pressure_factors.get('price_shock', 0.2) +
                0.20 * pressure_factors.get('trend_reversal', 0.2) +
                0.25 * pressure_factors.get('collective_failure', 0.3)
            )
            
            # 平滑处理（避免突变）
            if hasattr(self, 'last_pressure'):
                pressure = 0.7 * pressure + 0.3 * self.last_pressure
            self.last_pressure = pressure
            
            # 压力描述
            if pressure < 0.3:
                pressure_desc = "平静如水🌊"
            elif pressure < 0.6:
                pressure_desc = "波涛渐起⚡"
            elif pressure < 0.8:
                pressure_desc = "狂风暴雨🌪️"
            else:
                pressure_desc = "末日浩劫💀"
            
            # 环境压力已经在小预言中输出，这里只保留debug级别详细信息
            logger.debug(f"🌍 环境压力评估: {pressure:.2f} ({pressure_desc})")
            logger.debug(f"   压力因素: 波动{pressure_factors.get('volatility', 0):.2f} | "
                        f"价格{pressure_factors.get('price_shock', 0):.2f} | "
                        f"反转{pressure_factors.get('trend_reversal', 0):.2f} | "
                        f"集体{pressure_factors.get('collective_failure', 0):.2f}")
            
            return pressure
            
        except Exception as e:
            logger.error(f"环境压力评估失败: {e}")
            return 0.3  # 默认中低压力
    
    def minor_prophecy(self, market_data=None, current_market_state=None,
                       top_performers=None, agent_performance_stats=None) -> Optional[Dict]:
        """
        小预言 (Minor Prophecy) - 每个交易周期执行
        
        轻量级分析，关注短期走势
        执行频率：每3-5个交易周期（约1分钟）
        
        Args:
            market_data: 市场数据 (DataFrame或Dict)
            current_market_state: 当前市场状态
            top_performers: 表现最好的Agent列表
            
        Returns:
            Dict: 小预言结果
        """
        try:
            # ========== 1. 解读市场数据 ==========
            trend = 'neutral'
            trend_strength = 0.5
            momentum = 'neutral'
            momentum_score = 0.5
            volatility = 'normal'
            opportunity_score = 0.5
            
            if current_market_state:
                # 趋势（统一命名：强/弱上升/下降趋势）
                if hasattr(current_market_state, 'trend'):
                    trend_value = current_market_state.trend.value if hasattr(current_market_state.trend, 'value') else str(current_market_state.trend)
                    if '强上升' in trend_value:
                        trend = 'strong_bullish'
                        trend_strength = 0.9
                    elif '上升' in trend_value:
                        trend = 'bullish'
                        trend_strength = 0.7
                    elif '强下降' in trend_value:
                        trend = 'strong_bearish'
                        trend_strength = 0.1
                    elif '下降' in trend_value:
                        trend = 'bearish'
                        trend_strength = 0.3
                    else:
                        trend = 'neutral'
                        trend_strength = 0.5
                
                # 动量
                if hasattr(current_market_state, 'momentum'):
                    momentum_value = current_market_state.momentum.value if hasattr(current_market_state.momentum, 'value') else str(current_market_state.momentum)
                    momentum = momentum_value
                    # momentum_score 在 MarketState 中是 0-100，需要归一化到 0-1
                    raw_momentum_score = getattr(current_market_state, 'momentum_score', 50)
                    momentum_score = raw_momentum_score / 100.0 if raw_momentum_score > 1 else raw_momentum_score
                
                # 波动率
                if hasattr(current_market_state, 'volatility'):
                    volatility = current_market_state.volatility.value if hasattr(current_market_state.volatility, 'value') else 'normal'
                
                # 机会分数（已经是 0-1 范围）
                opportunity_score = getattr(current_market_state, 'opportunity_score', 0.5)
            
            # ========== 2. 先知占卜（纯预测，不给建议）==========
            # 计算短期价格动量（最近价格变化，避免滞后）
            recent_price_momentum = 0.5  # 默认中性
            if market_data is not None and len(market_data) > 0:
                try:
                    current_price = market_data['close'].iloc[-1]
                    # 短期：最近3根K线的价格变化
                    if len(market_data) >= 3:
                        price_3_ago = market_data['close'].iloc[-3]
                        short_term_change = (current_price - price_3_ago) / price_3_ago
                        # 归一化到0-1：-2%对应0，+2%对应1
                        recent_price_momentum = max(0, min(1, 0.5 + short_term_change * 25))
                except Exception as e:
                    logger.warning(f"计算短期价格动量失败: {e}")
            
            # 综合评分（看涨得分：0~1，越高越看涨）
            # 增加短期价格动量权重，降低滞后指标权重
            bullish_score = (
                trend_strength * 0.25 +      # 降低EMA权重（滞后指标）
                momentum_score * 0.20 +      # 降低动量权重（滞后指标）
                opportunity_score * 0.20 +   # 降低机会得分权重
                recent_price_momentum * 0.35 # 增加短期价格动量权重（实时指标）
            )
            
            # 走势预测（只描述市场状态，不给交易建议）
            if bullish_score >= 0.7:
                trend_forecast = '强烈看涨'
                forecast_confidence = bullish_score
            elif bullish_score >= 0.55:
                trend_forecast = '看涨'
                forecast_confidence = bullish_score
            elif bullish_score <= 0.3:
                trend_forecast = '强烈看跌'
                forecast_confidence = 1 - bullish_score
            elif bullish_score <= 0.45:
                trend_forecast = '看跌'
                forecast_confidence = 1 - bullish_score
            else:
                trend_forecast = '震荡'
                forecast_confidence = 0.5
            
            # ========== 3. 交易量预测 ==========
            # 基于动量和波动率预测交易量
            if momentum_score >= 0.7 or volatility in ['高波动', '极高波动']:
                volume_forecast = '放量'
                volume_intensity = 'high'
            elif momentum_score <= 0.3:
                volume_forecast = '缩量'
                volume_intensity = 'low'
            else:
                volume_forecast = '正常'
                volume_intensity = 'normal'
            
            # ========== 4. 风险评估 ==========
            risk_level = 'low'
            risk_factors = []
            
            if volatility in ['高波动', '极高波动']:
                risk_level = 'high'
                risk_factors.append('高波动风险')
            if '超买' in str(momentum):
                risk_factors.append('超买回调风险')
            if '超卖' in str(momentum):
                risk_factors.append('超卖反弹风险')
            if abs(bullish_score - 0.5) < 0.1:
                risk_factors.append('方向不明确')
            
            if len(risk_factors) >= 2:
                risk_level = 'high'
            elif len(risk_factors) == 1:
                risk_level = 'medium'
            
            # ========== 5. 评估环境压力（v4.1 OGAE）==========
            environmental_pressure = self.evaluate_environmental_pressure(
                market_data=market_data,
                current_market_state=current_market_state,
                agent_performance_stats=agent_performance_stats
            )
            
            # 压力等级描述
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
            
            # ========== 6. 构建小预言结果 ==========
            prophecy = {
                'type': 'prophecy',
                'prophecy_level': 'minor',  # 小预言
                
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
                    'trend_strength': trend_strength,
                    'momentum': momentum,
                    'momentum_score': momentum_score,
                    'volatility': volatility,
                },
                
                # 风险评估
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                
                # 环境压力（v4.1新增）
                'environmental_pressure': environmental_pressure,
                'pressure_level': pressure_level,
                'pressure_description': pressure_desc,
                
                # 优秀Agent参考
                'top_performers': [p[0] if isinstance(p, tuple) else str(p) for p in (top_performers or [])[:3]],
                
                # 时间戳
                'timestamp': datetime.now().isoformat()
            }
            
            prophecy_msg = f"🔮 小预言: {trend_forecast}(信心:{forecast_confidence:.0%}) | 量能:{volume_forecast} | 风险:{risk_level} | 压力:{environmental_pressure:.2f}({pressure_desc})"
            logger.info(prophecy_msg)
            return prophecy
            
        except Exception as e:
            logger.error(f"小预言失败: {e}")
            return {
                'type': 'prophecy',
                'prophecy_level': 'minor',
                'trend_forecast': '震荡',
                'forecast_confidence': 0.5,
                'bullish_score': 0.5,
                'volume_forecast': '正常',
                'volume_intensity': 'normal',
                'market_reading': {
                    'trend': '中性',
                    'trend_strength': 0.5,
                    'momentum': '中性',
                    'momentum_score': 0.5,
                    'volatility': '正常'
                },
                'risk_level': 'medium',
                'risk_factors': ['信息不足'],
                'top_performers': [],
                'timestamp': None
            }
    
    def grand_prophecy(self, market_data=None, current_market_state=None,
                       top_performers=None, historical_data=None, agent_performance_stats=None) -> Optional[Dict]:
        """
        大预言 (Grand Prophecy) - 创世时和每8小时执行
        
        全面深度分析，关注中长期趋势
        执行时机：创世时 + 每8小时（00:00, 08:00, 16:00）
        
        Args:
            market_data: 市场数据
            current_market_state: 当前市场状态
            top_performers: 表现最好的Agent列表
            historical_data: 历史数据（过去7天）
            
        Returns:
            Dict: 大预言结果
        """
        try:
            logger.info("="*50)
            logger.info("📜 大预言 (Grand Prophecy) 开始")
            logger.info("="*50)
            
            # ========== 1. 基础市场分析（与小预言相同）==========
            trend = 'neutral'
            trend_strength = 0.5
            momentum = 'neutral'
            momentum_score = 0.5
            volatility = 'normal'
            opportunity_score = 0.5
            
            if current_market_state:
                # 趋势（统一命名：强/弱上升/下降趋势）
                if hasattr(current_market_state, 'trend'):
                    trend_value = current_market_state.trend.value if hasattr(current_market_state.trend, 'value') else str(current_market_state.trend)
                    if '强上升' in trend_value:
                        trend = 'strong_bullish'
                        trend_strength = 0.9
                    elif '上升' in trend_value:
                        trend = 'bullish'
                        trend_strength = 0.7
                    elif '强下降' in trend_value:
                        trend = 'strong_bearish'
                        trend_strength = 0.1
                    elif '下降' in trend_value:
                        trend = 'bearish'
                        trend_strength = 0.3
                
                if hasattr(current_market_state, 'momentum'):
                    momentum_value = current_market_state.momentum.value if hasattr(current_market_state.momentum, 'value') else str(current_market_state.momentum)
                    momentum = momentum_value
                    # momentum_score 在 MarketState 中是 0-100，需要归一化到 0-1
                    raw_momentum_score = getattr(current_market_state, 'momentum_score', 50)
                    momentum_score = raw_momentum_score / 100.0 if raw_momentum_score > 1 else raw_momentum_score
                
                if hasattr(current_market_state, 'volatility'):
                    volatility = current_market_state.volatility.value if hasattr(current_market_state.volatility, 'value') else 'normal'
                
                opportunity_score = getattr(current_market_state, 'opportunity_score', 0.5)
            
            # ========== 2. 历史数据分析（大预言特有）==========
            historical_analysis = {
                'change_7d': 0,
                'change_24h': 0,
                'high_7d': 0,
                'low_7d': 0,
                'avg_volume': 0,
                'price_position': 0.5,  # 当前价格在7日区间的位置 0~1
                'trend_consistency': 0.5,  # 趋势一致性
            }
            
            if historical_data is not None:
                try:
                    import pandas as pd
                    if isinstance(historical_data, pd.DataFrame) and len(historical_data) > 0:
                        # 7日涨跌幅
                        if 'close' in historical_data.columns:
                            first_price = historical_data['close'].iloc[0]
                            last_price = historical_data['close'].iloc[-1]
                            historical_analysis['change_7d'] = (last_price - first_price) / first_price * 100
                            
                            # 高低点
                            historical_analysis['high_7d'] = historical_data['close'].max()
                            historical_analysis['low_7d'] = historical_data['close'].min()
                            
                            # 价格位置
                            price_range = historical_analysis['high_7d'] - historical_analysis['low_7d']
                            if price_range > 0:
                                historical_analysis['price_position'] = (last_price - historical_analysis['low_7d']) / price_range
                        
                        # 24小时涨跌幅
                        if len(historical_data) >= 24:
                            price_24h_ago = historical_data['close'].iloc[-24]
                            historical_analysis['change_24h'] = (last_price - price_24h_ago) / price_24h_ago * 100
                        
                        # 平均交易量
                        if 'volume' in historical_data.columns:
                            historical_analysis['avg_volume'] = historical_data['volume'].mean()
                        
                        # 趋势一致性（计算上涨天数/总天数）
                        if 'close' in historical_data.columns:
                            daily_changes = historical_data['close'].diff()
                            up_days = (daily_changes > 0).sum()
                            historical_analysis['trend_consistency'] = up_days / len(daily_changes) if len(daily_changes) > 0 else 0.5
                        
                        logger.info(f"   历史分析: 7日涨跌={historical_analysis['change_7d']:.1f}%, 24h涨跌={historical_analysis['change_24h']:.1f}%")
                except Exception as e:
                    logger.warning(f"历史数据分析异常: {e}")
            
            # ========== 3. 综合评分（大预言权重不同）==========
            # 计算短期价格动量（最近价格变化）
            recent_price_momentum = 0.5  # 默认中性
            if historical_data is not None and len(historical_data) > 0:
                try:
                    current_price = historical_data['close'].iloc[-1]
                    if len(historical_data) >= 3:
                        price_3_ago = historical_data['close'].iloc[-3]
                        short_term_change = (current_price - price_3_ago) / price_3_ago
                        recent_price_momentum = max(0, min(1, 0.5 + short_term_change * 25))
                except Exception as e:
                    logger.warning(f"计算短期价格动量失败: {e}")
            
            # 大预言更看重历史趋势和一致性
            change_7d_score = 0.5 + historical_analysis['change_7d'] / 20  # -10%~+10% -> 0~1
            change_7d_score = max(0, min(1, change_7d_score))
            
            bullish_score = (
                trend_strength * 0.20 +          # 当前趋势（降低权重）
                momentum_score * 0.10 +          # 动量（降低权重）
                opportunity_score * 0.10 +       # 机会分数（降低权重）
                recent_price_momentum * 0.25 +   # 短期价格动量（新增）
                change_7d_score * 0.20 +         # 7日涨跌
                historical_analysis['trend_consistency'] * 0.15  # 趋势一致性
            )
            
            # ========== 4. 走势预测 ==========
            if bullish_score >= 0.75:
                trend_forecast = '强烈看涨'
                forecast_confidence = bullish_score
            elif bullish_score >= 0.6:
                trend_forecast = '看涨'
                forecast_confidence = bullish_score
            elif bullish_score <= 0.25:
                trend_forecast = '强烈看跌'
                forecast_confidence = 1 - bullish_score
            elif bullish_score <= 0.4:
                trend_forecast = '看跌'
                forecast_confidence = 1 - bullish_score
            else:
                trend_forecast = '震荡'
                forecast_confidence = 0.5
            
            # ========== 5. 交易量预测 ==========
            if momentum_score >= 0.7 or volatility in ['高波动', '极高波动']:
                volume_forecast = '放量'
                volume_intensity = 'high'
            elif momentum_score <= 0.3:
                volume_forecast = '缩量'
                volume_intensity = 'low'
            else:
                volume_forecast = '正常'
                volume_intensity = 'normal'
            
            # ========== 6. 风险评估（大预言更全面）==========
            risk_level = 'low'
            risk_factors = []
            
            if volatility in ['高波动', '极高波动']:
                risk_factors.append('高波动风险')
            if '超买' in str(momentum):
                risk_factors.append('超买回调风险')
            if '超卖' in str(momentum):
                risk_factors.append('超卖反弹风险')
            if abs(bullish_score - 0.5) < 0.1:
                risk_factors.append('方向不明确')
            if abs(historical_analysis['change_7d']) > 15:
                risk_factors.append('近期波动剧烈')
            if historical_analysis['price_position'] > 0.9:
                risk_factors.append('接近7日高点')
            if historical_analysis['price_position'] < 0.1:
                risk_factors.append('接近7日低点')
            
            if len(risk_factors) >= 3:
                risk_level = 'high'
            elif len(risk_factors) >= 1:
                risk_level = 'medium'
            
            # ========== 7. 支撑位/阻力位分析（大预言特有）==========
            support_resistance = {
                'support_1': historical_analysis['low_7d'],
                'support_2': historical_analysis['low_7d'] * 0.98,  # 2%下方
                'resistance_1': historical_analysis['high_7d'],
                'resistance_2': historical_analysis['high_7d'] * 1.02,  # 2%上方
            }
            
            # ========== 8. 评估环境压力（v4.1 OGAE）==========
            environmental_pressure = self.evaluate_environmental_pressure(
                market_data=historical_data if historical_data is not None else market_data,
                current_market_state=current_market_state,
                agent_performance_stats=agent_performance_stats
            )
            
            # 压力等级描述
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
            
            # ========== 9. 构建大预言结果 ==========
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
                    'trend_strength': trend_strength,
                    'momentum': momentum,
                    'momentum_score': momentum_score,
                    'volatility': volatility,
                },
                
                # 历史分析（大预言特有）
                'historical_analysis': historical_analysis,
                
                # 支撑/阻力位（大预言特有）
                'support_resistance': support_resistance,
                
                # 风险评估
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                
                # 环境压力（v4.1新增）
                'environmental_pressure': environmental_pressure,
                'pressure_level': pressure_level,
                'pressure_description': pressure_desc,
                
                # 优秀Agent参考
                'top_performers': [p[0] if isinstance(p, tuple) else str(p) for p in (top_performers or [])[:3]],
                
                # 时间戳
                'timestamp': datetime.now().isoformat(),
                
                # 下次大预言时间（8小时后）
                'next_grand_prophecy': (datetime.now() + timedelta(hours=8)).isoformat()
            }
            
            logger.info(f"📜 大预言: {trend_forecast}(信心:{forecast_confidence:.0%})")
            logger.info(f"   7日涨跌: {historical_analysis['change_7d']:.1f}% | 价格位置: {historical_analysis['price_position']*100:.0f}%")
            logger.info(f"   风险等级: {risk_level} | 风险因素: {risk_factors}")
            logger.info(f"   环境压力: {environmental_pressure:.2f} ({pressure_desc})")
            logger.info("="*50)
            
            return prophecy
            
        except Exception as e:
            logger.error(f"大预言失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认大预言
            return {
                'type': 'prophecy',
                'prophecy_level': 'grand',
                'trend_forecast': '震荡',
                'forecast_confidence': 0.5,
                'bullish_score': 0.5,
                'volume_forecast': '正常',
                'volume_intensity': 'normal',
                'market_reading': {
                    'trend': '中性',
                    'trend_strength': 0.5,
                    'momentum': '中性',
                    'momentum_score': 0.5,
                    'volatility': '正常'
                },
                'historical_analysis': {},
                'support_resistance': {},
                'risk_level': 'medium',
                'risk_factors': ['信息不足'],
                'top_performers': [],
                'timestamp': datetime.now().isoformat(),
                'next_grand_prophecy': None
            }
    
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
    
    # ========== v4.0 公告板集成 ==========
    
    def announce_strategy(self, 
                          strategy_type: str,
                          parameters: Dict,
                          reason: str = ""):
        """
        发布战略公告
        
        Args:
            strategy_type: 策略类型 (conservative/aggressive/balanced)
            parameters: 策略参数
            reason: 原因说明
        """
        if not self.bulletin_board:
            logger.warning("公告板未初始化，无法发布战略公告")
            return
        
        # 发布到战略公告板
        self.bulletin_board.post(
            tier='strategic',
            title=f'全局战略调整：{strategy_type}',
            content={
                'type': 'STRATEGY_ADJUSTMENT',
                'strategy_type': strategy_type,
                'parameters': parameters,
                'reason': reason,
                'market_regime': self.market_regime.value
            },
            publisher='Mastermind',
            priority='high' if strategy_type == 'conservative' else 'normal',
            tags=['strategy', strategy_type]
        )
        
        logger.info(f"📢 战略公告已发布: {strategy_type} - {reason}")
    
    def trigger_nirvana(self, reason: str, target_count: int = 10):
        """
        触发涅槃机制（快速复活Agent）
        
        Args:
            reason: 触发原因
            target_count: 目标复活数量
        """
        if not self.nirvana_system:
            logger.warning("涅槃系统未初始化")
            return
        
        # 触发涅槃
        logger.info(f"🔥 主脑触发涅槃机制: {reason}，目标复活 {target_count} 个Agent")
        
        # 发布公告
        if self.bulletin_board:
            self.bulletin_board.post(
                tier='strategic',
                title='🔥 涅槃机制启动',
                content={
                    'type': 'NIRVANA_EVENT',
                    'reason': reason,
                    'target_count': target_count,
                    'message': '极端市场环境，启动大规模复活机制'
                },
                publisher='Mastermind',
                priority='urgent',
                tags=['nirvana', 'emergency']
            )
    
    def set_global_risk_level(self, risk_level: int, reason: str = ""):
        """
        设置全局风险等级
        
        Args:
            risk_level: 风险等级 (1-5)
            reason: 原因
        """
        if not 1 <= risk_level <= 5:
            logger.error(f"无效的风险等级: {risk_level}")
            return
        
        old_level = self.strategy.risk_level
        self.strategy.risk_level = risk_level
        
        logger.info(f"风险等级调整: {old_level} → {risk_level} ({reason})")
        
        # 发布公告
        if self.bulletin_board:
            self.bulletin_board.post(
                tier='strategic',
                title=f'风险等级调整：Level {risk_level}',
                content={
                    'type': 'RISK_LEVEL_CHANGE',
                    'old_level': old_level,
                    'new_level': risk_level,
                    'reason': reason
                },
                publisher='Mastermind',
                priority='high' if abs(risk_level - old_level) >= 2 else 'normal'
            )
    
    def generate_evolution_hints(self, market_data: Dict) -> Dict:
        """
        生成进化提示（v4.2 自适应进化系统）
        
        根据市场环境分析，为Agent进化提供建议（不是强制）
        
        Args:
            market_data: 市场数据
        
        Returns:
            {
                'pressure': float,  # 环境压力
                'regime': str,  # 市场状态
                'suggested_traits': list,  # 建议解锁的参数
                'reasoning': str  # 建议理由
            }
        """
        # 1. 分析市场环境
        volatility = self._calculate_volatility(market_data)
        trend_strength = abs(market_data.get('trend_strength', 0))
        
        # 获取最新的环境压力
        prophecy = self.bulletin_board.get_latest('prophecy') if self.bulletin_board else None
        pressure = prophecy.get('environmental_pressure', 0.3) if prophecy else 0.3
        
        # 识别市场状态
        regime = self._identify_market_regime(volatility, trend_strength)
        
        # 2. 根据环境给出建议
        suggested_traits = []
        reasoning = []
        
        # 高波动环境 → 建议波动率管理能力
        if volatility > 0.025:
            suggested_traits.extend(['volatility_pref', 'stop_loss_discipline'])
            reasoning.append(f"高波动(σ={volatility:.3f})→建议波动管理能力")
        
        # 强趋势环境 → 建议趋势跟随能力
        if trend_strength > 0.6:
            suggested_traits.extend(['momentum_pref', 'bull_skill'])
            reasoning.append(f"强趋势(强度={trend_strength:.2f})→建议趋势能力")
        
        # 高压力环境 → 建议防御能力
        if pressure > 0.7:
            suggested_traits.extend(['fear_control', 'adaptation_rate'])
            reasoning.append(f"高压力({pressure:.2f})→建议防御能力")
        
        # 震荡环境 → 建议均值回归能力
        if volatility < 0.015 and trend_strength < 0.3:
            suggested_traits.extend(['contrarian_pref', 'position_sizing'])
            reasoning.append("震荡市场→建议均值回归能力")
        
        # 去重
        suggested_traits = list(set(suggested_traits))
        
        hints = {
            'pressure': pressure,
            'regime': regime,
            'volatility': volatility,
            'trend_strength': trend_strength,
            'suggested_traits': suggested_traits,
            'reasoning': ' | '.join(reasoning) if reasoning else '正常市场，无特殊建议'
        }
        
        logger.info(f"🔮 先知进化启示: {regime} | 建议解锁: {suggested_traits}")
        logger.debug(f"   理由: {hints['reasoning']}")
        
        return hints
    
    def _identify_market_regime(self, volatility: float, trend_strength: float) -> str:
        """识别市场状态"""
        if volatility > 0.03 and trend_strength > 0.7:
            return '趋势+高波动'
        elif volatility > 0.03:
            return '震荡+高波动'
        elif trend_strength > 0.7:
            return '趋势+低波动'
        elif volatility < 0.015 and trend_strength < 0.3:
            return '盘整'
        else:
            return '正常'
    
    def _calculate_volatility(self, market_data: Dict) -> float:
        """计算波动率"""
        # 简化实现：从市场数据中提取
        return market_data.get('volatility', 0.02)

