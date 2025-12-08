# 📦 Prometheus 归档

本目录包含历史版本的代码和测试，仅供参考。

---

## 🗂️ 目录结构

```
archive/
├── v5/              # v5.0版本归档
│   ├── tests/       # 90+个v5测试文件
│   └── docs/        # v5文档
├── v4/              # v4.0版本归档（预留）
└── experiments/     # 实验性代码归档
```

---

## ⚠️ 重要说明

### 为什么归档？

v6.0代表了Prometheus的**范式转变**：

```
v1.0-5.0的方向（已废弃）：
❌ 试图让Agent"变聪明"
❌ 复杂的心理机制（恐惧、贪婪）
❌ GenomeVector（50参数）
❌ 多层决策系统

v6.0的正确方向：
✅ 在极简环境筛选强基因
✅ 生态驱动（而非市场驱动）
✅ StrategyParams（6参数）
✅ 种群进化 + 中央调度
```

因此，v5.0的大部分代码和测试已经不再适用。

---

## 📋 归档内容

### v5/tests/ (90+个测试文件)

包括但不限于：
- `test_v5*.py` - v5核心测试
- `test_v53*.py` - v5.3测试
- `test_fear*.py` - 恐惧机制测试（已废弃）
- `test_genome*.py` - 旧基因系统测试
- `test_daimon*.py` - 旧决策系统测试
- `test_evolution*.py` - 旧进化系统测试
- `test_extreme*.py` - 压力测试
- 其他实验性测试

**这些测试**：
- ⚠️ 不推荐运行（可能失败）
- ⚠️ 基于已废弃的架构
- ⚠️ 仅供参考历史设计
- ✅ 保留用于学习教训

---

## 🔍 如何查看

### 浏览归档测试

```bash
# 查看所有v5测试
ls archive/v5/tests/

# 查看特定类型
ls archive/v5/tests/test_fear*.py
```

### 对比v5和v6

```bash
# 对比v5和v6的Agent实现
git diff v5.0-before-simplification v6.0-stage1 -- prometheus/core/agent.py

# 对比基因系统
git diff v5.0-before-simplification v6.0-stage1 -- prometheus/core/gene.py
```

---

## 💡 从v5学到的教训

### 误区1：过度复杂的Agent

```python
# v5.0的误区
class Agent:
    def __init__(self):
        self.genome = GenomeVector(50)  # 50个参数！
        self.fear_level = ...
        self.greed_level = ...
        self.fomo = ...
        # 试图模拟人类心理
```

**教训**：复杂不等于智能。进化需要简单的规则。

---

### 误区2：直接在复杂市场训练

```python
# v5.0的误区
# 直接用历史数据训练，噪音 > 信号
market_data = load_historical_data("BTC-2020-2024.csv")
train(market_data)  # 进化随机，无法收敛
```

**教训**：复杂智能只能从简化环境中首先出现。

---

### 误区3：让Agent"理解"市场

```python
# v5.0的误区
class Daimon:
    def make_decision(self, market_data):
        # 复杂的市场分析
        # 试图理解趋势、支撑、阻力...
        # 三重投票系统
```

**教训**：Agent应该执行策略参数，而不是"理解"市场。

---

## ✅ v6.0的正确方向

### 简化Agent

```python
# v6.0的正确方向
class StrategyParams:
    directional_bias: float      # 0-1
    position_size_base: float    # 0-1
    holding_preference: float    # 0-1
    # 只有6个核心参数
```

### 极简环境训练

```python
# v6.0的正确方向
# Stage 1: 极简市场（无噪音）
market = MockTrainingSchool()
# Stage 2: 中等复杂（Regime切换）
# Stage 3: 历史数据
# Stage 4: 实盘
```

### 生态驱动

```python
# v6.0的正确方向
# Agent是牺牲品（策略载体）
# 进化筛选强基因
# Prophet中央调度
```

---

## 📚 参考

- [v6.0架构文档](../docs/v6/V6_ARCHITECTURE.md)
- [Stage 1黄金规则](../docs/v6/STAGE1_GOLDEN_RULES.md)
- [为什么v6.0是正确的](../docs/v6/STAGE1_GOLDEN_RULES.md#为什么这是正确的)

---

## 🚫 不推荐

- ❌ 不要运行归档的测试
- ❌ 不要基于v5代码开发
- ❌ 不要尝试"修复"v5
- ✅ 使用v6.0的新架构

---

## 🎯 总结

```
归档的意义：
✅ 保留历史（学习教训）
✅ 保持git历史完整
✅ 清理主代码库
✅ 避免新用户困惑

v5的价值：
✅ 失败也是经验
✅ 证明了什么不该做
✅ 推动了范式转变
✅ 为v6.0铺平道路
```

---

**记住**：v5.0失败了，但失败是成功之母。v6.0基于v5的教训，走上了正确的道路。

**不要重复v5的错误！** ⚠️

