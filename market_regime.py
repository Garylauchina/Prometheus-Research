"""
MarketRegimeDetector - 市场状态检测器
"""

import numpy as np

class MarketRegimeDetector:
    """市场状态检测器"""
    
    def __init__(self, regimes=None):
        """初始化"""
        self.regimes = regimes or {}
    
    def detect(self, prices) -> str:
        """兼容旧版本"""
        return self.detect_regime(prices)
    
    def detect_regime(self, prices) -> str:
        """
        检测市场状态
        
        Args:
            prices: 价格序列
            
        Returns:
            市场状态: 'strong_bull', 'weak_bull', 'sideways', 'weak_bear', 'strong_bear'
        """
        if len(prices) < 30:
            return 'sideways'
        
        prices = np.array(prices)
        
        # 计算30天涨跌幅
        trend = (prices[-1] - prices[-30]) / prices[-30]
        
        # 根据涨跌幅判断市场状态
        if trend > 0.20:  # 涨幅>20%
            return 'strong_bull'
        elif trend > 0.05:  # 涨幅5-20%
            return 'weak_bull'
        elif trend > -0.05:  # 涨跌幅在±5%之间
            return 'sideways'
        elif trend > -0.20:  # 跌幅5-20%
            return 'weak_bear'
        else:  # 跌幅>20%
            return 'strong_bear'
