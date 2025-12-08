"""
系统资金配置模块
================

提供系统级资金配置的数据类和工具函数，用于统一管理：
- 系统注资总额
- 创世配资比例
- Agent初始资金
- 资金储备策略
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class SystemCapitalConfig:
    """
    系统资金配置
    
    用于统一管理系统级资金参数，支持：
    1. 创世初始化（genesis）
    2. 中途追加投资（expansion）
    3. 紧急救援（rescue）
    4. Mock模拟场景
    
    示例：
        # 创世配置（20%配资，80%储备）
        config = SystemCapitalConfig(
            agent_count=50,
            capital_per_agent=10000,
            genesis_allocation_ratio=0.2
        )
        
        # Mock模拟配置（小额快速测试）
        config = SystemCapitalConfig(
            agent_count=20,
            capital_per_agent=5000,
            genesis_allocation_ratio=0.5
        )
    """
    
    # 基础参数
    agent_count: int = 50
    capital_per_agent: float = 10000.0
    
    # 配资策略
    genesis_allocation_ratio: float = 0.2  # 创世配资比例（默认20%）
    
    # 可选参数
    purpose: str = "genesis"  # 注资目的: genesis/expansion/rescue/mock
    reason: str = ""          # 详细原因
    timestamp: Optional[str] = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def total_system_capital(self) -> float:
        """系统注资总额"""
        return self.agent_count * self.capital_per_agent
    
    @property
    def genesis_allocation(self) -> float:
        """创世时实际分配金额"""
        return self.total_system_capital * self.genesis_allocation_ratio
    
    @property
    def reserve_amount(self) -> float:
        """储备金额（进入资金池）"""
        return self.total_system_capital - self.genesis_allocation
    
    @property
    def actual_capital_per_agent(self) -> float:
        """每个Agent实际获得的初始资金"""
        if self.agent_count == 0:
            return 0.0
        return self.genesis_allocation / self.agent_count
    
    @property
    def reserve_ratio(self) -> float:
        """储备比例"""
        return 1.0 - self.genesis_allocation_ratio
    
    def to_dict(self) -> Dict:
        """转换为字典（用于日志和序列化）"""
        return {
            "agent_count": self.agent_count,
            "capital_per_agent": self.capital_per_agent,
            "genesis_allocation_ratio": self.genesis_allocation_ratio,
            "total_system_capital": self.total_system_capital,
            "genesis_allocation": self.genesis_allocation,
            "reserve_amount": self.reserve_amount,
            "actual_capital_per_agent": self.actual_capital_per_agent,
            "reserve_ratio": self.reserve_ratio,
            "purpose": self.purpose,
            "reason": self.reason,
            "timestamp": self.timestamp
        }
    
    def validate(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            bool: True if valid, raises ValueError otherwise
        """
        if self.agent_count <= 0:
            raise ValueError(f"agent_count必须 > 0，当前: {self.agent_count}")
        
        if self.capital_per_agent <= 0:
            raise ValueError(f"capital_per_agent必须 > 0，当前: {self.capital_per_agent}")
        
        if not (0 < self.genesis_allocation_ratio <= 1.0):
            raise ValueError(f"genesis_allocation_ratio必须在(0, 1]之间，当前: {self.genesis_allocation_ratio}")
        
        return True
    
    def summary(self) -> str:
        """
        生成配置摘要（用于日志输出）
        
        Returns:
            str: 格式化的配置摘要
        """
        return f"""
系统资金配置摘要
{'='*60}
目的: {self.purpose} {f'({self.reason})' if self.reason else ''}
Agent数: {self.agent_count}
目标规模: ${self.capital_per_agent:,.2f}/Agent
系统注资: ${self.total_system_capital:,.2f}
{'='*60}
创世分配: ${self.genesis_allocation:,.2f} ({self.genesis_allocation_ratio:.0%})
资金储备: ${self.reserve_amount:,.2f} ({self.reserve_ratio:.0%})
实际资金: ${self.actual_capital_per_agent:,.2f}/Agent
{'='*60}
时间戳: {self.timestamp}
"""


# 预设配置模板
class CapitalConfigPresets:
    """常用配置预设"""
    
    @staticmethod
    def conservative_genesis() -> SystemCapitalConfig:
        """保守创世配置（20%配资，80%储备）"""
        return SystemCapitalConfig(
            agent_count=50,
            capital_per_agent=10000,
            genesis_allocation_ratio=0.2,
            purpose="genesis",
            reason="conservative_exploration"
        )
    
    @staticmethod
    def aggressive_genesis() -> SystemCapitalConfig:
        """激进创世配置（50%配资，50%储备）"""
        return SystemCapitalConfig(
            agent_count=50,
            capital_per_agent=10000,
            genesis_allocation_ratio=0.5,
            purpose="genesis",
            reason="aggressive_exploration"
        )
    
    @staticmethod
    def mock_test() -> SystemCapitalConfig:
        """Mock测试配置（小规模快速测试）"""
        return SystemCapitalConfig(
            agent_count=20,
            capital_per_agent=5000,
            genesis_allocation_ratio=0.3,
            purpose="mock",
            reason="quick_simulation"
        )
    
    @staticmethod
    def expansion(additional_amount: float) -> SystemCapitalConfig:
        """追加投资配置（100%立即可用）"""
        return SystemCapitalConfig(
            agent_count=1,  # 占位，实际不创建新Agent
            capital_per_agent=additional_amount,
            genesis_allocation_ratio=1.0,  # 100%立即可用
            purpose="expansion",
            reason="additional_investment"
        )
    
    @staticmethod
    def rescue(rescue_amount: float) -> SystemCapitalConfig:
        """紧急救援配置（100%立即可用）"""
        return SystemCapitalConfig(
            agent_count=1,  # 占位
            capital_per_agent=rescue_amount,
            genesis_allocation_ratio=1.0,
            purpose="rescue",
            reason="capital_pool_depletion"
        )

