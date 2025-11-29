"""
Account类 - 管理单个市场的交易账户
"""

class Account:
    """交易账户类"""
    
    def __init__(self, market, initial_capital: float):
        """
        初始化账户
        
        Args:
            market: Market对象
            initial_capital: 初始资金
        """
        self.market = market
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0.0  # 当前仓位 (-1.0 to 1.0)
        self.entry_price = 0.0  # 入场价格
        self.trades = 0
        self.total_fees = 0.0
        self.unrealized_pnl = 0.0
        
    def get_roi(self) -> float:
        """计算ROI"""
        if self.initial_capital == 0:
            return 0.0
        return (self.capital - self.initial_capital) / self.initial_capital
    
    def get_total_value(self, current_price: float) -> float:
        """
        计算账户总价值（资金 + 未实现盈亏）
        
        Args:
            current_price: 当前价格
            
        Returns:
            总价值
        """
        if self.position == 0:
            return self.capital
        
        # 计算未实现盈亏
        price_change = current_price - self.entry_price
        unrealized_pnl = self.position * price_change * self.initial_capital * self.market.leverage
        
        return self.capital + unrealized_pnl
    
    def trade(self, current_price: float, target_position: float) -> float:
        """
        执行交易
        
        Args:
            current_price: 当前价格
            target_position: 目标仓位 (-1.0 to 1.0)
            
        Returns:
            本次交易的盈亏
        """
        # 限制仓位范围
        target_position = max(self.market.min_position, 
                            min(self.market.max_position, target_position))
        
        # 计算仓位变化
        position_change = abs(target_position - self.position)
        
        # 仓位变化太小，不交易
        if position_change < 0.01:
            return 0.0
        
        pnl = 0.0
        
        # 如果有旧仓位，先平仓
        if self.position != 0:
            # 计算平仓盈亏
            price_change = current_price - self.entry_price
            pnl = self.position * price_change * self.initial_capital * self.market.leverage
            self.capital += pnl
        
        # 计算交易价值（用于计算手续费）
        trade_value = position_change * self.capital
        
        # 计算并扣除手续费
        fee = trade_value * self.market.fee_rate
        self.capital -= fee
        self.total_fees += fee
        
        # 更新仓位和入场价格
        self.position = target_position
        if self.position != 0:
            self.entry_price = current_price
        
        self.trades += 1
        
        return pnl
    
    def force_close(self, current_price: float) -> float:
        """
        强制平仓（用于爆仓保护）
        
        Args:
            current_price: 当前价格
            
        Returns:
            平仓盈亏
        """
        if self.position == 0:
            return 0.0
        
        # 平仓
        pnl = self.trade(current_price, 0.0)
        
        return pnl
    
    def check_liquidation(self, current_price: float, threshold: float = -0.90) -> bool:
        """
        检查是否需要爆仓
        
        Args:
            current_price: 当前价格
            threshold: 爆仓阈值 (e.g., -0.90 for 90% loss)
            
        Returns:
            是否需要爆仓
        """
        if self.position == 0:
            return False
        
        total_value = self.get_total_value(current_price)
        loss_ratio = (total_value - self.initial_capital) / self.initial_capital
        
        return loss_ratio <= threshold
    
    def __repr__(self):
        return (f"Account(market={self.market.name}, capital=${self.capital:.2f}, "
                f"position={self.position:.2f}, ROI={self.get_roi():.2%})")
