#!/usr/bin/env python3
"""
OKX交易所API封装
==================

支持：
1. 实盘交易（Live Trading）
2. 虚拟盘交易（Paper Trading）
3. 市场数据获取
4. 订单管理
"""

import ccxt
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class OKXExchange:
    """OKX交易所接口"""
    
    def __init__(
        self, 
        api_key: str = "", 
        api_secret: str = "", 
        passphrase: str = "",
        paper_trading: bool = True,
        testnet: bool = False
    ):
        """
        初始化OKX交易所接口
        
        Args:
            api_key: API Key
            api_secret: API Secret
            passphrase: API Passphrase
            paper_trading: 是否使用虚拟盘（模拟交易）
            testnet: 是否使用测试网
        """
        self.paper_trading = paper_trading
        self.testnet = testnet
        
        # 初始化ccxt
        exchange_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
        }
        
        # 关键修复：OKX模拟盘的正确配置方式
        if testnet:
            exchange_config['sandbox'] = True  # 修复：直接在顶层配置sandbox
            exchange_config['options'] = {'defaultType': 'swap'}  # 永续合约
            logger.info("🧪 OKX Sandbox模式（模拟盘）")
        
        self.exchange = ccxt.okx(exchange_config)
        
        # paper_trading模式（本地模拟）
        if paper_trading and not testnet:
            self.paper_positions = {}
            self.paper_balance = {'USDT': 100000.0}  # 虚拟资金10万
            self.paper_orders = []
            logger.info("📝 OKX本地模拟模式（初始资金: $100,000）")
        elif not testnet and not paper_trading:
            logger.warning("⚠️  OKX实盘模式 - 请谨慎操作！")
        
        logger.info(f"✅ OKX交易所初始化完成")
    
    # ==================== 市场数据 ====================
    
    def get_ticker(self, symbol: str = 'BTC/USDT') -> Dict:
        """
        获取行情数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
        
        Returns:
            {
                'symbol': 'BTC/USDT',
                'last': 50000.0,  # 最新价
                'bid': 49999.0,   # 买一价
                'ask': 50001.0,   # 卖一价
                'timestamp': 1234567890
            }
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            return None
    
    def get_orderbook(self, symbol: str = 'BTC/USDT', depth: int = 10) -> Dict:
        """
        获取订单簿
        
        Args:
            symbol: 交易对
            depth: 深度（档位数）
        
        Returns:
            {
                'bids': [[price, size], ...],  # 买单
                'asks': [[price, size], ...],  # 卖单
                'timestamp': 1234567890
            }
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, depth)
            return {
                'bids': orderbook['bids'][:depth],
                'asks': orderbook['asks'][:depth],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return None
    
    def get_klines(
        self, 
        symbol: str = 'BTC/USDT',
        timeframe: str = '1m',
        limit: int = 100
    ) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期 ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: 数量
        
        Returns:
            [
                {
                    'timestamp': 1234567890,
                    'open': 50000,
                    'high': 50100,
                    'low': 49900,
                    'close': 50050,
                    'volume': 123.45
                },
                ...
            ]
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [
                {
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return []
    
    # ==================== 账户信息 ====================
    
    def get_balance(self) -> Dict:
        """
        获取账户余额
        
        Returns:
            {
                'USDT': {
                    'free': 10000.0,   # 可用
                    'used': 5000.0,    # 冻结
                    'total': 15000.0   # 总计
                },
                'BTC': {...}
            }
        """
        if self.paper_trading:
            # 虚拟盘返回模拟余额
            return {
                currency: {
                    'free': balance,
                    'used': 0.0,
                    'total': balance
                }
                for currency, balance in self.paper_balance.items()
            }
        
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {}
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对，None表示获取所有持仓
        
        Returns:
            [
                {
                    'symbol': 'BTC/USDT',
                    'side': 'long',     # 'long' or 'short'
                    'size': 0.1,        # 数量
                    'entry_price': 50000.0,  # 开仓价
                    'current_price': 51000.0, # 当前价
                    'pnl': 100.0,       # 未实现盈亏
                    'leverage': 10.0    # 杠杆
                },
                ...
            ]
        """
        if self.paper_trading:
            # 虚拟盘返回模拟持仓
            positions = []
            for pos_symbol, pos_data in self.paper_positions.items():
                if symbol is None or pos_symbol == symbol:
                    # 获取当前价格
                    ticker = self.get_ticker(pos_symbol)
                    if ticker:
                        current_price = ticker['last']
                        pnl = (current_price - pos_data['entry_price']) * pos_data['size']
                        if pos_data['side'] == 'short':
                            pnl = -pnl
                        
                        positions.append({
                            'symbol': pos_symbol,
                            'side': pos_data['side'],
                            'size': pos_data['size'],
                            'entry_price': pos_data['entry_price'],
                            'current_price': current_price,
                            'pnl': pnl,
                            'leverage': pos_data.get('leverage', 1.0)
                        })
            return positions
        
        try:
            positions = self.exchange.fetch_positions([symbol] if symbol else None)
            return positions
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    # ==================== 订单管理 ====================
    
    def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        order_type: str = 'market',
        price: float = None,
        leverage: float = 1.0
    ) -> Optional[Dict]:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 'buy' or 'sell'
            size: 数量
            order_type: 'market' or 'limit'
            price: 限价单价格
            leverage: 杠杆倍数
        
        Returns:
            {
                'order_id': '123456',
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'size': 0.1,
                'price': 50000.0,
                'status': 'filled',
                'timestamp': 1234567890
            }
        """
        if self.paper_trading:
            # 虚拟盘下单
            return self._place_paper_order(symbol, side, size, order_type, price, leverage)
        
        try:
            # 转换symbol格式：BTC/USDT → BTC-USDT-SWAP
            inst_id = symbol.replace('/', '-').replace(':USDT', '') + '-SWAP'
            if inst_id.endswith('-SWAP-SWAP'):
                inst_id = inst_id.replace('-SWAP-SWAP', '-SWAP')
            
            # 使用OKX私有API直接下单（避免ccxt的参数转换问题）
            request = {
                'instId': inst_id,
                'tdMode': 'cross',  # 全仓模式
                'side': side,
                'posSide': 'long' if side == 'buy' else 'short',  # 持仓方向
                'ordType': 'market' if order_type == 'market' else 'limit',
                'sz': str(int(size * 100))  # 转换为张数（1 BTC = 100张）
            }
            
            # 限价单需要价格
            if order_type == 'limit':
                request['px'] = str(price)
            
            # 设置杠杆
            if leverage > 1:
                request['lever'] = str(int(leverage))
            
            # 调用OKX私有API
            response = self.exchange.privatePostTradeOrder(request)
            
            if response['code'] == '0' and response['data']:
                order_data = response['data'][0]
                # logger.info(f"✅ 订单已提交: {symbol} {side} {size} @ {order_type}")  # 关闭详细日志
                
                return {
                    'order_id': order_data['ordId'],
                    'symbol': symbol,
                    'side': side,
                    'size': size,
                    'price': price,
                    'status': 'submitted',
                    'timestamp': int(order_data['ts'])
                }
            else:
                logger.error(f"下单失败: {response}")
                return None
        except Exception as e:
            logger.error(f"下单失败: {e}")
            return None
    
    def _place_paper_order(
        self,
        symbol: str,
        side: str,
        size: float,
        order_type: str,
        price: float,
        leverage: float
    ) -> Optional[Dict]:
        """虚拟盘下单（内部方法）"""
        try:
            # 获取当前价格
            ticker = self.get_ticker(symbol)
            if not ticker:
                logger.error("无法获取市场价格")
                return None
            
            # 市价单使用当前价
            execution_price = price if order_type == 'limit' else ticker['last']
            
            # 计算所需保证金
            position_value = execution_price * size
            margin_required = position_value / leverage if leverage > 1 else position_value
            
            # 检查余额
            if self.paper_balance.get('USDT', 0) < margin_required:
                logger.error(f"余额不足: 需要{margin_required}, 可用{self.paper_balance.get('USDT', 0)}")
                return None
            
            # 扣除保证金
            self.paper_balance['USDT'] -= margin_required
            
            # 更新持仓
            if symbol not in self.paper_positions:
                self.paper_positions[symbol] = {
                    'side': 'long' if side == 'buy' else 'short',
                    'size': size,
                    'entry_price': execution_price,
                    'leverage': leverage,
                    'margin': margin_required
                }
            else:
                # 简化：同方向累加，反方向对冲
                existing = self.paper_positions[symbol]
                if (side == 'buy' and existing['side'] == 'long') or \
                   (side == 'sell' and existing['side'] == 'short'):
                    # 加仓
                    total_value = existing['entry_price'] * existing['size'] + execution_price * size
                    total_size = existing['size'] + size
                    existing['entry_price'] = total_value / total_size
                    existing['size'] = total_size
                    existing['margin'] += margin_required
                else:
                    # 减仓或平仓
                    if size >= existing['size']:
                        # 完全平仓或反向开仓
                        # 简化：直接删除旧仓，开新仓
                        self.paper_balance['USDT'] += existing['margin']
                        if size > existing['size']:
                            self.paper_positions[symbol] = {
                                'side': 'long' if side == 'buy' else 'short',
                                'size': size - existing['size'],
                                'entry_price': execution_price,
                                'leverage': leverage,
                                'margin': margin_required
                            }
                        else:
                            del self.paper_positions[symbol]
                    else:
                        # 部分平仓
                        existing['size'] -= size
                        released_margin = margin_required * (size / existing['size'])
                        existing['margin'] -= released_margin
                        self.paper_balance['USDT'] += released_margin
            
            order_id = f"paper_{int(time.time() * 1000)}"
            
            logger.info(f"📝 虚拟盘订单: {symbol} {side} {size} @ {execution_price:.2f}")
            
            return {
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': execution_price,
                'status': 'filled',
                'timestamp': int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"虚拟盘下单失败: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对
        
        Returns:
            True if successful
        """
        if self.paper_trading:
            logger.info(f"📝 虚拟盘取消订单: {order_id}")
            return True
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"✅ 订单已取消: {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    def close_position(self, symbol: str, side: str = None) -> bool:
        """
        平仓
        
        Args:
            symbol: 交易对
            side: 'long' or 'short'，None表示全部平仓
        
        Returns:
            True if successful
        """
        positions = self.get_positions(symbol)
        
        for pos in positions:
            if side is None or pos['side'] == side:
                # 平仓就是反向开单
                close_side = 'sell' if pos['side'] == 'long' else 'buy'
                order = self.place_order(
                    symbol=pos['symbol'],
                    side=close_side,
                    size=abs(pos['size']),
                    order_type='market'
                )
                
                if order:
                    logger.info(f"✅ 已平仓: {pos['symbol']} {pos['side']} {pos['size']}")
                else:
                    logger.error(f"平仓失败: {pos['symbol']}")
                    return False
        
        return True
    
    # ==================== 工具方法 ====================
    
    def get_account_value(self) -> float:
        """
        获取账户总价值（USDT计价）
        
        Returns:
            总价值
        """
        if self.paper_trading:
            # 虚拟盘计算
            total = self.paper_balance.get('USDT', 0)
            
            # 加上持仓未实现盈亏
            positions = self.get_positions()
            for pos in positions:
                total += pos['pnl']
            
            return total
        
        try:
            balance = self.get_balance()
            # 简化：只计算USDT余额
            total = balance.get('USDT', {}).get('total', 0)
            
            # 加上持仓未实现盈亏
            positions = self.get_positions()
            for pos in positions:
                total += pos.get('unrealizedPnl', 0)
            
            return total
        except Exception as e:
            logger.error(f"获取账户价值失败: {e}")
            return 0.0
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            ticker = self.get_ticker('BTC/USDT')
            if ticker:
                logger.info(f"✅ OKX连接成功 - BTC价格: ${ticker['last']:,.2f}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ OKX连接失败: {e}")
            return False


def test_okx_api():
    """测试OKX API"""
    print()
    print("=" * 80)
    print("🧪 OKX API测试")
    print("=" * 80)
    print()
    
    # 创建虚拟盘实例
    exchange = OKXExchange(paper_trading=True)
    
    # 1. 测试连接
    print("1. 测试连接...")
    if exchange.test_connection():
        print("   ✅ 连接成功")
    else:
        print("   ❌ 连接失败")
        return
    
    # 2. 获取行情
    print("\n2. 获取行情...")
    ticker = exchange.get_ticker('BTC/USDT')
    if ticker:
        print(f"   BTC/USDT: ${ticker['last']:,.2f}")
        print(f"   买一: ${ticker['bid']:,.2f}")
        print(f"   卖一: ${ticker['ask']:,.2f}")
    
    # 3. 获取订单簿
    print("\n3. 获取订单簿...")
    orderbook = exchange.get_orderbook('BTC/USDT', depth=5)
    if orderbook:
        print(f"   买单前5档: {orderbook['bids'][:3]}")
        print(f"   卖单前5档: {orderbook['asks'][:3]}")
    
    # 4. 查看初始余额
    print("\n4. 初始余额...")
    balance = exchange.get_balance()
    print(f"   USDT: ${balance['USDT']['total']:,.2f}")
    
    # 5. 模拟下单
    print("\n5. 模拟下单（买入0.01 BTC）...")
    order = exchange.place_order(
        symbol='BTC/USDT',
        side='buy',
        size=0.01,
        leverage=10.0
    )
    if order:
        print(f"   ✅ 订单成功: {order['order_id']}")
        print(f"   价格: ${order['price']:,.2f}")
    
    # 6. 查看持仓
    print("\n6. 查看持仓...")
    positions = exchange.get_positions()
    for pos in positions:
        print(f"   {pos['symbol']} {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")
        print(f"   当前价: ${pos['current_price']:,.2f}")
        print(f"   盈亏: ${pos['pnl']:,.2f}")
    
    # 7. 账户总价值
    print("\n7. 账户总价值...")
    account_value = exchange.get_account_value()
    print(f"   总价值: ${account_value:,.2f}")
    
    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_okx_api()

