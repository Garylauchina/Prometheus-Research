"""
Evolution System - 进化系统核心模块

提供完整的Agent进化机制，包括：
- 增强资金池（资金循环系统）
- 环境压力系统（自适应调整）
- 繁殖机制（基因传递与变异）
- 死亡机制（多维度淘汰）

Author: Prometheus Evolution Team
Version: 2.0
Date: 2025-12-01
"""

from .capital_pool import EnhancedCapitalPool
from .environmental_pressure import EnvironmentalPressure

__version__ = "2.0.0"
__all__ = [
    "EnhancedCapitalPool",
    "EnvironmentalPressure",
]

# 版本信息
VERSION_INFO = {
    'major': 2,
    'minor': 0,
    'patch': 0,
    'release': 'stable'
}

def get_version():
    """返回版本字符串"""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}-{VERSION_INFO['release']}"


# 模块级文档
DOCUMENTATION = """
Evolution System 使用指南
=======================

1. 资金池系统:
```python
from evolution import EnhancedCapitalPool

pool = EnhancedCapitalPool(initial_capital=10000)
pool.allocate_to_agent(2000)  # 分配
pool.recycle_from_death(1500)  # 回收
pool.subsidize_reproduction(800)  # 资助
```

2. 环境压力系统:
```python
from evolution import EnvironmentalPressure

pressure = EnvironmentalPressure()
current_pressure = pressure.update(market_features, agents, pool_status)
phase_code, phase_name = pressure.get_phase()

# 自动调整配置
adjusted_config = pressure.adjust_reproduction_config(base_config)
```

3. 集成使用:
```python
# 在TradingSystem中集成
self.capital_pool = EnhancedCapitalPool(CONFIG['initial_capital'])
self.environmental_pressure = EnvironmentalPressure()

# 每个进化周期
pressure = self.environmental_pressure.update(market, agents, pool.get_status())
reproduction_config = self.environmental_pressure.adjust_reproduction_config(base_config)
death_config = self.environmental_pressure.adjust_death_config(base_config)
```

更多文档请参考: docs/evolution/
"""

def print_docs():
    """打印使用文档"""
    print(DOCUMENTATION)

