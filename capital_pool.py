"""
CapitalPool - 资金池模块

职责: 管理系统的空闲资金
"""

from typing import Dict


class CapitalPool:
    """空闲资金池 - 系统的资金银行"""
    
    def __init__(self, initial_capital: float = 0):
        """
        Args:
            initial_capital: 初始资金
        """
        self.balance = initial_capital
        
        # 统计
        self.stats = {
            'total_deposits': initial_capital,
            'total_withdrawals': 0.0,
            'death_deposits': 0.0,
            'manager_deposits': 0.0,
            'elimination_deposits': 0.0,
            'reproduction_withdrawals': 0.0,
            'reallocation_withdrawals': 0.0,
            'initialization_withdrawals': 0.0,
        }
    
    def deposit(self, amount: float, source: str = 'other'):
        """
        存入资金
        
        Args:
            amount: 金额
            source: 来源 ('death', 'manager', 'elimination', 'other')
        """
        if amount <= 0:
            return
        
        self.balance += amount
        self.stats['total_deposits'] += amount
        
        if source == 'death':
            self.stats['death_deposits'] += amount
        elif source == 'manager':
            self.stats['manager_deposits'] += amount
        elif source == 'elimination':
            self.stats['elimination_deposits'] += amount
    
    def withdraw(self, amount: float, purpose: str = 'other') -> float:
        """
        取出资金
        
        Args:
            amount: 请求金额
            purpose: 用途 ('reproduction', 'reallocation', 'initialization', 'other')
        
        Returns:
            实际取出金额（可能少于请求金额）
        """
        if amount <= 0:
            return 0.0
        
        # 最多取出当前余额
        actual_amount = min(amount, self.balance)
        
        if actual_amount > 0:
            self.balance -= actual_amount
            self.stats['total_withdrawals'] += actual_amount
            
            if purpose == 'reproduction':
                self.stats['reproduction_withdrawals'] += actual_amount
            elif purpose == 'reallocation':
                self.stats['reallocation_withdrawals'] += actual_amount
            elif purpose == 'initialization':
                self.stats['initialization_withdrawals'] += actual_amount
        
        return actual_amount
    
    def get_available_capital(self) -> float:
        """获取可用资金"""
        return self.balance
    
    def can_withdraw(self, amount: float) -> bool:
        """是否可以取出指定金额"""
        return self.balance >= amount
    
    def get_utilization_rate(self, total_system_capital: float) -> float:
        """
        计算资金池利用率
        
        Args:
            total_system_capital: 系统总资金
        
        Returns:
            利用率 (0-1)，1表示完全利用（资金池为空）
        """
        if total_system_capital <= 0:
            return 0.0
        
        return 1.0 - (self.balance / total_system_capital)
    
    def get_report(self) -> Dict:
        """获取报告"""
        return {
            'balance': self.balance,
            'stats': self.stats.copy()
        }
    
    def __repr__(self) -> str:
        return f"CapitalPool(balance=${self.balance:.2f})"
