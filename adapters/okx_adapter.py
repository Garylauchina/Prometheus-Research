"""
OKX Trading Adapter - Main adapter class with enhanced error handling
"""

import logging
import time
import random
from .market_data import MarketDataManager
from .order_manager import OrderManager
from .account_sync import AccountSync
from .risk_manager import RiskManager
from .errors import (
    RiskControlError, OrderError, APIError, NetworkError, DataConsistencyError
)

logger = logging.getLogger(__name__)


class OKXTradingAdapter:
    """
    增强的OKX交易适配器
    
    添加了重试机制、增强的错误处理和数据验证功能
    """
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - api_key: API密钥
                - secret_key: 密钥
                - passphrase: 密码
                - flag: '0'实盘, '1'模拟盘
                - risk: 风控配置（可选）
                - max_retries: 最大重试次数（可选，默认3）
                - retry_base_delay: 重试基础延迟（可选，默认1秒）
        """
        self.config = config
        
        # 初始化各个管理器
        self.market_data = MarketDataManager(config)
        self.order_manager = OrderManager(config)
        self.account_sync = AccountSync(config)
        self.risk_manager = RiskManager(config)
        
        # 重试配置
        self.max_retries = config.get('max_retries', 3)
        self.retry_base_delay = config.get('retry_base_delay', 1.0)
        
        # API调用统计
        self.api_call_stats = {
            'success': 0,
            'failure': 0,
            'retry': 0
        }
        
        logger.info(f"OKX交易适配器初始化完成 (flag={config.get('flag', '1')}, max_retries={self.max_retries})")
        
    def _retry_wrapper(self, func, *args, **kwargs):
        """
        重试装饰器，处理API调用的重试逻辑
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            相应的异常
        """
        retries = 0
        last_exception = None
        
        while retries <= self.max_retries:
            try:
                result = func(*args, **kwargs)
                self.api_call_stats['success'] += 1
                return result
            except (NetworkError, TimeoutError) as e:
                # 网络错误和超时可以重试
                last_exception = e
                retries += 1
                self.api_call_stats['retry'] += 1
                
                if retries > self.max_retries:
                    self.api_call_stats['failure'] += 1
                    logger.error(f"API调用失败: {func.__name__} 重试 {self.max_retries} 次后仍失败")
                    raise
                
                # 指数退避策略
                delay = self.retry_base_delay * (2 ** (retries - 1)) * (0.5 + random.random())
                logger.warning(f"API调用失败: {e}, {delay:.2f}秒后第 {retries} 次重试")
                time.sleep(delay)
            except (APIError, OrderError) as e:
                # 根据错误信息决定是否重试
                error_msg = str(e)
                retryable_errors = [
                    "Rate limit", "Too many requests", "Service unavailable",
                    "Gateway timeout", "Request timeout"
                ]
                
                if any(error in error_msg for error in retryable_errors):
                    last_exception = e
                    retries += 1
                    self.api_call_stats['retry'] += 1
                    
                    if retries > self.max_retries:
                        self.api_call_stats['failure'] += 1
                        logger.error(f"API调用失败: {func.__name__} 重试 {self.max_retries} 次后仍失败")
                        raise
                    
                    delay = self.retry_base_delay * (2 ** (retries - 1)) * (0.5 + random.random())
                    logger.warning(f"API调用失败: {e}, {delay:.2f}秒后第 {retries} 次重试")
                    time.sleep(delay)
                else:
                    # 其他错误直接抛出
                    self.api_call_stats['failure'] += 1
                    raise
            except Exception as e:
                # 未知错误直接抛出
                self.api_call_stats['failure'] += 1
                raise
    
    def get_current_price(self, symbol):
        """
        获取当前价格
        
        Args:
            symbol: 交易对，如'BTC-USDT'
        
        Returns:
            float: 当前价格
            
        Raises:
            APIError: API调用失败
            DataConsistencyError: 数据不一致错误
        """
        def _get_price():
            price = self.market_data.get_ticker(symbol)
            
            # 验证价格有效性
            if price is None or price <= 0:
                raise DataConsistencyError(f"获取到无效价格: {price}")
            
            return price
        
        return self._retry_wrapper(_get_price)
    
    def get_market_data(self, symbol):
        """
        获取市场数据
        
        Args:
            symbol: 交易对
        
        Returns:
            dict: 市场数据
        """
        return self.market_data.get_market_data(symbol)
    
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
        
        Raises:
            RiskControlError: 风控拒绝
            OrderError: 下单失败
            ValueError: 参数验证失败
        """
        # 预检查订单参数
        required_fields = ['market', 'symbol', 'side', 'order_type', 'size']
        for field in required_fields:
            if field not in order_request or order_request[field] is None:
                raise ValueError(f"缺少必需的订单字段: {field}")
        
        # 验证参数有效性
        if order_request['size'] <= 0:
            raise ValueError(f"无效的订单数量: {order_request['size']}")
        
        if order_request['order_type'] == 'limit' and ('price' not in order_request or order_request['price'] <= 0):
            raise ValueError(f"限价单必须指定有效价格: {order_request.get('price')}")
        
        # 验证交易方向
        if order_request['side'] not in ['buy', 'sell']:
            raise ValueError(f"无效的交易方向: {order_request['side']}")
        
        def _place_order():
            # 获取账户余额（用于风控检查）
            try:
                account_summary = self.account_sync.get_account_summary()
            except Exception as e:
                logger.warning(f"无法获取账户摘要进行风控检查: {e}")
                # 账户信息获取失败时，风控会更严格
                account_summary = {'total_equity': 0, 'available_balance': 0}
            
            # 风控检查
            try:
                self.risk_manager.check_order(order_request, account_summary)
            except RiskControlError as e:
                logger.error(f"订单被风控拒绝: {e}")
                raise
            
            # 下单
            order = self.order_manager.place_order(order_request)
            
            # 验证订单结果
            if order is None or not hasattr(order, 'order_id'):
                raise OrderError(f"下单成功但返回无效订单对象: {order}")
            
            return order
        
        return self._retry_wrapper(_place_order)
    
    def cancel_order(self, order_id, symbol=None):
        """
        撤单
        
        Args:
            order_id: 订单ID
            symbol: 交易对（可选）
        
        Returns:
            bool: 是否成功
        """
        return self.order_manager.cancel_order(order_id, symbol)
    
    def get_order_status(self, order_id, symbol=None):
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对（可选）
        
        Returns:
            Order对象
        """
        return self.order_manager.get_order_status(order_id, symbol)
    
    def get_account_balance(self, ccy=None):
        """
        获取账户余额
        
        Args:
            ccy: 币种（可选）
        
        Returns:
            dict: 余额信息
        """
        return self.account_sync.get_balance(ccy)
    
    def get_positions(self, inst_type=None):
        """
        获取持仓
        
        Args:
            inst_type: 产品类型（可选）
        
        Returns:
            dict: 持仓信息
        """
        return self.account_sync.get_positions(inst_type)
    
    def get_account_summary(self):
        """
        获取账户摘要
        
        Returns:
            dict: 账户摘要
            
        Raises:
            APIError: API调用失败
            DataConsistencyError: 数据不一致错误
        """
        def _get_account_summary():
            summary = self.account_sync.get_account_summary()
            
            # 验证摘要数据
            if summary is None:
                raise DataConsistencyError("获取到空的账户摘要")
            
            # 基本字段检查
            expected_fields = ['total_equity']  # 只检查必要的total_equity字段
            for field in expected_fields:
                if field not in summary:
                    logger.warning(f"账户摘要缺少预期字段: {field}")
            
            # 对于available_balance，使用更宽松的检查，因为OKX API可能返回不同字段名
            if 'available_balance' not in summary:
                # 尝试从其他可能的字段获取可用余额
                if 'availBal' in summary:
                    summary['available_balance'] = summary['availBal']
                else:
                    logger.debug(f"账户摘要未找到可用余额字段，将available_balance设置为total_equity")
                    summary['available_balance'] = summary.get('total_equity', 0)
            
            return summary
        
        return self._retry_wrapper(_get_account_summary)
    
    def get_usdt_balance(self):
        """
        获取USDT余额
        
        Returns:
            float: USDT可用余额
        """
        return self.account_sync.get_usdt_balance()
    
    def get_risk_metrics(self):
        """
        获取风控指标
        
        Returns:
            dict: 风控指标
        """
        return self.risk_manager.get_risk_metrics()
    
    def check_stop_loss(self, position, current_price):
        """
        检查止损
        
        Args:
            position: 持仓信息
            current_price: 当前价格
        
        Returns:
            bool: 是否需要止损
        """
        try:
            # 验证输入参数
            if position is None or current_price is None or current_price <= 0:
                logger.warning(f"止损检查参数无效: position={position}, price={current_price}")
                # 保守处理，返回需要止损
                return True
            
            return self.risk_manager.check_stop_loss(position, current_price)
        except Exception as e:
            logger.error(f"止损检查失败: {e}")
            # 出错时保守处理，返回需要止损
            return True
    
    def get_api_stats(self):
        """
        获取API调用统计信息
        
        Returns:
            dict: API调用统计
                - success: 成功次数
                - failure: 失败次数
                - retry: 重试次数
        """
        return self.api_call_stats.copy()
    
    def reset_api_stats(self):
        """
        重置API调用统计
        """
        self.api_call_stats = {
            'success': 0,
            'failure': 0,
            'retry': 0
        }
    
    def get_price(self, symbol):
        """
        获取价格（别名）
        
        Args:
            symbol: 交易对
        
        Returns:
            float: 当前价格
        """
        return self.get_current_price(symbol)
    
    def get_candles(self, symbol, bar='1H', limit=100):
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            bar: K线周期
            limit: 数量
        
        Returns:
            list: K线数据
            
        Raises:
            APIError: API调用失败
            DataConsistencyError: 数据不一致错误
        """
        def _get_candles():
            candles = self.market_data.get_candles(symbol, bar, limit)
            
            # 验证K线数据
            if not candles:
                raise DataConsistencyError(f"获取到空的K线数据: {symbol}")
            
            if len(candles) < max(5, limit // 4):  # 至少需要一些数据
                raise DataConsistencyError(f"K线数据不足: {len(candles)}/{limit}")
            
            # 检查数据有效性
            for candle in candles:
                # 检查OHLC数据是否有效
                if len(candle) < 5:  # 至少需要包含时间戳、开、高、低、收
                    raise DataConsistencyError(f"无效的K线数据格式: {candle}")
                
                # 检查价格数据是否合理
                price_values = candle[1:5]  # 假设索引1-4是OHLC
                for price in price_values:
                    if price is None:  # 首先检查None
                        raise DataConsistencyError(f"检测到无效价格: {price} in {candle}")
                    try:
                        price_float = float(price)  # 转换为浮点数
                        if price_float <= 0:
                            raise DataConsistencyError(f"检测到无效价格: {price} in {candle}")
                    except ValueError:
                        raise DataConsistencyError(f"价格格式无效: {price} in {candle}")
            
            return candles
        
        return self._retry_wrapper(_get_candles)
