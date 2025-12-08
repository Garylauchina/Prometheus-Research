"""
订单簿单元测试

测试OrderBook的核心功能：
  1. 订单添加和撤销
  2. 市价单撮合
  3. 限价单撮合
  4. 流动性计算
  5. 价格优先、时间优先规则
"""

import pytest
from prometheus.v6.self_play.order_book import (
    OrderBook,
    Order,
    OrderType,
    OrderSide,
    OrderStatus
)


class TestOrderBook:
    """订单簿测试套件"""
    
    def setup_method(self):
        """每个测试前初始化"""
        self.order_book = OrderBook()
    
    # ===== 基础功能测试 =====
    
    def test_add_limit_order(self):
        """测试：添加限价单"""
        order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=100.0
        )
        
        self.order_book.add_order(order)
        
        assert len(self.order_book.buy_orders) == 1
        assert self.order_book.best_bid() == 100.0
    
    def test_cancel_order(self):
        """测试：撤销订单"""
        order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=100.0
        )
        
        self.order_book.add_order(order)
        self.order_book.cancel_order("O001")
        
        assert order.status == OrderStatus.CANCELLED
        assert "O001" not in self.order_book.orders_map
    
    # ===== 市价单测试 =====
    
    def test_match_market_buy_order(self):
        """测试：市价买单成交"""
        order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            amount=10.0
        )
        
        current_price = 100.0
        trade, price_impact = self.order_book.match_market_order(order, current_price)
        
        assert trade is not None
        assert trade.amount == 10.0
        assert price_impact > 0  # 买单推高价格
        assert order.status == OrderStatus.FILLED
    
    def test_match_market_sell_order(self):
        """测试：市价卖单成交"""
        order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            amount=10.0
        )
        
        current_price = 100.0
        trade, price_impact = self.order_book.match_market_order(order, current_price)
        
        assert trade is not None
        assert trade.amount == 10.0
        assert price_impact < 0  # 卖单压低价格
        assert order.status == OrderStatus.FILLED
    
    # ===== 限价单测试 =====
    
    def test_match_limit_order_success(self):
        """测试：限价单匹配成功"""
        # 添加卖单
        sell_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=10.0,
            price=100.0
        )
        self.order_book.add_order(sell_order)
        
        # 添加买单（价格>=卖单价格，应该成交）
        buy_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=101.0
        )
        
        trade = self.order_book.match_limit_order(buy_order)
        
        assert trade is not None
        assert trade.amount == 10.0
        assert trade.price == 100.0  # 成交价=卖单价格
        assert buy_order.status == OrderStatus.FILLED
        assert sell_order.status == OrderStatus.FILLED
    
    def test_match_limit_order_no_match(self):
        """测试：限价单无法匹配"""
        # 添加卖单
        sell_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=10.0,
            price=100.0
        )
        self.order_book.add_order(sell_order)
        
        # 添加买单（价格<卖单价格，无法成交）
        buy_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=99.0
        )
        
        trade = self.order_book.match_limit_order(buy_order)
        
        assert trade is None
        assert buy_order.status == OrderStatus.PENDING
    
    def test_partial_fill(self):
        """测试：部分成交"""
        # 添加小的卖单
        sell_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=5.0,
            price=100.0
        )
        self.order_book.add_order(sell_order)
        
        # 添加大的买单（只能部分成交）
        buy_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=100.0
        )
        
        trade = self.order_book.match_limit_order(buy_order)
        
        assert trade is not None
        assert trade.amount == 5.0  # 只成交5.0
        assert buy_order.status == OrderStatus.PARTIAL
        assert buy_order.filled_amount == 5.0
        assert sell_order.status == OrderStatus.FILLED
    
    # ===== 价格优先测试 =====
    
    def test_price_priority(self):
        """测试：价格优先"""
        # 添加两个卖单，价格不同
        sell_order1 = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=10.0,
            price=101.0
        )
        sell_order2 = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=10.0,
            price=100.0  # 价格更低，应该优先
        )
        
        self.order_book.add_order(sell_order1)
        self.order_book.add_order(sell_order2)
        
        # 添加买单
        buy_order = Order(
            order_id="O003",
            agent_id="A003",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=102.0
        )
        
        trade = self.order_book.match_limit_order(buy_order)
        
        assert trade is not None
        assert trade.sell_order_id == "O002"  # 价格更低的卖单优先成交
        assert trade.price == 100.0
    
    # ===== 流动性测试 =====
    
    def test_liquidity_calculation(self):
        """测试：流动性计算"""
        # 添加买单和卖单
        buy_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=99.0
        )
        sell_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=20.0,
            price=101.0
        )
        
        self.order_book.add_order(buy_order)
        self.order_book.add_order(sell_order)
        
        liquidity = self.order_book.liquidity()
        
        assert liquidity == 30.0  # 10 + 20
    
    def test_spread_calculation(self):
        """测试：买卖价差计算"""
        # 添加买单和卖单
        buy_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=99.0
        )
        sell_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=10.0,
            price=101.0
        )
        
        self.order_book.add_order(buy_order)
        self.order_book.add_order(sell_order)
        
        spread = self.order_book.spread()
        
        assert spread == 2.0  # 101 - 99
    
    # ===== 统计信息测试 =====
    
    def test_get_statistics(self):
        """测试：获取统计信息"""
        # 添加一些订单
        buy_order = Order(
            order_id="O001",
            agent_id="A001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=10.0,
            price=99.0
        )
        sell_order = Order(
            order_id="O002",
            agent_id="A002",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            amount=20.0,
            price=101.0
        )
        
        self.order_book.add_order(buy_order)
        self.order_book.add_order(sell_order)
        
        stats = self.order_book.get_statistics()
        
        assert stats['buy_orders_count'] == 1
        assert stats['sell_orders_count'] == 1
        assert stats['liquidity'] == 30.0
        assert stats['best_bid'] == 99.0
        assert stats['best_ask'] == 101.0
        assert stats['spread'] == 2.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

