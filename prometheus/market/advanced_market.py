"""
高级对手市场（完整版）

整合所有组件，提供完整的市场模拟环境：
- 5个微观结构组件
- 6种对手盘（96个实例）
- 完整的市场模拟流程

Author: Prometheus Team
Version: v5.3
Date: 2025-12-06
"""

import sys
from pathlib import Path

# 添加项目路径（用于直接运行）
if __name__ == "__main__" or not __package__:
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

import numpy as np
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from prometheus.market.market_microstructure import (
    OrderBook,
    SpreadManager,
    SlippageCalculator,
    LiquidityManager,
    MarketImpactCalculator,
    Trade
)

from prometheus.market.advanced_opponents import (
    MarketMaker,
    Arbitrageur,
    Whale,
    HighFrequencyTrader,
    PassiveInvestor,
    PanicTrader,
    OpponentOrder
)

logger = logging.getLogger(__name__)


@dataclass
class MarketSimulationResult:
    """市场模拟结果"""
    cycle: int
    timestamp: datetime
    
    # 价格信息
    price: float
    bid_price: float
    ask_price: float
    spread: float
    spread_pct: float
    
    # 订单簿信息
    order_book_depth: Dict
    best_bid: float
    best_ask: float
    
    # 流动性信息
    liquidity_factor: float
    current_liquidity: float
    
    # 交易信息
    total_trades: int
    opponent_trades: int
    total_volume: float
    
    # 对手盘活动
    opponent_activity: Dict = field(default_factory=dict)
    
    # 价格历史
    price_history: List[float] = field(default_factory=list)


class AdvancedOpponentMarket:
    """
    高级对手市场（完整版）
    
    整合所有微观结构和对手盘组件，提供真实的市场模拟环境。
    
    组件：
    - 5个微观结构组件
    - 6种对手盘（96个实例）
    
    特性：
    - 真实的价格形成机制
    - 动态的买卖价差
    - 滑点和流动性冲击
    - 多样化的对手盘行为
    """
    
    def __init__(
        self,
        initial_price: float = 50000.0,
        num_market_makers: int = 5,
        num_arbitrageurs: int = 8,
        num_whales: int = 3,
        num_hfts: int = 15,
        num_passive: int = 25,
        num_panic: int = 40,
        base_liquidity: float = 1_000_000.0,
        enable_natural_volatility: bool = True,
        volatility_std: float = 0.005
    ):
        """
        初始化高级对手市场
        
        Args:
            initial_price: 初始价格
            num_*: 各类对手盘数量
            base_liquidity: 基础流动性
            enable_natural_volatility: 是否启用自然波动
            volatility_std: 波动率标准差
        """
        self.initial_price = initial_price
        self.current_price = initial_price
        self.enable_natural_volatility = enable_natural_volatility
        self.volatility_std = volatility_std
        
        # ===== 微观结构组件 =====
        logger.info("🏗️ 初始化市场微观结构...")
        
        self.order_book = OrderBook(
            num_levels=10,
            initial_mid_price=initial_price
        )
        
        self.spread_manager = SpreadManager(base_spread_bps=10.0)
        
        self.slippage_calc = SlippageCalculator()
        
        self.liquidity_mgr = LiquidityManager(base_liquidity=base_liquidity)
        
        self.impact_calc = MarketImpactCalculator()
        
        logger.info("✅ 微观结构组件已初始化")
        
        # ===== 对手盘 =====
        logger.info(f"🤖 初始化对手盘（{num_market_makers + num_arbitrageurs + num_whales + num_hfts + num_passive + num_panic}个）...")
        
        self.market_makers = [
            MarketMaker(f"MM_{i}", initial_capital=100_000)
            for i in range(num_market_makers)
        ]
        
        self.arbitrageurs = [
            Arbitrageur(f"ARB_{i}", initial_capital=100_000)
            for i in range(num_arbitrageurs)
        ]
        
        self.whales = [
            Whale(f"WHALE_{i}", initial_capital=1_000_000)
            for i in range(num_whales)
        ]
        
        self.hfts = [
            HighFrequencyTrader(f"HFT_{i}", initial_capital=50_000)
            for i in range(num_hfts)
        ]
        
        self.passive_investors = [
            PassiveInvestor(f"PASS_{i}", initial_capital=50_000)
            for i in range(num_passive)
        ]
        
        self.panic_traders = [
            PanicTrader(f"PANIC_{i}", initial_capital=20_000)
            for i in range(num_panic)
        ]
        
        # 所有对手盘
        self.all_opponents = (
            self.market_makers +
            self.arbitrageurs +
            self.whales +
            self.hfts +
            self.passive_investors +
            self.panic_traders
        )
        
        logger.info(f"✅ 对手盘已初始化:")
        logger.info(f"   做市商(MarketMaker): {num_market_makers}个")
        logger.info(f"   套利者(Arbitrageur): {num_arbitrageurs}个")
        logger.info(f"   大户(Whale): {num_whales}个")
        logger.info(f"   高频交易者(HFT): {num_hfts}个")
        logger.info(f"   被动投资者(Passive): {num_passive}个")
        logger.info(f"   恐慌交易者(Panic): {num_panic}个")
        
        # ===== 市场状态 =====
        self.price_history: List[float] = [initial_price]
        self.trade_history: List[Trade] = []
        self.cycle_count = 0
        
        # 统计
        self.stats = {
            'total_trades': 0,
            'total_volume': 0.0,
            'opponent_trades_by_type': {
                'MarketMaker': 0,
                'Arbitrageur': 0,
                'Whale': 0,
                'HFT': 0,
                'PassiveInvestor': 0,
                'PanicTrader': 0
            }
        }
        
        logger.info(f"🎯 高级对手市场初始化完成 | 初始价格: ${initial_price:,.2f}")
    
    def simulate_step(self, cycle: int) -> MarketSimulationResult:
        """
        模拟一个市场步骤
        
        完整流程：
        1. 收集所有对手盘订单
        2. 更新订单簿
        3. 订单匹配和成交
        4. 计算价格影响
        5. 应用自然波动
        6. 更新流动性
        7. 返回结果
        
        Args:
            cycle: 当前周期数
            
        Returns:
            MarketSimulationResult
        """
        self.cycle_count = cycle
        
        # ===== 1. 收集对手盘订单 =====
        all_orders: List[OpponentOrder] = []
        opponent_activity = {
            'MarketMaker': 0,
            'Arbitrageur': 0,
            'Whale': 0,
            'HFT': 0,
            'PassiveInvestor': 0,
            'PanicTrader': 0
        }
        
        # 准备市场数据
        market_data = {
            'price_history': self.price_history,
            'current_cycle': cycle,
            'volatility': self._calculate_volatility()
        }
        
        # 订单簿数据
        order_book_data = {
            'best_bid': self.order_book.bids[0].price if self.order_book.bids else self.current_price * 0.999,
            'best_ask': self.order_book.asks[0].price if self.order_book.asks else self.current_price * 1.001,
            'depth': self.order_book.get_depth(levels=5)
        }
        
        # 收集每个对手盘的订单
        for opponent in self.all_opponents:
            orders = opponent.make_decision(
                self.current_price,
                order_book_data,
                market_data
            )
            all_orders.extend(orders)
            
            # 统计活动
            if orders:
                opponent_type = opponent.__class__.__name__
                if opponent_type not in opponent_activity:
                    opponent_activity[opponent_type] = 0
                opponent_activity[opponent_type] += len(orders)
        
        # ===== 2. 处理订单并更新订单簿 =====
        # 做市商的限价单直接加入订单簿
        for order in all_orders:
            if order.trader_type == 'MarketMaker' and order.price is not None:
                self.order_book.add_order(
                    side='bid' if order.side == 'buy' else 'ask',
                    price=order.price,
                    size=order.size
                )
        
        # ===== 3. 执行市价单 =====
        executed_trades: List[Trade] = []
        
        for order in all_orders:
            # 只处理市价单（price=None）
            if order.price is None:
                trades = self.order_book.match_order(
                    side=order.side,
                    size=order.size
                )
                
                # 记录成交
                for trade in trades:
                    trade.trader_type = order.trader_type
                    executed_trades.append(trade)
                    self.trade_history.append(trade)
                
                # 更新对手盘持仓
                if trades:
                    total_value = sum(t.price * t.size for t in trades)
                    total_size = sum(t.size for t in trades)
                    avg_price = total_value / total_size if total_size > 0 else self.current_price
                    
                    # 找到对应的对手盘并更新
                    for opponent in self.all_opponents:
                        if opponent.trader_id == order.trader_id:
                            opponent.update_position({
                                'side': order.side,
                                'size': total_size,
                                'price': avg_price
                            })
                            break
        
        # ===== 4. 计算价格影响 =====
        if executed_trades:
            # 计算净买卖压力
            buy_volume = sum(t.size for t in executed_trades if t.side == 'buy')
            sell_volume = sum(t.size for t in executed_trades if t.side == 'sell')
            net_pressure = (buy_volume - sell_volume) / self.liquidity_mgr.base_liquidity
            
            # 价格影响（基于净压力）
            price_impact = net_pressure * 0.02  # 最多±2%
            self.current_price *= (1 + price_impact)
            
            # 应用流动性冲击
            total_volume = buy_volume + sell_volume
            if total_volume > 0:
                self.liquidity_mgr.apply_shock(
                    trade_size=total_volume,
                    trade_price=self.current_price,
                    side='mixed'
                )
        
        # ===== 5. 应用自然波动 =====
        if self.enable_natural_volatility:
            natural_volatility = np.random.normal(0, self.volatility_std)
            
            # 5%概率出现3倍波动（模拟重要新闻）
            if random.random() < 0.05:
                natural_volatility *= 3
            
            self.current_price *= (1 + natural_volatility)
            
            # 限制单轮最大变化±5%
            if len(self.price_history) > 0:
                prev_price = self.price_history[-1]
                max_change = prev_price * 0.05
                self.current_price = np.clip(
                    self.current_price,
                    prev_price - max_change,
                    prev_price + max_change
                )
        
        # ===== 6. 更新订单簿和流动性 =====
        volatility = self._calculate_volatility()
        self.order_book.update_prices(self.current_price, volatility)
        self.liquidity_mgr.recover()
        
        # ===== 7. 更新价格历史 =====
        self.price_history.append(self.current_price)
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        
        # ===== 8. 更新统计 =====
        self.stats['total_trades'] += len(executed_trades)
        self.stats['total_volume'] += sum(t.size for t in executed_trades)
        
        for trade in executed_trades:
            if trade.trader_type in self.stats['opponent_trades_by_type']:
                self.stats['opponent_trades_by_type'][trade.trader_type] += 1
        
        # ===== 9. 计算价差 =====
        best_bid, best_ask = self.order_book.get_best_bid_ask()
        spread_abs, spread_pct = self.order_book.get_spread()
        
        # ===== 10. 构建结果 =====
        result = MarketSimulationResult(
            cycle=cycle,
            timestamp=datetime.now(),
            price=self.current_price,
            bid_price=best_bid,
            ask_price=best_ask,
            spread=spread_abs,
            spread_pct=spread_pct,
            order_book_depth=self.order_book.get_depth(levels=5),
            best_bid=best_bid,
            best_ask=best_ask,
            liquidity_factor=self.liquidity_mgr.get_liquidity_factor(),
            current_liquidity=self.liquidity_mgr.current_liquidity,
            total_trades=len(executed_trades),
            opponent_trades=len(executed_trades),
            total_volume=sum(t.size for t in executed_trades),
            opponent_activity=opponent_activity,
            price_history=self.price_history[-100:]  # 最近100个价格
        )
        
        # ===== 日志 =====
        if len(executed_trades) > 0:
            logger.info(
                f"💹 周期{cycle} | 价格: ${self.current_price:,.2f} | "
                f"成交: {len(executed_trades)}笔 | "
                f"成交量: {result.total_volume:.2f} BTC | "
                f"价差: {spread_pct:.3%} | "
                f"流动性: {result.liquidity_factor:.1%}"
            )
        else:
            logger.debug(f"周期{cycle} | 价格: ${self.current_price:,.2f} | 无成交")
        
        return result
    
    def _calculate_volatility(self) -> float:
        """计算当前波动率"""
        if len(self.price_history) < 20:
            return 0.01  # 默认1%
        
        recent_prices = self.price_history[-20:]
        returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(returns)
        
        return volatility
    
    def get_market_stats(self) -> Dict:
        """获取市场统计信息"""
        return {
            'current_price': self.current_price,
            'price_change': (self.current_price / self.initial_price - 1) * 100,
            'total_trades': self.stats['total_trades'],
            'total_volume': self.stats['total_volume'],
            'opponent_trades_by_type': self.stats['opponent_trades_by_type'],
            'liquidity_factor': self.liquidity_mgr.get_liquidity_factor(),
            'volatility': self._calculate_volatility(),
            'cycles': self.cycle_count
        }
    
    def get_opponent_stats(self) -> List[Dict]:
        """获取所有对手盘的统计信息"""
        return [opponent.get_stats() for opponent in self.all_opponents]


# ============================================================================
# 测试函数
# ============================================================================

def test_advanced_market():
    """测试高级对手市场"""
    print("\n" + "="*70)
    print("🧪 高级对手市场测试")
    print("="*70)
    
    # 创建市场
    market = AdvancedOpponentMarket(
        initial_price=50000.0,
        num_market_makers=5,
        num_arbitrageurs=8,
        num_whales=3,
        num_hfts=15,
        num_passive=25,
        num_panic=40,
        enable_natural_volatility=True,
        volatility_std=0.008
    )
    
    print(f"\n📊 运行10个市场周期...")
    
    for cycle in range(10):
        result = market.simulate_step(cycle)
        
        print(f"\n周期 {cycle+1}:")
        print(f"  价格: ${result.price:,.2f}")
        print(f"  价差: {result.spread_pct:.3%}")
        print(f"  成交: {result.total_trades}笔")
        print(f"  成交量: {result.total_volume:.2f} BTC")
        print(f"  流动性: {result.liquidity_factor:.1%}")
        
        if result.opponent_activity:
            active_types = [k for k, v in result.opponent_activity.items() if v > 0]
            print(f"  活跃对手: {', '.join(active_types)}")
    
    print(f"\n{'='*70}")
    print(f"📈 市场统计:")
    stats = market.get_market_stats()
    print(f"  价格变化: {stats['price_change']:+.2f}%")
    print(f"  总成交: {stats['total_trades']}笔")
    print(f"  总成交量: {stats['total_volume']:.2f} BTC")
    print(f"  当前波动率: {stats['volatility']:.3%}")
    
    print(f"\n💼 对手盘类型分布:")
    for trader_type, count in stats['opponent_trades_by_type'].items():
        if count > 0:
            print(f"  {trader_type}: {count}笔")
    
    print(f"\n{'='*70}")
    print("✅ 测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 运行测试
    test_advanced_market()

