"""
订单簿模块

实现真实市场的订单簿机制，包括：
- 订单管理（添加、撤销、匹配）
- 市价单撮合（立即成交）
- 限价单撮合（等待匹配）
- 流动性计算

遵循三大铁律：
  - 铁律1: 通过AdversarialMarket统一调用
  - 铁律2: 本模块为Self-Play内部实现
  - 铁律3: 所有订单撮合原子化
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
import heapq
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = 'market'    # 市价单
    LIMIT = 'limit'      # 限价单


class OrderSide(Enum):
    """订单方向"""
    BUY = 'buy'
    SELL = 'sell'


class OrderStatus(Enum):
    """订单状态"""
    PENDING = 'pending'                      # 待成交
    PARTIAL = 'partial'                      # 部分成交
    FILLED = 'filled'                        # 完全成交
    CANCELLED = 'cancelled'                  # 已撤销
    REJECTED_INSUFFICIENT_CAPITAL = 'rejected_capital'  # 资金不足
    REJECTED_RISK_LIMIT = 'rejected_risk'    # 风控限制
    REJECTED_EXCHANGE_ERROR = 'rejected_exchange'  # 交易所错误


@dataclass
class Order:
    """
    订单数据结构
    
    属性：
      - order_id: 订单ID
      - agent_id: Agent ID
      - order_type: 订单类型（market/limit）
      - side: 订单方向（buy/sell）
      - amount: 数量
      - price: 价格（限价单必须，市价单为None）
      - timestamp: 时间戳
      - status: 订单状态
    """
    order_id: str
    agent_id: str
    order_type: OrderType
    side: OrderSide
    amount: float
    price: Optional[float] = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    
    def __lt__(self, other):
        """
        比较函数（用于heapq）
        
        买单：价格高的优先
        卖单：价格低的优先
        同价：时间早的优先
        """
        if self.side == OrderSide.BUY:
            # 买单：价格降序，时间升序
            if self.price != other.price:
                return self.price > other.price
            return self.timestamp < other.timestamp
        else:
            # 卖单：价格升序，时间升序
            if self.price != other.price:
                return self.price < other.price
            return self.timestamp < other.timestamp


@dataclass
class Trade:
    """
    成交记录
    
    属性：
      - trade_id: 成交ID
      - buy_order_id: 买单ID
      - sell_order_id: 卖单ID
      - price: 成交价
      - amount: 成交量
      - timestamp: 时间戳
    """
    trade_id: str
    buy_order_id: str
    sell_order_id: str
    buyer_agent_id: str
    seller_agent_id: str
    price: float
    amount: float
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class OrderBook:
    """
    订单簿
    
    功能：
      1. 管理买单和卖单
      2. 撮合市价单（立即成交）
      3. 撮合限价单（等待匹配）
      4. 计算流动性
    
    数据结构：
      - buy_orders: 买单队列（最大堆）
      - sell_orders: 卖单队列（最小堆）
    """
    
    def __init__(self):
        self.buy_orders: List[Order] = []   # 买单（价格降序）
        self.sell_orders: List[Order] = []  # 卖单（价格升序）
        self.orders_map: Dict[str, Order] = {}  # order_id -> Order
        self.trades: List[Trade] = []
        self.next_trade_id: int = 0
    
    # ===== 订单管理 =====
    
    def add_order(self, order: Order):
        """
        添加订单到订单簿
        
        参数：
          - order: 订单对象
        """
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                heapq.heappush(self.buy_orders, order)
            else:
                heapq.heappush(self.sell_orders, order)
            
            self.orders_map[order.order_id] = order
            logger.debug(f"添加限价单: {order.order_id} {order.side.value} {order.amount}@{order.price}")
    
    def cancel_order(self, order_id: str):
        """
        撤销订单
        
        参数：
          - order_id: 订单ID
        """
        if order_id in self.orders_map:
            order = self.orders_map[order_id]
            order.status = OrderStatus.CANCELLED
            del self.orders_map[order_id]
            logger.debug(f"撤销订单: {order_id}")
    
    # ===== 订单撮合 =====
    
    def match_market_order(
        self,
        order: Order,
        current_price: float
    ) -> Tuple[Optional[Trade], float]:
        """
        撮合市价单
        
        市价单特点：
          - 立即成交
          - 但会产生价格冲击
          - 如果流动性不足，会部分成交
        
        参数：
          - order: 市价单
          - current_price: 当前市场价格
        
        返回：
          - trade: 成交记录（如果成功）
          - price_impact: 价格冲击
        """
        if order.order_type != OrderType.MARKET:
            logger.warning(f"订单{order.order_id}不是市价单")
            return None, 0.0
        
        # 计算价格冲击
        liquidity = self.liquidity()
        if liquidity <= 0:
            liquidity = 1000.0  # 默认流动性
        
        price_impact = self._calculate_price_impact(order.amount, liquidity, order.side)
        execution_price = current_price + price_impact
        
        # 创建成交记录
        trade = Trade(
            trade_id=f"T{self.next_trade_id:06d}",
            buy_order_id=order.order_id if order.side == OrderSide.BUY else "MARKET",
            sell_order_id=order.order_id if order.side == OrderSide.SELL else "MARKET",
            buyer_agent_id=order.agent_id if order.side == OrderSide.BUY else "MARKET",
            seller_agent_id=order.agent_id if order.side == OrderSide.SELL else "MARKET",
            price=execution_price,
            amount=order.amount
        )
        
        self.next_trade_id += 1
        self.trades.append(trade)
        
        order.status = OrderStatus.FILLED
        order.filled_amount = order.amount
        
        logger.debug(
            f"市价单成交: {order.order_id} {order.side.value} "
            f"{order.amount}@{execution_price:.2f} (冲击: {price_impact:+.2f})"
        )
        
        return trade, price_impact
    
    def match_limit_order(self, order: Order) -> Optional[Trade]:
        """
        撮合限价单
        
        限价单特点：
          - 等待匹配
          - 价格优先，时间优先
          - 可能部分成交
        
        参数：
          - order: 限价单
        
        返回：
          - trade: 成交记录（如果匹配成功）
        """
        if order.order_type != OrderType.LIMIT:
            logger.warning(f"订单{order.order_id}不是限价单")
            return None
        
        # 尝试匹配
        if order.side == OrderSide.BUY:
            # 买单：尝试匹配卖单
            if not self.sell_orders:
                return None
            
            best_sell = self.sell_orders[0]
            if order.price >= best_sell.price:
                # 价格匹配，撮合成交
                heapq.heappop(self.sell_orders)
                
                # 成交价格：限价单价格
                execution_price = best_sell.price
                execution_amount = min(order.amount - order.filled_amount, 
                                      best_sell.amount - best_sell.filled_amount)
                
                trade = Trade(
                    trade_id=f"T{self.next_trade_id:06d}",
                    buy_order_id=order.order_id,
                    sell_order_id=best_sell.order_id,
                    buyer_agent_id=order.agent_id,
                    seller_agent_id=best_sell.agent_id,
                    price=execution_price,
                    amount=execution_amount
                )
                
                self.next_trade_id += 1
                self.trades.append(trade)
                
                # 更新订单状态
                order.filled_amount += execution_amount
                best_sell.filled_amount += execution_amount
                
                if order.filled_amount >= order.amount:
                    order.status = OrderStatus.FILLED
                else:
                    order.status = OrderStatus.PARTIAL
                
                if best_sell.filled_amount >= best_sell.amount:
                    best_sell.status = OrderStatus.FILLED
                    del self.orders_map[best_sell.order_id]
                else:
                    best_sell.status = OrderStatus.PARTIAL
                    heapq.heappush(self.sell_orders, best_sell)
                
                logger.debug(
                    f"限价单成交: Buy{order.order_id} x Sell{best_sell.order_id} "
                    f"{execution_amount}@{execution_price:.2f}"
                )
                
                return trade
        
        else:
            # 卖单：尝试匹配买单
            if not self.buy_orders:
                return None
            
            best_buy = self.buy_orders[0]
            if order.price <= best_buy.price:
                # 价格匹配，撮合成交
                heapq.heappop(self.buy_orders)
                
                # 成交价格：限价单价格
                execution_price = best_buy.price
                execution_amount = min(order.amount - order.filled_amount,
                                      best_buy.amount - best_buy.filled_amount)
                
                trade = Trade(
                    trade_id=f"T{self.next_trade_id:06d}",
                    buy_order_id=best_buy.order_id,
                    sell_order_id=order.order_id,
                    buyer_agent_id=best_buy.agent_id,
                    seller_agent_id=order.agent_id,
                    price=execution_price,
                    amount=execution_amount
                )
                
                self.next_trade_id += 1
                self.trades.append(trade)
                
                # 更新订单状态
                order.filled_amount += execution_amount
                best_buy.filled_amount += execution_amount
                
                if order.filled_amount >= order.amount:
                    order.status = OrderStatus.FILLED
                else:
                    order.status = OrderStatus.PARTIAL
                
                if best_buy.filled_amount >= best_buy.amount:
                    best_buy.status = OrderStatus.FILLED
                    del self.orders_map[best_buy.order_id]
                else:
                    best_buy.status = OrderStatus.PARTIAL
                    heapq.heappush(self.buy_orders, best_buy)
                
                logger.debug(
                    f"限价单成交: Buy{best_buy.order_id} x Sell{order.order_id} "
                    f"{execution_amount}@{execution_price:.2f}"
                )
                
                return trade
        
        return None
    
    # ===== 辅助方法 =====
    
    def liquidity(self) -> float:
        """
        计算流动性
        
        流动性 = 订单簿深度
              = 买单总量 + 卖单总量
        """
        buy_liquidity = sum(o.amount - o.filled_amount for o in self.buy_orders)
        sell_liquidity = sum(o.amount - o.filled_amount for o in self.sell_orders)
        return buy_liquidity + sell_liquidity
    
    def _calculate_price_impact(
        self,
        amount: float,
        liquidity: float,
        side: OrderSide
    ) -> float:
        """
        计算价格冲击
        
        公式：impact = k * (amount / liquidity)^0.5
        
        参数：
          - amount: 订单数量
          - liquidity: 流动性
          - side: 订单方向
        
        返回：
          - price_impact: 价格冲击（买单为正，卖单为负）
        """
        if liquidity <= 0:
            return 0.0
        
        impact_coefficient = 0.001  # 冲击系数
        normalized_amount = amount / liquidity
        impact = impact_coefficient * (normalized_amount ** 0.5)
        
        # 买单推高价格，卖单压低价格
        if side == OrderSide.BUY:
            return impact
        else:
            return -impact
    
    def best_bid(self) -> Optional[float]:
        """最优买价"""
        if self.buy_orders:
            return self.buy_orders[0].price
        return None
    
    def best_ask(self) -> Optional[float]:
        """最优卖价"""
        if self.sell_orders:
            return self.sell_orders[0].price
        return None
    
    def spread(self) -> Optional[float]:
        """买卖价差"""
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is not None and ask is not None:
            return ask - bid
        return None
    
    def get_statistics(self) -> Dict:
        """获取订单簿统计信息"""
        return {
            'buy_orders_count': len(self.buy_orders),
            'sell_orders_count': len(self.sell_orders),
            'liquidity': self.liquidity(),
            'best_bid': self.best_bid(),
            'best_ask': self.best_ask(),
            'spread': self.spread(),
            'total_trades': len(self.trades)
        }
    
    def clear(self):
        """清空订单簿"""
        self.buy_orders.clear()
        self.sell_orders.clear()
        self.orders_map.clear()
        logger.debug("订单簿已清空")

