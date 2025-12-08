"""
Self-Play对抗系统

提供Agent vs Agent的对抗训练环境，包括：
  1. AdversarialMarket（对手盘生成器）
  2. AgentArena（竞技场）
  3. PressureController（压力调节器）
  4. OrderBook（订单簿）
  5. PriceImpactModel（价格冲击模型）

核心理念：
  - 对抗压力驱动进化
  - 竞争博弈产生涌现
  - Self-Play是"天才策略"的摇篮

遵循三大铁律：
  - 铁律1: 通过SelfPlaySystem统一入口
  - 铁律2: 内部模块封装
  - 铁律3: 所有交易原子化
"""

from .order_book import (
    OrderBook,
    Order,
    Trade,
    OrderType,
    OrderSide,
    OrderStatus
)

from .price_impact_model import PriceImpactModel
from .adversarial_market import AdversarialMarket, AdversarialAgent
from .agent_arena import AgentArena, Leaderboard, MatchRecord, AgentStats
from .pressure_controller import PressureController, PressureHistory

# 对手盘Agent (这些类在adversaries包中，但暂时不在此导入)
# from .adversaries import (
#     MarketMakerAdversary,
#     TrendFollowerAdversary,
#     ContrarianAdversary,
#     ArbitrageurAdversary,
#     NoiseTraderAdversary
# )

__all__ = [
    # 核心组件
    'OrderBook',
    'Order',
    'Trade',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'PriceImpactModel',
    'AdversarialMarket',
    'AdversarialAgent',
    'AgentArena',
    'PressureController',
    
    # 竞技场组件
    'Leaderboard',
    'MatchRecord',
    'AgentStats',
    'PressureHistory',
]

__version__ = '6.0.0-alpha'

