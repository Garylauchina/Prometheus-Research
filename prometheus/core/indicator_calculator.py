"""
Prometheus v4.0 - 技术指标计算器

负责计算所有技术指标（一次性计算，避免重复）
由Supervisor内部使用
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    
    # 趋势指标
    trend: Dict[str, float]  # ADX, EMA等
    
    # 动量指标
    momentum: Dict[str, float]  # RSI, Stochastic, CCI等
    
    # 波动率指标
    volatility: Dict[str, float]  # ATR, Bollinger Bands等
    
    # 成交量指标
    volume: Dict[str, float]  # OBV等
    
    # 价格信息
    price: Dict[str, float]  # 当前价、最高、最低等
    
    # 计算时间
    timestamp: datetime


class IndicatorCalculator:
    """
    技术指标计算器
    
    负责计算8大核心技术指标：
    1. ADX (Average Directional Index) - 趋势强度
    2. ATR (Average True Range) - 波动率
    3. RSI (Relative Strength Index) - 相对强弱
    4. Stochastic - 随机指标
    5. CCI (Commodity Channel Index) - 商品通道指标
    6. EMA (Exponential Moving Average) - 指数移动平均
    7. Bollinger Bands - 布林带
    8. OBV (On-Balance Volume) - 能量潮
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化
        
        Args:
            config: 配置参数（周期等）
        """
        self.config = config or self._default_config()
        logger.info("技术指标计算器已初始化")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'rsi_period': 14,
            'adx_period': 14,
            'atr_period': 14,
            'stoch_k_period': 14,
            'stoch_d_period': 3,
            'cci_period': 20,
            'ema_periods': [9, 21, 55],
            'bb_period': 20,
            'bb_std': 2.0
        }
    
    def calculate_all(self, market_data: pd.DataFrame) -> TechnicalIndicators:
        """
        计算所有技术指标（一次性）
        
        Args:
            market_data: 市场数据（OHLCV格式）
                - open, high, low, close, volume
        
        Returns:
            TechnicalIndicators: 所有技术指标
        """
        try:
            # 1. 趋势指标
            trend = {
                'ADX': self._calculate_adx(market_data),
                'EMA_9': self._calculate_ema(market_data['close'], 9),
                'EMA_21': self._calculate_ema(market_data['close'], 21),
                'EMA_55': self._calculate_ema(market_data['close'], 55),
                'trend_strength': None  # 将在市场状态分析中计算
            }
            
            # 2. 动量指标
            momentum = {
                'RSI': self._calculate_rsi(market_data['close']),
                'Stochastic_K': None,  # 计算中
                'Stochastic_D': None,
                'CCI': self._calculate_cci(market_data)
            }
            
            # 计算Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(market_data)
            momentum['Stochastic_K'] = stoch_k
            momentum['Stochastic_D'] = stoch_d
            
            # 3. 波动率指标
            volatility = {
                'ATR': self._calculate_atr(market_data),
                'BB_upper': None,  # 布林带上轨
                'BB_middle': None,  # 布林带中轨
                'BB_lower': None,  # 布林带下轨
                'BB_width': None  # 布林带宽度
            }
            
            # 计算布林带
            bb = self._calculate_bollinger_bands(market_data['close'])
            volatility.update(bb)
            
            # 4. 成交量指标
            volume = {
                'OBV': self._calculate_obv(market_data),
                'volume_ma': market_data['volume'].rolling(20).mean().iloc[-1]
            }
            
            # 5. 价格信息
            price = {
                'current': market_data['close'].iloc[-1],
                'high_24h': market_data['high'].iloc[-24:].max(),
                'low_24h': market_data['low'].iloc[-24:].min(),
                'change_24h': (market_data['close'].iloc[-1] / market_data['close'].iloc[-24] - 1) * 100
            }
            
            indicators = TechnicalIndicators(
                trend=trend,
                momentum=momentum,
                volatility=volatility,
                volume=volume,
                price=price,
                timestamp=datetime.now()
            )
            
            logger.debug(f"技术指标计算完成: RSI={momentum['RSI']:.2f}, ADX={trend['ADX']:.2f}")
            return indicators
            
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
            raise
    
    # ========== 趋势指标 ==========
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = None) -> float:
        """
        计算ADX (Average Directional Index)
        
        ADX > 25: 强趋势
        ADX < 20: 弱趋势/震荡
        """
        period = period or self.config['adx_period']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 计算+DM和-DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # 计算TR (True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 平滑
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # 计算ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1]
    
    def _calculate_ema(self, series: pd.Series, period: int) -> float:
        """计算EMA (Exponential Moving Average)"""
        ema = series.ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]
    
    # ========== 动量指标 ==========
    
    def _calculate_rsi(self, series: pd.Series, period: int = None) -> float:
        """
        计算RSI (Relative Strength Index)
        
        RSI > 70: 超买
        RSI < 30: 超卖
        """
        period = period or self.config['rsi_period']
        
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def _calculate_stochastic(self, data: pd.DataFrame) -> tuple:
        """
        计算Stochastic随机指标
        
        Returns:
            (K值, D值)
        
        K > 80: 超买
        K < 20: 超卖
        """
        k_period = self.config['stoch_k_period']
        d_period = self.config['stoch_d_period']
        
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()
        
        k = 100 * (data['close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=d_period).mean()
        
        return k.iloc[-1], d.iloc[-1]
    
    def _calculate_cci(self, data: pd.DataFrame, period: int = None) -> float:
        """
        计算CCI (Commodity Channel Index)
        
        CCI > 100: 超买
        CCI < -100: 超卖
        """
        period = period or self.config['cci_period']
        
        tp = (data['high'] + data['low'] + data['close']) / 3  # Typical Price
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (tp - sma_tp) / (0.015 * mad)
        
        return cci.iloc[-1]
    
    # ========== 波动率指标 ==========
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = None) -> float:
        """
        计算ATR (Average True Range)
        
        波动率指标，值越大波动越大
        """
        period = period or self.config['atr_period']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1]
    
    def _calculate_bollinger_bands(self, series: pd.Series) -> Dict[str, float]:
        """
        计算布林带 (Bollinger Bands)
        
        Returns:
            上轨、中轨、下轨、宽度
        """
        period = self.config['bb_period']
        std_mult = self.config['bb_std']
        
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper = middle + (std * std_mult)
        lower = middle - (std * std_mult)
        width = (upper - lower) / middle
        
        return {
            'BB_upper': upper.iloc[-1],
            'BB_middle': middle.iloc[-1],
            'BB_lower': lower.iloc[-1],
            'BB_width': width.iloc[-1] * 100  # 百分比
        }
    
    # ========== 成交量指标 ==========
    
    def _calculate_obv(self, data: pd.DataFrame) -> float:
        """
        计算OBV (On-Balance Volume)
        
        成交量能量潮指标
        """
        obv = (np.sign(data['close'].diff()) * data['volume']).fillna(0).cumsum()
        return obv.iloc[-1]
    
    def get_indicator_summary(self, indicators: TechnicalIndicators) -> Dict[str, str]:
        """
        获取指标摘要（供公告板发布）
        
        Args:
            indicators: 技术指标
        
        Returns:
            摘要字典
        """
        summary = {}
        
        # 趋势
        adx = indicators.trend['ADX']
        if adx > 25:
            summary['trend'] = "强趋势"
        elif adx < 20:
            summary['trend'] = "弱趋势/震荡"
        else:
            summary['trend'] = "中等趋势"
        
        # RSI
        rsi = indicators.momentum['RSI']
        if rsi > 70:
            summary['rsi'] = "超买"
        elif rsi < 30:
            summary['rsi'] = "超卖"
        else:
            summary['rsi'] = "正常"
        
        # 随机指标
        stoch_k = indicators.momentum['Stochastic_K']
        if stoch_k > 80:
            summary['stochastic'] = "超买"
        elif stoch_k < 20:
            summary['stochastic'] = "超卖"
        else:
            summary['stochastic'] = "正常"
        
        # 波动率
        atr_pct = (indicators.volatility['ATR'] / indicators.price['current']) * 100
        if atr_pct > 5:
            summary['volatility'] = "高波动"
        elif atr_pct < 2:
            summary['volatility'] = "低波动"
        else:
            summary['volatility'] = "中等波动"
        
        return summary


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
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
    
    print("\n=== 技术指标计算结果 ===")
    print(f"\n趋势指标:")
    for k, v in indicators.trend.items():
        print(f"  {k}: {v}")
    
    print(f"\n动量指标:")
    for k, v in indicators.momentum.items():
        print(f"  {k}: {v}")
    
    print(f"\n波动率指标:")
    for k, v in indicators.volatility.items():
        print(f"  {k}: {v}")
    
    print(f"\n成交量指标:")
    for k, v in indicators.volume.items():
        print(f"  {k}: {v}")
    
    print(f"\n摘要:")
    summary = calculator.get_indicator_summary(indicators)
    for k, v in summary.items():
        print(f"  {k}: {v}")

