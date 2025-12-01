# Evolution System - 进化系统核心模块

## 📖 概述

Evolution模块是Prometheus v30交易系统的核心进化引擎，实现了完整的Agent自适应进化机制。

### 核心特性

- ✅ **资金完全循环**: 死亡Agent资金100%回收，用于资助新Agent
- ✅ **环境自适应**: 根据市场、种群和资金状况动态调整策略
- ✅ **多维度淘汰**: 5层死亡判断机制，精准淘汰劣质Agent
- ✅ **混合资助**: 父代转移+资金池资助，降低繁殖负担
- ✅ **平滑过渡**: 压力平滑机制，避免策略突变

---

## 🏗️ 模块结构

```
evolution/
├── __init__.py                  # 模块入口
├── capital_pool.py              # 增强资金池
├── environmental_pressure.py    # 环境压力系统
├── reproduction.py              # 繁殖机制（待实现）
├── death_mechanism.py           # 死亡机制（待实现）
└── README.md                    # 本文档
```

---

## 🚀 快速开始

### 1. 资金池系统

```python
from evolution import EnhancedCapitalPool

# 初始化资金池
pool = EnhancedCapitalPool(initial_capital=10000)

# 分配资金给Agent
success = pool.allocate_to_agent(2000)

# Agent死亡，回收资金
recycled = pool.recycle_from_death(agent_capital, recovery_rate=1.0)

# 资助繁殖
subsidy = pool.subsidize_reproduction(requested_amount)

# 查看状态
status = pool.get_status()
print(f"利用率: {status['utilization']:.1%}")
```

### 2. 环境压力系统

```python
from evolution import EnvironmentalPressure

# 初始化压力系统
pressure = EnvironmentalPressure()

# 更新压力（每个进化周期）
current_pressure = pressure.update(
    market_features=market_data,
    agents=all_agents,
    capital_pool_status=pool.get_status()
)

# 获取当前阶段
phase_code, phase_name = pressure.get_phase()
# 返回: ("prosperity", "🌟 繁荣期") 或 ("crisis", "🔥 危机期")

# 自动调整配置
reproduction_config = pressure.adjust_reproduction_config({
    'min_roi': 0.05,
    'min_trades': 2,
    'pool_subsidy_ratio': 0.30
})

death_config = pressure.adjust_death_config({
    'death_roi_threshold': -0.35,
    'parent_protection_period': 3,
    'elite_roi_threshold': 0.20
})
```

---

## 📊 设计原理

### 资金循环系统

```
┌─────────────────────────────────────┐
│        资金池 (Capital Pool)         │
│                                     │
│  可用: $2000  ┌─────────┐           │
│  已分配: $8000│ 总$10000│           │
└───────┬───────┴─────────┴───────┬───┘
        │ 分配                回收 │
        ↓                         ↑
┌───────────────┐           ┌──────────┐
│   新Agent     │           │死亡Agent  │
│   创建/繁殖   │           │ 资金回收  │
└───────┬───────┘           └────┬─────┘
        │ 成长                   │
        ↓                        │
┌───────────────────────────────────┐
│        Agent生命周期               │
│  出生 → 成长 → 繁殖/死亡           │
└────────────────────────────────────┘
```

### 环境压力计算

```
pressure = 市场因素(40%) + 种群因素(30%) + 资金池因素(30%)

市场因素 = (波动率 × 0.6 + 恐慌指标 × 0.4) × 0.4
种群因素 = ((1-ROI) × 0.6 + (1-存活率) × 0.4) × 0.3
资金池因素 = U型曲线(利用率)

压力阶段:
0.0-0.3: 🌟 繁荣期 → 鼓励繁殖，宽松淘汰
0.3-0.7: ⚖️ 平衡期 → 正常运作
0.7-1.0: 🔥 危机期 → 抑制繁殖，严格淘汰
```

---

## 🎯 核心API

### EnhancedCapitalPool

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `allocate_to_agent(amount)` | 分配资金给Agent | bool |
| `recycle_from_death(amount, rate)` | 回收死亡Agent资金 | float |
| `subsidize_reproduction(amount)` | 资助繁殖 | float |
| `get_status()` | 获取状态 | dict |
| `get_metrics()` | 获取性能指标 | dict |

### EnvironmentalPressure

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `update(market, agents, pool)` | 更新压力值 | float |
| `get_phase()` | 获取当前阶段 | (code, name) |
| `adjust_reproduction_config(config)` | 调整繁殖配置 | dict |
| `adjust_death_config(config)` | 调整死亡配置 | dict |

---

## 📈 使用示例

### 完整集成示例

```python
from evolution import EnhancedCapitalPool, EnvironmentalPressure

class TradingSystem:
    def __init__(self, initial_capital):
        # 初始化进化系统
        self.capital_pool = EnhancedCapitalPool(initial_capital)
        self.environmental_pressure = EnvironmentalPressure()
        self.agents = []
    
    def evolution_cycle(self, market_features):
        """进化周期"""
        # 1. 更新环境压力
        pool_status = self.capital_pool.get_status()
        pressure = self.environmental_pressure.update(
            market_features, 
            self.agents, 
            pool_status
        )
        
        # 2. 获取当前阶段
        phase_code, phase_name = self.environmental_pressure.get_phase()
        print(f"当前压力: {pressure:.2%} - {phase_name}")
        
        # 3. 调整配置
        reproduction_config = self.environmental_pressure.adjust_reproduction_config({
            'min_roi': 0.05,
            'min_trades': 2,
            'pool_subsidy_ratio': 0.30
        })
        
        death_config = self.environmental_pressure.adjust_death_config({
            'death_roi_threshold': -0.35,
            'parent_protection_period': 3
        })
        
        # 4. 执行繁殖
        for agent in self.agents:
            if agent.can_reproduce(reproduction_config):
                child = agent.reproduce(
                    new_id=len(self.agents),
                    config=reproduction_config,
                    capital_pool=self.capital_pool
                )
                self.agents.append(child)
        
        # 5. 执行淘汰
        for agent in self.agents:
            if agent.should_die(death_config, self.agents):
                recycled = agent.die(self.capital_pool)
                print(f"Agent {agent.id} 死亡，回收${recycled:.2f}")
```

---

## 🔬 测试

```python
# 运行资金池测试
python -m evolution.capital_pool

# 运行压力系统测试
python -m evolution.environmental_pressure

# 运行集成测试
python tests/integration/trading_test_30min.py
```

---

## 📚 扩展阅读

- [Evolution System Design](../docs/evolution/DESIGN.md)
- [Capital Pool Architecture](../docs/evolution/CAPITAL_POOL.md)
- [Pressure System Guide](../docs/evolution/PRESSURE_SYSTEM.md)
- [API Reference](../docs/evolution/API_REFERENCE.md)

---

## 🤝 贡献

如需添加新功能或改进现有实现，请遵循以下原则：

1. 保持API稳定性
2. 添加完整的文档字符串
3. 编写单元测试
4. 更新README和API文档

---

## 📝 版本历史

- **v2.0.0** (2025-12-01)
  - ✨ 新增环境压力系统
  - ✨ 新增增强资金池
  - ✨ 完整资金循环机制
  - ✨ 自适应进化策略

- **v1.0.0** (2025-11-xx)
  - 🎉 初始版本
  - 基础Agent进化功能

---

## 📄 许可证

Copyright © 2025 Prometheus Evolution Team

