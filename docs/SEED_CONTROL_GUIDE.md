# 🎲 随机种子控制指南

## 概述

从 v6.0 开始，Prometheus-Quant 提供了完整的随机种子控制机制，支持：

1. **创世种子（Genesis Seed）**：控制初始种群的生成
2. **演化种子（Evolution Seed）**：控制进化过程的随机性
3. **主种子（Main Seed）**：同时控制创世和演化

---

## 三种使用模式

### 模式A：固定创世 + 随机演化

**用途**：观察相同初始种群在不同演化路径下的表现差异

```python
from prometheus.facade.v6_facade import run_scenario

facade = run_scenario(
    mode="backtest",
    total_cycles=1000,
    market_feed=your_market_feed,
    agent_count=50,
    genesis_seed=1000,      # ✅ 固定创世
    evolution_seed=None,    # ✅ 随机演化
    # ...
)
```

**实验问题**：
- 相同的初始基因组合，能演化出多少种不同的盈利策略？
- 进化的随机性对最终结果的影响有多大？

---

### 模式B：不同创世 + 固定演化

**用途**：观察不同初始种群在相同演化路径下的最终差异

```python
# 第一次运行
facade1 = run_scenario(
    mode="backtest",
    total_cycles=1000,
    market_feed=your_market_feed,
    agent_count=50,
    genesis_seed=1000,      # ✅ 创世A
    evolution_seed=5000,    # ✅ 固定演化
    # ...
)

# 第二次运行
facade2 = run_scenario(
    mode="backtest",
    total_cycles=1000,
    market_feed=your_market_feed,
    agent_count=50,
    genesis_seed=2000,      # ✅ 创世B（不同）
    evolution_seed=5000,    # ✅ 固定演化（相同）
    # ...
)
```

**实验问题**：
- 创世基因对最终结果的影响有多强？
- "先天"（创世）vs "后天"（演化）谁更重要？

---

### 模式C：完全固定（可重复实验）

**用途**：调试、验证、论文实验

```python
facade = run_scenario(
    mode="backtest",
    total_cycles=1000,
    market_feed=your_market_feed,
    agent_count=50,
    seed=1000,  # ✅ 主种子，同时控制创世和演化
    # ...
)
```

**特点**：
- 每次运行结果完全相同
- 适合调试和验证
- 适合论文和报告

---

## 种子优先级

如果同时指定了多个种子参数，优先级如下：

```
genesis_seed > seed  (创世阶段)
evolution_seed > seed  (演化阶段)
```

**示例**：

```python
run_scenario(
    seed=1000,           # 主种子
    genesis_seed=2000,   # ✅ 创世时使用2000
    evolution_seed=3000  # ✅ 演化时使用3000
)
```

---

## 种子配置的保存

所有种子配置会自动保存到 `results/<mode>/<date>/<run_id>/config.json`：

```json
{
  "mode": "backtest",
  "agent_count": 50,
  "seed_config": {
    "main_seed": 1000,
    "genesis_seed": 1000,
    "evolution_seed": 1000,
    "timestamp": "2025-12-07T12:34:56"
  }
}
```

---

## 创世验证

设置种子后，系统会自动验证创世质量：

```
✅ 创世完成并通过验证：50 agents
   📊 家族分布: 50个活跃家族
   ✅ 账簿挂载: 50/50个Agent
   📈 基因多样性: 95.0% (48/50个独特基因组)
   🧠 本能多样性: 92.0% (46/50个独特本能)
   🎯 创世质量评分: 94.3%
   🌟 创世质量优秀！
```

---

## 实验示例脚本

完整的实验脚本见：`test_seed_experiments.py`

运行方式：

```bash
# 运行所有实验
python test_seed_experiments.py

# 运行单个实验
python test_seed_experiments.py a  # 实验A：固定创世
python test_seed_experiments.py b  # 实验B：不同创世
python test_seed_experiments.py c  # 实验C：完全可重复
```

---

## 注意事项

### ⚠️ 市场数据的影响

即使使用相同的种子，如果市场数据不同，结果也会不同。确保：

```python
# ✅ 正确：使用相同的市场数据
prices = load_prices(limit=1000)
market_feed = make_market_feed(prices)

run_scenario(..., market_feed=market_feed, seed=1000)
run_scenario(..., market_feed=market_feed, seed=1000)  # 结果相同

# ❌ 错误：每次加载新数据
run_scenario(..., market_feed=load_new_data(), seed=1000)
run_scenario(..., market_feed=load_new_data(), seed=1000)  # 结果不同！
```

### ⚠️ 外部随机性

某些外部因素可能影响可重复性：

- 系统时间（如果代码中使用）
- 网络请求（实盘模式）
- 文件I/O顺序

建议在回测模式下进行种子实验。

---

## 技术细节

### 种子设置时机

```python
# build_facade 中的实现
def build_facade(..., genesis_seed=None, evolution_seed=None):
    import random
    import numpy as np
    
    # 1️⃣ 创世前设置创世种子
    if genesis_seed is not None:
        random.seed(genesis_seed)
        np.random.seed(genesis_seed)
    
    # 2️⃣ 创世（受创世种子影响）
    facade.init_population(...)
    
    # 3️⃣ 创世后重置为演化种子
    if evolution_seed is not None:
        random.seed(evolution_seed)
        np.random.seed(evolution_seed)
    
    return facade
```

### 受种子控制的随机过程

**创世阶段**：
- 家族分配（如果随机）
- 基因参数初始化（Beta分布）
- 本能参数初始化（Beta分布）
- Agent ID生成（如果随机）

**演化阶段**：
- 选择操作（适应度排序 + 随机扰动）
- 交叉操作（染色体片段选择）
- 变异操作（变异位点选择）
- 移民注入（新家族生成）

---

## 研究建议

### 论文级实验设计

1. **消融实验**（Ablation Study）
   - 固定所有种子，只改变一个参数
   - 观察该参数对结果的影响

2. **鲁棒性测试**
   - 相同配置，不同种子，运行N次（N≥30）
   - 计算均值、标准差、置信区间

3. **对比实验**
   - A组：策略A + 50个不同种子
   - B组：策略B + 50个不同种子
   - 统计检验（t-test, Mann-Whitney U）

---

## 常见问题

**Q: 为什么需要分开控制创世和演化种子？**

A: 这样可以解耦"先天"（初始基因）和"后天"（进化路径）的影响，进行更精细的实验。

**Q: 如果不设置种子会怎样？**

A: 系统使用Python和NumPy的默认随机数生成器，每次运行结果都不同。

**Q: 种子设置会影响性能吗？**

A: 不会。种子只在初始化时设置一次，不影响运行时性能。

**Q: 可以在运行中途修改种子吗？**

A: 技术上可以，但不推荐，会破坏实验的可重复性。

---

## 版本历史

- **v6.0** (2025-12-07): 首次引入完整的种子控制机制
- 支持创世种子、演化种子、主种子三种模式
- 添加创世质量验证
- 自动保存种子配置

---

## 相关文档

- `docs/V6_FACADE_PLAN.md` - V6架构设计
- `test_seed_experiments.py` - 实验示例脚本
- `templates/STANDARD_TEST_TEMPLATE.py` - 标准测试模板

