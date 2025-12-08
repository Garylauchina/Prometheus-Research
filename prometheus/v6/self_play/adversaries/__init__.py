"""
对手盘Adversaries

提供5种类型的对手盘Agent，模拟真实市场中的不同参与者：
  1. MarketMaker（做市商）- 提供流动性，赚取价差
  2. TrendFollower（趋势跟随）- 追涨杀跌，制造动量
  3. Contrarian（逆向交易）- 高点做空，低点做多
  4. Arbitrageur（套利者）- 消除价差，快速平仓
  5. NoiseTrader（噪音交易者）- 随机交易，制造市场噪音

设计理念：
  - 不是为了盈利，而是为了制造压力
  - 模拟真实市场的复杂性
  - 让主Agent学会"博弈"，而不只是"统计"
"""

from .market_maker import MarketMakerAdversary
from .trend_follower import TrendFollowerAdversary
from .contrarian import ContrarianAdversary
from .arbitrageur import ArbitrageurAdversary
from .noise_trader import NoiseTraderAdversary

__all__ = [
    'MarketMakerAdversary',
    'TrendFollowerAdversary',
    'ContrarianAdversary',
    'ArbitrageurAdversary',
    'NoiseTraderAdversary',
]

