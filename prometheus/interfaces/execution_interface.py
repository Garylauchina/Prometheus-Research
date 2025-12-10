"""
ExecutionInterface - v8.0交易执行接口⭐⭐⭐

职责：
  • 为Moirai提供统一的交易执行接口
  • 支持实盘、回测、模拟三种模式
  • 屏蔽底层交易所差异

设计理念：
  • v7.0 Moirai只依赖这个接口
  • v8.0可以轻松切换交易所
  • 不侵入v7.0代码

Created: 2025-12-11
Author: Prometheus Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"      # 市价单
    LIMIT = "limit"        # 限价单
    STOP_LOSS = "stop_loss"  # 止损单
    TAKE_PROFIT = "take_profit"  # 止盈单


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"      # 待提交
    SUBMITTED = "submitted"  # 已提交
    FILLED = "filled"        # 已成交
    PARTIAL = "partial"      # 部分成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"    # 被拒绝
    FAILED = "failed"        # 失败


@dataclass
class Order:
    """
    订单数据结构⭐
    """
    # 基础信息
    order_id: str
    agent_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    
    # 数量和价格
    quantity: float
    price: Optional[float] = None  # 限价单需要
    
    # 状态
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    
    # 时间
    created_at: datetime = None
    updated_at: datetime = None
    filled_at: Optional[datetime] = None
    
    # 费用
    commission: float = 0.0
    commission_asset: str = "USDT"
    
    # 市场摩擦
    slippage: float = 0.0  # 滑点
    latency: float = 0.0   # 延迟（秒）
    
    # 扩展数据
    extras: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'agent_id': self.agent_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'commission': self.commission,
            'slippage': self.slippage,
            'latency': self.latency
        }


@dataclass
class Position:
    """
    持仓数据结构⭐
    """
    symbol: str
    agent_id: str
    side: OrderSide  # LONG or SHORT
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'agent_id': self.agent_id,
            'side': self.side.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }


class ExecutionInterface(ABC):
    """
    交易执行接口（抽象基类）⭐⭐⭐
    
    v7.0 Moirai通过这个接口执行交易
    v8.0提供多种实现：实盘、回测、模拟
    """
    
    @abstractmethod
    def submit_order(
        self,
        agent_id: str,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None
    ) -> Order:
        """
        提交订单⭐
        
        Args:
            agent_id: Agent ID
            symbol: 交易对
            side: 买/卖
            quantity: 数量
            order_type: 订单类型
            price: 价格（限价单需要）
        
        Returns:
            Order: 订单对象
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        查询订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            Optional[Order]: 订单对象，不存在返回None
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, agent_id: Optional[str] = None) -> List[Order]:
        """
        查询未完成订单
        
        Args:
            agent_id: Agent ID（可选，为None则返回所有）
        
        Returns:
            List[Order]: 未完成订单列表
        """
        pass
    
    @abstractmethod
    def get_position(self, agent_id: str, symbol: str) -> Optional[Position]:
        """
        查询持仓
        
        Args:
            agent_id: Agent ID
            symbol: 交易对
        
        Returns:
            Optional[Position]: 持仓对象，不存在返回None
        """
        pass
    
    @abstractmethod
    def get_all_positions(self, agent_id: Optional[str] = None) -> List[Position]:
        """
        查询所有持仓
        
        Args:
            agent_id: Agent ID（可选，为None则返回所有）
        
        Returns:
            List[Position]: 持仓列表
        """
        pass
    
    @abstractmethod
    def close_position(self, agent_id: str, symbol: str) -> Order:
        """
        平仓
        
        Args:
            agent_id: Agent ID
            symbol: 交易对
        
        Returns:
            Order: 平仓订单
        """
        pass
    
    @abstractmethod
    def close_all_positions(self, agent_id: Optional[str] = None) -> List[Order]:
        """
        平掉所有持仓（紧急止损用）⭐
        
        Args:
            agent_id: Agent ID（可选，为None则平掉所有Agent的持仓）
        
        Returns:
            List[Order]: 平仓订单列表
        """
        pass
    
    @abstractmethod
    def get_account_balance(self, agent_id: str) -> Dict[str, float]:
        """
        查询账户余额
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Dict: {'asset': amount}，例如{'USDT': 10000.0, 'BTC': 0.5}
        """
        pass


class LiveExecution(ExecutionInterface):
    """
    实盘交易执行⭐
    
    通过交易所API执行真实交易
    """
    
    def __init__(self, exchange: str, api_key: str, api_secret: str):
        """
        Args:
            exchange: 交易所名称（'okx', 'binance'等）
            api_key: API密钥
            api_secret: API密钥secret
        """
        self.exchange = exchange
        self.api_key = api_key
        
        # TODO: 初始化交易所连接
        logger.info(f"🔗 LiveExecution已初始化: {exchange}")
    
    def submit_order(self, agent_id: str, symbol: str, side: OrderSide, quantity: float, 
                    order_type: OrderType = OrderType.MARKET, price: Optional[float] = None) -> Order:
        """提交真实订单到交易所"""
        # TODO: 实现真实交易所API调用
        raise NotImplementedError("LiveExecution.submit_order() 待实现")
    
    def cancel_order(self, order_id: str) -> bool:
        """取消真实订单"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.cancel_order() 待实现")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """查询真实订单"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.get_order() 待实现")
    
    def get_open_orders(self, agent_id: Optional[str] = None) -> List[Order]:
        """查询真实未完成订单"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.get_open_orders() 待实现")
    
    def get_position(self, agent_id: str, symbol: str) -> Optional[Position]:
        """查询真实持仓"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.get_position() 待实现")
    
    def get_all_positions(self, agent_id: Optional[str] = None) -> List[Position]:
        """查询所有真实持仓"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.get_all_positions() 待实现")
    
    def close_position(self, agent_id: str, symbol: str) -> Order:
        """平掉真实持仓"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.close_position() 待实现")
    
    def close_all_positions(self, agent_id: Optional[str] = None) -> List[Order]:
        """平掉所有真实持仓（紧急止损）"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.close_all_positions() 待实现")
    
    def get_account_balance(self, agent_id: str) -> Dict[str, float]:
        """查询真实账户余额"""
        # TODO: 实现
        raise NotImplementedError("LiveExecution.get_account_balance() 待实现")


class SimulatedExecution(ExecutionInterface):
    """
    模拟交易执行⭐⭐⭐
    
    不连接真实交易所，在内存中模拟交易
    用于训练和测试
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        """
        Args:
            initial_balance: 初始资金
        """
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.balances: Dict[str, Dict[str, float]] = {}
        self.order_counter = 0
        
        logger.info(f"🎮 SimulatedExecution已初始化，初始资金=${initial_balance:,.2f}")
    
    def submit_order(self, agent_id: str, symbol: str, side: OrderSide, quantity: float,
                    order_type: OrderType = OrderType.MARKET, price: Optional[float] = None) -> Order:
        """
        模拟提交订单（立即成交）
        
        简化版：市价单立即100%成交
        """
        self.order_counter += 1
        order_id = f"SIM_{self.order_counter}"
        
        # 创建订单
        order = Order(
            order_id=order_id,
            agent_id=agent_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.FILLED,  # 简化：立即成交
            filled_quantity=quantity,
            avg_fill_price=price or 50000.0,  # 简化：使用指定价格或默认价格
            created_at=datetime.now(),
            filled_at=datetime.now(),
            commission=quantity * (price or 50000.0) * 0.001  # 0.1%手续费
        )
        
        self.orders[order_id] = order
        
        logger.debug(f"✅ 模拟订单已成交: {agent_id} {side.value} {quantity} {symbol} @ {order.avg_fill_price}")
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """取消模拟订单"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """查询模拟订单"""
        return self.orders.get(order_id)
    
    def get_open_orders(self, agent_id: Optional[str] = None) -> List[Order]:
        """查询未完成的模拟订单"""
        open_orders = [
            order for order in self.orders.values()
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL]
        ]
        if agent_id:
            open_orders = [o for o in open_orders if o.agent_id == agent_id]
        return open_orders
    
    def get_position(self, agent_id: str, symbol: str) -> Optional[Position]:
        """查询模拟持仓"""
        key = f"{agent_id}_{symbol}"
        return self.positions.get(key)
    
    def get_all_positions(self, agent_id: Optional[str] = None) -> List[Position]:
        """查询所有模拟持仓"""
        positions = list(self.positions.values())
        if agent_id:
            positions = [p for p in positions if p.agent_id == agent_id]
        return positions
    
    def close_position(self, agent_id: str, symbol: str) -> Order:
        """平掉模拟持仓"""
        position = self.get_position(agent_id, symbol)
        if not position:
            raise ValueError(f"持仓不存在: {agent_id}/{symbol}")
        
        # 创建平仓订单
        side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
        order = self.submit_order(
            agent_id=agent_id,
            symbol=symbol,
            side=side,
            quantity=position.quantity,
            price=position.current_price
        )
        
        # 删除持仓
        key = f"{agent_id}_{symbol}"
        del self.positions[key]
        
        return order
    
    def close_all_positions(self, agent_id: Optional[str] = None) -> List[Order]:
        """平掉所有模拟持仓"""
        positions = self.get_all_positions(agent_id)
        orders = []
        
        for position in positions:
            try:
                order = self.close_position(position.agent_id, position.symbol)
                orders.append(order)
            except Exception as e:
                logger.error(f"平仓失败: {position.agent_id}/{position.symbol}, {e}")
        
        return orders
    
    def get_account_balance(self, agent_id: str) -> Dict[str, float]:
        """查询模拟账户余额"""
        return self.balances.get(agent_id, {'USDT': 10000.0})


# ========== 工厂函数 ==========

def create_execution(
    mode: str,
    **kwargs
) -> ExecutionInterface:
    """
    工厂函数：创建交易执行接口⭐⭐⭐
    
    Args:
        mode: 模式（'live', 'simulation'）
        **kwargs: 各模式特定参数
    
    Returns:
        ExecutionInterface: 交易执行接口实例
    
    Examples:
        # 实盘
        execution = create_execution('live', exchange='okx', api_key='xxx', api_secret='yyy')
        
        # 模拟
        execution = create_execution('simulation', initial_balance=10000.0)
    """
    if mode == 'live':
        return LiveExecution(**kwargs)
    elif mode == 'simulation':
        return SimulatedExecution(**kwargs)
    else:
        raise ValueError(f"不支持的模式: {mode}")


if __name__ == "__main__":
    # 测试代码
    print("测试SimulatedExecution...")
    execution = SimulatedExecution(initial_balance=10000.0)
    
    # 提交买单
    order = execution.submit_order(
        agent_id='agent_1',
        symbol='BTC-USDT',
        side=OrderSide.BUY,
        quantity=0.1,
        price=50000.0
    )
    print(f"订单已提交: {order.order_id}, 状态={order.status.value}")
    
    # 查询订单
    retrieved_order = execution.get_order(order.order_id)
    print(f"订单查询: {retrieved_order.order_id}, 成交价={retrieved_order.avg_fill_price}")
    
    print("\n✅ ExecutionInterface设计完成！")

