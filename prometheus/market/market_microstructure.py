"""
市场微观结构模拟模块

实现真实市场的微观结构特征：
1. OrderBook - 订单簿（多档位买卖报价）
2. SpreadManager - 价差管理（动态买卖价差）
3. SlippageCalculator - 滑点计算（大额订单成交价差异）
4. LiquidityManager - 流动性管理（流动性冲击和恢复）
5. MarketImpactCalculator - 市场冲击成本（综合交易成本）

Author: Prometheus Team
Version: v5.3
Date: 2025-12-06
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """订单簿单档位"""
    price: float
    size: float
    timestamp: datetime = None


@dataclass
class Trade:
    """成交记录"""
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    timestamp: datetime
    trader_type: str = "unknown"


class OrderBook:
    """
    订单簿（Order Book）
    
    维护多档位的买卖报价，模拟真实交易所的订单簿。
    
    特性：
    - 双向多档报价（默认10档）
    - 实时订单匹配
    - 深度查询
    - 最优买卖价
    """
    
    def __init__(self, num_levels: int = 10, initial_mid_price: float = 50000.0):
        """
        初始化订单簿
        
        Args:
            num_levels: 每侧的档位数量
            initial_mid_price: 初始中间价
        """
        self.num_levels = num_levels
        self.mid_price = initial_mid_price
        
        # 订单簿：[(price, size), ...]
        self.bids: List[OrderBookLevel] = []  # 买单（价格从高到低）
        self.asks: List[OrderBookLevel] = []  # 卖单（价格从低到高）
        
        # 初始化订单簿
        self._initialize_book()
        
        logger.debug(f"订单簿已初始化 | 档位: {num_levels} | 中间价: ${initial_mid_price:,.2f}")
    
    def _initialize_book(self):
        """初始化订单簿（创建初始报价）"""
        # 基础价差：0.1%
        base_spread = self.mid_price * 0.001
        
        # 创建买单（从最优买价开始，价格递减）
        best_bid = self.mid_price - base_spread / 2
        for i in range(self.num_levels):
            price = best_bid - i * (base_spread * 0.5)
            size = np.random.uniform(5, 20)  # 5-20 BTC
            self.bids.append(OrderBookLevel(price, size, datetime.now()))
        
        # 创建卖单（从最优卖价开始，价格递增）
        best_ask = self.mid_price + base_spread / 2
        for i in range(self.num_levels):
            price = best_ask + i * (base_spread * 0.5)
            size = np.random.uniform(5, 20)
            self.asks.append(OrderBookLevel(price, size, datetime.now()))
    
    def get_best_bid_ask(self) -> Tuple[float, float]:
        """
        获取最优买卖价
        
        Returns:
            (best_bid, best_ask)
        """
        if not self.bids or not self.asks:
            return self.mid_price * 0.999, self.mid_price * 1.001
        
        return self.bids[0].price, self.asks[0].price
    
    def get_spread(self) -> Tuple[float, float]:
        """
        获取价差
        
        Returns:
            (spread_absolute, spread_percentage)
        """
        best_bid, best_ask = self.get_best_bid_ask()
        spread_abs = best_ask - best_bid
        spread_pct = spread_abs / self.mid_price
        return spread_abs, spread_pct
    
    def get_mid_price(self) -> float:
        """获取中间价"""
        best_bid, best_ask = self.get_best_bid_ask()
        return (best_bid + best_ask) / 2
    
    def get_depth(self, levels: int = 5) -> Dict:
        """
        获取市场深度
        
        Args:
            levels: 查询档位数
            
        Returns:
            {
                'bids': [(price, size), ...],
                'asks': [(price, size), ...],
                'bid_total_size': float,
                'ask_total_size': float
            }
        """
        levels = min(levels, self.num_levels)
        
        bids_data = [(b.price, b.size) for b in self.bids[:levels]]
        asks_data = [(a.price, a.size) for a in self.asks[:levels]]
        
        bid_total = sum(b[1] for b in bids_data)
        ask_total = sum(a[1] for a in asks_data)
        
        return {
            'bids': bids_data,
            'asks': asks_data,
            'bid_total_size': bid_total,
            'ask_total_size': ask_total,
            'depth_imbalance': (bid_total - ask_total) / (bid_total + ask_total) if (bid_total + ask_total) > 0 else 0
        }
    
    def add_order(self, side: str, price: float, size: float):
        """
        添加订单到订单簿
        
        Args:
            side: 'bid' or 'ask'
            price: 价格
            size: 数量
        """
        order = OrderBookLevel(price, size, datetime.now())
        
        if side == 'bid':
            self.bids.append(order)
            # 保持价格从高到低排序
            self.bids.sort(key=lambda x: x.price, reverse=True)
            # 只保留最好的N档
            self.bids = self.bids[:self.num_levels]
        else:
            self.asks.append(order)
            # 保持价格从低到高排序
            self.asks.sort(key=lambda x: x.price)
            self.asks = self.asks[:self.num_levels]
    
    def match_order(self, side: str, size: float, aggressive: bool = True) -> List[Trade]:
        """
        匹配订单（模拟市价单成交）
        
        Args:
            side: 'buy' or 'sell'
            size: 订单大小
            aggressive: True=吃单（市价单），False=挂单（限价单）
            
        Returns:
            成交列表
        """
        trades = []
        remaining_size = size
        
        # 买单：吃卖单
        if side == 'buy':
            for i, ask in enumerate(self.asks):
                if remaining_size <= 0:
                    break
                
                # 成交数量
                fill_size = min(remaining_size, ask.size)
                
                # 记录成交
                trades.append(Trade(
                    price=ask.price,
                    size=fill_size,
                    side='buy',
                    timestamp=datetime.now()
                ))
                
                # 更新订单簿
                self.asks[i].size -= fill_size
                remaining_size -= fill_size
            
            # 移除完全成交的订单
            self.asks = [a for a in self.asks if a.size > 0]
        
        # 卖单：吃买单
        else:
            for i, bid in enumerate(self.bids):
                if remaining_size <= 0:
                    break
                
                fill_size = min(remaining_size, bid.size)
                
                trades.append(Trade(
                    price=bid.price,
                    size=fill_size,
                    side='sell',
                    timestamp=datetime.now()
                ))
                
                self.bids[i].size -= fill_size
                remaining_size -= fill_size
            
            self.bids = [b for b in self.bids if b.size > 0]
        
        # 如果有未成交的，说明流动性不足
        if remaining_size > 0:
            logger.warning(f"订单部分未成交 | 剩余: {remaining_size:.2f}")
        
        return trades
    
    def update_prices(self, new_mid_price: float, volatility: float = 0.001):
        """
        更新订单簿价格（市场价格变动）
        
        Args:
            new_mid_price: 新的中间价
            volatility: 波动率（影响价差）
        """
        old_mid = self.mid_price
        self.mid_price = new_mid_price
        price_change_ratio = new_mid_price / old_mid
        
        # 更新所有买卖单价格
        for bid in self.bids:
            bid.price *= price_change_ratio
        
        for ask in self.asks:
            ask.price *= price_change_ratio
        
        # 根据波动率调整价差
        self._adjust_spread_for_volatility(volatility)
        
        # 补充流动性（如果档位不足）
        self._replenish_liquidity()
    
    def _adjust_spread_for_volatility(self, volatility: float):
        """根据波动率调整价差"""
        # 波动率越高，价差越大
        spread_multiplier = 1.0 + volatility * 10
        
        if self.bids and self.asks:
            current_spread = self.asks[0].price - self.bids[0].price
            target_spread = self.mid_price * 0.001 * spread_multiplier
            
            if current_spread < target_spread:
                # 扩大价差
                adjustment = (target_spread - current_spread) / 2
                for bid in self.bids:
                    bid.price -= adjustment
                for ask in self.asks:
                    ask.price += adjustment
    
    def _replenish_liquidity(self):
        """补充流动性（确保有足够的档位）"""
        # 补充买单
        while len(self.bids) < self.num_levels:
            if self.bids:
                last_price = self.bids[-1].price
                new_price = last_price - self.mid_price * 0.0005
            else:
                new_price = self.mid_price * 0.999
            
            size = np.random.uniform(5, 20)
            self.bids.append(OrderBookLevel(new_price, size, datetime.now()))
        
        # 补充卖单
        while len(self.asks) < self.num_levels:
            if self.asks:
                last_price = self.asks[-1].price
                new_price = last_price + self.mid_price * 0.0005
            else:
                new_price = self.mid_price * 1.001
            
            size = np.random.uniform(5, 20)
            self.asks.append(OrderBookLevel(new_price, size, datetime.now()))


class SpreadManager:
    """
    价差管理器（Spread Manager）
    
    动态管理买卖价差，考虑：
    - 波动率（高波动 → 大价差）
    - 流动性（低流动性 → 大价差）
    - 市场时间（低峰期 → 大价差）
    """
    
    def __init__(self, base_spread_bps: float = 10.0):
        """
        Args:
            base_spread_bps: 基础价差（基点，1 bps = 0.01%）
        """
        self.base_spread_bps = base_spread_bps
        self.current_spread_bps = base_spread_bps
        
        logger.debug(f"价差管理器已初始化 | 基础价差: {base_spread_bps} bps")
    
    def calculate_spread(
        self,
        mid_price: float,
        volatility: float,
        liquidity_factor: float,
        time_of_day_factor: float = 1.0
    ) -> Tuple[float, float]:
        """
        计算当前价差
        
        Args:
            mid_price: 中间价
            volatility: 波动率（0-1）
            liquidity_factor: 流动性因子（0-1，1=正常）
            time_of_day_factor: 时间因子（0.5-1.5）
            
        Returns:
            (bid_price, ask_price)
        """
        # 波动率影响（波动率越高，价差越大）
        volatility_multiplier = 1.0 + volatility * 5
        
        # 流动性影响（流动性越低，价差越大）
        liquidity_multiplier = 2.0 - liquidity_factor  # 0.5流动性 → 1.5倍价差
        
        # 综合价差
        total_spread_bps = (self.base_spread_bps * 
                           volatility_multiplier * 
                           liquidity_multiplier * 
                           time_of_day_factor)
        
        # 限制最大最小价差
        total_spread_bps = np.clip(total_spread_bps, 5.0, 50.0)  # 0.05% - 0.5%
        
        self.current_spread_bps = total_spread_bps
        
        # 计算买卖价
        spread_amount = mid_price * (total_spread_bps / 10000)
        bid_price = mid_price - spread_amount / 2
        ask_price = mid_price + spread_amount / 2
        
        return bid_price, ask_price
    
    def get_spread_cost(self, size: float, mid_price: float) -> float:
        """
        计算价差成本
        
        Args:
            size: 交易数量
            mid_price: 中间价
            
        Returns:
            价差成本（USD）
        """
        spread_pct = self.current_spread_bps / 10000
        return size * mid_price * spread_pct / 2  # 单边成本


class SlippageCalculator:
    """
    滑点计算器（Slippage Calculator）
    
    计算大额订单的滑点：
    - 订单越大，滑点越大
    - 订单簿深度越浅，滑点越大
    - 买单向上滑点，卖单向下滑点
    """
    
    def __init__(self):
        logger.debug("滑点计算器已初始化")
    
    def calculate_slippage(
        self,
        order_size: float,
        order_book: OrderBook,
        side: str
    ) -> Tuple[float, float, List[Trade]]:
        """
        计算滑点
        
        Args:
            order_size: 订单大小（BTC）
            order_book: 订单簿
            side: 'buy' or 'sell'
            
        Returns:
            (average_fill_price, slippage_pct, trades)
        """
        # 模拟订单成交
        trades = order_book.match_order(side, order_size)
        
        if not trades:
            # 无法成交
            logger.warning(f"订单无法成交 | 规模: {order_size} | 方向: {side}")
            mid_price = order_book.get_mid_price()
            return mid_price, 0.0, []
        
        # 计算平均成交价
        total_value = sum(t.price * t.size for t in trades)
        total_size = sum(t.size for t in trades)
        avg_price = total_value / total_size if total_size > 0 else 0
        
        # 计算滑点
        mid_price = order_book.get_mid_price()
        slippage_pct = abs(avg_price - mid_price) / mid_price
        
        logger.debug(
            f"滑点计算 | 规模: {order_size:.2f} | "
            f"中间价: ${mid_price:,.2f} | 成交价: ${avg_price:,.2f} | "
            f"滑点: {slippage_pct:.4%}"
        )
        
        return avg_price, slippage_pct, trades
    
    def estimate_slippage(
        self,
        order_size: float,
        order_book: OrderBook,
        side: str
    ) -> float:
        """
        估算滑点（不实际执行订单）
        
        Returns:
            估计滑点百分比
        """
        depth = order_book.get_depth(levels=10)
        mid_price = order_book.get_mid_price()
        
        # 简化估算：基于订单簿深度
        if side == 'buy':
            available_liquidity = depth['ask_total_size']
        else:
            available_liquidity = depth['bid_total_size']
        
        # 滑点与订单大小/流动性比例正相关
        liquidity_ratio = order_size / available_liquidity if available_liquidity > 0 else 1.0
        
        # 基础滑点模型：0.1% * (size/liquidity)^0.5
        estimated_slippage = 0.001 * (liquidity_ratio ** 0.5)
        
        # 限制最大滑点
        estimated_slippage = min(estimated_slippage, 0.05)  # 最大5%
        
        return estimated_slippage


class LiquidityManager:
    """
    流动性管理器（Liquidity Manager）
    
    管理市场流动性：
    - 追踪流动性水平
    - 处理流动性冲击
    - 流动性恢复机制
    """
    
    def __init__(self, base_liquidity: float = 1_000_000.0):
        """
        Args:
            base_liquidity: 基础流动性（USD）
        """
        self.base_liquidity = base_liquidity
        self.current_liquidity = base_liquidity
        
        # 流动性冲击记录
        self.shocks: List[Dict] = []
        
        # 恢复速度（每周期恢复10%）
        self.recovery_rate = 0.1
        
        logger.info(f"流动性管理器已初始化 | 基础流动性: ${base_liquidity:,.0f}")
    
    def get_liquidity_factor(self) -> float:
        """
        获取当前流动性因子
        
        Returns:
            0-1之间，1表示正常流动性
        """
        return min(self.current_liquidity / self.base_liquidity, 1.0)
    
    def apply_shock(self, trade_size: float, trade_price: float, side: str):
        """
        应用流动性冲击
        
        Args:
            trade_size: 交易大小（BTC）
            trade_price: 交易价格
            side: 'buy' or 'sell'
        """
        trade_value = trade_size * trade_price
        
        # 冲击程度与交易规模成正比
        shock_factor = trade_value / self.base_liquidity
        
        if shock_factor > 0.1:  # 大于10%基础流动性才有显著冲击
            # 流动性暂时下降
            shock_amount = self.base_liquidity * shock_factor * 0.5
            self.current_liquidity -= shock_amount
            self.current_liquidity = max(self.current_liquidity, self.base_liquidity * 0.3)  # 最低30%
            
            # 记录冲击
            shock_record = {
                'timestamp': datetime.now(),
                'size': trade_size,
                'value': trade_value,
                'side': side,
                'shock_amount': shock_amount,
                'liquidity_after': self.current_liquidity
            }
            self.shocks.append(shock_record)
            
            logger.info(
                f"💥 流动性冲击 | 交易: {trade_size:.2f} BTC | "
                f"冲击: ${shock_amount:,.0f} | "
                f"流动性: {self.get_liquidity_factor():.2%}"
            )
    
    def recover(self):
        """流动性恢复（每周期调用）"""
        if self.current_liquidity < self.base_liquidity:
            recovery_amount = (self.base_liquidity - self.current_liquidity) * self.recovery_rate
            self.current_liquidity += recovery_amount
            self.current_liquidity = min(self.current_liquidity, self.base_liquidity)
            
            logger.debug(f"🔄 流动性恢复 | +${recovery_amount:,.0f} | 当前: {self.get_liquidity_factor():.2%}")
        
        # 清理旧的冲击记录（保留最近50条）
        if len(self.shocks) > 50:
            self.shocks = self.shocks[-50:]
    
    def get_stats(self) -> Dict:
        """获取流动性统计"""
        return {
            'base_liquidity': self.base_liquidity,
            'current_liquidity': self.current_liquidity,
            'liquidity_factor': self.get_liquidity_factor(),
            'total_shocks': len(self.shocks),
            'recent_shocks': self.shocks[-5:] if self.shocks else []
        }


class MarketImpactCalculator:
    """
    市场冲击成本计算器（Market Impact Calculator）
    
    综合计算交易的总成本：
    - 价差成本（Spread Cost）
    - 滑点成本（Slippage Cost）
    - 市场冲击成本（Market Impact Cost）
    """
    
    def __init__(self):
        logger.debug("市场冲击成本计算器已初始化")
    
    def calculate_total_cost(
        self,
        order_size: float,
        mid_price: float,
        spread_cost: float,
        slippage_pct: float,
        liquidity_factor: float
    ) -> Dict[str, float]:
        """
        计算总交易成本
        
        Args:
            order_size: 订单大小（BTC）
            mid_price: 中间价
            spread_cost: 价差成本（USD）
            slippage_pct: 滑点百分比
            liquidity_factor: 流动性因子（0-1）
            
        Returns:
            {
                'spread_cost': float,
                'slippage_cost': float,
                'impact_cost': float,
                'total_cost': float,
                'cost_bps': float  # 总成本（基点）
            }
        """
        order_value = order_size * mid_price
        
        # 1. 价差成本（已提供）
        
        # 2. 滑点成本
        slippage_cost = order_value * slippage_pct
        
        # 3. 市场冲击成本（额外的永久价格影响）
        # 基于Almgren-Chriss模型的简化版本
        liquidity_penalty = (1.0 - liquidity_factor) ** 2
        impact_cost = order_value * 0.001 * liquidity_penalty  # 基础0.1%，流动性低时增加
        
        # 总成本
        total_cost = spread_cost + slippage_cost + impact_cost
        
        # 基点表示
        cost_bps = (total_cost / order_value) * 10000 if order_value > 0 else 0
        
        return {
            'spread_cost': spread_cost,
            'slippage_cost': slippage_cost,
            'impact_cost': impact_cost,
            'total_cost': total_cost,
            'cost_bps': cost_bps,
            'order_value': order_value
        }
    
    def estimate_execution_price(
        self,
        side: str,
        order_size: float,
        mid_price: float,
        spread_pct: float,
        slippage_pct: float
    ) -> float:
        """
        估算实际成交价
        
        Returns:
            预期平均成交价
        """
        # 买单：中间价 + 半价差 + 滑点
        if side == 'buy':
            execution_price = mid_price * (1 + spread_pct/2 + slippage_pct)
        # 卖单：中间价 - 半价差 - 滑点
        else:
            execution_price = mid_price * (1 - spread_pct/2 - slippage_pct)
        
        return execution_price


# ============================================================================
# 测试函数
# ============================================================================

def test_microstructure():
    """测试微观结构组件"""
    print("\n" + "="*70)
    print("🧪 市场微观结构测试")
    print("="*70)
    
    # 1. 测试订单簿
    print("\n📖 测试 OrderBook...")
    ob = OrderBook(num_levels=10, initial_mid_price=50000)
    
    best_bid, best_ask = ob.get_best_bid_ask()
    print(f"  最优买价: ${best_bid:,.2f}")
    print(f"  最优卖价: ${best_ask:,.2f}")
    
    spread_abs, spread_pct = ob.get_spread()
    print(f"  价差: ${spread_abs:,.2f} ({spread_pct:.3%})")
    
    depth = ob.get_depth(levels=5)
    print(f"  买盘深度: {depth['bid_total_size']:.2f} BTC")
    print(f"  卖盘深度: {depth['ask_total_size']:.2f} BTC")
    
    # 2. 测试价差管理
    print("\n💹 测试 SpreadManager...")
    sm = SpreadManager(base_spread_bps=10)
    
    bid, ask = sm.calculate_spread(
        mid_price=50000,
        volatility=0.02,  # 2%波动率
        liquidity_factor=0.8,  # 80%流动性
        time_of_day_factor=1.2  # 低峰期
    )
    print(f"  计算买价: ${bid:,.2f}")
    print(f"  计算卖价: ${ask:,.2f}")
    print(f"  当前价差: {sm.current_spread_bps:.1f} bps")
    
    # 3. 测试滑点计算
    print("\n📉 测试 SlippageCalculator...")
    sc = SlippageCalculator()
    
    # 小订单
    avg_price, slippage, trades = sc.calculate_slippage(10, ob, 'buy')
    print(f"  10 BTC买单:")
    print(f"    平均成交价: ${avg_price:,.2f}")
    print(f"    滑点: {slippage:.3%}")
    print(f"    成交笔数: {len(trades)}")
    
    # 大订单
    ob2 = OrderBook(num_levels=10, initial_mid_price=50000)
    avg_price2, slippage2, trades2 = sc.calculate_slippage(100, ob2, 'buy')
    print(f"  100 BTC买单:")
    print(f"    平均成交价: ${avg_price2:,.2f}")
    print(f"    滑点: {slippage2:.3%}")
    print(f"    成交笔数: {len(trades2)}")
    
    # 4. 测试流动性管理
    print("\n💧 测试 LiquidityManager...")
    lm = LiquidityManager(base_liquidity=1_000_000)
    
    print(f"  初始流动性因子: {lm.get_liquidity_factor():.2%}")
    
    # 应用大额交易冲击
    lm.apply_shock(trade_size=500, trade_price=50000, side='sell')
    print(f"  冲击后流动性因子: {lm.get_liquidity_factor():.2%}")
    
    # 恢复
    for i in range(5):
        lm.recover()
    print(f"  5轮恢复后流动性因子: {lm.get_liquidity_factor():.2%}")
    
    # 5. 测试市场冲击成本
    print("\n💰 测试 MarketImpactCalculator...")
    mic = MarketImpactCalculator()
    
    cost_breakdown = mic.calculate_total_cost(
        order_size=100,
        mid_price=50000,
        spread_cost=5000,  # $5,000
        slippage_pct=0.003,  # 0.3%
        liquidity_factor=0.7
    )
    
    print(f"  100 BTC订单成本分解:")
    print(f"    价差成本: ${cost_breakdown['spread_cost']:,.2f}")
    print(f"    滑点成本: ${cost_breakdown['slippage_cost']:,.2f}")
    print(f"    冲击成本: ${cost_breakdown['impact_cost']:,.2f}")
    print(f"    总成本: ${cost_breakdown['total_cost']:,.2f} ({cost_breakdown['cost_bps']:.1f} bps)")
    
    # 估算成交价
    exec_price = mic.estimate_execution_price(
        side='buy',
        order_size=100,
        mid_price=50000,
        spread_pct=0.002,
        slippage_pct=0.003
    )
    print(f"  预期成交价: ${exec_price:,.2f} (vs 中间价 $50,000)")
    
    print("\n" + "="*70)
    print("✅ 所有测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 运行测试
    test_microstructure()


