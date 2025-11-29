"""
Market类 - 定义交易市场的规则和特性
"""

class Market:
    """交易市场类"""
    
    def __init__(self, name: str, fee_rate: float, leverage: float = 1.0,
                 min_position: float = 0.0, max_position: float = 1.0):
        """
        初始化市场
        
        Args:
            name: 市场名称 ('spot' or 'futures')
            fee_rate: 交易手续费率 (e.g., 0.001 for 0.1%)
            leverage: 杠杆倍数 (1.0 for spot, up to 5.0 for futures in Phase 1)
            min_position: 最小仓位 (0.0 for spot, -1.0 for futures)
            max_position: 最大仓位 (1.0 for both)
        """
        self.name = name
        self.fee_rate = fee_rate
        self.leverage = leverage
        self.min_position = min_position
        self.max_position = max_position
    
    def __repr__(self):
        return (f"Market(name={self.name}, fee_rate={self.fee_rate:.4f}, "
                f"leverage={self.leverage:.1f}x)")
