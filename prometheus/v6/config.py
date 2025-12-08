"""
Prometheus v6.0 配置模块

Version: 6.0.0
Date: 2025-12-08
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class SystemCapitalConfig:
    """
    系统资金配置
    
    v6.0新增配置类，统一管理系统资金分配
    """
    
    # ===== 基础配置 =====
    total_capital: float = 1000000.0        # 系统总资金
    agent_count: int = 50                   # Agent数量
    capital_per_agent: float = 2000.0       # 每个Agent初始资金
    
    # ===== 创世配置 =====
    genesis_allocation_ratio: float = 0.20  # 创世配资比例（20%）
    
    # ===== 税收配置 =====
    enable_dynamic_tax: bool = True         # 启用动态税率
    target_capital_utilization: float = 0.80  # 目标资金利用率（80%）
    
    # ===== 元数据 =====
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证配置"""
        assert self.total_capital > 0, "总资金必须大于0"
        assert self.agent_count > 0, "Agent数量必须大于0"
        assert self.capital_per_agent > 0, "Agent初始资金必须大于0"
        assert 0 < self.genesis_allocation_ratio <= 1.0, "创世配资比例必须在(0,1]"
        assert 0 < self.target_capital_utilization <= 1.0, "目标资金利用率必须在(0,1]"
    
    def get_genesis_allocation(self) -> float:
        """计算创世配资金额"""
        return self.total_capital * self.genesis_allocation_ratio
    
    def get_reserved_capital(self) -> float:
        """计算预留资金"""
        return self.total_capital * (1 - self.genesis_allocation_ratio)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'total_capital': self.total_capital,
            'agent_count': self.agent_count,
            'capital_per_agent': self.capital_per_agent,
            'genesis_allocation_ratio': self.genesis_allocation_ratio,
            'enable_dynamic_tax': self.enable_dynamic_tax,
            'target_capital_utilization': self.target_capital_utilization,
            'metadata': self.metadata
        }

