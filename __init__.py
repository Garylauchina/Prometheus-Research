"""
Prometheus v3.0 - 进化交易系统

特性:
- 模块化架构
- 空闲资金池机制
- 动态资金分配
- 活跃度要求
"""

from .gene import Gene, MARKET_FEATURES
from .strategy import Strategy
from .agent import Agent
from .capital_pool import CapitalPool
from .agent_manager import AgentManager
from .capital_manager import CapitalManager
from .market_analyzer import MarketAnalyzer
from .system import PrometheusV3
from .config import CONFIG_V3, CONFIG_V3_AGGRESSIVE, CONFIG_V3_CONSERVATIVE
from .pretrainer import PreTrainer
from .pretraining_config import PRETRAINING_CONFIG

__version__ = '3.0.0'
__all__ = [
    'Gene',
    'Strategy',
    'Agent',
    'CapitalPool',
    'AgentManager',
    'CapitalManager',
    'MarketAnalyzer',
    'PrometheusV3',
    'CONFIG_V3',
    'CONFIG_V3_AGGRESSIVE',
    'CONFIG_V3_CONSERVATIVE',
    'MARKET_FEATURES',
    'PreTrainer',
    'PRETRAINING_CONFIG',
]
