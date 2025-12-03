"""
Prometheus v4.0 - 模拟交易模块
用于快速调试，无需连接OKX交易所
"""
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class MockTrading:
    """
    模拟交易类 - 实现与OKXPaperTrading相同的接口
    用于快速调试，生成合理的模拟数据
    """
    
    def __init__(self, initial_balance: float = 100000.0, initial_price: float = 92800.0):
        """
        初始化模拟交易
        
        Args:
            initial_balance: 初始资金（默认10万USDT）
            initial_price: 初始BTC价格（默认92800）
        """
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.current_price = initial_price
        self.base_price = initial_price
        
        # 兼容OKX接口 - exchange属性指向自身
        self.exchange = self
        
        # 模拟持仓
        self.positions = {
            'long': {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0},
            'short': {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0}
        }
        
        # 订单历史
        self.orders = []
        self.order_id_counter = 1000000
        
        # 价格历史（用于生成K线）
        self.price_history = []
        self.start_time = datetime.now()
        
        # 价格波动参数
        self.volatility = 0.002  # 每次波动约0.2%
        self.trend_strength = 0.0  # 趋势强度 (-1到1)
        self.trend_duration = 0  # 趋势持续周期
        
        logger.info(f"✅ 模拟交易已初始化（余额: ${initial_balance:,.2f}, 初始价格: ${initial_price:,.2f}）")
    
    def fetch_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        
        Returns:
            模拟的余额信息
        """
        # 计算浮动盈亏
        unrealized_pnl = 0.0
        if self.positions['long']['amount'] > 0:
            unrealized_pnl += (self.current_price - self.positions['long']['entry_price']) * self.positions['long']['amount']
        if self.positions['short']['amount'] > 0:
            unrealized_pnl += (self.positions['short']['entry_price'] - self.current_price) * self.positions['short']['amount']
        
        total_equity = self.balance + unrealized_pnl
        
        return {
            'USDT': {
                'free': self.balance,
                'used': self.positions['long']['total_cost'] + self.positions['short']['total_cost'],
                'total': total_equity
            }
        }
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List[List]:
        """
        生成模拟K线数据
        
        Args:
            symbol: 交易对（忽略）
            timeframe: 时间周期
            limit: 数量
            
        Returns:
            模拟的OHLCV数据
        """
        ohlcv = []
        
        # 时间间隔（毫秒）
        interval_map = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000
        }
        interval_ms = interval_map.get(timeframe, 15 * 60 * 1000)
        
        # 从当前时间往前推
        now_ms = int(time.time() * 1000)
        
        # 生成历史K线
        price = self.base_price
        for i in range(limit - 1, -1, -1):
            timestamp = now_ms - i * interval_ms
            
            # 随机游走 + 趋势
            change = random.gauss(0, self.volatility)
            if random.random() < 0.3:  # 30%概率改变趋势
                self.trend_strength = random.uniform(-0.3, 0.3)
                self.trend_duration = random.randint(5, 20)
            
            if self.trend_duration > 0:
                change += self.trend_strength * 0.001
                self.trend_duration -= 1
            
            price = price * (1 + change)
            
            # 生成OHLCV
            high = price * (1 + abs(random.gauss(0, self.volatility * 0.5)))
            low = price * (1 - abs(random.gauss(0, self.volatility * 0.5)))
            open_price = price * (1 + random.gauss(0, self.volatility * 0.3))
            close = price
            volume = random.uniform(100, 500)
            
            ohlcv.append([timestamp, open_price, high, low, close, volume])
        
        # 更新当前价格为最新收盘价
        if ohlcv:
            self.current_price = ohlcv[-1][4]
        
        return ohlcv
    
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取当前行情
        
        Args:
            symbol: 交易对
            
        Returns:
            模拟的ticker数据
        """
        # 更新当前价格（小幅波动）
        change = random.gauss(0, self.volatility * 0.5)
        self.current_price = self.current_price * (1 + change)
        
        return {
            'symbol': symbol,
            'last': self.current_price,
            'bid': self.current_price * 0.9999,
            'ask': self.current_price * 1.0001,
            'high': self.current_price * 1.01,
            'low': self.current_price * 0.99,
            'volume': random.uniform(1000, 5000)
        }
    
    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            symbols: 交易对列表（忽略）
            
        Returns:
            模拟的持仓列表
        """
        positions = []
        
        if self.positions['long']['amount'] > 0:
            unrealized_pnl = (self.current_price - self.positions['long']['entry_price']) * self.positions['long']['amount']
            positions.append({
                'symbol': 'BTC/USDT:USDT',
                'side': 'long',
                'contracts': self.positions['long']['amount'],
                'contractSize': 1,
                'entryPrice': self.positions['long']['entry_price'],
                'markPrice': self.current_price,
                'notional': self.positions['long']['amount'] * self.current_price,
                'unrealizedPnl': unrealized_pnl,
                'percentage': (unrealized_pnl / self.positions['long']['total_cost']) * 100 if self.positions['long']['total_cost'] > 0 else 0
            })
        
        if self.positions['short']['amount'] > 0:
            unrealized_pnl = (self.positions['short']['entry_price'] - self.current_price) * self.positions['short']['amount']
            positions.append({
                'symbol': 'BTC/USDT:USDT',
                'side': 'short',
                'contracts': self.positions['short']['amount'],
                'contractSize': 1,
                'entryPrice': self.positions['short']['entry_price'],
                'markPrice': self.current_price,
                'notional': self.positions['short']['amount'] * self.current_price,
                'unrealizedPnl': unrealized_pnl,
                'percentage': (unrealized_pnl / self.positions['short']['total_cost']) * 100 if self.positions['short']['total_cost'] > 0 else 0
            })
        
        return positions
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建市价单
        
        Args:
            symbol: 交易对
            side: 方向 ('buy', 'sell')
            amount: 数量
            params: 额外参数（如posSide）
            
        Returns:
            模拟的订单信息
        """
        params = params or {}
        pos_side = params.get('posSide', 'long')
        
        # 生成订单ID
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        
        # 计算成交价格（加入微小滑点）
        slippage = random.uniform(-0.0001, 0.0001)
        filled_price = self.current_price * (1 + slippage)
        
        # 计算手续费（taker: 0.05%）
        fee_rate = 0.0005
        fee = amount * filled_price * fee_rate
        
        # 更新持仓和余额
        if side == 'buy' and pos_side == 'long':
            # 开多 / 加多
            old_amount = self.positions['long']['amount']
            old_cost = self.positions['long']['total_cost']
            new_cost = amount * filled_price + fee
            
            self.positions['long']['amount'] = old_amount + amount
            self.positions['long']['total_cost'] = old_cost + new_cost
            self.positions['long']['entry_price'] = (old_amount * self.positions['long']['entry_price'] + amount * filled_price) / (old_amount + amount) if old_amount > 0 else filled_price
            
            self.balance -= new_cost
            
        elif side == 'sell' and pos_side == 'short':
            # 开空 / 加空
            old_amount = self.positions['short']['amount']
            old_cost = self.positions['short']['total_cost']
            new_cost = amount * filled_price + fee
            
            self.positions['short']['amount'] = old_amount + amount
            self.positions['short']['total_cost'] = old_cost + new_cost
            self.positions['short']['entry_price'] = (old_amount * self.positions['short']['entry_price'] + amount * filled_price) / (old_amount + amount) if old_amount > 0 else filled_price
            
            self.balance -= new_cost
            
        elif side == 'sell' and pos_side == 'long':
            # 平多
            epsilon = 1e-8  # 浮点数精度容差
            if self.positions['long']['amount'] >= amount - epsilon:
                # 如果接近持仓总量，直接清空（避免浮点数残余）
                if abs(self.positions['long']['amount'] - amount) < epsilon:
                    amount = self.positions['long']['amount']
                
                pnl = (filled_price - self.positions['long']['entry_price']) * amount - fee
                self.balance += amount * filled_price - fee
                self.positions['long']['amount'] -= amount
                self.positions['long']['total_cost'] -= (self.positions['long']['total_cost'] / (self.positions['long']['amount'] + amount)) * amount
                
                if self.positions['long']['amount'] < 0.0001:
                    self.positions['long'] = {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0}
            else:
                logger.error(f"平多失败: 持仓不足 (持有{self.positions['long']['amount']}, 尝试平{amount})")
                
        elif side == 'buy' and pos_side == 'short':
            # 平空
            epsilon = 1e-8  # 浮点数精度容差
            if self.positions['short']['amount'] >= amount - epsilon:
                # 如果接近持仓总量，直接清空（避免浮点数残余）
                if abs(self.positions['short']['amount'] - amount) < epsilon:
                    amount = self.positions['short']['amount']
                
                pnl = (self.positions['short']['entry_price'] - filled_price) * amount - fee
                self.balance += amount * self.positions['short']['entry_price'] - (amount * filled_price + fee)
                self.positions['short']['amount'] -= amount
                self.positions['short']['total_cost'] -= (self.positions['short']['total_cost'] / (self.positions['short']['amount'] + amount)) * amount
                
                if self.positions['short']['amount'] < 0.0001:
                    self.positions['short'] = {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0}
            else:
                logger.error(f"平空失败: 持仓不足 (持有{self.positions['short']['amount']}, 尝试平{amount})")
        
        # 创建订单记录
        order = {
            'id': order_id,
            'symbol': symbol,
            'type': 'market',
            'side': side,
            'amount': amount,
            'price': filled_price,
            'average': filled_price,
            'filled': amount,
            'remaining': 0,
            'status': 'closed',
            'fee': {'cost': fee, 'currency': 'USDT'},
            'timestamp': int(time.time() * 1000),
            'datetime': datetime.now().isoformat(),
            'info': {'posSide': pos_side}
        }
        
        self.orders.append(order)
        return order
    
    def close_position(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """
        平仓
        
        Args:
            symbol: 交易对
            side: 持仓方向 ('long', 'short')
            amount: 平仓数量
            
        Returns:
            模拟的平仓订单
        """
        if side == 'long':
            return self.create_market_order(symbol, 'sell', amount, {'posSide': 'long'})
        else:
            return self.create_market_order(symbol, 'buy', amount, {'posSide': 'short'})
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取模拟交易统计
        
        Returns:
            统计信息
        """
        balance_info = self.fetch_balance()
        total_equity = balance_info['USDT']['total']
        total_pnl = total_equity - self.initial_balance
        roi = (total_pnl / self.initial_balance) * 100
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_equity': total_equity,
            'total_pnl': total_pnl,
            'roi': roi,
            'total_orders': len(self.orders),
            'current_price': self.current_price,
            'long_position': self.positions['long']['amount'],
            'short_position': self.positions['short']['amount']
        }
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓（兼容OKX接口）
        
        Returns:
            持仓列表
        """
        return self.fetch_positions()
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        reduce_only: bool = False,
        pos_side: str = 'long'
    ) -> Dict[str, Any]:
        """
        下市价单（兼容OKX接口）
        
        Args:
            symbol: 交易对
            side: 方向 ('buy', 'sell')
            amount: 数量
            reduce_only: 是否只减仓
            pos_side: 持仓方向 ('long', 'short')
            
        Returns:
            订单信息
        """
        params = {'posSide': pos_side}
        return self.create_market_order(symbol, side, amount, params)
    
    def close_all_positions(self) -> bool:
        """
        清空所有持仓（兼容OKX接口）
        
        Returns:
            是否成功
        """
        logger.info("🧹 清空所有模拟持仓")
        self.positions = {
            'long': {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0},
            'short': {'amount': 0.0, 'entry_price': 0.0, 'total_cost': 0.0}
        }
        return True

