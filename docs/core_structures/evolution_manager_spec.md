# EvolutionManagerV5 完整规范

**文件路径：** `prometheus/core/evolution_manager_v5.py`  
**最后更新：** 2025-12-11 00:25  
**重要程度：** ⭐⭐⭐（最容易出错的组件）  
**v7.0更新：** 新增MoiraiV7接口要求

---

## 📋 **类定义**

```python
class EvolutionManagerV5:
    """
    v6.0 AlphaZero式进化管理器（极简训练版）
    
    核心职责：
    1. 评估种群表现（纯Fitness）
    2. 淘汰最差Agent（性能淘汰）
    3. 病毒式复制（克隆精英+变异）
    4. 退休/死亡检查（5奖章/10代）
    5. 直接创建新生（离开→新生，1:1补充）
    """
```

---

## ⚠️ **核心设计原则（必须理解！）⭐⭐⭐**

### **关键设计决策**

```
EvolutionManagerV5 不存储 agents！⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

agents 存储在哪里？
→ 存储在 moirai.agents

如何访问agents？
→ 通过 self.moirai.agents

为什么这样设计？
→ Moirai是Agent的管理者
→ EvolutionManager只是提供进化算法
→ 分离关注点，职责清晰
```

---

## 🔧 **初始化参数**

### **完整签名**

```python
def __init__(
    self,
    moirai,                              # Moirai实例（⭐⭐⭐必须先创建）
    elite_ratio: float = 0.2,            # 精英比例
    elimination_ratio: float = 0.3,      # 淘汰比例
    capital_pool=None,                   # 资金池（可选）
    fitness_mode: str = 'profit_factor', # Fitness计算模式
    retirement_enabled: bool = False,    # 是否启用退休机制
    medal_system_enabled: bool = False,  # 是否启用奖章系统
    immigration_enabled: bool = True     # 是否启用Immigration
):
```

### **参数详解**

#### **1. moirai** ⭐⭐⭐（最重要！）
- **类型**：Moirai实例（`MoiraiV7`或具有相同接口的对象）
- **v7.0推荐**：直接使用`MoiraiV7`实例
- **必须条件**：
  - moirai对象必须已经创建
  - moirai对象必须有 `agents` 属性（列表）
  - moirai.agents 中存储了所有Agent
  - moirai对象必须有以下属性：
    - `next_agent_id`: int - Agent ID计数器
    - `TARGET_RESERVE_RATIO`: float - 目标储备率（通常0.3）
    - `generation`: int - 代数计数器
  - moirai对象必须实现以下方法：
    - `terminate_agent(agent, current_price, reason)` - 淘汰Agent
    - `retire_agent(agent, reason, current_price, awards)` - 退休Agent
- **作用**：EvolutionManager通过 `self.moirai.agents` 访问和修改Agent列表

**v7.0接口要求（完整）：**
```python
class MoiraiInterface:
    # 必需属性
    agents: List[AgentV5]           # Agent列表
    next_agent_id: int              # Agent ID计数器
    TARGET_RESERVE_RATIO: float     # 目标储备率
    generation: int                 # 代数计数器
    
    # 必需方法
    def terminate_agent(self, agent, current_price: float, reason: str):
        """淘汰Agent"""
        pass
    
    def retire_agent(self, agent, reason: str, current_price: float, awards: int):
        """退休Agent"""
        pass
```

#### **2. fitness_mode: str** ⭐
- **可选值**：
  - `'profit_factor'`：使用Profit Factor作为Fitness（v6.0 Stage 1.1默认）
  - `'absolute_return'`：使用绝对收益（v6.0原版）
- **推荐**：`'profit_factor'`

#### **3. retirement_enabled: bool** ⭐
- **说明**：是否启用退休机制（5奖章/10代）
- **v6.0推荐**：`True`

#### **4. medal_system_enabled: bool** ⭐
- **说明**：是否启用奖章系统
- **v6.0推荐**：`True`

#### **5. immigration_enabled: bool** ⭐
- **说明**：是否启用Immigration机制
- **v6.0推荐**：`False`（已封存，留给v7.0 Prophet）

---

## ✅ **正确的初始化方式**

### **v7.0标准方式（使用MoiraiV7）⭐⭐⭐**

```python
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.agent_v5 import AgentV5, LineageVector, GenomeVector, StrategyParams
from prometheus.core.meta_genome import MetaGenome
import numpy as np

# Step 1: 创建BulletinBoard
bb = BulletinBoard(board_name="test_board")

# Step 2: 创建初始Agent列表
agents = []
for i in range(100):
    agent = AgentV5(
        agent_id=f"agent_{i}",
        initial_capital=10000.0,
        lineage=LineageVector(np.random.rand(10)),
        genome=GenomeVector(np.random.rand(50)),
        strategy_params=StrategyParams(...),
        generation=0,
        meta_genome=MetaGenome()
    )
    agents.append(agent)

# Step 3: 创建MoiraiV7（先不传evolution_manager）⭐
moirai = MoiraiV7(
    bulletin_board=bb,
    evolution_manager=None,  # ⭐ 先传None
    initial_agents=agents    # ⭐ 传入初始agents
)

# Step 4: 创建EvolutionManagerV5（传入moirai）⭐
evolution_mgr = EvolutionManagerV5(
    moirai=moirai,  # ⭐ 传入MoiraiV7实例
    elite_ratio=0.2,
    elimination_ratio=0.3,
    capital_pool=None,
    fitness_mode='profit_factor',
    retirement_enabled=True,
    medal_system_enabled=True,
    immigration_enabled=False
)

# Step 5: 将EvolutionManager注入MoiraiV7⭐
moirai.evolution_manager = evolution_mgr

# ✅ 现在可以正常使用了
# 访问agents: moirai.agents
# 访问agents: evolution_mgr.moirai.agents（同一个列表）
```

### **v6.0兼容方式（使用临时wrapper）⚠️**

如果无法使用`MoiraiV7`，可以创建临时wrapper（**不推荐**）：

```python
# Step 1: 创建Moirai包装器（仅用于测试）
class TestMoirai:
    def __init__(self):
        self.agents = []  # ⭐ 必须有这个属性
        self.next_agent_id = 0  # ⭐ v7.0新增：繁殖时需要
        self.generation = 0
        self.TARGET_RESERVE_RATIO = 0.3
    
    def retire_agent(self, agent, reason, current_price, awards=0):
        if agent in self.agents:
            self.agents.remove(agent)
    
    def terminate_agent(self, agent, current_price, reason=None):
        if agent in self.agents:
            self.agents.remove(agent)

moirai = TestMoirai()

# Step 2-4: 同上
# ...
```

**⚠️ 警告：临时wrapper方案已废弃，v7.0必须使用MoiraiV7！**

---

## 🔍 **如何访问agents**

### **正确的方式⭐⭐⭐**

```python
# 在EvolutionManagerV5的方法中
agents = self.moirai.agents  # ✅ 正确

# 在外部代码中
agents = evolution_mgr.moirai.agents  # ✅ 正确
```

### **错误的方式**

```python
# ❌ 错误：EvolutionManagerV5没有agents属性
agents = self.agents
# 结果：AttributeError: 'EvolutionManagerV5' object has no attribute 'agents'

# ❌ 错误：evolution_mgr没有agents属性
agents = evolution_mgr.agents
# 结果：AttributeError: 'EvolutionManagerV5' object has no attribute 'agents'
```

---

## 🔧 **核心方法**

### **run_evolution_cycle(current_price: float)**
- **说明**：执行一次完整的进化周期
- **参数**：`current_price` - 当前价格（用于退休平仓）
- **流程**：
  1. 评估所有Agent的Fitness
  2. 排序
  3. 淘汰最差的30%
  4. 克隆精英的20%并变异
  5. 检查退休条件（5奖章或10代）
  6. 补充新生Agent（1:1替代离开者）

### **典型调用**

```python
# 在Moirai中调用
if should_evolve:
    evolution_mgr.run_evolution_cycle(current_price=50000.0)
```

---

## ❌ **常见错误**

### **错误1：agents访问错误**

```python
❌ 错误代码：
def some_method(self):
    agents = self.evolution_manager.agents  # AttributeError!

✅ 正确代码：
def some_method(self):
    agents = self.evolution_manager.moirai.agents
```

### **错误2：初始化顺序错误**

```python
❌ 错误顺序：
evolution_mgr = EvolutionManagerV5(moirai=moirai, ...)
moirai.agents = [...]  # 太晚了！

✅ 正确顺序：
moirai.agents = [...]  # 先创建agents
evolution_mgr = EvolutionManagerV5(moirai=moirai, ...)
```

### **错误3：Moirai缺少必需方法**

```python
❌ 错误：Moirai缺少方法
class SimpleMoirai:
    def __init__(self):
        self.agents = []
    # 缺少 retire_agent 和 terminate_agent

# 结果：调用 run_evolution_cycle 时报错

✅ 正确：Moirai必须实现所有必需方法
class SimpleMoirai:
    def __init__(self):
        self.agents = []
        self.TARGET_RESERVE_RATIO = 0.3
    
    def retire_agent(self, agent, reason, current_price, awards=0):
        if agent in self.agents:
            self.agents.remove(agent)
    
    def terminate_agent(self, agent, current_price, reason=None):
        if agent in self.agents:
            self.agents.remove(agent)
```

---

## 📊 **在测试中使用**

### **最小可用示例**

```python
import pytest
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.agent_v5 import AgentV5, LineageVector, GenomeVector, StrategyParams
from prometheus.core.meta_genome import MetaGenome
import numpy as np

def test_evolution():
    # 1. 创建Moirai包装器
    class TestMoirai:
        def __init__(self):
            self.agents = []
            self.TARGET_RESERVE_RATIO = 0.3
        
        def retire_agent(self, agent, reason, current_price, awards=0):
            if agent in self.agents:
                self.agents.remove(agent)
        
        def terminate_agent(self, agent, current_price, reason=None):
            if agent in self.agents:
                self.agents.remove(agent)
    
    moirai = TestMoirai()
    
    # 2. 创建测试Agent
    for i in range(10):
        agent = AgentV5(
            agent_id=f"test_agent_{i}",
            initial_capital=10000.0,
            lineage=LineageVector(np.random.rand(10)),
            genome=GenomeVector(np.random.rand(50)),
            strategy_params=StrategyParams(...),
            generation=0,
            meta_genome=MetaGenome()
        )
        agent.total_roi = np.random.uniform(-0.1, 0.1)
        agent.profit_factor = np.random.uniform(0.5, 2.0)
        moirai.agents.append(agent)
    
    # 3. 创建EvolutionManager
    evolution_mgr = EvolutionManagerV5(
        moirai=moirai,
        elite_ratio=0.2,
        elimination_ratio=0.3,
        fitness_mode='profit_factor',
        retirement_enabled=True,
        medal_system_enabled=True,
        immigration_enabled=False
    )
    
    # 4. 运行进化
    initial_count = len(moirai.agents)
    evolution_mgr.run_evolution_cycle(current_price=50000.0)
    
    # 5. 验证
    assert len(moirai.agents) > 0  # 应该还有存活的Agent
```

---

## 🔗 **相关文档**

- [AgentV5规范](./agent_v5_spec.md) - Agent的创建规范
- [Moirai规范](./moirai_spec.md) - Moirai的完整接口（待创建）
- [测试模式规范](../integration_patterns/testing_patterns.md) - 如何测试进化机制
- [三大铁律](../three_iron_laws/README.md) - 测试的基本原则

---

## 📝 **版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0 | 2025-12-10 | 初始创建，记录EvolutionManagerV5的核心设计和常见错误 |
| v1.1 | 2025-12-11 | ⭐ v7.0重大更新：新增MoiraiV7接口要求，废弃临时wrapper方案，新增next_agent_id要求 |

---

**⚠️ 核心要点总结：**

1. EvolutionManagerV5 **不存储agents**
2. agents存储在 `moirai.agents`
3. 访问agents必须通过 `self.moirai.agents`
4. Moirai必须先创建并包含agents，再传给EvolutionManager
5. Moirai必须实现 `retire_agent` 和 `terminate_agent` 方法

**记住这5点，就能避免90%的错误！⭐⭐⭐**

