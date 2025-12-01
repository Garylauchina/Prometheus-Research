# Prometheus v3.0 迁移指南

## 📋 概述

本文档帮助您从旧的项目结构迁移到新的v3.0重构版本。

**重构日期**: 2025-12-02  
**影响范围**: 项目结构、导入路径  
**向后兼容**: 部分兼容

---

## 🎯 主要变化

### 1. 目录结构重组

#### 之前 (旧结构)

```
prometheus-v30/
├── agent.py
├── live_agent.py
├── multi_market_agent.py
├── system.py
├── system_multi_market.py
├── strategy.py
├── strategy_v2.py
├── config.py
├── config_multi_market.py
├── test_*.py (散落在根目录)
├── check_*.py (散落在根目录)
├── deploy.sh (散落在根目录)
└── ...
```

#### 现在 (新结构)

```
prometheus-v30/
├── prometheus/              # 🆕 核心包
│   ├── core/               # 核心业务
│   ├── adapters/           # 适配器
│   ├── evolution/          # 进化系统
│   ├── strategies/         # 策略
│   └── monitoring/         # 监控
│
├── configs/                # 🆕 统一配置
│   ├── config.py
│   ├── multi_market_config.py
│   └── pretraining_config.py
│
├── tests/                  # 🆕 统一测试
│   ├── unit/
│   ├── integration/
│   └── performance/
│
├── scripts/                # 🆕 工具脚本
│   ├── deploy.sh
│   ├── monitor.sh
│   └── ...
│
└── examples/               # 示例代码
```

---

## 🔄 导入路径变化

### Agent相关

```python
# ❌ 旧方式
from live_agent import LiveAgent
from agent import Agent
from multi_market_agent import MultiMarketAgent

# ✅ 新方式
from prometheus.core.agent import LiveAgent
# 注：已统一为LiveAgent实现
```

### System相关

```python
# ❌ 旧方式
from live_trading_system import LiveTradingSystem
from system import PrometheusV3
from system_multi_market import PrometheusV3MultiMarket

# ✅ 新方式
from prometheus.core.trading_system import LiveTradingSystem
# 注：已统一为LiveTradingSystem实现
```

### Strategy相关

```python
# ❌ 旧方式
from strategy import Strategy
from strategy_v2 import StrategyV2

# ✅ 新方式
from prometheus.strategies.strategy import Strategy
# 注：已使用v2版本作为标准实现
```

### 配置相关

```python
# ❌ 旧方式
from config import CONFIG
from config_multi_market import CONFIG_MULTI_MARKET

# ✅ 新方式
from configs.config import CONFIG
from configs.multi_market_config import CONFIG_MULTI_MARKET
```

### Evolution系统

```python
# ✅ 保持不变（Evolution系统已经模块化）
from evolution import EnhancedCapitalPool, EnvironmentalPressure
```

### Adapters

```python
# ✅ 保持不变（adapters已经模块化）
from adapters.okx_adapter import OKXTradingAdapter
from adapters.market_data import MarketDataManager
```

---

## 📝 迁移步骤

### 步骤1: 更新依赖

```bash
# 确保使用最新版本
git pull origin main

# 重新安装依赖（如果需要）
pip install -r requirements.txt
```

### 步骤2: 更新导入语句

使用以下脚本批量更新（或手动修改）：

```python
# update_imports.py
import re
from pathlib import Path

IMPORT_MAP = {
    'from live_agent import': 'from prometheus.core.agent import',
    'from agent import': 'from prometheus.core.agent import',
    'from live_trading_system import': 'from prometheus.core.trading_system import',
    'from system import': 'from prometheus.core.trading_system import',
    'from strategy_v2 import': 'from prometheus.strategies.strategy import',
    'from strategy import': 'from prometheus.strategies.strategy import',
    'from config import': 'from configs.config import',
    'from config_multi_market import': 'from configs.multi_market_config import',
}

def update_file(filepath):
    content = filepath.read_text(encoding='utf-8')
    for old, new in IMPORT_MAP.items():
        content = re.sub(old, new, content)
    filepath.write_text(content, encoding='utf-8')

# 使用
for py_file in Path('.').rglob('*.py'):
    if 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
        update_file(py_file)
```

### 步骤3: 验证代码

```bash
# 运行测试
python -m pytest tests/

# 运行示例
python examples/simple_evolution_demo.py

# 运行集成测试
python tests/integration/trading_test_30min.py
```

---

## 🔍 常见问题

### Q1: 旧代码还能运行吗？

**A**: 可以，但建议更新：

- ✅ 旧的导入路径仍然有效（根目录文件保留）
- ⚠️ 但这些是副本，建议迁移到新路径
- ⚠️ 未来版本可能移除根目录副本

### Q2: Evolution系统需要迁移吗？

**A**: 不需要！

```python
# ✅ Evolution系统保持不变
from evolution import EnhancedCapitalPool, EnvironmentalPressure
```

### Q3: 配置文件在哪里？

**A**: 已移动到 `configs/` 目录

```python
# 旧位置: ./config.py
# 新位置: ./configs/config.py

from configs.config import CONFIG
```

### Q4: 测试文件在哪里？

**A**: 已组织到 `tests/` 目录

```
tests/
├── unit/                  # 单元测试
│   ├── test_system.py
│   └── test_gene_diversity.py
├── integration/           # 集成测试
│   ├── trading_test_30min.py
│   ├── check_positions.py
│   └── ...
└── performance/          # 性能测试
    └── test_performance.py
```

### Q5: 如何使用新的模块化架构？

**A**: 更清晰的导入

```python
# 核心功能
from prometheus.core.agent import LiveAgent
from prometheus.core.trading_system import LiveTradingSystem
from prometheus.core.gene import Gene

# 进化系统
from evolution import EnhancedCapitalPool, EnvironmentalPressure

# 策略
from prometheus.strategies.strategy import Strategy

# 配置
from configs.config import CONFIG
```

---

## 📊 文件映射表

### 核心文件

| 旧位置 | 新位置 | 状态 |
|--------|--------|------|
| `live_agent.py` | `prometheus/core/agent.py` | ✅ 已复制 |
| `live_trading_system.py` | `prometheus/core/trading_system.py` | ✅ 已复制 |
| `gene.py` | `prometheus/core/gene.py` | ✅ 已复制 |
| `capital_manager.py` | `prometheus/core/capital_manager.py` | ✅ 已复制 |
| `market_analyzer.py` | `prometheus/core/market_analyzer.py` | ✅ 已复制 |
| `market_regime.py` | `prometheus/core/market_regime.py` | ✅ 已复制 |
| `lifecycle_manager.py` | `prometheus/core/lifecycle_manager.py` | ✅ 已复制 |

### 策略文件

| 旧位置 | 新位置 | 状态 |
|--------|--------|------|
| `strategy_v2.py` | `prometheus/strategies/strategy.py` | ✅ 已复制 |
| `strategy.py` | - | ⚠️ 已废弃（使用v2） |

### 配置文件

| 旧位置 | 新位置 | 状态 |
|--------|--------|------|
| `config.py` | `configs/config.py` | ✅ 已复制 |
| `config_multi_market.py` | `configs/multi_market_config.py` | ✅ 已复制 |
| `pretraining_config.py` | `configs/pretraining_config.py` | ✅ 已复制 |

### 测试文件

| 旧位置 | 新位置 | 状态 |
|--------|--------|------|
| `test_system.py` | `tests/unit/test_system.py` | ✅ 已移动 |
| `test_gene_diversity.py` | `tests/unit/test_gene_diversity.py` | ✅ 已移动 |
| `test_performance.py` | `tests/performance/test_performance.py` | ✅ 已移动 |
| `trading_test_30min.py` | `tests/integration/trading_test_30min.py` | ✅ 已移动 |
| `check_positions.py` | `tests/integration/check_positions.py` | ✅ 已移动 |

### 脚本文件

| 旧位置 | 新位置 | 状态 |
|--------|--------|------|
| `deploy.sh` | `scripts/deploy.sh` | ✅ 已移动 |
| `monitor.sh` | `scripts/monitor.sh` | ✅ 已移动 |
| `healthcheck.sh` | `scripts/healthcheck.sh` | ✅ 已移动 |
| `view_logs.ps1` | `scripts/view_logs.ps1` | ✅ 已移动 |

### 废弃文件

| 文件 | 原因 | 替代方案 |
|------|------|----------|
| `agent.py` | 功能简单 | 使用`prometheus/core/agent.py` |
| `multi_market_agent.py` | 已合并 | 使用`prometheus/core/agent.py` |
| `system.py` | 功能过时 | 使用`prometheus/core/trading_system.py` |
| `system_multi_market.py` | 已合并 | 使用`prometheus/core/trading_system.py` |
| `strategy.py` | v1版本 | 使用`prometheus/strategies/strategy.py` (v2) |
| `capital_pool.py` | 旧版本 | Evolution使用`evolution/capital_pool.py` |
| `simple_capital_manager.py` | 功能冗余 | 使用`prometheus/core/capital_manager.py` |

---

## 🚀 新功能使用

### Evolution系统完整使用

```python
from evolution import EnhancedCapitalPool, EnvironmentalPressure
from prometheus.core.agent import LiveAgent
from prometheus.core.trading_system import LiveTradingSystem

# 初始化Evolution系统
capital_pool = EnhancedCapitalPool(10000)
environmental_pressure = EnvironmentalPressure()

# 创建Agent
for i in range(15):
    if capital_pool.allocate_to_agent(633):
        agent = LiveAgent(f"agent_{i}", 633, config)
        agents.append(agent)

# 进化周期
def evolution_cycle():
    # 更新压力
    pressure = environmental_pressure.update(
        market_features,
        agents,
        capital_pool.get_status()
    )
    
    # 获取调整后配置
    repro_config = environmental_pressure.adjust_reproduction_config(base_config)
    death_config = environmental_pressure.adjust_death_config(base_config)
    
    # 执行进化
    for agent in agents:
        if agent.should_die(death_config, agents):
            recycled = agent.die(capital_pool)
        elif agent.can_reproduce(repro_config):
            child = agent.reproduce(new_id, repro_config, capital_pool)
```

详细文档：[Evolution系统完整指南](EVOLUTION_SYSTEM.md)

---

## ✅ 迁移检查清单

### 基本迁移
- [ ] 更新代码到最新版本
- [ ] 更新所有导入语句
- [ ] 更新配置文件路径
- [ ] 验证测试通过

### Evolution系统（如果使用）
- [ ] 确认Evolution模块导入正常
- [ ] 验证资金池功能
- [ ] 验证环境压力系统
- [ ] 运行Evolution演示

### 生产环境（如果适用）
- [ ] 备份现有配置
- [ ] 备份API密钥
- [ ] 备份历史数据
- [ ] 在测试环境验证
- [ ] 逐步部署到生产

---

## 📞 获取帮助

如果迁移过程中遇到问题：

1. 查看 [故障排查指南](TROUBLESHOOTING.md)
2. 查看 [项目重构文档](PROJECT_REFACTORING.md)
3. 在GitHub提交Issue
4. 在Discord社区提问

---

## 📝 版本对照

| 版本 | 日期 | 主要变化 |
|------|------|----------|
| v3.0 | 2025-12-02 | 完整重构，模块化架构 |
| v3.0-beta | 2025-11-29 | Evolution系统，性能优化 |
| v2.5 | 2025-11-28 | 市场状态检测优化 |
| v1.0 | 2025-11-27 | 基础回测框架 |

---

**迁移建议**: 建议在测试环境充分验证后再迁移生产环境！

**文档版本**: 1.0  
**最后更新**: 2025-12-02

