# Prometheus v6.0 迁移指南

**From**: v5.x  
**To**: v6.0  
**Date**: 2025-12-08  
**Breaking**: 不向后兼容（Breaking Changes）

---

## 📋 目录

1. [为什么不向后兼容](#为什么不向后兼容)
2. [核心差异总结](#核心差异总结)
3. [迁移步骤](#迁移步骤)
4. [代码对比](#代码对比)
5. [常见问题](#常见问题)

---

## ❌ 为什么不向后兼容

### 设计理念的根本转变

```
v5.x: 迭代累积，功能堆叠 → 架构臃肿，难以维护
v6.0: AlphaZero哲学，简化+智能 → 干净重生，可持续发展
```

### 无法兼容的原因

1. **三大铁律强制执行**
   - v6.0将三大铁律内置到架构中
   - 底层模块标记为私有（文件名前缀`_`）
   - 如果兼容v5.x的直接调用方式，铁律形同虚设

2. **核心组件重新设计**
   - Agent特征：Instinct/Emotion → StrategyParams
   - 繁殖机制：交叉+变异 → 病毒式复制
   - WorldSignature：V2（当下）→ V3（过去+当下+未来）
   - 数据结构完全不兼容

3. **新增MemoryLayer**
   - ExperienceDB（经验数据库）
   - IntelligentGenesis（智能创世）
   - v5.x没有对应组件，无法平滑迁移

4. **强制Facade入口**
   - v5.x允许直接调用底层模块
   - v6.0强制通过Facade
   - 如果兼容，铁律1无法执行

### 决策：彻底重生

```
与其在v5.x基础上打补丁（妥协、复杂、难以维护）
不如推倒重来（干净、简洁、可持续发展）

v6.0不是v5.x的延续，而是一次重生
```

---

## 🔀 核心差异总结

### 架构层面

| 维度 | v5.x | v6.0 |
|------|------|------|
| **目录** | `prometheus/` 扁平结构 | `prometheus/v6/` 独立目录 |
| **入口** | `v6_facade.py` | `v6/__init__.py` + `facade.py` |
| **核心模块** | 公开（可直接导入） | 私有（`_core/`，不可直接导入） |
| **测试** | 自由发挥 | 强制模板 |

### 代码层面

| 功能 | v5.x | v6.0 |
|------|------|------|
| **创建系统** | `from prometheus.facade.v6_facade import build_facade` | `from prometheus.v6 import build_facade` |
| **运行系统** | `facade.run_scenario(...)` | `run_scenario(facade, ...)` |
| **Agent特征** | `Instinct` + `Emotion` | `StrategyParams` |
| **繁殖** | `crossover()` + `mutate()` | `viral_replicate()` |
| **WorldSignature** | `WorldSignature_V2` | `WorldSignature_V3` |
| **创世** | 随机 | 智能（基于历史经验） |

### 概念层面

| 概念 | v5.x | v6.0 |
|------|------|------|
| **设计哲学** | 功能堆叠 | AlphaZero简化 |
| **三大铁律** | 建议 | 强制执行 |
| **向后兼容** | 尽量兼容 | 不兼容（重生） |
| **Immigration** | 有 | 无（已移除） |
| **Tier解锁** | 有 | 无（全开放） |
| **记忆层** | 无 | 有（MemoryLayer） |

---

## 🔧 迁移步骤

### Step 1: 备份v5.x代码

```bash
# 创建v5.x备份
cd /Users/liugang/Cursor_Store/Prometheus-Quant
git checkout -b v5_backup
git add .
git commit -m "Backup v5.x before migrating to v6.0"

# 切换回主分支
git checkout main
```

### Step 2: 安装v6.0依赖

```bash
# v6.0可能有新的依赖
pip install -r requirements_v6.txt
```

### Step 3: 更新导入语句

**v5.x:**
```python
from prometheus.facade.v6_facade import build_facade, run_scenario
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.genome import GenomeVector
```

**v6.0:**
```python
# 只从v6导入
from prometheus.v6 import build_facade, run_scenario
from prometheus.v6.config import SystemCapitalConfig

# ❌ 不能直接导入底层模块
# from prometheus.v6._core._agent import AgentV5  # 错误
```

### Step 4: 更新build_facade调用

**v5.x:**
```python
facade = build_facade(
    market_data=btc_data,
    total_capital=1000000,
    agent_count=50,
    scenario='backtest',
    seed=7001
)
```

**v6.0:**
```python
from prometheus.v6.config import SystemCapitalConfig

config = SystemCapitalConfig(
    total_capital=1000000,
    agent_count=50,
    capital_per_agent=2000,
    genesis_allocation_ratio=0.20
)

facade = build_facade(
    market_data=btc_data,
    config=config,
    scenario='backtest',
    seed=7001,
    use_intelligent_genesis=True,  # 新增
    experience_db_path="data/experience_db.json"  # 新增
)
```

### Step 5: 更新run_scenario调用

**v5.x:**
```python
results = facade.run_scenario(
    max_cycles=500,
    evolution_interval=50
)
```

**v6.0:**
```python
results = run_scenario(
    facade=facade,
    max_cycles=500,
    breeding_tax_rate=None,  # 新增（动态税率）
    evolution_interval=50
)
```

### Step 6: 更新测试文件

**v5.x:**
```python
# 自己写的测试
import pytest
from prometheus.core.agent_v5 import AgentV5

def test_something():
    agents = [AgentV5() for _ in range(50)]
    # ... 自己写的逻辑
```

**v6.0:**
```python
# 基于标准模板
# 1. 复制templates/STANDARD_TEST_TEMPLATE_V6.py
# 2. 重命名为test_something.py
# 3. 填写参数
# 4. 运行

from prometheus.v6 import build_facade, run_scenario

# 必须使用Facade入口（铁律1）
facade = build_facade(...)
results = run_scenario(facade, ...)

# 必须包含对账验证（铁律3）
assert results['reconciliation_pass_rate'] == 1.0
```

### Step 7: 删除旧代码

```bash
# v6.0不再需要的文件
rm -rf prometheus/facade/v6_facade.py  # 已迁移到v6/facade.py
rm -rf test_ultimate_1000x_COMPLETE.py  # 违反三大铁律的测试

# 保留v5.x代码（但不再维护）
# 如果需要参考，可以从v5_backup分支查看
```

---

## 📝 代码对比

### 1. 系统初始化

#### v5.x
```python
from prometheus.facade.v6_facade import build_facade

facade = build_facade(
    market_data=btc_data,
    total_capital=1000000,
    agent_count=50,
    scenario='backtest',
    seed=7001
)

# 运行
results = facade.run_scenario(max_cycles=500)
```

#### v6.0
```python
from prometheus.v6 import build_facade, run_scenario
from prometheus.v6.config import SystemCapitalConfig

# 配置
config = SystemCapitalConfig(
    total_capital=1000000,
    agent_count=50,
    capital_per_agent=2000,
    genesis_allocation_ratio=0.20
)

# 构建
facade = build_facade(
    market_data=btc_data,
    config=config,
    scenario='backtest',
    seed=7001,
    use_intelligent_genesis=True,
    experience_db_path="data/experience_db.json"
)

# 运行
results = run_scenario(
    facade=facade,
    max_cycles=500,
    breeding_tax_rate=None,
    evolution_interval=50
)
```

### 2. Agent创建

#### v5.x
```python
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.genome import GenomeVector
from prometheus.core.instinct import Instinct

# 手动创建Agent
genome = GenomeVector.create_random()
instinct = Instinct.create_random()
agent = AgentV5(genome=genome, instinct=instinct)
```

#### v6.0
```python
# ❌ 不能直接创建Agent（违反铁律1）
# Agent创建由Facade内部完成

# ✅ 通过Facade创建
facade = build_facade(
    ...,
    use_intelligent_genesis=True  # 使用智能创世
)

# Facade内部会：
# 1. 如果ExperienceDB不为空 → 智能创世（基于历史最优）
# 2. 如果ExperienceDB为空 → 随机创世
```

### 3. 交易执行

#### v5.x
```python
from prometheus.core.moirai import Moirai

# 可以直接创建Moirai
moirai = Moirai(...)

# 可以自己写循环
for cycle in range(500):
    for agent in moirai.agents:
        decision = agent.decide(...)
        moirai.execute_trade(agent, decision.action, ...)
```

#### v6.0
```python
# ❌ 不能直接创建Moirai（违反铁律1）
# from prometheus.v6._core._moirai import Moirai  # 错误，无法导入

# ✅ 通过Facade运行
results = run_scenario(facade, max_cycles=500)

# Facade内部自动处理：
# - 交易执行
# - 账簿记录
# - 自动对账
# - 进化
```

### 4. 测试编写

#### v5.x
```python
# 自由发挥
def test_agent():
    agent = AgentV5()
    assert agent is not None
```

#### v6.0
```python
# 必须基于标准模板
# 1. 复制templates/STANDARD_TEST_TEMPLATE_V6.py
# 2. 填写参数

from prometheus.v6 import build_facade, run_scenario

def main():
    facade = build_facade(...)
    results = run_scenario(facade, ...)
    
    # 必须包含对账验证（铁律3）
    assert results['reconciliation_pass_rate'] == 1.0
```

---

## ❓ 常见问题

### Q1: 为什么不能直接导入底层模块？

**A:** 这是三大铁律的核心要求。

```
v5.x的最大问题：架构混乱，到处都是旁路
→ 测试自己写循环，绕过核心机制
→ 导致账簿不一致，数据不可信

v6.0的解决方案：强制Facade唯一入口
→ 底层模块标记为私有（文件名前缀_）
→ __init__.py不导出底层类
→ 违反 → 代码无法导入
```

### Q2: 我的v5.x测试怎么办？

**A:** 需要重写，基于标准模板。

```
v5.x测试可能违反三大铁律：
  - 自己写循环（铁律1）
  - 自创简化版（铁律2）
  - 省略对账验证（铁律3）

v6.0要求：
  - 复制templates/STANDARD_TEST_TEMPLATE_V6.py
  - 填写参数
  - 运行
  - 验证对账通过率=100%
```

### Q3: v5.x的Immigration机制哪去了？

**A:** v6.0移除了Immigration，理由如下：

```
1. Immigration是手动干预，违反"自然演化"原则
2. 增加复杂度但效果不明显
3. AlphaZero不需要Immigration也能进化

v6.0的替代方案：
  - 智能创世（30%随机Agent作为探索）
  - 基因突变率（保证多样性）
  - MemoryLayer（记录多样性策略）
```

### Q4: 我需要修改Agent的特征怎么办？

**A:** v6.0不再有Instinct/Emotion，改用StrategyParams。

```
v5.x:
  Instinct（本能）: 探索欲望、死亡恐惧、顿悟等
  Emotion（情绪）: 贪婪、恐惧等
  → 过度设计，拟人化

v6.0:
  StrategyParams（策略参数）: 客观、可量化
  → 例如：max_position_pct, leverage, stop_loss等
  → AlphaZero式简化

不需要手动修改Agent特征：
  - 由Genome控制（50参数）
  - 通过进化自动优化
```

### Q5: 如何验证我的代码符合三大铁律？

**A:** 使用检查清单。

```
写代码时：
□ 是否使用build_facade()初始化？
□ 是否使用run_scenario()运行？
□ 是否有自己写的循环调用底层模块？
□ 是否有直接导入_core模块？

写测试时：
□ 是否基于STANDARD_TEST_TEMPLATE_V6.py？
□ 是否包含对账验证（assert reconciliation_pass_rate == 1.0）？

运行测试时：
□ 对账通过率是否100%？
```

### Q6: 我可以同时运行v5.x和v6.0吗？

**A:** 不建议，但理论上可以。

```
v5.x: prometheus/facade/v6_facade.py
v6.0: prometheus/v6/

理论上两者独立，可以共存
但强烈建议：
  1. 完全迁移到v6.0
  2. v5.x代码备份到git分支
  3. v5.x不再维护
```

### Q7: v6.0的性能如何？

**A:** 预期与v5.x相当或更好。

```
v6.0简化了很多机制：
  - 移除Immigration（减少计算）
  - 移除Instinct/Emotion（减少复杂度）
  - 适应度函数简化（只计算绝对利润）

但增加了：
  - MemoryLayer（经验查询）
  - WorldSignature V3（领先指标计算）

总体预期：性能相当或稍好
```

### Q8: 如果我发现v6.0的bug怎么办？

**A:** 立即报告，不要妥协。

```
v6.0的哲学：
  - 宁可不运行，不能带病运行
  - 对账失败 → 立即异常终止
  - 不允许"测试通过但数据错误"

报告bug：
  1. GitHub Issue
  2. 附上完整日志
  3. 附上数据文件
  4. 附上测试代码
```

---

## 📌 迁移总结

### 核心要点

```
1. v6.0不向后兼容（彻底重生）
2. 必须使用Facade统一入口
3. 必须基于标准测试模板
4. 必须验证对账通过率=100%
5. 不能直接导入底层模块
```

### 迁移工作量

```
小型项目（< 10个测试文件）: 1-2天
中型项目（10-50个测试文件）: 3-5天
大型项目（> 50个测试文件）: 1-2周

主要工作：
  - 更新导入语句（10%）
  - 重写测试文件（70%）
  - 验证对账（20%）
```

### 迁移收益

```
短期：
  - 架构清晰，易于维护
  - 三大铁律强制执行，防止架构混乱
  - 自动对账，账簿一致性有保障

长期：
  - MemoryLayer积累经验，持续学习
  - 智能创世，更快收敛到最优解
  - 可持续发展，不会像v5.x那样臃肿
```

### 最后建议

```
✅ 立即开始迁移（越早越好）
✅ 不要试图兼容v5.x（妥协会导致更多问题）
✅ 严格遵守三大铁律（不得贪污）
✅ 使用标准测试模板（不要自创）
✅ 验证对账通过率=100%（金融系统生命线）
```

---

**不忘初心，方得始终。**  
**在黑暗中寻找亮光，在混沌中寻找规则，在死亡中寻找生命。** 💡📐💀🌱

