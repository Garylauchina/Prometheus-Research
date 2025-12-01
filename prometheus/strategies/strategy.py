"""
StrategyV2 - 支持动态多空比例的策略
"""

import numpy as np

class StrategyV2:
    """策略V2 - 支持市场状态自适应和动态多空比例"""
    
    def __init__(self, gene: dict):
        """
        初始化策略
        
        Args:
            gene: 基因字典
        """
        self.gene = gene
        self.weights = gene.get('weights', [0.25, 0.25, 0.25, 0.25])
        
        # 市场状态对应的多空比例
        self.market_ratios = {
            'strong_bull': {'long': 0.90, 'short': 0.10},
            'weak_bull': {'long': 0.70, 'short': 0.30},
            'sideways': {'long': 0.50, 'short': 0.50},
            'weak_bear': {'long': 0.30, 'short': 0.70},
            'strong_bear': {'long': 0.10, 'short': 0.90}
        }
    
    def calculate(self, market_data: dict) -> float:
        """
        计算基础交易信号
        
        Args:
            market_data: 市场数据
            
        Returns:
            交易信号 (-1.0 to 1.0)
        """
        prices = market_data.get('prices', [])
        
        if len(prices) < 30:
            return 0.0
        
        # 计算4个市场特征
        features = self._calculate_features(prices)
        
        # 加权求和
        signal = sum(w * f for w, f in zip(self.weights, features))
        
        # 限制在-1到1之间
        signal = max(-1.0, min(1.0, signal))
        
        return signal
    
    def _calculate_features(self, prices):
        """计算市场特征"""
        prices = np.array(prices)
        
        # 特征1: 短期趋势 (5日)
        if len(prices) >= 5:
            trend_5 = (prices[-1] - prices[-5]) / prices[-5]
        else:
            trend_5 = 0
        
        # 特征2: 中期趋势 (20日)
        if len(prices) >= 20:
            trend_20 = (prices[-1] - prices[-20]) / prices[-20]
        else:
            trend_20 = 0
        
        # 特征3: 动量 (价格相对于均值)
        if len(prices) >= 10:
            ma_10 = np.mean(prices[-10:])
            momentum = (prices[-1] - ma_10) / ma_10
        else:
            momentum = 0
        
        # 特征4: 波动率 (标准差)
        if len(prices) >= 20:
            volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
            # 波动率越高，信号越弱
            volatility_signal = -volatility * 10  # 归一化
        else:
            volatility_signal = 0
        
        return [trend_5, trend_20, momentum, volatility_signal]
    
    def calculate_dynamic_ratio(self, market_regime: str) -> tuple:
        """
        根据市场状态计算动态多空比例
        
        Args:
            market_regime: 市场状态 ('strong_bull', 'weak_bull', 'sideways', 'weak_bear', 'strong_bear')
            
        Returns:
            (long_ratio, short_ratio)
        """
        ratios = self.market_ratios.get(market_regime, {'long': 0.5, 'short': 0.5})
        return ratios['long'], ratios['short']
