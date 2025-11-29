"""
Risk Manager for trading
"""

import logging
from datetime import datetime
from .errors import RiskControlError

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - max_daily_trades: 日内最大交易次数
                - max_daily_loss: 日内最大亏损比例
                - max_leverage: 最大杠杆倍数
                - max_position_pct: 最大仓位比例
                - stop_loss_pct: 止损比例
        """
        self.config = config
        self.risk_config = config.get('risk', {})
        
        # 日内计数器
        self.daily_trades = 0
        self.daily_loss = 0.0
        self.last_reset_date = datetime.now().date()
        
        # 风控参数
        self.max_daily_trades = self.risk_config.get('max_daily_trades', 1000)
        self.max_daily_loss = self.risk_config.get('max_daily_loss', 0.10)  # 10%
        self.max_leverage = self.risk_config.get('max_leverage', 5)
        self.max_position_pct = self.risk_config.get('max_position_pct', 0.20)  # 20%
        self.stop_loss_pct = self.risk_config.get('stop_loss_pct', 0.05)  # 5%
        
        logger.info(f"RiskManager initialized: max_daily_trades={self.max_daily_trades}, "
                   f"max_daily_loss={self.max_daily_loss}, max_leverage={self.max_leverage}")
    
    def check_order(self, order_request, account_balance=None):
        """
        检查订单是否符合风控要求
        
        Args:
            order_request: 订单请求
            account_balance: 账户余额（可选）
        
        Returns:
            bool: 是否通过风控
        
        Raises:
            RiskControlError: 风控拒绝
        """
        # 重置日内计数器
        self._reset_daily_counters()
        
        # 检查日内交易次数
        if not self._check_daily_trades():
            raise RiskControlError(f"Daily trade limit exceeded: {self.daily_trades}/{self.max_daily_trades}")
        
        # 检查日内亏损
        if not self._check_daily_loss():
            raise RiskControlError(f"Daily loss limit exceeded: {self.daily_loss:.2%}/{self.max_daily_loss:.2%}")
        
        # 检查杠杆
        if not self._check_leverage(order_request):
            leverage = order_request.get('leverage', 1)
            raise RiskControlError(f"Leverage exceeds limit: {leverage}/{self.max_leverage}")
        
        # 检查仓位（如果提供了账户余额）
        if account_balance and not self._check_position_size(order_request, account_balance):
            raise RiskControlError(f"Position size exceeds limit: {self.max_position_pct:.2%}")
        
        logger.debug(f"Order passed risk control: {order_request}")
        return True
    
    def _reset_daily_counters(self):
        """重置日内计数器"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            logger.info(f"Resetting daily counters: trades={self.daily_trades}, loss={self.daily_loss:.2%}")
            self.daily_trades = 0
            self.daily_loss = 0.0
            self.last_reset_date = today
    
    def _check_daily_trades(self):
        """检查日内交易次数"""
        return self.daily_trades < self.max_daily_trades
    
    def _check_daily_loss(self):
        """检查日内亏损"""
        return self.daily_loss < self.max_daily_loss
    
    def _check_leverage(self, order_request):
        """检查杠杆"""
        if order_request.get('market') != 'futures':
            return True
        
        leverage = order_request.get('leverage', 1)
        return leverage <= self.max_leverage
    
    def _check_position_size(self, order_request, account_balance):
        """
        检查仓位大小
        
        Args:
            order_request: 订单请求
            account_balance: 账户余额
        
        Returns:
            bool: 是否通过
        """
        # 计算订单价值
        size = order_request.get('size', 0)
        price = order_request.get('price', 0)
        leverage = order_request.get('leverage', 1)
        
        if price == 0:
            # 市价单，无法精确计算
            logger.warning("Cannot check position size for market order without price")
            return True
        
        order_value = size * price / leverage  # 保证金
        
        # 获取总权益
        total_equity = account_balance.get('total_equity', 0)
        
        if total_equity == 0:
            logger.warning("Total equity is 0, cannot check position size")
            return True
        
        # 计算仓位比例
        position_pct = order_value / total_equity
        
        return position_pct <= self.max_position_pct
    
    def record_trade(self, order, result):
        """
        记录交易
        
        Args:
            order: 订单对象
            result: 交易结果
                - pnl: 盈亏
                - fee: 手续费
        """
        self.daily_trades += 1
        
        # 记录亏损
        pnl = result.get('pnl', 0)
        if pnl < 0:
            self.daily_loss += abs(pnl)
        
        logger.info(f"Trade recorded: daily_trades={self.daily_trades}, daily_loss={self.daily_loss:.2%}")
    
    def check_stop_loss(self, position, current_price):
        """
        检查止损
        
        Args:
            position: 持仓信息
                - avg_price: 平均价格
                - side: 持仓方向
            current_price: 当前价格
        
        Returns:
            bool: 是否需要止损
        """
        avg_price = position.get('avg_price', 0)
        side = position.get('side', 'long')
        
        if avg_price == 0:
            return False
        
        # 计算盈亏比例
        if side == 'long':
            pnl_pct = (current_price - avg_price) / avg_price
        else:  # short
            pnl_pct = (avg_price - current_price) / avg_price
        
        # 检查是否触发止损
        if pnl_pct < -self.stop_loss_pct:
            logger.warning(f"Stop loss triggered: pnl={pnl_pct:.2%}, threshold={-self.stop_loss_pct:.2%}")
            return True
        
        return False
    
    def get_risk_metrics(self):
        """
        获取风控指标
        
        Returns:
            dict: 风控指标
        """
        return {
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.max_daily_trades,
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.max_daily_loss,
            'max_leverage': self.max_leverage,
            'max_position_pct': self.max_position_pct,
            'stop_loss_pct': self.stop_loss_pct
        }
