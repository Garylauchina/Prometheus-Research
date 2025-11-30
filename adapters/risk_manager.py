"""
Risk Manager for trading
"""

import logging
import time
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
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
                - take_profit_pct: 止盈比例
                - drawdown_limit: 最大回撤限制
                - cooldown_period: 触发风控后的冷却期（秒）
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
        self.take_profit_pct = self.risk_config.get('take_profit_pct', 0.10)  # 10%
        self.drawdown_limit = self.risk_config.get('drawdown_limit', 0.20)  # 20%
        self.cooldown_period = self.risk_config.get('cooldown_period', 300)  # 5分钟
        
        # 基础参数（用于动态调整）
        self.base_max_daily_trades = self.max_daily_trades
        self.base_max_daily_loss = self.max_daily_loss
        self.base_max_leverage = self.max_leverage
        self.base_max_position_pct = self.max_position_pct
        self.base_stop_loss_pct = self.stop_loss_pct
        
        # 波动率相关
        self.price_history: List[float] = []
        self.volatility_history: List[float] = []
        self.max_price_history = 100  # 最多保存100个价格点
        self.current_volatility = 0.0
        self.normal_volatility = self.risk_config.get('normal_volatility', 0.02)  # 默认2%
        
        # 连续亏损计数器
        self.consecutive_losses = 0
        self.max_consecutive_losses = self.risk_config.get('max_consecutive_losses', 5)
        
        # 风控冷却期
        self.last_risk_violation = 0
        self.risk_cooldown_active = False
        
        # 最高权益记录（用于计算回撤）
        self.highest_equity = 0.0
        
        logger.info(f"风险管理器初始化完成: max_daily_trades={self.max_daily_trades}, "
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
        
        # 检查风控冷却期
        if not self._check_cooldown_period():
            time_since = int(time.time() - self.last_risk_violation)
            time_left = max(0, self.cooldown_period - time_since)
            raise RiskControlError(f"风控冷却期内: 还有{time_left}秒")
        
        # 检查连续亏损
        if not self._check_consecutive_losses():
            raise RiskControlError(f"连续亏损次数过多: 当前{self.consecutive_losses}/{self.max_consecutive_losses}")
        
        # 检查日内交易次数
        if not self._check_daily_trades():
            raise RiskControlError(f"达到每日最大交易次数限制: 当前{self.daily_trades}/{self.max_daily_trades}")
        
        # 检查日内亏损
        if not self._check_daily_loss():
            raise RiskControlError(f"达到每日最大亏损限制: 当前{self.daily_loss:.2%}/{self.max_daily_loss:.2%}")
        
        # 检查杠杆
        if not self._check_leverage(order_request):
            leverage = order_request.get('leverage', 1)
            raise RiskControlError(f"超过最大杠杆限制: 请求{leverage}x，限制{self.max_leverage}x")
        
        # 检查仓位（如果提供了账户余额）
        if account_balance:
            # 更新最高权益记录
            total_equity = account_balance.get('total_equity', 0)
            if total_equity > self.highest_equity:
                self.highest_equity = total_equity
                
            # 检查最大回撤
            if not self._check_drawdown(total_equity):
                current_drawdown = (self.highest_equity - total_equity) / self.highest_equity if self.highest_equity > 0 else 0
                raise RiskControlError(f"达到最大回撤限制: 当前{current_drawdown:.2%}/{self.drawdown_limit:.2%}")
            
            # 检查仓位大小
            if not self._check_position_size(order_request, account_balance):
                # 计算详细信息
                size = order_request.get('size', 0)
                price = order_request.get('price', 0)
                leverage = order_request.get('leverage', 1)
                order_value = size * price / leverage if price > 0 else 0
                total_equity = account_balance.get('total_equity', 0)
                position_pct = order_value / total_equity if total_equity > 0 else 0
                raise RiskControlError(
                    f"超过最大仓位限制: 当前{position_pct:.2%}/{self.max_position_pct:.2%}, "
                    f"订单价值={order_value}, 账户权益={total_equity}"
                )
        
        # 检查市场条件
        if not self._check_market_conditions():
            raise RiskControlError("当前市场条件不适合交易")
            
        # 获取市场条件警报（非关键级别）
        market_condition_alert = self.get_market_condition_alert()
        if market_condition_alert and market_condition_alert.get('severity') != 'critical':
            logger.warning(market_condition_alert['message'])
        
        # 检查波动率警报
        volatility_alert = self.get_volatility_alert()
        if volatility_alert:
            logger.warning(volatility_alert['message'])
            
        logger.debug(f"订单通过风控检查: {order_request}")
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
        检查仓位大小和风险控制
        
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
        order_type = order_request.get('type', 'limit')
        
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
        
        # 检查是否超过最大仓位比例
        if position_pct > self.max_position_pct:
            return False
        
        # 对于市价单和止损单，需要更严格的仓位控制
        if order_type in ['market', 'stop', 'stop_limit']:
            # 市价单和止损单的最大订单价值是限价单的70%
            if position_pct > self.max_position_pct * 0.7:
                return False
        
        return True
    
    def record_trade(self, order, result):
        """
        记录交易
        
        Args:
            order: 订单对象
            result: 交易结果
                - pnl: 盈亏
                - fee: 手续费
                - price: 成交价格（用于波动率计算）
        """
        self.daily_trades += 1
        
        # 记录亏损
        pnl = result.get('pnl', 0)
        if pnl < 0:
            self.daily_loss += abs(pnl)
        
        # 如果有成交价格，更新波动率计算
        price = result.get('price')
        if price:
            self.update_volatility(price)
        
        logger.info(f"记录交易: 交易次数={self.daily_trades}, 日亏损={self.daily_loss:.2%}, "
                   f"当前波动率={getattr(self, 'current_volatility', 0):.2%}")
    
    def position_check(self, position, current_price):
        """
        检查仓位是否需要止损或止盈
        
        Args:
            position: 持仓信息
                - avg_price: 平均价格
                - side: 持仓方向
            current_price: 当前价格
        
        Returns:
            dict: 包含是否需要操作的信息
                - action: 操作类型 ('stop_loss', 'take_profit', 'trailing_stop', None)
                - reason: 操作原因
                - pnl_pct: 盈亏百分比
        """
        avg_price = position.get('avg_price', 0)
        side = position.get('side', 'long')
        max_pnl_pct = position.get('max_pnl_pct', 0)
        
        if avg_price == 0:
            return {
                'action': None,
                'reason': '无效的平均价格',
                'pnl_pct': 0
            }
        
        # 计算盈亏比例
        if side == 'long':
            pnl_pct = (current_price - avg_price) / avg_price
        else:  # short
            pnl_pct = (avg_price - current_price) / avg_price
        
        # 检查是否需要止盈
        if pnl_pct > self.take_profit_pct:
            logger.warning(f"Take profit triggered: pnl={pnl_pct:.2%}, threshold={self.take_profit_pct:.2%}")
            return {
                'action': 'take_profit',
                'reason': f"盈利达到止盈目标 {self.take_profit_pct:.2%}",
                'pnl_pct': pnl_pct
            }
        
        # 检查是否需要止损
        if pnl_pct < -self.stop_loss_pct:
            logger.warning(f"Stop loss triggered: pnl={pnl_pct:.2%}, threshold={-self.stop_loss_pct:.2%}")
            return {
                'action': 'stop_loss',
                'reason': f"亏损超过止损限制 {self.stop_loss_pct:.2%}",
                'pnl_pct': pnl_pct
            }
        
        # 检查是否达到移动止损条件（如果已经有一定盈利）
        if pnl_pct > 0.02:  # 至少2%的盈利才开始移动止损
            trailing_stop_threshold = max_pnl_pct - self.stop_loss_pct * 0.5
            if max_pnl_pct > 0 and pnl_pct < trailing_stop_threshold:
                logger.warning(f"Trailing stop triggered: pnl fell from {max_pnl_pct:.2%} to {pnl_pct:.2%}")
                return {
                    'action': 'trailing_stop',
                    'reason': "盈利回落后触发移动止损",
                    'pnl_pct': pnl_pct
                }
        
        return {
            'action': None,
            'reason': '继续持有',
            'pnl_pct': pnl_pct
        }
    
    def check_stop_loss(self, position, current_price):
        """
        检查止损（向后兼容方法）
        
        Args:
            position: 持仓信息
            current_price: 当前价格
        
        Returns:
            bool: 是否需要止损
        """
        result = self.position_check(position, current_price)
        return result['action'] in ['stop_loss', 'trailing_stop']
    
    def update_volatility(self, current_price):
        """
        更新市场波动率并动态调整风控参数
        
        Args:
            current_price: 当前价格
        """
        # 更新价格历史
        self.price_history.append(current_price)
        if len(self.price_history) > self.max_price_history:
            self.price_history.pop(0)
        
        # 计算波动率（使用过去30个价格点的对数收益率标准差）
        if len(self.price_history) >= 30:
            # 计算对数收益率
            prices = np.array(self.price_history)
            log_returns = np.diff(np.log(prices))
            self.current_volatility = np.std(log_returns[-29:]) * np.sqrt(24 * 60)  # 年化波动率
            
            # 存储波动率历史
            self.volatility_history.append(self.current_volatility)
            if len(self.volatility_history) > 100:
                self.volatility_history.pop(0)
            
            # 更新正常波动率（使用历史平均）
            if len(self.volatility_history) > 10:
                self.normal_volatility = np.mean(self.volatility_history)
            
            # 动态调整风控参数
            self._adjust_risk_parameters_based_on_volatility()
            
            logger.info(f"更新波动率: {self.current_volatility:.2%}, 波动率比率: {self.current_volatility/self.normal_volatility:.1f}x" if self.normal_volatility > 0 else f"更新波动率: {self.current_volatility:.2%}")
        
    def _adjust_risk_parameters_based_on_volatility(self):
        """
        根据波动率动态调整风控参数
        
        波动率高时降低风险敞口，波动率低时可以适度提高风险敞口
        """
        # 计算波动率比率
        if self.normal_volatility == 0:
            return
            
        volatility_ratio = self.current_volatility / self.normal_volatility
        
        # 基于波动率比率的调整系数
        if volatility_ratio > 3.0:  # 极端高波动
            # 大幅降低风险敞口
            self.max_position_pct = self.base_max_position_pct * 0.3
            self.max_leverage = min(1, self.base_max_leverage * 0.3)
            self.stop_loss_pct = self.base_stop_loss_pct * 1.5
            self.take_profit_pct = self.base_take_profit_pct * 2.0
            self.max_daily_trades = int(self.base_max_daily_trades * 0.5)
            self.max_daily_loss = self.base_max_daily_loss * 0.5
        elif volatility_ratio > 2.0:  # 高波动
            # 显著降低风险敞口
            self.max_position_pct = self.base_max_position_pct * 0.5
            self.max_leverage = min(2, self.base_max_leverage * 0.5)
            self.stop_loss_pct = self.base_stop_loss_pct * 1.3
            self.take_profit_pct = self.base_take_profit_pct * 1.5
            self.max_daily_trades = int(self.base_max_daily_trades * 0.7)
            self.max_daily_loss = self.base_max_daily_loss * 0.7
        elif volatility_ratio > 1.5:  # 中高波动
            # 适度降低风险敞口
            self.max_position_pct = self.base_max_position_pct * 0.8
            self.max_leverage = self.base_max_leverage * 0.8
            self.stop_loss_pct = self.base_stop_loss_pct * 1.1
            self.take_profit_pct = self.base_take_profit_pct * 1.2
            self.max_daily_trades = int(self.base_max_daily_trades * 0.9)
            self.max_daily_loss = self.base_max_daily_loss * 0.9
        elif volatility_ratio < 0.5:  # 超低波动
            # 适度提高风险敞口
            self.max_position_pct = min(self.base_max_position_pct * 1.2, 1.0)
            self.max_leverage = min(self.base_max_leverage * 1.2, 10.0)
            self.stop_loss_pct = self.base_stop_loss_pct * 0.9
            self.take_profit_pct = self.base_take_profit_pct * 0.8
            self.max_daily_trades = min(int(self.base_max_daily_trades * 1.1), 100)
            self.max_daily_loss = min(self.base_max_daily_loss * 1.1, 0.5)
        else:  # 正常波动
            # 恢复基准参数
            self.max_position_pct = self.base_max_position_pct
            self.max_leverage = self.base_max_leverage
            self.stop_loss_pct = self.base_stop_loss_pct
            self.take_profit_pct = self.base_take_profit_pct
            self.max_daily_trades = self.base_max_daily_trades
            self.max_daily_loss = self.base_max_daily_loss
            
        # 确保参数在合理范围内
        self._validate_risk_parameters()
        
        logger.info(f"动态调整风控参数: 波动率={self.current_volatility:.2%}, "
                   f"波动率比率={volatility_ratio:.1f}x, 仓位限制={self.max_position_pct:.2%}, "
                   f"杠杆限制={self.max_leverage}, 止损比例={self.stop_loss_pct:.2%}")
    
    def _validate_risk_parameters(self):
        """
        验证风控参数在合理范围内
        """
        # 确保最大仓位比例在0-1之间
        self.max_position_pct = max(0, min(1.0, self.max_position_pct))
        
        # 确保最大杠杆在1-10之间
        self.max_leverage = max(1, min(10.0, self.max_leverage))
        
        # 确保止损比例在0-1之间
        self.stop_loss_pct = max(0, min(1.0, self.stop_loss_pct))
        
        # 确保止盈比例在0-1之间
        self.take_profit_pct = max(0, min(1.0, self.take_profit_pct))
        
        # 确保最大日内交易次数为正整数
        self.max_daily_trades = max(1, int(self.max_daily_trades))
        
        # 确保最大日内亏损比例在0-0.5之间
        self.max_daily_loss = max(0, min(0.5, self.max_daily_loss))
        
        # 确保回撤限制在0-0.5之间
        self.drawdown_limit = max(0, min(0.5, self.drawdown_limit))
    
    def get_volatility_alert(self):
        """
        获取波动率警报
        
        Returns:
            dict: 警报信息，如果没有警报则返回None
        """
        if self.current_volatility > self.normal_volatility * 2:
            return {
                'type': 'high_volatility',
                'volatility': self.current_volatility,
                'message': f"高波动率警告: 当前波动率 {self.current_volatility:.2%}，超过正常水平2倍"
            }
        return None
    
    def _check_cooldown_period(self):
        """
        检查是否在风控冷却期内
        
        Returns:
            bool: 是否可以交易
        """
        if not self.risk_cooldown_active:
            return True
        
        time_since = time.time() - self.last_risk_violation
        if time_since >= self.cooldown_period:
            self.risk_cooldown_active = False
            logger.info("风控冷却期结束")
            return True
        
        return False
    
    def _check_consecutive_losses(self):
        """
        检查连续亏损次数
        
        Returns:
            bool: 是否允许继续交易
        """
        return self.consecutive_losses < self.max_consecutive_losses
    
    def _check_drawdown(self, current_equity):
        """
        检查最大回撤
        
        Args:
            current_equity: 当前权益
        
        Returns:
            bool: 是否在允许范围内
        """
        if self.highest_equity == 0:
            return True
        
        drawdown = (self.highest_equity - current_equity) / self.highest_equity
        return drawdown <= self.drawdown_limit
        
    def _check_market_conditions(self):
        """
        检查市场条件是否适合交易
        
        Returns:
            bool: 是否适合交易
        """
        # 检查风控冷却期
        if not self._check_cooldown_period():
            time_remaining = int(self.cooldown_period - (time.time() - self.last_risk_violation))
            logger.warning(f"风控冷却期内，{time_remaining}秒后可恢复交易")
            return False
        
        # 检查连续亏损
        if not self._check_consecutive_losses():
            logger.warning(f"连续亏损次数超出限制: {self.consecutive_losses}/{self.max_consecutive_losses}")
            # 触发风控冷却期
            self.trigger_risk_cooldown(f"连续亏损{self.consecutive_losses}次")
            return False
        
        # 如果波动率过高，暂停交易
        if self.normal_volatility > 0:
            if self.current_volatility > self.normal_volatility * 4:
                logger.warning(f"极端市场波动: 当前波动率 {self.current_volatility:.2%}, 正常波动率 {self.normal_volatility:.2%}")
                # 触发风控冷却期
                self.trigger_risk_cooldown("极端市场波动率")
                return False
            elif self.current_volatility > self.normal_volatility * 3:
                logger.warning(f"高市场波动: 当前波动率 {self.current_volatility:.2%}, 正常波动率 {self.normal_volatility:.2%}")
                # 提高警报级别但不触发冷却期，让系统减少交易频率
                return False
        
        # 获取市场条件警报
        alert = self.get_market_condition_alert()
        if alert and alert['severity'] == 'critical':
            logger.warning(f"关键市场警报: {alert['message']}")
            # 触发风控冷却期
            self.trigger_risk_cooldown(alert['message'])
            return False
        
        return True
    
    def get_market_condition_alert(self):
        """
        获取市场条件警报
        
        Returns:
            dict: 警报信息，如果没有警报则返回None
        """
        # 基于波动率判断市场条件
        if self.current_volatility > self.normal_volatility * 3:
            return {
                'type': 'extreme_volatility',
                'severity': 'critical',
                'message': f"极端波动率警告: 当前波动率 {self.current_volatility:.2%}，超过正常水平3倍"
            }
        elif self.current_volatility > self.normal_volatility * 2:
            return {
                'type': 'high_volatility',
                'severity': 'warning',
                'message': f"高波动率警告: 当前波动率 {self.current_volatility:.2%}，超过正常水平2倍"
            }
        
        # 基于连续亏损判断
        if self.consecutive_losses > self.max_consecutive_losses * 0.8:
            return {
                'type': 'consecutive_losses',
                'severity': 'warning',
                'message': f"连续亏损警告: 已连续亏损{self.consecutive_losses}次"
            }
        
        return None
    
    def trigger_risk_cooldown(self, reason):
        """
        触发风控冷却期
        
        Args:
            reason: 触发原因
        """
        self.risk_cooldown_active = True
        self.last_risk_violation = time.time()
        logger.warning(f"触发风控冷却期 ({self.cooldown_period}秒): {reason}")
    
    def update_trade_result(self, trade_result):
        """
        更新交易结果，用于风控统计
        
        Args:
            trade_result: 交易结果
                - success: 是否成功
                - pnl: 盈亏
                - fee: 手续费
        """
        if not trade_result.get('success'):
            return
        
        pnl = trade_result.get('pnl', 0)
        
        # 更新连续亏损计数器
        if pnl < 0:
            self.consecutive_losses += 1
            logger.warning(f"连续亏损次数: {self.consecutive_losses}")
            
            # 如果连续亏损过多，触发风控冷却期
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.trigger_risk_cooldown(f"连续亏损{self.consecutive_losses}次")
        else:
            # 盈利则重置连续亏损计数器
            self.consecutive_losses = 0
    
    def get_risk_metrics(self):
        """
        获取风控指标
        
        Returns:
            dict: 风控指标
        """
        # 计算当前回撤（如果有最高权益记录）
        current_drawdown = 0.0
        if self.highest_equity > 0:
            # 需要当前权益才能准确计算，这里用估计值
            current_drawdown = 0.0
        
        return {
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.max_daily_trades,
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.max_daily_loss,
            'max_leverage': self.max_leverage,
            'max_position_pct': self.max_position_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'current_volatility': self.current_volatility,
            'volatility_ratio': self.current_volatility / self.normal_volatility if self.current_volatility > 0 else 0,
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_losses': self.max_consecutive_losses,
            'risk_cooldown_active': self.risk_cooldown_active,
            'drawdown_limit': self.drawdown_limit,
            'current_drawdown': current_drawdown
        }
    
    def get_risk_summary(self):
        """
        获取风险控制摘要
        
        Returns:
            str: 风险控制摘要文本
        """
        summary = []
        summary.append("=== 风险控制摘要 ===")
        summary.append(f"日内交易: {self.daily_trades}/{self.max_daily_trades}")
        summary.append(f"日内亏损: {self.daily_loss:.2%}/{self.max_daily_loss:.2%}")
        summary.append(f"连续亏损: {self.consecutive_losses}/{self.max_consecutive_losses}")
        summary.append(f"最大杠杆: {self.max_leverage}x")
        summary.append(f"最大仓位: {self.max_position_pct:.2%}")
        summary.append(f"止损比例: {self.stop_loss_pct:.2%}")
        summary.append(f"止盈比例: {self.take_profit_pct:.2%}")
        summary.append(f"波动率: {self.current_volatility:.2%} ({self.current_volatility/self.normal_volatility:.1f}x)")
        summary.append(f"风控冷却: {'活跃' if self.risk_cooldown_active else '关闭'}")
        return '\n'.join(summary)
