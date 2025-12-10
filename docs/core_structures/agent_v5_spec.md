# AgentV5 完整规范

**文件路径：** `prometheus/core/agent_v5.py`  
**最后更新：** 2025-12-10 23:37  
**重要程度：** ⭐⭐⭐（核心中的核心）

---

## 📋 **类定义**

```python
class AgentV5:
    """
    Prometheus v6.0 AlphaZero式Agent
    
    这是系统的执行单元，负责自主交易决策
    """
```

---

## 🔧 **初始化参数（必需）⭐⭐⭐**

### **完整签名**

```python
def __init__(
    self,
    agent_id: str,                      # Agent唯一标识
    initial_capital: float,             # 初始资金
    lineage: LineageVector,             # 血统向量
    genome: GenomeVector,               # 基因组向量
    strategy_params: StrategyParams,    # 策略参数
    generation: int = 0,                # 代数（默认0）
    meta_genome: Optional['MetaGenome'] = None,  # 元基因组（可选）
):
```

### **参数详解**

#### **1. agent_id: str** ⭐
- **说明**：Agent的唯一标识符
- **格式**：建议格式 `"agent_{数字}"` 或 `"{前缀}_agent_{数字}"`
- **示例**：
  ```python
  ✅ "agent_001"
  ✅ "v7_agent_42"
  ❌ ""  # 空字符串不可接受
  ```

#### **2. initial_capital: float** ⭐
- **说明**：Agent的初始资金
- **单位**：美元（或系统基准货币）
- **范围**：必须 > 0
- **示例**：
  ```python
  ✅ 10000.0
  ✅ 50000.0
  ❌ 0.0      # 不能为0
  ❌ -1000.0  # 不能为负数
  ```

#### **3. lineage: LineageVector** ⭐⭐⭐
- **说明**：血统向量，记录Agent的遗传信息
- **类型**：`LineageVector` 对象
- **初始化**：`LineageVector(vector: np.ndarray)`
- **向量维度**：通常为 10
- **正确示例**：
  ```python
  ✅ lineage = LineageVector(np.random.rand(10))
  ✅ lineage = LineageVector(np.array([0.1, 0.2, ..., 1.0]))  # 长度10
  ```
- **错误示例**：
  ```python
  ❌ lineage = LineageVector()  # 缺少vector参数
  ❌ lineage = None             # 不能为None
  ❌ lineage = [0.1, 0.2, ...]  # 不能是Python列表
  ```

#### **4. genome: GenomeVector** ⭐⭐⭐
- **说明**：基因组向量，定义Agent的交易行为特征
- **类型**：`GenomeVector` 对象
- **初始化**：`GenomeVector(vector: np.ndarray)`
- **向量维度**：通常为 50
- **正确示例**：
  ```python
  ✅ genome = GenomeVector(np.random.rand(50))
  ✅ genome = GenomeVector(np.array([...]))  # 长度50
  ```
- **错误示例**：
  ```python
  ❌ genome = GenomeVector()    # 缺少vector参数
  ❌ genome = None               # 不能为None
  ```

#### **5. strategy_params: StrategyParams** ⭐⭐⭐
- **说明**：策略参数，定义交易规则
- **类型**：`StrategyParams` 对象
- **重要性**：决定Agent的具体交易逻辑
- **初始化**：需要查看 `StrategyParams` 的具体定义
- **正确示例**：
  ```python
  ✅ strategy_params = StrategyParams(
      entry_threshold=0.5,
      exit_threshold=0.3,
      position_size_base=0.1,
      max_holding_periods=20
  )
  # 注：具体参数需要查看StrategyParams的定义
  ```
- **错误示例**：
  ```python
  ❌ strategy_params = StrategyParams()  # 可能缺少必需参数
  ❌ strategy_params = None              # 不能为None
  ❌ strategy_params = {}                # 不能是字典
  ```

#### **6. generation: int** ⭐
- **说明**：Agent的代数
- **默认值**：0（初代）
- **用途**：用于退休机制（10代退休）
- **示例**：
  ```python
  ✅ generation = 0      # 初代Agent
  ✅ generation = 5      # 第5代
  ❌ generation = -1     # 不能为负数
  ```

#### **7. meta_genome: Optional[MetaGenome]** ⭐
- **说明**：元基因组，控制Agent的决策风格
- **类型**：`MetaGenome` 对象或 `None`
- **默认值**：`None`（会自动创建）
- **示例**：
  ```python
  ✅ meta_genome = MetaGenome()
  ✅ meta_genome = None  # 可选，会自动创建
  ```

---

## 📦 **必需属性（运行时）⭐⭐⭐**

以下属性在Agent运行过程中**必须存在且有效**：

### **财务属性**
```python
self.initial_capital: float      # 初始资金（初始化时设置）
self.current_capital: float      # 当前资金（运行时更新）
self.total_roi: float            # 总ROI（运行时计算）
self.total_profit: float         # 总盈利（运行时累积）
self.total_loss: float           # 总亏损（运行时累积）
```

### **交易统计**
```python
self.winning_trades: int         # 盈利交易数
self.losing_trades: int          # 亏损交易数
self.profit_factor: float        # 盈亏比（total_profit / total_loss）
```

### **进化相关**
```python
self.generation: int             # 代数
self.awards: int                 # 奖章数（用于退休机制）
```

### **可选属性（v7.0新增）**
```python
self.allocated_capital: float    # 分配的资本配额（Moirai动态调整）
```

---

## ❌ **禁止的用法**

### **1. 创建简化版/Mock版**

```python
❌ 错误示例：
class SimpleMockAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.total_roi = 0.0
        # ... 省略大量必需属性

# 后果：测试不可信，违反三大铁律第3条
```

### **2. 省略必需参数**

```python
❌ 错误示例：
agent = AgentV5(
    agent_id="agent_001",
    initial_capital=10000.0,
    # lineage缺失！
    # genome缺失！
    # strategy_params缺失！
)

# 后果：TypeError，运行失败
```

### **3. 使用错误的类型**

```python
❌ 错误示例：
agent = AgentV5(
    agent_id="agent_001",
    initial_capital=10000.0,
    lineage=[0.1, 0.2, 0.3],  # ❌ 应该是LineageVector，不是list
    genome=[...],              # ❌ 应该是GenomeVector
    strategy_params={},        # ❌ 应该是StrategyParams对象
)

# 后果：类型错误，后续调用失败
```

---

## ✅ **正确的创建方式**

### **完整示例（推荐）⭐⭐⭐**

```python
import numpy as np
from prometheus.core.agent_v5 import AgentV5, LineageVector, GenomeVector, StrategyParams
from prometheus.core.meta_genome import MetaGenome

# Step 1: 准备所有必需的组件
lineage = LineageVector(np.random.rand(10))
genome = GenomeVector(np.random.rand(50))
strategy_params = StrategyParams(
    # 根据StrategyParams的定义填写所有必需参数
    entry_threshold=0.5,
    exit_threshold=0.3,
    position_size_base=0.1,
    max_holding_periods=20
)
meta_genome = MetaGenome()

# Step 2: 创建Agent
agent = AgentV5(
    agent_id="agent_001",
    initial_capital=10000.0,
    lineage=lineage,
    genome=genome,
    strategy_params=strategy_params,
    generation=0,
    meta_genome=meta_genome
)

# Step 3: 初始化运行时属性（如果需要）
agent.total_roi = 0.0
agent.allocated_capital = 10000.0

# ✅ 这样创建的Agent是完整且可信的
```

---

## 🔗 **相关文档**

- [EvolutionManagerV5规范](./evolution_manager_spec.md) - 如何管理Agent
- [测试模式规范](../integration_patterns/testing_patterns.md) - 如何在测试中使用Agent
- [三大铁律](../three_iron_laws/README.md) - Agent创建的基本原则

---

## 📝 **版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0 | 2025-12-10 | 初始创建，记录AgentV5的完整规范 |

---

**⚠️ 重要提醒：任何对AgentV5的修改都必须同步更新此文档！**

