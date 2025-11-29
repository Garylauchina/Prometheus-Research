"""
Order Manager for OKX API
"""

import logging
import time
from okx import Trade
from .errors import APIError, OrderError

logger = logging.getLogger(__name__)


class Order:
    """订单对象"""
    
    def __init__(self, order_id, request, status='submitted', timestamp=None):
        """
        初始化订单
        
        Args:
            order_id: 订单ID
            request: 订单请求字典
            status: 订单状态
            timestamp: 时间戳
        """
        self.order_id = order_id
        self.request = request
        self.status = status
        self.timestamp = timestamp or time.time()
        
        # 从request中提取信息
        self.market = request.get('market')
        self.symbol = request.get('symbol')
        self.side = request.get('side')
        self.order_type = request.get('order_type')
        self.size = request.get('size')
        self.price = request.get('price')
        
        # 成交信息
        self.filled_size = 0.0
        self.filled_price = 0.0
        self.fee = 0.0
    
    def update_from_okx(self, okx_order):
        """
        从OKX订单数据更新
        
        Args:
            okx_order: OKX API返回的订单数据
        """
        # 更新状态
        state = okx_order.get('state')
        state_map = {
            'live': 'open',
            'partially_filled': 'partial',
            'filled': 'filled',
            'canceled': 'cancelled'
        }
        self.status = state_map.get(state, state)
        
        # 更新成交信息（处理空字符串）
        self.filled_size = float(okx_order.get('accFillSz') or 0)
        self.filled_price = float(okx_order.get('avgPx') or 0)
        self.fee = float(okx_order.get('fee') or 0)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'market': self.market,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'size': self.size,
            'price': self.price,
            'status': self.status,
            'filled_size': self.filled_size,
            'filled_price': self.filled_price,
            'fee': self.fee,
            'timestamp': self.timestamp
        }


class OrderManager:
    """订单管理器"""
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - api_key: API密钥
                - secret_key: 密钥
                - passphrase: 密码
                - flag: '0'实盘, '1'模拟盘
        """
        self.config = config
        self.trade_api = Trade.TradeAPI(
            config['api_key'],
            config['secret_key'],
            config['passphrase'],
            flag=config.get('flag', '1')
        )
        self.orders = {}  # orderId -> Order
        
        logger.info(f"OrderManager initialized (flag={config.get('flag', '1')})")
    
    def place_order(self, order_request):
        """
        下单
        
        Args:
            order_request: 订单请求
                - market: 'spot' or 'futures'
                - symbol: 交易对
                - side: 'buy' or 'sell'
                - order_type: 'market' or 'limit'
                - size: 数量
                - price: 价格（限价单）
                - leverage: 杠杆（合约）
        
        Returns:
            Order对象
        """
        try:
            # 转换为OKX格式
            okx_order = self._convert_to_okx_format(order_request)
            
            logger.info(f"Placing order: {okx_order}")
            
            # 下单
            result = self.trade_api.place_order(**okx_order)
            
            if result['code'] == '0' and len(result['data']) > 0:
                order_id = result['data'][0]['ordId']
                
                # 创建Order对象
                order = Order(
                    order_id=order_id,
                    request=order_request,
                    status='submitted',
                    timestamp=time.time()
                )
                
                # 保存订单
                self.orders[order_id] = order
                
                logger.info(f"Order placed successfully: {order_id}")
                return order
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to place order: {error_msg}")
                raise OrderError(f"Failed to place order: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in place_order: {e}")
            raise
    
    def cancel_order(self, order_id, symbol=None):
        """
        撤单
        
        Args:
            order_id: 订单ID
            symbol: 交易对（可选，如果提供则从订单中获取）
        
        Returns:
            bool: 是否成功
        """
        try:
            order = self.orders.get(order_id)
            if not order and not symbol:
                raise ValueError(f"Order {order_id} not found and symbol not provided")
            
            inst_id = symbol or order.symbol
            
            result = self.trade_api.cancel_order(
                instId=inst_id,
                ordId=order_id
            )
            
            if result['code'] == '0':
                if order:
                    order.status = 'cancelled'
                logger.info(f"Order cancelled: {order_id}")
                return True
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to cancel order: {error_msg}")
                raise OrderError(f"Failed to cancel order: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in cancel_order: {e}")
            raise
    
    def get_order_status(self, order_id, symbol=None):
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对（可选）
        
        Returns:
            Order对象
        """
        try:
            order = self.orders.get(order_id)
            if not order and not symbol:
                raise ValueError(f"Order {order_id} not found and symbol not provided")
            
            inst_id = symbol or order.symbol
            
            result = self.trade_api.get_order(
                instId=inst_id,
                ordId=order_id
            )
            
            if result['code'] == '0' and len(result['data']) > 0:
                okx_order = result['data'][0]
                
                if order:
                    order.update_from_okx(okx_order)
                else:
                    # 创建新的Order对象
                    order = Order(
                        order_id=order_id,
                        request={'symbol': inst_id},
                        status='unknown'
                    )
                    order.update_from_okx(okx_order)
                    self.orders[order_id] = order
                
                return order
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get order status: {error_msg}")
                raise OrderError(f"Failed to get order status: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in get_order_status: {e}")
            raise
    
    def _convert_to_okx_format(self, order_request):
        """
        转换为OKX格式
        
        Args:
            order_request: 订单请求
        
        Returns:
            dict: OKX格式的订单参数
        """
        market = order_request['market']
        
        if market == 'spot':
            # 现货订单（跨币种保证金模式使用cross）
            okx_order = {
                'instId': order_request['symbol'],
                'tdMode': 'cross',  # 跨币种保证金模式
                'side': order_request['side'],
                'ordType': order_request['order_type'],
                'sz': str(order_request['size'])
            }
            
            # 限价单需要价格
            if order_request['order_type'] == 'limit':
                okx_order['px'] = str(order_request['price'])
        
        elif market == 'futures':
            # 合约订单
            okx_order = {
                'instId': order_request['symbol'],
                'tdMode': 'isolated',  # 逐仓模式
                'side': order_request['side'],
                'posSide': 'long' if order_request['side'] == 'buy' else 'short',
                'ordType': order_request['order_type'],
                'sz': str(order_request['size'])
            }
            
            # 杠杆（注意：python-okx库中参数名可能是leverage而非lever）
            # 先不设置杠杆，通过账户配置设置
            
            # 限价单需要价格
            if order_request['order_type'] == 'limit':
                okx_order['px'] = str(order_request['price'])
        
        else:
            raise ValueError(f"Unknown market type: {market}")
        
        return okx_order
    
    def get_all_orders(self):
        """获取所有订单"""
        return list(self.orders.values())
    
    def get_open_orders(self):
        """获取所有未完成订单"""
        return [order for order in self.orders.values() if order.status in ['submitted', 'open', 'partial']]
