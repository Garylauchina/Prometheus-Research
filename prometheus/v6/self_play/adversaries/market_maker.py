"""
做市商对手盘

策略特点：
  - 双边挂单（买卖两侧同时挂单）
  - 赚取买卖价差
  - 提供流动性
  - 快速平仓（持仓时间极短）
  - 低风险偏好

行为模式：
  - 在当前价格附近挂买单和卖单
  - 价差固定（例如0.2%）
  - 一旦成交立即对冲
  - 库存管理（避免单边持仓过大）
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketMakerConfig:
    """做市商配置"""
    spread_pct: float = 0.002          # 价差（0.2%）
    order_size: float = 1.0            # 订单大小
    max_inventory: float = 10.0        # 最大库存
    quote_refresh_rate: int = 5        # 报价刷新频率（每5个周期）


class MarketMakerAdversary:
    """
    做市商对手盘
    
    核心功能：
      1. 双边报价（买+卖）
      2. 库存管理
      3. 快速对冲
    """
    
    def __init__(self, config: Optional[MarketMakerConfig] = None):
        self.config = config or MarketMakerConfig()
        self.inventory = 0.0  # 当前库存（正=多头，负=空头）
        self.last_quote_cycle = 0
        
        logger.info(f"做市商初始化: spread={self.config.spread_pct*100:.2f}%")
    
    def generate_quotes(
        self,
        current_price: float,
        cycle: int
    ) -> List[Dict]:
        """
        生成双边报价
        
        参数：
          - current_price: 当前市场价格
          - cycle: 当前周期
        
        返回：
          - quotes: 报价列表 [{'side': 'buy', 'price': ..., 'amount': ...}, ...]
        """
        quotes = []
        
        # 检查是否需要刷新报价
        if cycle - self.last_quote_cycle < self.config.quote_refresh_rate:
            return quotes
        
        self.last_quote_cycle = cycle
        
        # 计算买卖价格
        spread = current_price * self.config.spread_pct
        buy_price = current_price - spread / 2
        sell_price = current_price + spread / 2
        
        # 根据库存调整报价大小
        buy_size = self.config.order_size
        sell_size = self.config.order_size
        
        # 库存管理：如果库存过高，减少买单/增加卖单
        if self.inventory > self.config.max_inventory * 0.7:
            buy_size *= 0.5  # 减少买单
            sell_size *= 1.5  # 增加卖单
        elif self.inventory < -self.config.max_inventory * 0.7:
            buy_size *= 1.5  # 增加买单
            sell_size *= 0.5  # 减少卖单
        
        # 生成报价
        if abs(self.inventory) < self.config.max_inventory:
            quotes.append({
                'side': 'buy',
                'price': buy_price,
                'amount': buy_size,
                'type': 'limit'
            })
            quotes.append({
                'side': 'sell',
                'price': sell_price,
                'amount': sell_size,
                'type': 'limit'
            })
        
        logger.debug(
            f"做市商报价: buy@{buy_price:.2f} sell@{sell_price:.2f} "
            f"(inventory={self.inventory:.2f})"
        )
        
        return quotes
    
    def update_inventory(self, trade_side: str, trade_amount: float):
        """
        更新库存
        
        参数：
          - trade_side: 交易方向（'buy' or 'sell'）
          - trade_amount: 交易数量
        """
        if trade_side == 'buy':
            self.inventory += trade_amount
        else:
            self.inventory -= trade_amount
        
        logger.debug(f"做市商库存更新: {self.inventory:.2f}")
    
    def need_hedge(self) -> bool:
        """
        是否需要对冲
        
        规则：库存超过阈值时需要对冲
        """
        return abs(self.inventory) > self.config.max_inventory * 0.8
    
    def generate_hedge_order(self, current_price: float) -> Optional[Dict]:
        """
        生成对冲订单
        
        参数：
          - current_price: 当前市场价格
        
        返回：
          - order: 对冲订单
        """
        if not self.need_hedge():
            return None
        
        # 对冲方向：库存为正则卖出，库存为负则买入
        side = 'sell' if self.inventory > 0 else 'buy'
        amount = abs(self.inventory) * 0.5  # 对冲一半库存
        
        order = {
            'side': side,
            'price': None,  # 市价单
            'amount': amount,
            'type': 'market'
        }
        
        logger.info(f"做市商对冲: {side} {amount:.2f} (inventory={self.inventory:.2f})")
        
        return order
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        return {
            'type': 'market_maker',
            'inventory': self.inventory,
            'max_inventory': self.config.max_inventory,
            'spread_pct': self.config.spread_pct,
            'need_hedge': self.need_hedge()
        }

