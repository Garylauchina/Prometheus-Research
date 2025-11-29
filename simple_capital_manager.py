"""
SimpleCapitalManager - 简化的资金管理器
"""

class SimpleCapitalManager:
    """简化的资金管理器"""
    
    def __init__(self, total_capital: float, pool_ratio: float = 0.3):
        """
        初始化资金管理器
        
        Args:
            total_capital: 总资金
            pool_ratio: 资金池比例
        """
        self.total_capital = total_capital
        self.pool_ratio = pool_ratio
        self.pool_balance = total_capital * pool_ratio
        self.allocated = 0.0
    
    def allocate_capital(self, amount: float) -> float:
        """
        从资金池分配资金
        
        Args:
            amount: 请求分配的金额
        
        Returns:
            分配的资金数额
        """
        if self.pool_balance <= 0:
            return 0.0
        
        # 分配请求的金额，但不超过资金池余额
        allocation = min(amount, self.pool_balance)
        
        self.pool_balance -= allocation
        self.allocated += allocation
        
        return allocation
    
    def return_capital(self, amount: float):
        """
        归还资金到资金池
        
        Args:
            amount: 归还金额
        """
        self.pool_balance += amount
        self.allocated -= amount
    
    def get_utilization(self) -> float:
        """
        获取资金池利用率
        
        Returns:
            利用率 (0.0-1.0)
        """
        total = self.pool_balance + self.allocated
        if total == 0:
            return 0.0
        return self.allocated / total
