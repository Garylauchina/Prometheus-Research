"""
Strategy System - Agent的策略系统
================================

策略是Agent分析市场的"工具"，不是决策者。

设计哲学：
- Strategy只提供"市场评估"，不直接输出交易指令
- 输出：bullish_score/bearish_score（0-1），而不是buy/sell
- Daimon综合Strategy的评估和其他因素后做最终决策

Agent可以拥有3-5个策略，根据市场环境切换激活策略。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class StrategySignal:
    """
    策略信号：Strategy分析市场后的输出
    
    Attributes:
        strategy_name: 策略名称
        bullish_score: 看涨评分 (0-1)
        bearish_score: 看跌评分 (0-1)
        confidence: 分析信心 (0-1)
        reasoning: 推理说明
    """
    strategy_name: str
    bullish_score: float
    bearish_score: float
    confidence: float
    reasoning: str
    
    def __post_init__(self):
        """验证数据"""
        assert 0 <= self.bullish_score <= 1, f"bullish_score must be in [0, 1]: {self.bullish_score}"
        assert 0 <= self.bearish_score <= 1, f"bearish_score must be in [0, 1]: {self.bearish_score}"
        assert 0 <= self.confidence <= 1, f"confidence must be in [0, 1]: {self.confidence}"


class Strategy(ABC):
    """
    策略抽象基类
    
    所有具体策略必须继承此类并实现analyze方法
    """
    
    def __init__(self, name: str):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def analyze(self, market_data: Dict, agent_context: Dict) -> StrategySignal:
        """
        分析市场，生成信号
        
        Args:
            market_data: 市场数据
                - price: 当前价格
                - ohlcv: OHLCV数据
                - volume: 成交量
                - trend: 趋势（可选）
                - volatility: 波动率（可选）
            agent_context: Agent上下文
                - genome: 基因组（包含参数偏好）
                - position: 当前持仓
                - capital_ratio: 资金比率
        
        Returns:
            StrategySignal: 策略信号
        """
        pass
    
    @abstractmethod
    def is_compatible_with_genome(self, genome: 'GenomeVector') -> bool:
        """
        判断策略是否与Agent的基因组兼容
        
        Args:
            genome: Agent的基因组
        
        Returns:
            bool: True表示兼容，可以激活此策略
        """
        pass
    
    def get_required_params(self) -> List[str]:
        """
        获取策略需要的基因组参数
        
        Returns:
            List[str]: 参数名称列表
        """
        return []


class TrendFollowingStrategy(Strategy):
    """
    趋势跟随策略
    
    核心逻辑：
    - 识别市场趋势
    - 顺势而为（上涨时看涨，下跌时看跌）
    - 需要genome参数：trend_pref（趋势偏好）
    """
    
    def __init__(self):
        super().__init__("TrendFollowing")
    
    def analyze(self, market_data: Dict, agent_context: Dict) -> StrategySignal:
        """趋势跟随分析"""
        
        # 获取市场数据
        current_price = market_data.get('price', 0)
        ohlcv = market_data.get('ohlcv', [])
        
        # 简化版：使用最近10根K线计算趋势
        if len(ohlcv) < 10:
            return StrategySignal(
                strategy_name=self.name,
                bullish_score=0.5,
                bearish_score=0.5,
                confidence=0.3,
                reasoning="数据不足"
            )
        
        # 计算趋势强度
        recent_closes = [candle[4] for candle in ohlcv[-10:]]  # 收盘价
        
        # 简单移动平均
        sma_short = np.mean(recent_closes[-5:])
        sma_long = np.mean(recent_closes[-10:])
        
        # 价格相对于均线的位置
        price_vs_sma = (current_price - sma_long) / sma_long if sma_long > 0 else 0
        
        # 趋势方向
        trend_direction = (sma_short - sma_long) / sma_long if sma_long > 0 else 0
        
        # 获取Agent的趋势偏好
        genome = agent_context.get('genome')
        trend_pref = genome.active_params.get('trend_pref', 0.5) if genome else 0.5
        
        # 计算看涨/看跌评分
        if trend_direction > 0.01:  # 上升趋势
            bullish_score = min(0.5 + abs(trend_direction) * 10 * trend_pref, 0.95)
            bearish_score = max(0.5 - abs(trend_direction) * 10 * trend_pref, 0.05)
            reasoning = f"上升趋势(+{trend_direction:.2%}), 价格在均线上{price_vs_sma:.2%}"
        elif trend_direction < -0.01:  # 下降趋势
            bullish_score = max(0.5 + trend_direction * 10 * trend_pref, 0.05)
            bearish_score = min(0.5 - trend_direction * 10 * trend_pref, 0.95)
            reasoning = f"下降趋势({trend_direction:.2%}), 价格在均线下{price_vs_sma:.2%}"
        else:  # 震荡
            bullish_score = 0.5
            bearish_score = 0.5
            reasoning = "震荡市，无明确趋势"
        
        # 信心水平（基于趋势强度和Agent的趋势偏好）
        confidence = min(abs(trend_direction) * 20 + trend_pref * 0.3, 0.9)
        
        return StrategySignal(
            strategy_name=self.name,
            bullish_score=bullish_score,
            bearish_score=bearish_score,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def is_compatible_with_genome(self, genome: 'GenomeVector') -> bool:
        """需要trend_pref参数"""
        return 'trend_pref' in genome.active_params and genome.active_params['trend_pref'] > 0.5
    
    def get_required_params(self) -> List[str]:
        return ['trend_pref']


class MeanReversionStrategy(Strategy):
    """
    均值回归策略
    
    核心逻辑：
    - 识别价格偏离均值的程度
    - 反向操作（价格过高时看跌，价格过低时看涨）
    - 需要genome参数：mean_reversion（均值回归偏好）
    """
    
    def __init__(self):
        super().__init__("MeanReversion")
    
    def analyze(self, market_data: Dict, agent_context: Dict) -> StrategySignal:
        """均值回归分析"""
        
        # 获取市场数据
        current_price = market_data.get('price', 0)
        ohlcv = market_data.get('ohlcv', [])
        
        if len(ohlcv) < 20:
            return StrategySignal(
                strategy_name=self.name,
                bullish_score=0.5,
                bearish_score=0.5,
                confidence=0.3,
                reasoning="数据不足"
            )
        
        # 计算均值和标准差
        recent_closes = [candle[4] for candle in ohlcv[-20:]]
        mean_price = np.mean(recent_closes)
        std_price = np.std(recent_closes)
        
        # 价格偏离度（以标准差为单位）
        if std_price > 0:
            deviation = (current_price - mean_price) / std_price
        else:
            deviation = 0
        
        # 获取Agent的均值回归偏好
        genome = agent_context.get('genome')
        mean_reversion = genome.active_params.get('mean_reversion', 0.5) if genome else 0.5
        
        # 计算看涨/看跌评分（反向）
        if deviation > 1.0:  # 价格过高（超过1个标准差）
            # 均值回归策略认为应该看跌
            bullish_score = max(0.5 - min(deviation - 1, 2) * 0.2 * mean_reversion, 0.05)
            bearish_score = min(0.5 + min(deviation - 1, 2) * 0.2 * mean_reversion, 0.95)
            reasoning = f"价格过高(+{deviation:.1f}σ), 回归压力"
        elif deviation < -1.0:  # 价格过低
            # 均值回归策略认为应该看涨
            bullish_score = min(0.5 - min(-deviation - 1, 2) * 0.2 * mean_reversion, 0.95)
            bearish_score = max(0.5 + min(-deviation - 1, 2) * 0.2 * mean_reversion, 0.05)
            reasoning = f"价格过低({deviation:.1f}σ), 反弹机会"
        else:  # 价格接近均值
            bullish_score = 0.5
            bearish_score = 0.5
            reasoning = f"价格接近均值({deviation:.1f}σ), 观望"
        
        # 信心水平（基于偏离程度和Agent的均值回归偏好）
        confidence = min(abs(deviation) * 0.3 + mean_reversion * 0.4, 0.9)
        
        return StrategySignal(
            strategy_name=self.name,
            bullish_score=bullish_score,
            bearish_score=bearish_score,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def is_compatible_with_genome(self, genome: 'GenomeVector') -> bool:
        """需要mean_reversion参数"""
        return 'mean_reversion' in genome.active_params and genome.active_params['mean_reversion'] > 0.5
    
    def get_required_params(self) -> List[str]:
        return ['mean_reversion']


class GridTradingStrategy(Strategy):
    """
    网格交易策略
    
    核心逻辑：
    - 在震荡市中低买高卖
    - 识别价格网格位置
    - 需要genome参数：grid_size（网格大小）
    """
    
    def __init__(self):
        super().__init__("GridTrading")
    
    def analyze(self, market_data: Dict, agent_context: Dict) -> StrategySignal:
        """网格交易分析"""
        
        # 获取市场数据
        current_price = market_data.get('price', 0)
        ohlcv = market_data.get('ohlcv', [])
        
        if len(ohlcv) < 20:
            return StrategySignal(
                strategy_name=self.name,
                bullish_score=0.5,
                bearish_score=0.5,
                confidence=0.3,
                reasoning="数据不足"
            )
        
        # 计算价格区间
        recent_closes = [candle[4] for candle in ohlcv[-20:]]
        price_high = max(recent_closes)
        price_low = min(recent_closes)
        price_range = price_high - price_low
        
        # 获取Agent的网格大小偏好
        genome = agent_context.get('genome')
        grid_size = genome.active_params.get('grid_size', 0.05) if genome else 0.05
        
        # 计算当前价格在区间中的位置（0-1）
        if price_range > 0:
            price_position = (current_price - price_low) / price_range
        else:
            price_position = 0.5
        
        # 获取当前持仓
        position = agent_context.get('position', {})
        has_position = position.get('amount', 0) != 0
        
        # 网格策略逻辑
        if price_position < 0.3:  # 价格在区间下部
            # 适合买入
            bullish_score = 0.7 + (0.3 - price_position) * 0.5
            bearish_score = 0.3 - (0.3 - price_position) * 0.5
            reasoning = f"价格在区间下部({price_position:.1%}), 买入机会"
        elif price_position > 0.7:  # 价格在区间上部
            # 适合卖出
            bullish_score = 0.3 - (price_position - 0.7) * 0.5
            bearish_score = 0.7 + (price_position - 0.7) * 0.5
            reasoning = f"价格在区间上部({price_position:.1%}), 卖出机会"
        else:  # 价格在中部
            bullish_score = 0.5
            bearish_score = 0.5
            reasoning = f"价格在区间中部({price_position:.1%}), 观望"
        
        # 信心水平（震荡市信心更高）
        volatility = market_data.get('volatility', 0.05)
        if volatility < 0.03:  # 低波动
            confidence = 0.7
        elif volatility > 0.08:  # 高波动
            confidence = 0.3
        else:
            confidence = 0.5
        
        return StrategySignal(
            strategy_name=self.name,
            bullish_score=min(bullish_score, 0.95),
            bearish_score=min(bearish_score, 0.95),
            confidence=confidence,
            reasoning=reasoning
        )
    
    def is_compatible_with_genome(self, genome: 'GenomeVector') -> bool:
        """需要grid_size参数（或不需要特定参数，通用策略）"""
        return True  # 网格策略比较通用
    
    def get_required_params(self) -> List[str]:
        return ['grid_size']  # 可选参数


# ==================== 策略库 ====================

STRATEGY_LIBRARY = {
    'TrendFollowing': TrendFollowingStrategy,
    'MeanReversion': MeanReversionStrategy,
    'GridTrading': GridTradingStrategy,
}


def get_strategy_by_name(name: str) -> Optional[Strategy]:
    """
    根据名称获取策略实例
    
    Args:
        name: 策略名称
    
    Returns:
        Strategy: 策略实例，如果不存在则返回None
    """
    strategy_class = STRATEGY_LIBRARY.get(name)
    if strategy_class:
        return strategy_class()
    return None


def get_compatible_strategies(genome: 'GenomeVector') -> List[Strategy]:
    """
    获取与Agent基因组兼容的所有策略
    
    Args:
        genome: Agent的基因组
    
    Returns:
        List[Strategy]: 兼容的策略列表
    """
    compatible = []
    for strategy_class in STRATEGY_LIBRARY.values():
        strategy = strategy_class()
        if strategy.is_compatible_with_genome(genome):
            compatible.append(strategy)
    
    return compatible

