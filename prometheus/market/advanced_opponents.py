"""
高级对手盘行为模拟

实现6种不同类型的市场参与者：
1. MarketMaker - 做市商（提供流动性，赚取价差）
2. Arbitrageur - 套利者（发现价格偏差，快速套利）
3. Whale - 大户/鲸鱼（大额交易，影响价格）
4. HighFrequencyTrader - 高频交易者（极高频率，微小利润）
5. PassiveInvestor - 被动投资者（定期定额，长期持有）
6. PanicTrader - 恐慌性交易者（追涨杀跌，放大波动）

Author: Prometheus Team  
Version: v5.3  
Date: 2025-12-06
"""

import numpy as np
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class OpponentOrder:
    """对手盘订单"""
    trader_id: str
    trader_type: str
    side: str  # 'buy' or 'sell'
    size: float
    price: Optional[float] = None  # None表示市价单
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseOpponent(ABC):
    """对手盘基类"""
    
    def __init__(self, trader_id: str, initial_capital: float = 100000):
        self.trader_id = trader_id
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position = 0.0  # BTC持仓
        self.trades_history: List[Dict] = []
        self.pnl = 0.0
        
    @abstractmethod
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """
        做出交易决策
        
        Args:
            current_price: 当前价格
            order_book: 订单簿信息
            market_data: 市场数据（历史价格、波动率等）
            
        Returns:
            订单列表
        """
        pass
    
    def update_position(self, trade: Dict):
        """更新持仓"""
        if trade['side'] == 'buy':
            self.position += trade['size']
            self.current_capital -= trade['size'] * trade['price']
        else:
            self.position -= trade['size']
            self.current_capital += trade['size'] * trade['price']
        
        self.trades_history.append(trade)
        self._update_pnl(trade['price'])
    
    def _update_pnl(self, current_price: float):
        """更新盈亏"""
        position_value = self.position * current_price
        self.pnl = self.current_capital + position_value - self.initial_capital
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'trader_id': self.trader_id,
            'trader_type': self.__class__.__name__,
            'current_capital': self.current_capital,
            'position': self.position,
            'pnl': self.pnl,
            'total_trades': len(self.trades_history)
        }


class MarketMaker(BaseOpponent):
    """
    做市商（Market Maker）
    
    行为特征：
    - 同时挂买单和卖单
    - 赚取价差收益
    - 提供流动性
    - 库存风险管理
    """
    
    chinese_name = "做市商"
    
    def __init__(self, trader_id: str, initial_capital: float = 100000):
        super().__init__(trader_id, initial_capital)
        
        # 做市参数
        self.target_spread_bps = 20  # 目标价差20 bps (0.2%)
        self.max_inventory = 10.0  # 最大库存10 BTC
        self.quote_size = 1.0  # 每次报价1 BTC
        
        # 库存管理
        self.target_position = 0.0  # 目标持仓0（市场中性）
        
        logger.debug(f"做市商初始化 | ID: {trader_id} | 资金: ${initial_capital:,.0f}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """做市决策"""
        orders = []
        
        # 计算库存偏离
        inventory_skew = self.position - self.target_position
        
        # 根据库存调整报价（库存管理）
        # 如果持仓过多（多头），降低买价、降低卖价（促进卖出）
        # 如果持仓过少（空头），提高买价、提高卖价（促进买入）
        skew_adjustment = inventory_skew / self.max_inventory * 0.002  # 最多0.2%调整
        
        # 计算买卖报价
        spread = current_price * (self.target_spread_bps / 10000)
        
        bid_price = current_price - spread/2 - current_price * skew_adjustment
        ask_price = current_price + spread/2 - current_price * skew_adjustment
        
        # 挂买单（如果库存未满）
        if abs(self.position) < self.max_inventory:
            orders.append(OpponentOrder(
                trader_id=self.trader_id,
                trader_type="MarketMaker",
                side='buy',
                size=self.quote_size,
                price=bid_price
            ))
        
        # 挂卖单（如果有库存）
        if self.position > 0 or abs(self.position) < self.max_inventory:
            orders.append(OpponentOrder(
                trader_id=self.trader_id,
                trader_type="MarketMaker",
                side='sell',
                size=self.quote_size,
                price=ask_price
            ))
        
        return orders


class Arbitrageur(BaseOpponent):
    """
    套利者（Arbitrageur）
    
    行为特征：
    - 发现价格偏差
    - 快速执行套利
    - 平抑价格偏差
    """
    
    chinese_name = "套利者"
    
    def __init__(self, trader_id: str, initial_capital: float = 100000):
        super().__init__(trader_id, initial_capital)
        
        # 套利参数
        self.trigger_threshold = 0.02  # 2%偏离触发
        self.trade_size = random.uniform(50, 200)  # 50-200 BTC
        self.fair_value = None  # 公允价值（移动平均）
        
        logger.debug(f"套利者初始化 | ID: {trader_id} | 触发阈值: {self.trigger_threshold:.1%}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """套利决策"""
        orders = []
        
        # 计算公允价值（使用历史平均）
        price_history = market_data.get('price_history', [current_price])
        if len(price_history) >= 20:
            self.fair_value = np.mean(price_history[-20:])
        else:
            self.fair_value = current_price
        
        # 计算价格偏离
        deviation = (current_price - self.fair_value) / self.fair_value
        
        # 价格高估：卖出套利
        if deviation > self.trigger_threshold:
            logger.info(f"📊 套利机会 | {self.trader_id} | 高估{deviation:.2%} | 卖出套利")
            orders.append(OpponentOrder(
                trader_id=self.trader_id,
                trader_type="Arbitrageur",
                side='sell',
                size=self.trade_size,
                price=None  # 市价单
            ))
        
        # 价格低估：买入套利
        elif deviation < -self.trigger_threshold:
            logger.info(f"📊 套利机会 | {self.trader_id} | 低估{deviation:.2%} | 买入套利")
            orders.append(OpponentOrder(
                trader_id=self.trader_id,
                trader_type="Arbitrageur",
                side='buy',
                size=self.trade_size,
                price=None
            ))
        
        return orders


class Whale(BaseOpponent):
    """
    大户/鲸鱼（Whale）
    
    行为特征：
    - 大额交易（影响价格）
    - 分批执行（减少冲击）
    - 战略性建仓/清仓
    """
    
    chinese_name = "大户"
    
    def __init__(self, trader_id: str, initial_capital: float = 1000000):
        super().__init__(trader_id, initial_capital)
        
        # 大户参数
        self.trade_size_range = (50, 200)  # 单笔50-200 BTC
        self.execution_batches = random.randint(5, 10)  # 分5-10批执行
        
        # 战略状态
        self.strategy = None  # 'accumulate', 'distribute', or None
        self.strategy_start_time = None
        self.strategy_duration = timedelta(minutes=random.randint(30, 120))
        self.current_batch = 0
        
        logger.debug(f"大户初始化 | ID: {trader_id} | 资金: ${initial_capital:,.0f}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """大户决策"""
        orders = []
        
        # 检查是否需要开启新战略
        if self.strategy is None or (
            self.strategy_start_time and 
            datetime.now() - self.strategy_start_time > self.strategy_duration
        ):
            # 随机决定战略（30%概率启动）
            if random.random() < 0.3:
                self.strategy = random.choice(['accumulate', 'distribute'])
                self.strategy_start_time = datetime.now()
                self.current_batch = 0
                
                logger.info(f"🐋 大户战略 | {self.trader_id} | {self.strategy}")
            else:
                self.strategy = None
                return orders
        
        # 执行当前战略
        if self.strategy and self.current_batch < self.execution_batches:
            trade_size = random.uniform(*self.trade_size_range)
            
            if self.strategy == 'accumulate':
                # 建仓（买入）
                orders.append(OpponentOrder(
                    trader_id=self.trader_id,
                    trader_type="Whale",
                    side='buy',
                    size=trade_size,
                    price=None
                ))
                logger.debug(f"🐋 大户建仓 | 批次{self.current_batch+1}/{self.execution_batches} | {trade_size:.2f} BTC")
            
            elif self.strategy == 'distribute':
                # 清仓（卖出）
                if self.position > 0:
                    sell_size = min(trade_size, self.position)
                    orders.append(OpponentOrder(
                        trader_id=self.trader_id,
                        trader_type="Whale",
                        side='sell',
                        size=sell_size,
                        price=None
                    ))
                    logger.debug(f"🐋 大户清仓 | 批次{self.current_batch+1}/{self.execution_batches} | {sell_size:.2f} BTC")
            
            self.current_batch += 1
        
        return orders


class HighFrequencyTrader(BaseOpponent):
    """
    高频交易者（HFT）
    
    行为特征：
    - 极高频率交易
    - 微小价格波动捕捉
    - 快进快出
    - 统计套利
    """
    
    chinese_name = "高频交易者"
    
    def __init__(self, trader_id: str, initial_capital: float = 50000):
        super().__init__(trader_id, initial_capital)
        
        # HFT参数
        self.trigger_threshold = 0.0005  # 0.05%波动触发
        self.trade_size = random.uniform(1, 10)  # 1-10 BTC
        self.holding_period = random.randint(1, 3)  # 持仓1-3周期
        
        # 状态
        self.entry_price = None
        self.entry_time = None
        self.cycles_held = 0
        
        logger.debug(f"HFT初始化 | ID: {trader_id} | 触发阈值: {self.trigger_threshold:.2%}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """HFT决策"""
        orders = []
        
        # 如果有持仓，检查是否平仓
        if self.position != 0:
            self.cycles_held += 1
            
            # 计算盈亏
            if self.entry_price:
                pnl_pct = (current_price - self.entry_price) / self.entry_price
                
                # 止盈（>0.1%）或止损（<-0.05%）或到期
                if pnl_pct > 0.001 or pnl_pct < -0.0005 or self.cycles_held >= self.holding_period:
                    side = 'sell' if self.position > 0 else 'buy'
                    orders.append(OpponentOrder(
                        trader_id=self.trader_id,
                        trader_type="HFT",
                        side=side,
                        size=abs(self.position),
                        price=None
                    ))
                    
                    # 重置状态
                    self.entry_price = None
                    self.entry_time = None
                    self.cycles_held = 0
                    
                    return orders
        
        # 无持仓时，寻找交易机会
        price_history = market_data.get('price_history', [current_price])
        if len(price_history) >= 2:
            price_change = (price_history[-1] - price_history[-2]) / price_history[-2]
            
            # 微观趋势跟随
            if abs(price_change) > self.trigger_threshold:
                side = 'buy' if price_change > 0 else 'sell'
                orders.append(OpponentOrder(
                    trader_id=self.trader_id,
                    trader_type="HFT",
                    side=side,
                    size=self.trade_size,
                    price=None
                ))
                
                self.entry_price = current_price
                self.entry_time = datetime.now()
                self.cycles_held = 0
        
        return orders


class PassiveInvestor(BaseOpponent):
    """
    被动投资者（Passive Investor）
    
    行为特征：
    - 定期定额买入（DCA）
    - 长期持有
    - 不关注短期波动
    """
    
    chinese_name = "被动投资者"
    
    def __init__(self, trader_id: str, initial_capital: float = 50000):
        super().__init__(trader_id, initial_capital)
        
        # DCA参数
        self.dca_interval = random.randint(10, 20)  # 每10-20周期投资一次
        self.dca_amount_usd = random.uniform(5000, 20000)  # 每次5000-20000美元
        self.last_buy_cycle = -self.dca_interval  # 确保第一轮就能买
        
        logger.debug(f"被动投资者初始化 | ID: {trader_id} | 定投金额: ${self.dca_amount_usd:,.0f}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """被动投资决策"""
        orders = []
        
        current_cycle = market_data.get('current_cycle', 0)
        
        # 检查是否到定投时间
        if current_cycle - self.last_buy_cycle >= self.dca_interval:
            # 计算买入数量
            buy_size = self.dca_amount_usd / current_price
            
            # 检查资金是否足够
            if self.current_capital >= self.dca_amount_usd:
                orders.append(OpponentOrder(
                    trader_id=self.trader_id,
                    trader_type="PassiveInvestor",
                    side='buy',
                    size=buy_size,
                    price=None
                ))
                
                self.last_buy_cycle = current_cycle
                logger.debug(f"💰 定投买入 | {self.trader_id} | ${self.dca_amount_usd:,.0f} ≈ {buy_size:.4f} BTC")
        
        return orders


class PanicTrader(BaseOpponent):
    """
    恐慌性交易者（Panic Trader）
    
    行为特征：
    - 价格大跌时恐慌抛售
    - 价格暴涨时FOMO买入
    - 追涨杀跌
    - 放大波动
    """
    
    chinese_name = "恐慌交易者"
    
    def __init__(self, trader_id: str, initial_capital: float = 20000):
        super().__init__(trader_id, initial_capital)
        
        # 恐慌参数
        self.panic_sell_threshold = -0.05  # -5%触发恐慌抛售
        self.fomo_buy_threshold = 0.10  # +10%触发FOMO买入
        self.trade_size_pct = random.uniform(0.5, 1.0)  # 50%-100%资金/仓位
        
        logger.debug(f"恐慌交易者初始化 | ID: {trader_id}")
    
    def make_decision(
        self,
        current_price: float,
        order_book: Dict,
        market_data: Dict
    ) -> List[OpponentOrder]:
        """恐慌交易决策"""
        orders = []
        
        # 计算价格变化
        price_history = market_data.get('price_history', [current_price])
        if len(price_history) >= 5:
            recent_change = (current_price - price_history[-5]) / price_history[-5]
            
            # 恐慌抛售（价格大跌）
            if recent_change < self.panic_sell_threshold and self.position > 0:
                # 卖出大部分持仓
                sell_size = self.position * self.trade_size_pct
                orders.append(OpponentOrder(
                    trader_id=self.trader_id,
                    trader_type="PanicTrader",
                    side='sell',
                    size=sell_size,
                    price=None
                ))
                logger.info(f"😱 恐慌抛售 | {self.trader_id} | 跌幅{recent_change:.2%} | 卖出{sell_size:.4f} BTC")
            
            # FOMO买入（价格暴涨）
            elif recent_change > self.fomo_buy_threshold:
                # 买入大量
                available_capital = self.current_capital * self.trade_size_pct
                buy_size = available_capital / current_price
                
                if buy_size > 0:
                    orders.append(OpponentOrder(
                        trader_id=self.trader_id,
                        trader_type="PanicTrader",
                        side='buy',
                        size=buy_size,
                        price=None
                    ))
                    logger.info(f"🚀 FOMO买入 | {self.trader_id} | 涨幅{recent_change:.2%} | 买入{buy_size:.4f} BTC")
        
        return orders


# ============================================================================
# 测试函数
# ============================================================================

def test_opponents():
    """测试所有对手盘类型"""
    print("\n" + "="*70)
    print("🧪 对手盘行为测试")
    print("="*70)
    
    # 模拟市场数据
    current_price = 50000
    order_book = {
        'bids': [(49950, 10), (49940, 15)],
        'asks': [(50050, 12), (50060, 18)],
        'best_bid': 49950,
        'best_ask': 50050
    }
    market_data = {
        'price_history': [48000, 49000, 49500, 50000, 50000],
        'current_cycle': 15
    }
    
    # 1. 测试做市商
    print("\n🏦 测试 MarketMaker...")
    mm = MarketMaker("MM_001", initial_capital=100000)
    orders = mm.make_decision(current_price, order_book, market_data)
    print(f"  订单数量: {len(orders)}")
    for order in orders:
        print(f"    {order.side.upper()}: {order.size:.2f} BTC @ ${order.price:,.2f}")
    
    # 2. 测试套利者
    print("\n📊 测试 Arbitrageur...")
    arb = Arbitrageur("ARB_001", initial_capital=100000)
    
    # 测试价格高估场景
    market_data_high = market_data.copy()
    market_data_high['price_history'] = [48000, 48500, 49000, 49500, 51000]
    orders = arb.make_decision(51500, order_book, market_data_high)
    print(f"  价格高估场景: {len(orders)}个订单")
    
    # 3. 测试大户
    print("\n🐋 测试 Whale...")
    whale = Whale("WHALE_001", initial_capital=1000000)
    for i in range(3):
        orders = whale.make_decision(current_price, order_book, market_data)
        if orders:
            print(f"  周期{i+1}: {len(orders)}个订单, {orders[0].side}, {orders[0].size:.2f} BTC")
    
    # 4. 测试HFT
    print("\n⚡ 测试 HighFrequencyTrader...")
    hft = HighFrequencyTrader("HFT_001", initial_capital=50000)
    
    # 测试价格波动
    market_data_vol = market_data.copy()
    market_data_vol['price_history'] = [50000, 50030]  # +0.06%波动
    orders = hft.make_decision(50030, order_book, market_data_vol)
    print(f"  检测到波动: {len(orders)}个订单")
    
    # 5. 测试被动投资者
    print("\n💰 测试 PassiveInvestor...")
    passive = PassiveInvestor("PASSIVE_001", initial_capital=50000)
    orders = passive.make_decision(current_price, order_book, market_data)
    print(f"  定投周期: {len(orders)}个订单")
    if orders:
        print(f"    买入: {orders[0].size:.4f} BTC")
    
    # 6. 测试恐慌交易者
    print("\n😱 测试 PanicTrader...")
    panic = PanicTrader("PANIC_001", initial_capital=20000)
    
    # 先买入一些仓位
    panic.position = 0.5
    panic.entry_price = 50000
    
    # 测试恐慌抛售
    market_data_crash = market_data.copy()
    market_data_crash['price_history'] = [50000, 49000, 48000, 47000, 46000]  # -8%
    orders = panic.make_decision(46000, order_book, market_data_crash)
    print(f"  价格暴跌场景: {len(orders)}个订单")
    if orders:
        print(f"    恐慌抛售: {orders[0].size:.4f} BTC")
    
    print("\n" + "="*70)
    print("✅ 所有对手盘测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 运行测试
    test_opponents()

