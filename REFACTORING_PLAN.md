# Prometheus v3.0 完整重构计划

## 📋 项目现状分析

### 当前问题

```
❌ 文件组织混乱
   - 多版本文件共存（system.py, system_multi_market.py, system_multi_market_simple.py）
   - 测试文件散落在根目录
   - 临时文件未清理

❌ 功能冗余
   - 3个资金管理模块（capital_manager, simple_capital_manager, capital_pool）
   - 2个策略版本（strategy, strategy_v2）
   - 多个Agent实现（agent, live_agent, multi_market_agent）

❌ 文档分散
   - README不完整
   - 缺少Evolution系统说明
   - 配置文档不统一

❌ 测试混乱
   - 测试文件未组织
   - 临时测试脚本未清理
   - 检查脚本（check_*）未归类
```

---

## 🎯 重构目标

### 1. 清晰的模块结构

```
prometheus/
├── core/                    # 核心业务逻辑
├── adapters/               # 交易所适配器
├── evolution/              # 进化系统
├── strategies/             # 交易策略
├── monitoring/             # 监控系统
├── tests/                  # 统一测试目录
├── scripts/                # 工具脚本
├── configs/                # 配置文件
└── docs/                   # 文档
```

### 2. 消除冗余

- 合并多版本文件，保留最优实现
- 统一接口设计
- 清理临时文件

### 3. 完善文档

- 更新主README
- 添加Evolution系统说明
- 统一配置文档

---

## 📊 文件分类

### 核心模块（保留）

```
✅ 保留并优化
├── agent.py → core/agent.py
├── gene.py → core/gene.py
├── market_analyzer.py → core/market_analyzer.py
├── market_regime.py → core/market_regime.py
├── market.py → core/market.py
├── live_trading_system.py → core/trading_system.py
└── lifecycle_manager.py → core/lifecycle_manager.py
```

### 策略模块（合并）

```
🔄 合并
├── strategy.py (旧版) ───┐
└── strategy_v2.py (新版) ┴→ strategies/strategy.py
```

### 资金管理（合并）

```
🔄 合并
├── capital_manager.py ──┐
├── simple_capital_manager.py ──┼→ core/capital_manager.py
└── capital_pool.py (旧版) ──┘
   (注：evolution/capital_pool.py保留，用于进化系统)
```

### Agent实现（合并）

```
🔄 合并
├── agent.py (基础) ──┐
├── live_agent.py (实盘) ──┼→ core/agent.py (统一实现)
└── multi_market_agent.py ──┘
```

### 系统实现（合并）

```
🔄 合并
├── system.py ──┐
├── system_multi_market.py ──┼→ core/system.py (统一实现)
└── system_multi_market_simple.py ──┘
```

### 配置文件（整理）

```
🔄 移动到configs/
├── config.py → configs/config.py
├── config_multi_market.py → configs/multi_market_config.py
└── pretraining_config.py → configs/pretraining_config.py
```

### 测试文件（整理）

```
🔄 移动到tests/
├── test_*.py → tests/unit/
├── check_*.py → tests/integration/
├── detailed_*_test.py → tests/integration/
└── trading_test_30min.py → tests/integration/ (已完成)
```

### 脚本文件（整理）

```
🔄 移动到scripts/
├── deploy.sh
├── monitor.sh
├── healthcheck.sh
├── view_logs.ps1
└── install-pyenv-win.ps1
```

### 临时文件（删除）

```
❌ 删除
├── backup_signal_log.txt
├── debug_log.txt
├── signal_monitor_log.txt
├── gene_test_results_20251201_140733/ (移到results/archives/)
└── results/*.png (移到results/visualizations/)
```

---

## 🚀 重构步骤

### Phase 1: 创建新结构 ✅

1. 创建核心目录结构
2. 创建配置目录
3. 创建脚本目录
4. 整理测试目录

### Phase 2: 合并核心模块

1. 合并Agent实现
2. 合并System实现
3. 合并Strategy版本
4. 合并资金管理模块

### Phase 3: 文件迁移

1. 移动配置文件
2. 移动测试文件
3. 移动脚本文件
4. 清理临时文件

### Phase 4: 文档更新

1. 更新主README
2. 添加Evolution文档链接
3. 更新项目结构说明
4. 创建Migration Guide

### Phase 5: 测试验证

1. 运行单元测试
2. 运行集成测试
3. 验证导入路径
4. 验证功能完整性

---

## 📁 最终目录结构

```
prometheus-v30/
│
├── prometheus/                 # 主包目录
│   ├── __init__.py
│   │
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── agent.py           # 统一Agent实现
│   │   ├── gene.py            # 基因系统
│   │   ├── system.py          # 统一交易系统
│   │   ├── capital_manager.py # 资金管理
│   │   ├── market_analyzer.py # 市场分析
│   │   ├── market_regime.py   # 市场状态
│   │   ├── lifecycle_manager.py
│   │   └── backtest.py
│   │
│   ├── adapters/              # 交易所适配器
│   │   ├── __init__.py
│   │   ├── okx_adapter.py
│   │   ├── market_data.py
│   │   ├── order_manager.py
│   │   ├── account_sync.py
│   │   ├── risk_manager.py
│   │   └── errors.py
│   │
│   ├── evolution/             # 进化系统
│   │   ├── __init__.py
│   │   ├── capital_pool.py
│   │   ├── environmental_pressure.py
│   │   ├── reproduction.py    # TODO
│   │   ├── death_mechanism.py # TODO
│   │   └── README.md
│   │
│   ├── strategies/            # 交易策略
│   │   ├── __init__.py
│   │   ├── strategy.py        # 统一策略实现
│   │   └── indicators.py      # 技术指标
│   │
│   ├── monitoring/            # 监控系统
│   │   ├── __init__.py
│   │   ├── alert_system.py
│   │   ├── system_monitor.py
│   │   └── trade_reporter.py
│   │
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── configs/                   # 配置文件
│   ├── __init__.py
│   ├── config.py             # 主配置
│   ├── multi_market_config.py
│   └── pretraining_config.py
│
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── unit/                 # 单元测试
│   │   ├── test_agent.py
│   │   ├── test_gene.py
│   │   ├── test_strategy.py
│   │   └── test_capital_pool.py
│   ├── integration/          # 集成测试
│   │   ├── test_system.py
│   │   ├── test_trading.py
│   │   ├── check_positions.py
│   │   └── trading_test_30min.py
│   └── performance/          # 性能测试
│       └── test_performance.py
│
├── scripts/                   # 工具脚本
│   ├── deploy.sh
│   ├── monitor.sh
│   ├── healthcheck.sh
│   ├── view_logs.ps1
│   └── install-pyenv-win.ps1
│
├── examples/                  # 示例代码
│   ├── simple_evolution_demo.py
│   ├── simple_trading_demo.py
│   └── README.md
│
├── docs/                      # 文档
│   ├── README.md
│   ├── DESIGN.md
│   ├── EVOLUTION_SYSTEM.md
│   ├── PARAMETERS.md
│   ├── TROUBLESHOOTING.md
│   ├── API_REFERENCE.md
│   ├── MIGRATION_GUIDE.md    # 迁移指南
│   └── PROJECT_REFACTORING.md
│
├── results/                   # 结果输出
│   ├── visualizations/       # 可视化图表
│   ├── reports/              # 报告
│   └── archives/             # 历史数据
│
├── logs/                      # 日志（.gitignore）
├── trading_logs/             # 交易日志（.gitignore）
│
├── run.py                    # 主程序入口
├── README.md                 # 主README
├── QUICKSTART.md
├── QUICKSTART_EVOLUTION.md
├── requirements.txt
├── setup.py                  # 安装脚本
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── LICENSE
```

---

## ✅ 重构检查清单

### 结构优化
- [ ] 创建prometheus主包
- [ ] 创建core子模块
- [ ] 创建configs目录
- [ ] 创建scripts目录
- [ ] 整理tests目录

### 文件合并
- [ ] 合并Agent实现
- [ ] 合并System实现
- [ ] 合并Strategy版本
- [ ] 合并资金管理

### 文件迁移
- [ ] 移动配置文件
- [ ] 移动测试文件
- [ ] 移动脚本文件
- [ ] 整理结果文件

### 文件清理
- [ ] 删除临时文件
- [ ] 删除备份文件
- [ ] 删除调试日志
- [ ] 清理重复结果

### 文档更新
- [ ] 更新主README
- [ ] 创建迁移指南
- [ ] 更新导入示例
- [ ] 更新项目结构说明

### 测试验证
- [ ] 更新导入路径
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 验证Evolution模块

---

## 🔄 迁移影响

### 导入路径变化

```python
# 旧的导入方式
from agent import Agent
from strategy import Strategy
from capital_manager import CapitalManager

# 新的导入方式
from prometheus.core.agent import Agent
from prometheus.strategies.strategy import Strategy
from prometheus.core.capital_manager import CapitalManager
```

### 配置文件变化

```python
# 旧的导入方式
from config import CONFIG

# 新的导入方式
from configs.config import CONFIG
```

### Evolution模块

```python
# 保持不变（已经模块化）
from evolution import EnhancedCapitalPool, EnvironmentalPressure
```

---

## 📝 注意事项

1. **保持向后兼容性**
   - 在根目录保留兼容性导入文件
   - 添加弃用警告

2. **渐进式迁移**
   - 先复制后删除
   - 逐步测试验证

3. **保留重要文件**
   - .env配置
   - API密钥
   - 历史数据

4. **备份策略**
   - 重构前完整备份
   - Git提交记录清晰
   - 标记重构版本

---

## 预计收益

```
✅ 代码组织清晰度    ⭐⭐⭐⭐⭐
✅ 可维护性提升      ⭐⭐⭐⭐⭐
✅ 新人友好度        ⭐⭐⭐⭐⭐
✅ 测试覆盖率        ⭐⭐⭐⭐
✅ 文档完整性        ⭐⭐⭐⭐⭐
```

---

**开始重构日期**: 2025-12-02
**预计完成**: Phase 1-3
**下一步**: 等待确认后开始执行

