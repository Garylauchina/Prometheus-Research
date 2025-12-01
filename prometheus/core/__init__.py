"""
Core Module - 核心业务逻辑

包含Agent、System、资金管理、市场分析等核心组件
"""

# v4.0 核心组件
from .mastermind import Mastermind, MarketRegime, GlobalStrategy
from .supervisor import Supervisor, AgentHealthReport
from .agent_v4 import AgentV4, AgentState, DeathReason, AgentPersonality, EmotionalState

__all__ = [
    # 主脑
    'Mastermind',
    'MarketRegime',
    'GlobalStrategy',
    
    # 监督者
    'Supervisor',
    'AgentHealthReport',
    
    # Agent v4.0
    'AgentV4',
    'AgentState',
    'DeathReason',
    'AgentPersonality',
    'EmotionalState',
]

