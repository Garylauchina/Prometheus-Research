"""
Core Module - 核心业务逻辑

包含Agent、System、资金管理、市场分析等核心组件
"""

# v4.0 核心组件（三层架构）
from .mastermind import Mastermind, MarketRegime, GlobalStrategy
from .supervisor import Supervisor, AgentHealthReport
from .agent_v4 import AgentV4, AgentState, DeathReason, AgentPersonality, EmotionalState

# v4.1 进化系统
from .evolvable_gene import EvolvableGene
from .epiphany_system import EpiphanySystem, EpiphanyTrigger
from .evolution_manager import EvolutionManager

# 市场分析（整合到Supervisor）
from .indicator_calculator import IndicatorCalculator, TechnicalIndicators
from .market_state_analyzer import (
    MarketStateAnalyzer,
    MarketState,
    TrendState,
    MomentumState,
    VolatilityState
)

# 公告板v4（简化版）
from .bulletin_board_v4 import (
    BulletinBoardV4,
    Bulletin as BulletinV4,
    BulletinTier,
    BulletinBoardPermissions
)

# 旧版系统（兼容性）
try:
    from .gene_pool import GenePool, GeneRecord
except ImportError:
    pass

try:
    from .bulletin_board import BulletinBoardSystem, Bulletin, BulletinType, Priority
except ImportError:
    BulletinBoardSystem = None
    Bulletin = BulletinV4
    Priority = None

from .elysium import Elysium, Inscription, HallLevel
from .medal_system import MedalSystem, Medal, MedalType
from .nirvana_system import NirvanaSystem, NirvanaEvent, NirvanaReason
from .llm_oracle import LLMOracle, HumanOracle
from .trading_permissions import (
    TradingPermissionSystem, 
    RiskController, 
    PermissionLevel, 
    TradingProduct, 
    PermissionConfig
)

__all__ = [
    # ========== 三层架构 ==========
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
    
    # ========== 进化系统 v4.1 ==========
    'EvolvableGene',
    'EpiphanySystem',
    'EpiphanyTrigger',
    'EvolutionManager',
    
    # ========== 市场分析（整合到Supervisor）==========
    'IndicatorCalculator',
    'TechnicalIndicators',
    'MarketStateAnalyzer',
    'MarketState',
    'TrendState',
    'MomentumState',
    'VolatilityState',
    
    # ========== 公告板v4（三层架构）==========
    'BulletinBoardV4',
    'BulletinV4',
    'BulletinTier',
    'BulletinBoardPermissions',
    
    # ========== 系统 ==========
    # 极乐净土
    'Elysium',
    'Inscription',
    'HallLevel',
    
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
    
    # 交易权限系统
    'TradingPermissionSystem',
    'RiskController',
    'PermissionLevel',
    'TradingProduct',
    'PermissionConfig',
    
    # ========== 兼容性 ==========
    # 旧版公告板
    'BulletinBoardSystem',
    'Bulletin',
    'BulletinType',
    'Priority',
]

