"""
Agent市场接口

提供Agent与市场交互的标准接口：
- 查询市场状态（订单簿、价格、价差等）
- 评估交易成本（价差+滑点+冲击）
- 提交订单
- 查询订单状态

Author: Prometheus Team
Version: v5.3
Date: 2025-12-06
"""

import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"      # 待提交
    SUBMITTED = "submitted"  # 已提交
    FILLED = "filled"        # 已成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"    # 被拒绝


@dataclass
class MarketState:
    """市场状态快照"""
    price: float                      # 当前价格
    spread_pct: float                 # 价差（百分比）
    liquidity_factor: float           # 流动性因子（0-1）
    order_book_depth: Dict[str, List] # 订单簿深度 {'bids': [...], 'asks': [...]}
    timestamp: float                  # 时间戳


@dataclass
class TradeCost:
    """交易成本评估"""
    spread_cost: float        # 价差成本
    slippage_cost: float      # 滑点成本
    impact_cost: float        # 市场冲击成本
    total_cost: float         # 总成本
    total_cost_pct: float     # 总成本百分比
    estimated_price: float    # 预估成交价格


@dataclass
class Order:
    """订单"""
    order_id: str
    agent_id: str
    side: OrderSide
    quantity: float
    price: Optional[float] = None  # None表示市价单
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    cost: Optional[TradeCost] = None


class AgentMarketInterface:
    """
    Agent市场接口
    
    为Agent提供与市场交互的标准接口，包括：
    1. 查询市场状态
    2. 评估交易成本
    3. 提交订单
    4. 查询订单状态
    
    设计目标：
    - 简单易用
    - 考虑真实交易成本
    - 支持理性决策
    """
    
    def __init__(self, 
                 market,
                 network_simulator=None):
        """
        初始化Agent市场接口
        
        Args:
            market: 市场对象（AdvancedOpponentMarket）
            network_simulator: 网络延迟模拟器（可选）
        """
        self.market = market
        self.network = network_simulator
        
        self.orders = {}  # order_id -> Order
        self.next_order_id = 1
        
        logger.debug("🔌 Agent市场接口已初始化")
    
    def query_market_state(self) -> MarketState:
        """
        查询当前市场状态
        
        包含：价格、价差、流动性、订单簿深度
        
        Returns:
            MarketState对象
        """
        # 模拟市场数据延迟
        if self.network:
            self.network.simulate_market_data_delay(execute=True)
        
        # 获取市场状态
        spread_abs, spread_pct = self.market.order_book.get_spread()
        order_book_depth = self.market.order_book.get_depth(levels=5)
        
        market_state = MarketState(
            price=self.market.current_price,
            spread_pct=spread_pct,
            liquidity_factor=self.market.liquidity_mgr.current_liquidity,
            order_book_depth=order_book_depth,
            timestamp=0.0  # 简化：不使用时间戳
        )
        
        return market_state
    
    def estimate_trade_cost(self, 
                           side: OrderSide, 
                           quantity: float,
                           current_price: float) -> TradeCost:
        """
        评估交易成本
        
        包含：价差成本 + 滑点成本 + 市场冲击成本
        
        Args:
            side: 买/卖
            quantity: 交易数量
            current_price: 当前价格
            
        Returns:
            TradeCost对象
        """
        trade_value = quantity * current_price
        
        # 1. 价差成本
        _, spread_pct = self.market.order_book.get_spread()
        spread_cost = trade_value * spread_pct
        
        # 2. 滑点成本
        liquidity = self.market.liquidity_mgr.current_liquidity
        slippage_pct = self.market.slippage_calc.calculate_slippage(
            trade_value, 
            liquidity
        )
        slippage_cost = trade_value * slippage_pct
        
        # 3. 市场冲击成本
        impact_cost = self.market.impact_calc.calculate_total_cost(
            trade_value=trade_value,
            liquidity=liquidity,
            spread_pct=spread_pct
        )
        
        # 4. 总成本
        total_cost = spread_cost + slippage_cost + impact_cost
        total_cost_pct = total_cost / trade_value if trade_value > 0 else 0
        
        # 5. 预估成交价格
        if side == OrderSide.BUY:
            estimated_price = current_price * (1 + total_cost_pct)
        else:
            estimated_price = current_price * (1 - total_cost_pct)
        
        return TradeCost(
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            impact_cost=impact_cost,
            total_cost=total_cost,
            total_cost_pct=total_cost_pct,
            estimated_price=estimated_price
        )
    
    def submit_order(self, 
                    agent_id: str,
                    side: OrderSide, 
                    quantity: float,
                    price: Optional[float] = None) -> Order:
        """
        提交订单
        
        Args:
            agent_id: Agent ID
            side: 买/卖
            quantity: 数量
            price: 价格（None表示市价单）
            
        Returns:
            Order对象
        """
        # 模拟订单提交延迟
        if self.network:
            self.network.simulate_order_delay(execute=True)
        
        # 创建订单
        order_id = f"ORD_{self.next_order_id}"
        self.next_order_id += 1
        
        # 评估成本
        current_price = self.market.current_price
        cost = self.estimate_trade_cost(side, quantity, current_price)
        
        order = Order(
            order_id=order_id,
            agent_id=agent_id,
            side=side,
            quantity=quantity,
            price=price,
            status=OrderStatus.SUBMITTED,
            cost=cost
        )
        
        self.orders[order_id] = order
        
        # 简化：立即成交（未来可以实现订单簿撮合）
        order.status = OrderStatus.FILLED
        order.filled_quantity = quantity
        order.filled_price = cost.estimated_price
        
        logger.debug(f"📤 订单提交: {agent_id} | {side.value} {quantity:.4f} @ ${cost.estimated_price:.2f}")
        
        return order
    
    def check_order_status(self, order_id: str) -> Optional[Order]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            Order对象，如果订单不存在返回None
        """
        # 模拟确认延迟
        if self.network:
            self.network.simulate_confirmation_delay(execute=True)
        
        return self.orders.get(order_id)
    
    def can_afford_trade(self, 
                        agent_capital: float,
                        side: OrderSide,
                        quantity: float,
                        current_price: float) -> Tuple[bool, str]:
        """
        检查Agent是否有足够资金进行交易
        
        Args:
            agent_capital: Agent当前资金
            side: 买/卖
            quantity: 数量
            current_price: 当前价格
            
        Returns:
            (是否可以交易, 原因)
        """
        if side == OrderSide.BUY:
            # 买入需要资金
            cost = self.estimate_trade_cost(side, quantity, current_price)
            required = quantity * cost.estimated_price
            
            if agent_capital >= required:
                return True, "OK"
            else:
                return False, f"资金不足: 需要${required:.2f}, 拥有${agent_capital:.2f}"
        
        else:
            # 卖出需要持仓（简化：假设总是有持仓）
            return True, "OK"
    
    def get_stats(self) -> Dict:
        """获取接口统计"""
        return {
            'total_orders': len(self.orders),
            'filled_orders': sum(1 for o in self.orders.values() if o.status == OrderStatus.FILLED),
            'pending_orders': sum(1 for o in self.orders.values() if o.status == OrderStatus.PENDING),
            'network_stats': self.network.get_stats() if self.network else None
        }


# ============================================
# 测试代码
# ============================================

def test_agent_market_interface():
    """测试Agent市场接口"""
    print("="*70)
    print("🧪 Agent市场接口测试")
    print("="*70)
    
    # 需要导入市场和网络模拟器
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from prometheus.market.advanced_market import AdvancedOpponentMarket
        from prometheus.market.network_simulator import NetworkSimulator
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 1. 创建市场
    print("\n1️⃣ 创建市场...")
    market = AdvancedOpponentMarket(
        initial_price=50000.0,
        num_market_makers=2,
        num_arbitrageurs=3,
        num_whales=1,
        num_hfts=5,
        num_passive=10,
        num_panic=15
    )
    print("   ✅ 市场创建完成")
    
    # 2. 创建网络模拟器
    print("\n2️⃣ 创建网络模拟器...")
    network = NetworkSimulator(enabled=True, base_latency_ms=30, jitter_ms=10)
    print("   ✅ 网络模拟器创建完成")
    
    # 3. 创建Agent市场接口
    print("\n3️⃣ 创建Agent市场接口...")
    interface = AgentMarketInterface(market=market, network_simulator=network)
    print("   ✅ 接口创建完成")
    
    # 4. 查询市场状态
    print("\n4️⃣ 查询市场状态...")
    import time
    start = time.time()
    state = interface.query_market_state()
    elapsed = (time.time() - start) * 1000
    print(f"   价格: ${state.price:,.2f}")
    print(f"   价差: {state.spread_pct*100:.3f}%")
    print(f"   流动性: {state.liquidity_factor:.2f}")
    print(f"   查询延迟: {elapsed:.2f}ms")
    
    # 5. 评估交易成本
    print("\n5️⃣ 评估交易成本（买入0.1 BTC）...")
    cost = interface.estimate_trade_cost(
        side=OrderSide.BUY,
        quantity=0.1,
        current_price=state.price
    )
    print(f"   交易价值: ${0.1 * state.price:,.2f}")
    print(f"   价差成本: ${cost.spread_cost:.2f} ({cost.spread_cost/(0.1*state.price)*100:.3f}%)")
    print(f"   滑点成本: ${cost.slippage_cost:.2f}")
    print(f"   冲击成本: ${cost.impact_cost:.2f}")
    print(f"   总成本: ${cost.total_cost:.2f} ({cost.total_cost_pct*100:.3f}%)")
    print(f"   预估成交价: ${cost.estimated_price:,.2f}")
    
    # 6. 检查是否可以交易
    print("\n6️⃣ 检查资金是否足够...")
    agent_capital = 10000.0
    can_trade, reason = interface.can_afford_trade(
        agent_capital=agent_capital,
        side=OrderSide.BUY,
        quantity=0.1,
        current_price=state.price
    )
    print(f"   Agent资金: ${agent_capital:,.2f}")
    print(f"   可以交易: {can_trade}")
    print(f"   原因: {reason}")
    
    # 7. 提交订单
    if can_trade:
        print("\n7️⃣ 提交买单...")
        start = time.time()
        order = interface.submit_order(
            agent_id="AGENT_TEST_001",
            side=OrderSide.BUY,
            quantity=0.1
        )
        elapsed = (time.time() - start) * 1000
        print(f"   订单ID: {order.order_id}")
        print(f"   状态: {order.status.value}")
        print(f"   成交数量: {order.filled_quantity:.4f}")
        print(f"   成交价格: ${order.filled_price:,.2f}")
        print(f"   提交延迟: {elapsed:.2f}ms")
        
        # 8. 查询订单状态
        print("\n8️⃣ 查询订单状态...")
        start = time.time()
        order_status = interface.check_order_status(order.order_id)
        elapsed = (time.time() - start) * 1000
        print(f"   订单ID: {order_status.order_id}")
        print(f"   状态: {order_status.status.value}")
        print(f"   查询延迟: {elapsed:.2f}ms")
    
    # 9. 统计
    print("\n9️⃣ 接口统计...")
    stats = interface.get_stats()
    print(f"   总订单数: {stats['total_orders']}")
    print(f"   已成交: {stats['filled_orders']}")
    print(f"   待处理: {stats['pending_orders']}")
    if stats['network_stats']:
        net_stats = stats['network_stats']
        print(f"   网络延迟次数: {net_stats['total_delays']}")
        print(f"   平均延迟: {net_stats['avg_delay_ms']:.2f}ms")
    
    print("\n✅ 测试完成！")
    print("="*70)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    test_agent_market_interface()

