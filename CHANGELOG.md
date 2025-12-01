# 更新日志 (Changelog)

所有Prometheus项目的重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [3.1.0] - 2025-12-02

### 🎉 重大更新

这是一个里程碑版本，完成了项目的全面重构和Evolution系统的完整实现。

### ✨ 新增 (Added)

#### Evolution系统（核心创新）
- **资金循环机制**: 100%资金回收利用系统
- **环境压力系统**: 三维度压力计算（市场40% + 种群30% + 资金池30%）
- **多维度死亡机制**: 7层死亡判断（绝对ROI、年龄保护、父代保护、精英特权等）
- **混合资金资助**: 父代转移（20%）+ 资金池资助（30%）
- **压力平滑机制**: 70%旧值 + 30%新值，避免策略突变
- **完整示例程序**: `examples/simple_evolution_demo.py`

#### 项目架构
- **prometheus主包**: 清晰的模块化架构
  - `prometheus/core/`: 核心业务逻辑（8个模块）
  - `prometheus/strategies/`: 交易策略模块
  - `prometheus/utils/`: 工具函数（预留）
- **configs目录**: 统一配置管理（3个配置文件）
- **tests目录**: 完整测试套件
  - `tests/unit/`: 单元测试
  - `tests/integration/`: 集成测试
  - `tests/performance/`: 性能测试
- **scripts目录**: 工具脚本集中管理（5个脚本）
- **results目录**: 结果文件组织
  - `results/visualizations/`: 可视化图表
  - `results/archives/`: 历史数据归档

#### 文档体系
- **README.md**: 全新优化的项目总览（600行）
- **MIGRATION_GUIDE.md**: 详细迁移指南（400行）
- **REFACTORING_COMPLETE.md**: 重构完成报告（500行）
- **REFACTORING_PLAN.md**: 重构计划文档
- **CHANGELOG.md**: 本更新日志
- **evolution/README.md**: Evolution模块文档（300行）
- **docs/EVOLUTION_SYSTEM.md**: Evolution完整文档（800行）
- **QUICKSTART_EVOLUTION.md**: Evolution快速入门（200行）

### 🔄 变更 (Changed)

#### 文件组织
- 统一Agent实现: `live_agent.py` → `prometheus/core/agent.py`
- 统一System实现: `live_trading_system.py` → `prometheus/core/trading_system.py`
- 统一Strategy实现: `strategy_v2.py` → `prometheus/strategies/strategy.py`
- 配置文件迁移: `config*.py` → `configs/`
- 测试文件组织: `test_*.py` → `tests/`
- 脚本文件集中: `*.sh, *.ps1` → `scripts/`

#### 导入路径变化
```python
# 旧方式
from live_agent import LiveAgent
from config import CONFIG

# 新方式
from prometheus.core.agent import LiveAgent
from configs.config import CONFIG
```

### 🗑️ 移除 (Removed)

#### 冗余文件
- 删除重复的Agent实现（`agent.py`, `multi_market_agent.py`）
- 删除旧版本System实现（`system.py`, `system_multi_market.py`）
- 删除旧版本Strategy（`strategy.py`）
- 删除冗余资金管理（`simple_capital_manager.py`, `capital_pool.py`旧版）

#### 临时文件
- 删除 `backup_signal_log.txt`
- 删除 `debug_log.txt`
- 删除 `signal_monitor_log.txt`

#### 文件迁移
- 历史测试结果: `gene_test_results_*` → `results/archives/`
- 可视化图表: `*.png` → `results/visualizations/`

### 🐛 修复 (Fixed)

- 文件组织混乱问题
- 导入路径不清晰问题
- 测试文件分散问题
- 文档不完整问题

### 📚 文档 (Documentation)

- 新增3000+行完整文档体系
- Evolution系统完整设计文档
- 详细的API参考
- 完整的迁移指南
- 故障排查指南

### ✅ 测试 (Tests)

- Evolution模块导入验证 ✅
- 示例程序运行验证 ✅
- 资金池系统功能验证 ✅
- 环境压力系统验证 ✅
- 完整集成演示验证 ✅

---

## [3.0.0] - 2025-11-29

### ✨ 新增

#### 核心功能
- OKX API完整集成
- 实时交易系统
- 多Agent进化机制（基础版）
- 市场状态检测（5种状态）
- 完善的风控系统

#### 技术指标（已实现）✅
- RSI（相对强弱指标）- 完整实现
- MACD（移动平均收敛散度）- 完整实现
- Bollinger Bands（布林带）- 完整实现
- 综合信号系统（多指标加权组合）
- 可配置的指标权重（通过Agent基因）
- 详细文档：[docs/TECHNICAL_INDICATORS.md](docs/TECHNICAL_INDICATORS.md)

#### 性能优化
- API调用节流控制
- 市场数据缓存机制
- 并发代理更新优化
- 批量交易执行

#### 系统增强
- Docker容器化支持
- 跨平台启动脚本
- 性能测试工具
- 完善的部署脚本

### 📚 文档

- 基础README
- 部署文档（DEPLOY.md）
- 设计文档（docs/DESIGN.md）
- 故障排查（docs/TROUBLESHOOTING.md）

---

## [2.5.0] - 2025-11-28

### 🔄 变更

- 优化市场状态检测算法
- 改进动态多空比例计算
- ROI性能从55%提升到456.79%

---

## [1.0.0] - 2025-11-27

### ✨ 新增

- 基础回测框架
- 简单技术指标策略
- 基本Agent系统
- 初始文档

---

## 路线图

### [3.2.0] - 计划中（预计2025年12月）

#### 计划新增
- [ ] 动态止损/止盈策略
- [ ] Web监控面板
- [ ] 技术指标增强
  - ✅ **v3.1已实现**: RSI、MACD、布林带（基础版）
  - [ ] 动态参数调整
  - [ ] 更多指标类型（Stochastic、ATR、CCI、ADX等）
  - [ ] 多时间周期分析
  - [ ] 指标背离检测
- [ ] 智能资金分配算法
- [ ] 市场情绪分析增强

### [3.3.0] - 计划中（预计2026年Q1）

#### 计划新增
- [ ] 机器学习模型辅助策略优化
- [ ] 跨交易所套利功能
- [ ] 移动端App开发
- [ ] 多币种自动对冲策略
- [ ] 高级风险分析仪表盘

---

## 版本命名规则

遵循语义化版本（Semantic Versioning）：

```
主版本号.次版本号.修订号

- 主版本号：重大架构变更或不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的bug修复
```

示例：
- `3.1.0`: v3主版本，第1次功能更新
- `3.1.1`: v3.1的第1次bug修复
- `3.2.0`: v3.1之后的功能更新

---

## 贡献指南

在提交Pull Request时，请：

1. 更新此CHANGELOG.md
2. 遵循[Keep a Changelog](https://keepachangelog.com/)格式
3. 将变更放在[Unreleased]部分
4. 在版本发布时，将[Unreleased]内容移到新版本号下

---

## 链接

- [项目主页](README.md)
- [快速开始](QUICKSTART.md)
- [Evolution系统](QUICKSTART_EVOLUTION.md)
- [完整文档](docs/)
- [迁移指南](docs/MIGRATION_GUIDE.md)

---

**维护者**: Prometheus Team  
**最后更新**: 2025-12-02
