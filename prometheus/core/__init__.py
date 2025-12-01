"""
Core Module - 核心业务逻辑

包含Agent、System、资金管理、市场分析等核心组件
"""

# v4.0 核心组件
from .mastermind import Mastermind, MarketRegime, GlobalStrategy
from .supervisor import Supervisor, AgentHealthReport
from .agent_v4 import AgentV4, AgentState, DeathReason, AgentPersonality, EmotionalState
from .gene_pool import GenePool, GeneRecord
from .medal_system import MedalSystem, Medal, MedalType
from .nirvana_system import NirvanaSystem, NirvanaEvent, NirvanaReason
from .llm_oracle import LLMOracle, HumanOracle
from .bulletin_board import BulletinBoardSystem, Bulletin, BulletinType, Priority

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
    
    # 基因库
    'GenePool',
    'GeneRecord',
    
    # 奖章系统
    'MedalSystem',
    'Medal',
    'MedalType',
    
    # 涅槃系统
    'NirvanaSystem',
    'NirvanaEvent',
    'NirvanaReason',
    
    # 决策系统
    'LLMOracle',
    'HumanOracle',
    
    # 公告板系统
    'BulletinBoardSystem',
    'Bulletin',
    'BulletinType',
    'Priority',
]

