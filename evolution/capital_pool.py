"""
Evolution Capital Pool - 进化系统资金池

增强的资金池系统，支持：
- 资金分配追踪
- 死亡资金回收
- 繁殖资金资助
- 实时状态监控

Author: Prometheus Evolution Team
Version: 2.0
Date: 2025-12-01
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedCapitalPool:
    """
    增强的资金池系统
    
    核心功能:
    1. 资金分配管理（allocate_to_agent）
    2. 死亡资金回收（recycle_from_death）
    3. 繁殖资金资助（subsidize_reproduction）
    4. 状态实时查询（get_status）
    
    设计理念:
    - 资金守恒：死亡Agent的资金100%回收
    - 循环利用：回收资金用于资助新Agent
    - 透明追踪：所有资金流动可追溯
    """
    
    def __init__(self, initial_capital: float):
        """
        初始化资金池
        
        Args:
            initial_capital: 初始总资金
        """
        self.initial_capital = initial_capital
        self.total_capital = initial_capital
        self.allocated_capital = 0.0      # 已分配给Agent的资金
        self.available_capital = initial_capital  # 可用资金
        self.recycled_capital = 0.0       # 累计回收的资金
        self.subsidized_capital = 0.0     # 累计资助的资金
        
        logger.info(f"资金池初始化完成: 初始资金${initial_capital:,.2f}")
    
    def allocate_to_agent(self, amount: float) -> bool:
        """
        分配资金给Agent
        
        Args:
            amount: 分配金额
            
        Returns:
            bool: 是否分配成功
        """
        if amount <= 0:
            logger.error(f"无效的分配金额: ${amount}")
            return False
            
        if self.available_capital >= amount:
            self.available_capital -= amount
            self.allocated_capital += amount
            logger.debug(f"分配资金: ${amount:,.2f}, 剩余可用: ${self.available_capital:,.2f}")
            return True
        else:
            logger.warning(f"资金不足: 需要${amount:,.2f}, 可用${self.available_capital:,.2f}")
            return False
    
    def recycle_from_death(self, amount: float, recovery_rate: float = 1.0) -> float:
        """
        从死亡Agent回收资金
        
        Args:
            amount: Agent剩余资金
            recovery_rate: 回收率（0.0-1.0，默认100%）
            
        Returns:
            float: 实际回收金额
        """
        if amount <= 0:
            return 0.0
            
        recycled = amount * recovery_rate
        self.available_capital += recycled
        self.allocated_capital -= amount
        self.recycled_capital += recycled
        
        logger.info(f"回收资金: ${recycled:,.2f} (原${amount:,.2f}, 回收率{recovery_rate:.0%})")
        return recycled
    
    def subsidize_reproduction(self, amount: float) -> float:
        """
        资助繁殖（为新Agent提供资金）
        
        Args:
            amount: 请求资助金额
            
        Returns:
            float: 实际资助金额（可能少于请求）
        """
        if amount <= 0:
            return 0.0
            
        actual_subsidy = min(amount, self.available_capital)
        if actual_subsidy > 0:
            self.available_capital -= actual_subsidy
            self.allocated_capital += actual_subsidy
            self.subsidized_capital += actual_subsidy
            logger.info(f"资助繁殖: ${actual_subsidy:,.2f}")
        else:
            logger.warning(f"资金不足，无法资助繁殖（需要${amount:,.2f}）")
            
        return actual_subsidy
    
    def get_status(self) -> Dict[str, float]:
        """
        获取资金池当前状态
        
        Returns:
            dict: 状态信息
                - total: 总资金
                - available: 可用资金
                - allocated: 已分配资金
                - utilization: 资金利用率
                - recycled: 累计回收
                - subsidized: 累计资助
        """
        return {
            'total': self.total_capital,
            'available': self.available_capital,
            'allocated': self.allocated_capital,
            'utilization': self.allocated_capital / self.total_capital if self.total_capital > 0 else 0,
            'recycled': self.recycled_capital,
            'subsidized': self.subsidized_capital
        }
    
    def get_metrics(self) -> Dict[str, float]:
        """
        获取资金池性能指标
        
        Returns:
            dict: 性能指标
        """
        status = self.get_status()
        return {
            'utilization_rate': status['utilization'],
            'recycling_efficiency': self.recycled_capital / self.initial_capital if self.initial_capital > 0 else 0,
            'subsidy_rate': self.subsidized_capital / self.initial_capital if self.initial_capital > 0 else 0,
            'capital_turnover': (self.recycled_capital + self.subsidized_capital) / self.initial_capital if self.initial_capital > 0 else 0
        }
    
    def reset(self, new_capital: Optional[float] = None):
        """
        重置资金池（用于新的测试周期）
        
        Args:
            new_capital: 新的初始资金（None则使用原始值）
        """
        if new_capital is not None:
            self.initial_capital = new_capital
            self.total_capital = new_capital
        else:
            self.total_capital = self.initial_capital
            
        self.allocated_capital = 0.0
        self.available_capital = self.total_capital
        self.recycled_capital = 0.0
        self.subsidized_capital = 0.0
        
        logger.info(f"资金池已重置: ${self.total_capital:,.2f}")
    
    def __repr__(self) -> str:
        status = self.get_status()
        return (f"CapitalPool(total=${status['total']:,.2f}, "
                f"available=${status['available']:,.2f}, "
                f"utilization={status['utilization']:.1%})")


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    pool = EnhancedCapitalPool(10000)
    print("初始状态:", pool)
    
    # 分配资金
    pool.allocate_to_agent(2000)
    pool.allocate_to_agent(3000)
    print("分配后:", pool)
    
    # 回收资金
    pool.recycle_from_death(1500)
    print("回收后:", pool)
    
    # 资助繁殖
    pool.subsidize_reproduction(800)
    print("资助后:", pool)
    
    # 查看指标
    print("性能指标:", pool.get_metrics())

