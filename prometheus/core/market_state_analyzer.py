"""
Prometheus v4.0 - 市场状态分析器

负责分析市场状态（趋势、动量、波动率）
由Supervisor内部使用
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from prometheus.core.indicator_calculator import TechnicalIndicators

logger = logging.getLogger(__name__)


class TrendState(Enum):
    """趋势状态"""
    STRONG_UPTREND = "强上升趋势"
    WEAK_UPTREND = "弱上升趋势"
    RANGING = "震荡"
    WEAK_DOWNTREND = "弱下降趋势"
    STRONG_DOWNTREND = "强下降趋势"


class MomentumState(Enum):
    """动量状态"""
    STRONG_OVERBOUGHT = "严重超买"
    OVERBOUGHT = "超买"
    NEUTRAL = "中性"
    OVERSOLD = "超卖"
    STRONG_OVERSOLD = "严重超卖"


class VolatilityState(Enum):
    """波动率状态"""
    EXTREMELY_HIGH = "极高波动"
    HIGH = "高波动"
    NORMAL = "正常波动"
    LOW = "低波动"
    EXTREMELY_LOW = "极低波动"


@dataclass
class MarketState:
    """市场状态"""
    
    # 趋势
    trend: TrendState
    trend_strength: float  # 0-100
    
    # 动量
    momentum: MomentumState
    momentum_score: float  # 0-100
    
    # 波动率
    volatility: VolatilityState
    volatility_score: float  # 0-100
    
    # 综合评分
    market_difficulty: float  # 0-1，越高越难交易
    opportunity_score: float  # 0-1，越高机会越好
    
    # 建议
    recommendation: str
    
    # 时间戳
    timestamp: datetime


class MarketStateAnalyzer:
    """
    市场状态分析器
    
    基于技术指标分析市场状态
    """
    
    def __init__(self):
        logger.info("市场状态分析器已初始化")
    
    def analyze(self, indicators: TechnicalIndicators) -> MarketState:
        """
        分析市场状态
        
        Args:
            indicators: 技术指标
        
        Returns:
            MarketState: 市场状态
        """
        # 1. 分析趋势
        trend_state, trend_strength = self._analyze_trend(indicators)
        
        # 2. 分析动量
        momentum_state, momentum_score = self._analyze_momentum(indicators)
        
        # 3. 分析波动率
        volatility_state, volatility_score = self._analyze_volatility(indicators)
        
        # 4. 计算市场难度
        market_difficulty = self._calculate_market_difficulty(
            trend_strength, volatility_score
        )
        
        # 5. 计算机会评分
        opportunity_score = self._calculate_opportunity_score(
            trend_state, momentum_state, volatility_state
        )
        
        # 6. 生成建议
        recommendation = self._generate_recommendation(
            trend_state, momentum_state, volatility_state, market_difficulty
        )
        
        state = MarketState(
            trend=trend_state,
            trend_strength=trend_strength,
            momentum=momentum_state,
            momentum_score=momentum_score,
            volatility=volatility_state,
            volatility_score=volatility_score,
            market_difficulty=market_difficulty,
            opportunity_score=opportunity_score,
            recommendation=recommendation,
            timestamp=datetime.now()
        )
        
        logger.info(f"市场状态分析完成: {trend_state.value}, 难度={market_difficulty:.2f}")
        return state
    
    # ========== 趋势分析 ==========
    
    def _analyze_trend(self, indicators: TechnicalIndicators) -> tuple:
        """
        分析趋势
        
        Returns:
            (趋势状态, 趋势强度0-100)
        """
        adx = indicators.trend['ADX']
        ema_9 = indicators.trend['EMA_9']
        ema_21 = indicators.trend['EMA_21']
        ema_55 = indicators.trend['EMA_55']
        current_price = indicators.price['current']
        
        # 判断趋势方向
        if ema_9 > ema_21 > ema_55:
            # 上升趋势
            if adx > 30:
                trend_state = TrendState.STRONG_UPTREND
            else:
                trend_state = TrendState.WEAK_UPTREND
        elif ema_9 < ema_21 < ema_55:
            # 下降趋势
            if adx > 30:
                trend_state = TrendState.STRONG_DOWNTREND
            else:
                trend_state = TrendState.WEAK_DOWNTREND
        else:
            # 震荡
            trend_state = TrendState.RANGING
        
        # 趋势强度 = ADX
        trend_strength = min(adx, 100)
        
        return trend_state, trend_strength
    
    # ========== 动量分析 ==========
    
    def _analyze_momentum(self, indicators: TechnicalIndicators) -> tuple:
        """
        分析动量
        
        Returns:
            (动量状态, 动量评分0-100)
        """
        rsi = indicators.momentum['RSI']
        stoch_k = indicators.momentum['Stochastic_K']
        cci = indicators.momentum['CCI']
        
        # 综合动量评分（RSI权重最高）
        momentum_score = (
            rsi * 0.5 +
            stoch_k * 0.3 +
            min(max((cci + 100) / 2, 0), 100) * 0.2
        )
        
        # 判断状态
        if momentum_score > 80:
            momentum_state = MomentumState.STRONG_OVERBOUGHT
        elif momentum_score > 70:
            momentum_state = MomentumState.OVERBOUGHT
        elif momentum_score < 20:
            momentum_state = MomentumState.STRONG_OVERSOLD
        elif momentum_score < 30:
            momentum_state = MomentumState.OVERSOLD
        else:
            momentum_state = MomentumState.NEUTRAL
        
        return momentum_state, momentum_score
    
    # ========== 波动率分析 ==========
    
    def _analyze_volatility(self, indicators: TechnicalIndicators) -> tuple:
        """
        分析波动率
        
        Returns:
            (波动率状态, 波动率评分0-100)
        """
        atr = indicators.volatility['ATR']
        current_price = indicators.price['current']
        bb_width = indicators.volatility['BB_width']
        
        # ATR百分比
        atr_pct = (atr / current_price) * 100
        
        # 波动率评分（0-100）
        # ATR% > 5% = 极高波动
        # ATR% > 3% = 高波动
        # ATR% > 2% = 正常
        # ATR% > 1% = 低波动
        # ATR% < 1% = 极低波动
        
        if atr_pct > 5:
            volatility_score = 100
        elif atr_pct < 1:
            volatility_score = 20
        else:
            # 线性映射 1%-5% -> 20-100
            volatility_score = 20 + (atr_pct - 1) / 4 * 80
        
        # 结合布林带宽度
        volatility_score = volatility_score * 0.7 + min(bb_width * 2, 100) * 0.3
        
        # 判断状态
        if volatility_score > 80:
            volatility_state = VolatilityState.EXTREMELY_HIGH
        elif volatility_score > 60:
            volatility_state = VolatilityState.HIGH
        elif volatility_score < 30:
            volatility_state = VolatilityState.LOW
        elif volatility_score < 20:
            volatility_state = VolatilityState.EXTREMELY_LOW
        else:
            volatility_state = VolatilityState.NORMAL
        
        return volatility_state, volatility_score
    
    # ========== 综合分析 ==========
    
    def _calculate_market_difficulty(self, trend_strength: float, volatility_score: float) -> float:
        """
        计算市场难度
        
        难度因素：
        - 弱趋势（震荡）→ 难度高
        - 高波动 → 难度高
        
        Returns:
            0-1，越高越难
        """
        # 趋势越弱越难（ADX越低越难）
        trend_difficulty = 1 - (trend_strength / 100)
        
        # 波动越极端越难（过高或过低都难）
        # 最佳波动区间：40-60
        if 40 <= volatility_score <= 60:
            vol_difficulty = 0.2
        else:
            vol_difficulty = abs(volatility_score - 50) / 50
        
        # 综合难度
        difficulty = trend_difficulty * 0.6 + vol_difficulty * 0.4
        
        return min(max(difficulty, 0), 1)
    
    def _calculate_opportunity_score(
        self, 
        trend: TrendState, 
        momentum: MomentumState, 
        volatility: VolatilityState
    ) -> float:
        """
        计算机会评分
        
        机会好的情况：
        - 强趋势 + 动量确认
        - 超买/超卖 + 趋势反转信号
        - 正常波动
        
        Returns:
            0-1，越高机会越好
        """
        score = 0.5  # 基础分
        
        # 强趋势加分
        if trend in [TrendState.STRONG_UPTREND, TrendState.STRONG_DOWNTREND]:
            score += 0.2
        
        # 超买/超卖机会（反转）
        if momentum in [MomentumState.STRONG_OVERBOUGHT, MomentumState.STRONG_OVERSOLD]:
            score += 0.15
        
        # 正常波动加分
        if volatility == VolatilityState.NORMAL:
            score += 0.15
        
        # 极端波动减分
        if volatility in [VolatilityState.EXTREMELY_HIGH, VolatilityState.EXTREMELY_LOW]:
            score -= 0.2
        
        return min(max(score, 0), 1)
    
    def _generate_recommendation(
        self, 
        trend: TrendState, 
        momentum: MomentumState, 
        volatility: VolatilityState,
        difficulty: float
    ) -> str:
        """
        生成交易建议
        
        Args:
            trend: 趋势状态
            momentum: 动量状态
            volatility: 波动率状态
            difficulty: 市场难度
        
        Returns:
            建议文本
        """
        recommendations = []
        
        # 趋势建议
        if trend == TrendState.STRONG_UPTREND:
            recommendations.append("强上升趋势，适合顺势做多")
        elif trend == TrendState.STRONG_DOWNTREND:
            recommendations.append("强下降趋势，适合顺势做空")
        elif trend == TrendState.RANGING:
            recommendations.append("震荡行情，适合区间操作或观望")
        
        # 动量建议
        if momentum == MomentumState.STRONG_OVERBOUGHT:
            recommendations.append("严重超买，警惕回调风险")
        elif momentum == MomentumState.STRONG_OVERSOLD:
            recommendations.append("严重超卖，可能出现反弹")
        
        # 波动率建议
        if volatility == VolatilityState.EXTREMELY_HIGH:
            recommendations.append("极高波动，建议降低仓位，严控风险")
        elif volatility == VolatilityState.EXTREMELY_LOW:
            recommendations.append("极低波动，市场沉闷，可能酝酿变盘")
        
        # 难度建议
        if difficulty > 0.7:
            recommendations.append("⚠️ 市场难度高，新手建议观望")
        
        return "；".join(recommendations) if recommendations else "市场正常，可正常交易"
    
    def get_state_summary(self, state: MarketState) -> Dict[str, Any]:
        """
        获取状态摘要（供公告板发布）
        
        Args:
            state: 市场状态
        
        Returns:
            摘要字典
        """
        return {
            'trend': state.trend.value,
            'momentum': state.momentum.value,
            'volatility': state.volatility.value,
            'difficulty': f"{state.market_difficulty:.2f}",
            'opportunity': f"{state.opportunity_score:.2f}",
            'recommendation': state.recommendation
        }


if __name__ == "__main__":
    # 测试代码
    import pandas as pd
    import numpy as np
    from prometheus.core.indicator_calculator import IndicatorCalculator
    
    logging.basicConfig(level=logging.INFO)
    
    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    data = pd.DataFrame({
        'open': 50000 + np.random.randn(100).cumsum() * 100,
        'high': 50000 + np.random.randn(100).cumsum() * 100 + 100,
        'low': 50000 + np.random.randn(100).cumsum() * 100 - 100,
        'close': 50000 + np.random.randn(100).cumsum() * 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # 确保high > low
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    # 计算指标
    calculator = IndicatorCalculator()
    indicators = calculator.calculate_all(data)
    
    # 分析状态
    analyzer = MarketStateAnalyzer()
    state = analyzer.analyze(indicators)
    
    print("\n=== 市场状态分析结果 ===")
    print(f"趋势: {state.trend.value} (强度: {state.trend_strength:.2f})")
    print(f"动量: {state.momentum.value} (评分: {state.momentum_score:.2f})")
    print(f"波动率: {state.volatility.value} (评分: {state.volatility_score:.2f})")
    print(f"市场难度: {state.market_difficulty:.2f}")
    print(f"机会评分: {state.opportunity_score:.2f}")
    print(f"建议: {state.recommendation}")
    
    print("\n=== 摘要 ===")
    summary = analyzer.get_state_summary(state)
    for k, v in summary.items():
        print(f"{k}: {v}")

