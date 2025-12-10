# MoiraiV7 完整规范

## 概述
`MoiraiV7` 是Prometheus v7.0的核心种群管理者。本规范详细定义了其初始化参数、核心属性、必需方法及正确使用示例，确保与`EvolutionManagerV5`的正确集成。

## 核心设计理念⭐⭐⭐
- **直接管理Agent**：MoiraiV7自己存储和管理`agents`列表，不依赖外部wrapper
- **极简决策公式**：`delta = (S - current) × |E|`，只用5行代码完成规模调整
- **双周期机制**：
  - 轻量级调整：每周期调整Agent资本配额
  - 重量级调整：动态周期触发进化（繁殖/淘汰）
- **与EvolutionManagerV5协作**：通过`self.agents`属性提供Agent访问接口

## 初始化参数（必需）⭐⭐⭐

```python
class MoiraiV7:
    def __init__(
        self, 
        bulletin_board: BulletinBoard,
        evolution_manager: EvolutionManagerV5,  # 可以先传None，稍后注入
        initial_agents: List = None  # ⭐ v7.0新增
    ):
```

### 参数说明

- `bulletin_board`: `BulletinBoard`
  - Prophet和Moirai之间的信息传递接口
  - 必须是一个已初始化的`BulletinBoard`实例
  
- `evolution_manager`: `EvolutionManagerV5` (可选)
  - 进化管理器实例
  - 可以先传`None`，在创建`EvolutionManagerV5`后通过赋值注入
  
- `initial_agents`: `List[AgentV5]` (可选)
  - 初始Agent列表
  - 如果不提供，默认为空列表`[]`

### 正确的初始化顺序（两阶段）⭐⭐⭐

由于`MoiraiV7`和`EvolutionManagerV5`存在循环依赖，必须使用两阶段初始化：

```python
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.agent_v5 import AgentV5

# 1. 创建BulletinBoard
bb = BulletinBoard(board_name="test_board")

# 2. 创建初始Agent列表
agents = [AgentV5(...) for _ in range(100)]

# 3. 创建MoiraiV7（暂时不传evolution_manager）
moirai = MoiraiV7(
    bulletin_board=bb,
    evolution_manager=None,  # ⭐ 先传None
    initial_agents=agents    # ⭐ 传入初始agents
)

# 4. 创建EvolutionManagerV5（传入moirai）
evolution_mgr = EvolutionManagerV5(
    moirai=moirai,  # ⭐ 传入MoiraiV7实例
    elite_ratio=0.2,
    elimination_ratio=0.3,
    # ... 其他参数
)

# 5. 将EvolutionManager注入MoiraiV7
moirai.evolution_manager = evolution_mgr  # ⭐ 注入

# 现在moirai和evolution_mgr都可以正常工作了
```

## 核心属性⭐⭐⭐

MoiraiV7在初始化时会创建以下属性：

- `self.bulletin_board`: `BulletinBoard` - 公告板实例
- `self.evolution_manager`: `EvolutionManagerV5` - 进化管理器实例
- `self.agents`: `List[AgentV5]` - **⭐ Agent列表（MoiraiV7直接管理）**
- `self.current_scale`: `float` - 当前系统规模（0-1），初始值0.5
- `self.next_agent_id`: `int` - Agent ID计数器，初始值为`len(initial_agents)`
- `self.TARGET_RESERVE_RATIO`: `float` - 目标储备率，固定值0.3
- `self.generation`: `int` - 代数计数器，初始值0

## 核心方法⭐⭐⭐

### 1. `run_cycle(cycle: int, current_price: float = None)`

Moirai的主工作流程，每个交易周期调用一次。

```python
def run_cycle(self, cycle: int, current_price: float = None):
    """
    执行流程：
    1. 读取Prophet公告（S + E + risk_level）
    2. 自主决策（5行公式）
    3. 轻量级调整（每周期调整资本）
    4. 重量级调整（动态触发进化）
    5. 上报结果到Prophet
    """
```

### 2. `decide(S: float, E: float) -> float`

**终极决策公式（5行核心代码）⭐⭐⭐**

```python
target = S                              # 1. 目标 = S
speed = abs(E)                          # 2. 速度 = |E|
delta = (target - self.current_scale) * speed  # 3. 调整量
self.current_scale += delta             # 4. 执行调整
self.current_scale = max(0, min(1, self.current_scale))  # 5. 限制范围
```

### 3. `terminate_agent(agent, current_price: float, reason: str = "eliminated")`

淘汰Agent（由EvolutionManagerV5调用）

```python
def terminate_agent(self, agent, current_price: float, reason: str = "eliminated"):
    """
    从self.agents中移除Agent
    
    Args:
        agent: 要淘汰的AgentV5实例
        current_price: 当前价格
        reason: 淘汰原因
    """
```

### 4. `retire_agent(agent, reason: str, current_price: float, awards: int = 0)`

退休Agent（由EvolutionManagerV5调用）

```python
def retire_agent(self, agent, reason: str, current_price: float, awards: int = 0):
    """
    从self.agents中移除Agent（退休）
    
    Args:
        agent: 要退休的AgentV5实例
        reason: 退休原因
        current_price: 当前价格
        awards: 奖章数
    """
```

## 访问Agent规范⭐⭐⭐

### ✅ 正确的Agent访问方式

```python
# 1. 在MoiraiV7内部访问agents
class MoiraiV7:
    def some_method(self):
        agents = self.agents  # ✅ 正确
        
# 2. 在EvolutionManagerV5内部访问agents
class EvolutionManagerV5:
    def some_method(self):
        agents = self.moirai.agents  # ✅ 正确（通过moirai实例）
        
# 3. 在测试代码中访问agents
moirai = MoiraiV7(...)
agents = moirai.agents  # ✅ 正确
```

### ❌ 常见错误

```python
# ❌ 错误1：使用临时wrapper
moirai_wrapper = SomeWrapper()
moirai = MoiraiV7(...)
# 两个不同的agents列表，导致数据不同步！

# ❌ 错误2：在MoiraiV7内部通过evolution_manager访问
class MoiraiV7:
    def some_method(self):
        agents = self.evolution_manager.moirai.agents  # ❌ 循环引用，复杂

# ❌ 错误3：忘记注入evolution_manager
moirai = MoiraiV7(bb, None, agents)
evolution_mgr = EvolutionManagerV5(moirai, ...)
# 忘记：moirai.evolution_manager = evolution_mgr
```

## 与EvolutionManagerV5的协作⭐⭐⭐

### MoiraiV7为EvolutionManagerV5提供的接口

EvolutionManagerV5需要Moirai提供以下属性和方法：

1. **必需属性**：
   - `moirai.agents` - Agent列表
   - `moirai.next_agent_id` - Agent ID计数器
   - `moirai.TARGET_RESERVE_RATIO` - 目标储备率
   - `moirai.generation` - 代数计数器

2. **必需方法**：
   - `moirai.terminate_agent(agent, current_price, reason)` - 淘汰Agent
   - `moirai.retire_agent(agent, reason, current_price, awards)` - 退休Agent

### EvolutionManagerV5的调用示例

```python
# 在EvolutionManagerV5内部
class EvolutionManagerV5:
    def run_evolution_cycle(self, current_price: float):
        # 访问Agent列表
        agents = self.moirai.agents
        
        # 评估并淘汰
        for agent in weak_agents:
            self.moirai.terminate_agent(agent, current_price, "low_performance")
        
        # 繁殖新Agent
        child_id = f"Agent_{self.moirai.next_agent_id}"
        self.moirai.next_agent_id += 1
        # ... 创建新Agent并添加到self.moirai.agents
```

## 禁止行为⚠️

1. **❌ 创建临时wrapper**：
   - 不要创建`RealMoiraiWrapper`或其他临时包装类
   - 直接使用`MoiraiV7`
   
2. **❌ 直接修改agents列表**：
   - 添加/删除Agent必须通过`terminate_agent()`/`retire_agent()`方法
   - 或者在EvolutionManagerV5中直接操作`self.moirai.agents`（允许，因为它们是紧密协作的）
   
3. **❌ 忘记注入evolution_manager**：
   - 如果初始化时传入`None`，必须在创建`EvolutionManagerV5`后注入
   - 否则`run_cycle()`中的进化逻辑无法执行

## 测试规范⭐⭐⭐

### 正确的测试模式

```python
# ===== 标准测试流程 =====

# 1. 创建BulletinBoard
bb = BulletinBoard()

# 2. 创建初始agents
agents = [create_real_agent(f"agent_{i}") for i in range(100)]

# 3. 挂载账簿系统
public_ledger = PublicLedger()
attach_accounts(agents, public_ledger)

# 4. 创建MoiraiV7（先不传evolution_manager）
moirai = MoiraiV7(bb, None, agents)

# 5. 创建EvolutionManagerV5
evolution_mgr = EvolutionManagerV5(moirai, ...)

# 6. 注入evolution_manager
moirai.evolution_manager = evolution_mgr

# 7. 运行测试循环
for cycle in range(1, 51):
    # 交易
    simulate_agent_trading(moirai.agents, ...)
    
    # Prophet决策
    prophet.run_decision_cycle()
    
    # Moirai执行
    moirai.run_cycle(cycle, current_price)
```

---

**最后更新时间：** 2025-12-11 00:25

**更新原因：** 重构MoiraiV7架构，删除临时wrapper方案，实现直接管理agents

**影响范围：** 所有使用MoiraiV7的测试代码和集成代码

