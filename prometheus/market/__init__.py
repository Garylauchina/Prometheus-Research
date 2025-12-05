"""
市场模拟模块

提供两个级别的市场模拟：
1. SimpleOpponentMarket（v5.2）- 简单轻量，适合快速测试
2. AdvancedOpponentMarket（v5.3）- 高度真实，适合深度验证

Author: Prometheus Team
Version: v5.3
"""

# v5.2: 简单版本（快速测试）
from .simple_opponents import (
    SimpleInstitution,
    SimpleRetailer,
    SimpleOpponentMarket
)

# v5.3: 高级版本（深度测试）
from .advanced_market import AdvancedOpponentMarket

# v5.3: 微观结构组件（高级用法）
from .market_microstructure import (
    OrderBook,
    SpreadManager,
    SlippageCalculator,
    LiquidityManager,
    MarketImpactCalculator
)

# v5.3: 高级对手盘（高级用法）
from .advanced_opponents import (
    MarketMaker,      # 做市商
    Arbitrageur,      # 套利者
    Whale,            # 大户
    HighFrequencyTrader,  # 高频交易者
    PassiveInvestor,  # 被动投资者
    PanicTrader       # 恐慌交易者
)

__all__ = [
    # === 简单版本（v5.2）===
    'SimpleOpponentMarket',
    'SimpleInstitution',
    'SimpleRetailer',
    
    # === 高级版本（v5.3）===
    'AdvancedOpponentMarket',
    
    # === 微观结构组件 ===
    'OrderBook',
    'SpreadManager',
    'SlippageCalculator',
    'LiquidityManager',
    'MarketImpactCalculator',
    
    # === 高级对手盘 ===
    'MarketMaker',
    'Arbitrageur',
    'Whale',
    'HighFrequencyTrader',
    'PassiveInvestor',
    'PanicTrader'
]
