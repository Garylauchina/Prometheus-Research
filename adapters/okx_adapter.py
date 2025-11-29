"""
OKX Trading Adapter - Main adapter class
"""

import logging
from .market_data import MarketDataManager
from .order_manager import OrderManager
from .account_sync import AccountSync
from .risk_manager import RiskManager
from .errors import RiskControlError, OrderError

logger = logging.getLogger(__name__)


class OKXTradingAdapter:
    """OKX交易适配器"""
    
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
        """
        self.config = config
        
        # 初始化各个管理器
        self.market_data = MarketDataManager(config)
        self.order_manager = OrderManager(config)
        self.account_sync = AccountSync(config)
        self.risk_manager = RiskManager(config)
        
        logger.info(f"OKXTradingAdapter initialized (flag={config.get('flag', '1')})")
    
    def get_current_price(self, symbol):
        """
        获取当前价格
        
        Args:
            symbol: 交易对，如'BTC-USDT'
        
        Returns:
            float: 当前价格
        """
        return self.market_data.get_ticker(symbol)
    
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
        """
        # 获取账户余额（用于风控检查）
        try:
            account_summary = self.account_sync.get_account_summary()
        except Exception as e:
            logger.warning(f"Failed to get account summary for risk check: {e}")
            account_summary = None
        
        # 风控检查
        try:
            self.risk_manager.check_order(order_request, account_summary)
        except RiskControlError as e:
            logger.error(f"Order rejected by risk control: {e}")
            raise
        
        # 下单
        try:
            order = self.order_manager.place_order(order_request)
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
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
        """
        return self.account_sync.get_account_summary()
    
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
        return self.risk_manager.check_stop_loss(position, current_price)
    
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
        """
        return self.market_data.get_candles(symbol, bar, limit)
