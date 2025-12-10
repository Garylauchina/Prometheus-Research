"""
Prometheus v8.0 Interfaces⭐⭐⭐

标准化接口层，用于v7.0核心系统与外部世界的交互

三大接口：
  1. MarketDataInterface - 市场数据获取
  2. ExecutionInterface - 交易执行
  3. TrainingInterface - 对抗训练

设计理念：
  • v7.0只依赖接口，不依赖具体实现
  • v8.0可以轻松切换实现（实盘/回测/模拟）
  • 不侵入v7.0核心代码

Created: 2025-12-11
Author: Prometheus Team
"""

from prometheus.interfaces.market_data_interface import (
    MarketDataInterface,
    MarketSnapshot,
    LiveMarketData,
    BacktestMarketData,
    SimulatedMarketData,
    create_market_data
)

from prometheus.interfaces.execution_interface import (
    ExecutionInterface,
    Order,
    Position,
    OrderSide,
    OrderType,
    OrderStatus,
    LiveExecution,
    SimulatedExecution,
    create_execution
)

from prometheus.interfaces.training_interface import (
    TrainingInterface,
    TrainingScenario,
    TrainingResult,
    ScenarioType,
    AdversarialTraining,
    get_standard_test_suite,
    get_extreme_test_suite
)

__all__ = [
    # Market Data
    'MarketDataInterface',
    'MarketSnapshot',
    'LiveMarketData',
    'BacktestMarketData',
    'SimulatedMarketData',
    'create_market_data',
    
    # Execution
    'ExecutionInterface',
    'Order',
    'Position',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'LiveExecution',
    'SimulatedExecution',
    'create_execution',
    
    # Training
    'TrainingInterface',
    'TrainingScenario',
    'TrainingResult',
    'ScenarioType',
    'AdversarialTraining',
    'get_standard_test_suite',
    'get_extreme_test_suite',
]

