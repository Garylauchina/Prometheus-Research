# Prometheus v6.0 三大铁律详解

**Version**: 6.0.0  
**Date**: 2025-12-08  
**Status**: 强制执行（Mandatory）  
**Origin**: 2025-12-07确立，源于账簿问题深刻教训

---

## 📋 目录

1. [三大铁律的诞生背景](#三大铁律的诞生背景)
2. [铁律1: 统一封装，统一调用，严禁旁路](#铁律1-统一封装统一调用严禁旁路)
3. [铁律2: 严格执行测试规范](#铁律2-严格执行测试规范)
4. [铁律3: 不可为测试通过而简化底层机制](#铁律3-不可为测试通过而简化底层机制)
5. [三大铁律的强制执行机制](#三大铁律的强制执行机制)
6. [违反铁律的后果](#违反铁律的后果)
7. [检查清单](#检查清单)

---

## 💀 三大铁律的诞生背景

### 2025-12-07 下午：账簿危机

**问题：**
```
测试文件：test_ultimate_1000x_COMPLETE.py
现象：
  - 测试"通过"
  - 但产生数千条空记录
  - 账簿不一致："私有无多头但公共计算有"
  - 数据完全不可信
  - 浪费大量调试时间（1小时+）
```

**根本原因分析：**
```
1. 旁路问题（违反铁律1）
   - 测试文件自己写循环直接调用底层模块
   - 只开仓不平仓
   - 绕过了Facade的完整机制

2. 自创测试（违反铁律2）
   - 不基于标准模板
   - 省略了双账簿挂载验证
   - 省略了对账验证

3. 简化机制（违反铁律3）
   - PrivateLedger存在is_real=True/False双轨制
   - 实盘存储到long_position/short_position
   - 回测/Mock存储到virtual_position
   - 但对账器只检查long_position/short_position
   - 导致系统性"私有无多头但公共计算有"错误
```

**深刻教训：**
```
❌ 虽然"测试通过"，但数据完全不可信
❌ 架构混乱导致难以调试
❌ 浪费大量时间在无意义的工作上
✅ 必须从根本上解决：三大铁律
```

---

## 🔒 铁律1: 统一封装，统一调用，严禁旁路

### 原则

```
必须使用v6 Facade统一入口（build_facade/run_scenario）
严禁自己写循环直接调用底层模块
任何测试都必须通过Facade，不能为了"简化"而绕过架构
```

### 错误示例（test_ultimate_1000x_COMPLETE.py的错误）

```python
# ❌ 错误：自己写循环，直接调用底层模块
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 初始化（简化版）
moirai = Moirai(...)
evolution = EvolutionManagerV5(...)

# 自己写循环
for cycle in range(1000):
    # 只开仓，不平仓（旁路）
    for agent in moirai.agents:
        decision = agent.decide(...)
        if decision == 'buy':
            moirai.execute_trade(agent, 'buy', ...)
        # ❌ 没有平仓逻辑
    
    # 进化（省略Immigration）
    evolution.run_evolution_cycle(...)
    # ❌ 没有对账验证

# 结果：数千条空记录，账簿混乱
```

**问题：**
1. 自己写循环 → 绕过Facade的完整机制
2. 只开仓不平仓 → 交易生命周期不完整
3. 省略Immigration → 进化机制不完整
4. 没有对账验证 → 账簿错误无法发现

### 正确示例（v6.0强制方式）

```python
# ✅ 正确：使用Facade统一入口
from prometheus.v6 import build_facade, run_scenario

# 1. 构建Facade（统一初始化）
facade = build_facade(
    market_data=btc_data,
    config=SystemCapitalConfig(
        total_capital=1000000,
        agent_count=50,
        capital_per_agent=2000
    ),
    scenario='backtest',
    seed=7001,
    use_intelligent_genesis=True
)

# 2. 运行场景（统一运行）
results = run_scenario(
    facade=facade,
    max_cycles=1000,
    evolution_interval=50
)

# 3. 自动包含：
#    ✅ 完整交易生命周期（开仓→持仓→平仓）
#    ✅ 完整进化机制（选择、繁殖、变异、淘汰）
#    ✅ 自动对账（每笔交易）
#    ✅ 标准报告（ROI、夏普、对账通过率）
```

### 强制执行机制

**1. 底层模块标记为私有**
```python
# prometheus/v6/_core/_moirai.py
# 文件名前缀 _ 表示私有，不应直接导入

# prometheus/v6/_core/__init__.py
__all__ = []  # 不导出任何内容
```

**2. Facade是唯一对外接口**
```python
# prometheus/v6/__init__.py
from .facade import build_facade, run_scenario

__all__ = [
    'build_facade',
    'run_scenario',
]

# 警告：不要直接导入_core、world_signature等模块
```

**3. 文档明确警告**
```
所有模块的__init__.py和README都明确说明：
"不要直接导入，必须通过Facade"
```

---

## 📋 铁律2: 严格执行测试规范

### 原则

```
templates/STANDARD_TEST_TEMPLATE_V6.py是唯一标准
所有新测试必须基于此模板
模板包含：完整架构初始化、双账簿挂载验证、对账验证
不能自创简化版
```

### 错误示例（自创简化版测试）

```python
# ❌ 错误：自创简化版测试
import pytest
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.genome import GenomeVector

def test_simple():
    # 简化初始化（省略Facade）
    agents = [AgentV5(genome=GenomeVector.create_random()) for _ in range(50)]
    
    # 自己写循环
    for cycle in range(100):
        for agent in agents:
            # ... 简化逻辑
            pass
    
    # 没有对账验证
    assert len(agents) == 50  # 只检查Agent数量
```

**问题：**
1. 省略Facade → 架构不完整
2. 省略双账簿挂载验证 → 可能账簿未正确初始化
3. 省略对账验证 → 账簿错误无法发现
4. 简化逻辑 → 可能绕过关键机制

### 正确示例（基于标准模板）

```python
# ✅ 正确：基于STANDARD_TEST_TEMPLATE_V6.py

"""
测试：XXX功能验证

遵守三大铁律：
  1. 使用Facade统一入口（build_facade/run_scenario）
  2. 基于标准测试模板
  3. 完整机制，自动对账
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import logging
from prometheus.v6 import build_facade, run_scenario
from prometheus.v6.config import SystemCapitalConfig

logger = logging.getLogger(__name__)

def main():
    # ========== 1. 数据准备 ==========
    btc_data = pd.read_csv('data/btc_usdt_1h.csv')
    
    # ========== 2. 配置 ==========
    config = SystemCapitalConfig(
        total_capital=1000000,
        agent_count=50,
        capital_per_agent=2000,
        genesis_allocation_ratio=0.20
    )
    
    # ========== 3. 构建Facade（统一入口）==========
    facade = build_facade(
        market_data=btc_data,
        config=config,
        scenario='backtest',
        seed=7001,
        use_intelligent_genesis=True,
        experience_db_path="data/experience_db.json"
    )
    
    # ========== 4. 运行场景（统一运行）==========
    results = run_scenario(
        facade=facade,
        max_cycles=500,
        breeding_tax_rate=None,  # 自动计算
        evolution_interval=50
    )
    
    # ========== 5. 验证结果 ==========
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"系统ROI: {results['system_roi']:.2%}")
    print(f"Agent平均ROI: {results['agent_avg_roi']:.2%}")
    print(f"对账通过率: {results['reconciliation_pass_rate']:.2%}")
    print()
    
    # ========== 6. 断言（必须包含对账检查）==========
    assert results['reconciliation_pass_rate'] == 1.0, \
        f"对账失败！通过率: {results['reconciliation_pass_rate']:.2%}"
    
    assert results['system_roi'] > -1.0, \
        f"系统ROI异常: {results['system_roi']:.2%}"
    
    print("✅ 所有检查通过")

if __name__ == "__main__":
    main()
```

### 标准测试模板的核心要素

**必须包含：**
```
1. ✅ 使用build_facade()初始化
2. ✅ 使用run_scenario()运行
3. ✅ 自动对账（run_scenario内置）
4. ✅ 对账通过率验证（assert reconciliation_pass_rate == 1.0）
5. ✅ 完整配置（不省略任何参数）
6. ✅ 标准报告（系统ROI、Agent平均ROI、对账通过率）
```

**不能省略：**
```
❌ 不能省略Facade初始化
❌ 不能自己写循环
❌ 不能省略对账验证
❌ 不能简化配置
❌ 不能绕过标准流程
```

### 强制执行机制

**1. CI检查**
```yaml
# .github/workflows/test.yml
- name: Check test compliance
  run: |
    python scripts/check_test_compliance.py
    # 检查所有test_*.py是否符合模板
    # 不符合 → 测试失败
```

**2. 测试模板注释**
```python
# templates/STANDARD_TEST_TEMPLATE_V6.py
"""
⚠️ 警告：这是v6.0的标准测试模板
⚠️ 所有测试必须基于此模板
⚠️ 不能自创简化版
⚠️ 违反将导致测试失败

三大铁律：
  1. 使用Facade统一入口
  2. 基于此模板
  3. 完整机制，不简化
"""
```

---

## ⚙️ 铁律3: 不可为测试通过而简化底层机制

### 原则

```
测试必须使用完整的交易生命周期（开仓→持仓→平仓）
完整的账簿系统（不手动修改current_capital）
完整的进化机制（不省略Immigration/多样性监控，虽然v6.0已移除Immigration）
如果测试不通过，修复问题而不是简化机制
账簿一致性是金融系统生命线，任何妥协都可能导致灾难
```

### 错误示例1：简化交易生命周期

```python
# ❌ 错误：只开仓，不平仓
for agent in agents:
    if agent.decide() == 'buy':
        moirai.execute_trade(agent, 'buy', amount=1.0)
        # ❌ 没有平仓逻辑

# 结果：持仓一直累积，账簿混乱
```

**正确做法：**
```python
# ✅ 正确：使用Facade，自动包含完整生命周期
results = run_scenario(facade, max_cycles=500)
# 内部自动处理：开仓 → 持仓 → 平仓（根据Daimon决策）
```

### 错误示例2：手动修改账簿

```python
# ❌ 错误：为了让测试通过，手动修改账簿
agent.account.private_ledger.virtual_capital += 10000  # 手动加钱

# 结果：账簿不一致，对账失败
```

**正确做法：**
```python
# ✅ 正确：所有资金变动必须通过交易记录
facade.moirai.match_trade(agent, 'buy', ...)
# 内部自动处理：
#   1. 记录私账
#   2. 记录公账
#   3. 自动对账
```

### 错误示例3：省略对账验证

```python
# ❌ 错误：为了让测试"通过"，不做对账验证
for cycle in range(500):
    # ... 交易逻辑
    pass

# 没有对账验证
print("测试通过")  # 假通过

# 结果：账簿可能早就错了，但不知道
```

**正确做法：**
```python
# ✅ 正确：每笔交易自动对账
# AgentAccountSystem.record_trade()内置对账
def record_trade(self, agent, action, amount, price, ...):
    # 1. 记录私账
    self.private_ledger.record(...)
    
    # 2. 记录公账
    self.public_ledger.record(...)
    
    # 3. 自动对账（强制）
    self._auto_reconcile(agent)
    # 不一致 → 立即抛出异常
```

### 2025-12-07的双轨制缺陷（已修复）

**问题：**
```python
# PrivateLedger的双轨制设计缺陷
class PrivateLedger:
    def record(self, trade, is_real):
        if is_real:
            # 实盘：存储到long_position/short_position
            if trade.direction == 'long':
                self.long_position.append(trade)
            else:
                self.short_position.append(trade)
        else:
            # 回测/Mock：存储到virtual_position
            self.virtual_position.append(trade)

# 对账器只检查long_position/short_position
def reconcile(self):
    private_long = sum(self.long_position)
    private_short = sum(self.short_position)
    # ❌ 不检查virtual_position
    
    public_long = public_ledger.get_long()
    public_short = public_ledger.get_short()
    
    # 结果："私有无多头但公共计算有"错误
```

**修复（v6.0）：**
```python
# ✅ 废除双轨制，统一使用long_position/short_position
class PrivateLedger:
    def record(self, trade):
        # 不再区分is_real
        if trade.direction == 'long':
            self.long_position.append(trade)
        else:
            self.short_position.append(trade)

# 对账器统一检查
def reconcile(self):
    private_long = sum(self.long_position)
    private_short = sum(self.short_position)
    
    public_long = public_ledger.get_long()
    public_short = public_ledger.get_short()
    
    assert private_long == public_long
    assert private_short == public_short
    # 不一致 → 立即抛出异常
```

### 强制执行机制

**1. 自动对账（每笔交易）**
```python
# prometheus/v6/ledger/account_system.py
class AgentAccountSystem:
    def record_trade(self, agent, action, amount, price, ...):
        # 1. 记录私账
        self.private_ledger.record(...)
        
        # 2. 记录公账
        self.public_ledger.record(...)
        
        # 3. 自动对账（强制，无法绕过）
        try:
            self._auto_reconcile(agent)
        except ReconciliationError as e:
            logger.error(f"❌ 对账失败: {e}")
            raise  # 立即终止，不允许继续
```

**2. 原子操作（不可分割）**
```python
def record_trade(self, ...):
    # 私账 + 公账 + 对账 = 原子操作
    # 不能只调用其中一个
    # 不能跳过对账
    pass
```

**3. 统一入口（Moirai.match_trade）**
```python
# prometheus/v6/_core/_moirai.py
class Moirai:
    def match_trade(self, agent, action, amount, ...):
        # 1. 风控检查
        if not self._risk_check(agent, action, amount):
            return False
        
        # 2. 执行交易（场景相关）
        executed_price = self._execute_trade(action, amount)
        
        # 3. 记录账簿（自动对账）
        self.account_system.record_trade(
            agent, action, amount, executed_price, ...
        )
        # 内部自动对账，不一致 → 立即异常
        
        return True
```

---

## 🛡️ 三大铁律的强制执行机制

### 铁律1: 统一封装

| 机制 | 实施方式 | 效果 |
|------|----------|------|
| 文件名前缀 | `_moirai.py`, `_evolution.py` | 明确标记为私有 |
| `__init__.py`控制 | 不导出底层类 | 无法直接导入 |
| Facade唯一入口 | `build_facade()`, `run_scenario()` | 强制统一入口 |
| 文档警告 | 所有README和注释 | 明确禁止直接调用 |

### 铁律2: 测试规范

| 机制 | 实施方式 | 效果 |
|------|----------|------|
| 标准模板 | `STANDARD_TEST_TEMPLATE_V6.py` | 统一测试结构 |
| CI检查 | `check_test_compliance.py` | 自动验证模板符合性 |
| 对账断言 | `assert reconciliation_pass_rate == 1.0` | 强制对账验证 |
| 模板注释 | 明确警告和要求 | 防止遗忘 |

### 铁律3: 完整机制

| 机制 | 实施方式 | 效果 |
|------|----------|------|
| 自动对账 | `record_trade()`内置 | 每笔交易强制对账 |
| 原子操作 | 私账+公账+对账不可分割 | 防止旁路 |
| 统一入口 | `Moirai.match_trade()` | 强制完整流程 |
| 异常终止 | 对账失败立即raise | 不允许带病运行 |

---

## ⚠️ 违反铁律的后果

### 违反铁律1: 统一封装

**后果：**
```
❌ 代码无法正常工作（底层模块无法导入）
❌ 绕过Facade导致机制不完整
❌ 账簿混乱，数据不可信
❌ 浪费大量调试时间
```

**案例：test_ultimate_1000x_COMPLETE.py**
```
自己写循环 → 只开仓不平仓 → 数千条空记录 → 1小时+调试时间
```

### 违反铁律2: 测试规范

**后果：**
```
❌ 测试"通过"但数据错误
❌ 账簿错误无法发现
❌ CI检查失败
❌ 架构混乱，难以维护
```

**案例：自创简化版测试**
```
省略对账验证 → 账簿早就错了 → 但不知道 → 假通过
```

### 违反铁律3: 完整机制

**后果：**
```
❌ 对账失败，立即异常终止
❌ 账簿不一致，金融系统生命线断裂
❌ 数据完全不可信
❌ 系统无法正常运行
```

**案例：手动修改账簿**
```
agent.capital += 10000 → 私账不一致 → 对账失败 → 异常
```

---

## ✅ 检查清单

### 写代码时

```
□ 是否使用build_facade()初始化？
□ 是否使用run_scenario()运行？
□ 是否有自己写的循环调用底层模块？
□ 是否有直接导入_core模块？
□ 是否有手动修改账簿？
```

### 写测试时

```
□ 是否基于STANDARD_TEST_TEMPLATE_V6.py？
□ 是否包含完整架构初始化？
□ 是否包含对账验证（assert reconciliation_pass_rate == 1.0）？
□ 是否省略了任何核心机制？
□ 是否为了"测试通过"而简化逻辑？
```

### 运行测试时

```
□ 对账通过率是否100%？
□ 是否有"私有无多头但公共计算有"错误？
□ 是否有异常被忽略？
□ 系统ROI是否合理？
□ Agent总资金是否为$0？（异常信号）
```

### Code Review时

```
□ 是否违反铁律1（旁路）？
□ 是否违反铁律2（自创测试）？
□ 是否违反铁律3（简化机制）？
□ 是否有手动修改账簿？
□ 是否有绕过Facade的代码？
```

---

## 📌 总结

### 三大铁律的本质

```
铁律1: 统一封装 → 防止架构混乱
铁律2: 测试规范 → 防止假通过
铁律3: 完整机制 → 防止账簿错误

核心目标: 确保系统可靠、数据可信、账簿一致
```

### 为什么必须强制执行

```
金融系统的生命线是账簿一致性
1分钱的对账错误都是不可接受的
任何妥协都可能导致灾难
```

### v6.0的设计理念

```
不是建议，是强制
不是选项，是唯一路径
违反 → 代码无法运行 / 测试无法通过 / 系统立即异常

这是v6.0与v5.x的根本差异
```

---

**执行标准：每个测试必须过三关**
1. 使用Facade入口（铁律1）
2. 基于标准模板（铁律2）
3. 对账验证无误（铁律3）

**违反后果：**
- 像test_ultimate_1000x_COMPLETE.py那样产生数千条空记录
- 账簿不一致
- 虽然"测试通过"但数据完全不可信
- 浪费大量调试时间

**不得贪污！** 🔒

