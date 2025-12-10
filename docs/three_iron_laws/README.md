# Prometheus-Quant 三大铁律

**制定日期：2025-12-07**  
**最后更新：2025-12-10**  
**重要程度：⭐⭐⭐⭐⭐（绝对不可违反）**

---

## 🔥 **诞生背景**

2025-12-07，在解决账簿一致性问题的深刻教训后，我们确立了Prometheus-Quant开发的**三大铁律**。

**核心教训：**
- 测试看似通过，但账簿不一致，数据完全不可信
- 原因：自己写循环绕过架构，只开仓不平仓
- 结果：产生数千条空记录，浪费大量调试时间

**从此确立：**
> **不为测试通过而简化机制，不为省事而绕过架构！**

---

## ⚖️ **三大铁律**

### **铁律1：统一封装，统一调用，严禁旁路**

```
必须使用v6 Facade统一入口（run_scenario/build_facade）

严禁自己写循环直接调用底层模块

任何测试都必须通过Facade，不能为了"简化"而绕过架构
```

**原因：**
- Facade封装了完整的交易生命周期（开仓→持仓→平仓）
- 自己写循环容易遗漏关键步骤
- 绕过架构会导致账簿不一致

**违反后果：**
- 只开仓不平仓
- 账簿混乱
- 数据不可信

---

### **铁律2：严格执行测试规范**

```
templates/STANDARD_TEST_TEMPLATE.py 是唯一标准

所有新测试必须基于此模板

不能自创简化版
```

**模板必须包含：**
1. 完整架构初始化
2. 双账簿挂载验证（attach_accounts）
3. Supervisor/Moirai/EvolutionManagerV5/BulletinBoard完整组件
4. 对账验证

**违反后果：**
- 测试看似通过，实则数据错误
- 无法发现账簿不一致
- 浪费大量调试时间

---

### **铁律3：不可为测试通过而简化底层机制**

```
测试必须使用：
- 完整的交易生命周期（开仓→持仓→平仓）
- 完整的账簿系统（不手动修改current_capital）
- 完整的进化机制（不省略Immigration/多样性监控）

如果测试不通过，修复问题而不是简化机制
```

**账簿一致性是金融系统生命线，任何妥协都可能导致灾难！**

**违反后果：**
- 创建Mock版Agent（不是真实的AgentV5）
- 省略双账簿系统
- 绕过Facade
- 测试结果完全不可信

---

## 📋 **测试前必查清单⭐⭐⭐**

### **在写任何测试代码前，必须完成以下检查：**

#### **第1关：架构检查**
```
[ ] 是否使用v6 Facade作为统一入口？
[ ] 是否基于 templates/STANDARD_TEST_TEMPLATE.py？
[ ] 是否自己写了循环调用底层？（如果是，立即停止！）
```

#### **第2关：组件检查**
```
[ ] 是否包含完整的Supervisor？
[ ] 是否包含完整的Moirai？
[ ] 是否包含完整的EvolutionManagerV5？
[ ] 是否包含完整的BulletinBoard？
[ ] 是否包含双账簿系统（PublicLedger + PrivateLedger + AgentAccountSystem）？
```

#### **第3关：Agent检查**
```
[ ] 是否使用真实的AgentV5？（不是Mock版）
[ ] 是否正确初始化所有必需参数？
  [ ] agent_id
  [ ] initial_capital
  [ ] lineage (LineageVector对象)
  [ ] genome (GenomeVector对象)
  [ ] strategy_params (StrategyParams对象)
  [ ] generation
  [ ] meta_genome
[ ] 是否正确初始化所有运行时属性？
  [ ] total_roi
  [ ] current_capital
  [ ] profit_factor
  [ ] winning_trades / losing_trades
  [ ] total_profit / total_loss
```

#### **第4关：账簿检查**
```
[ ] 是否挂载了PublicLedger？
[ ] 是否挂载了PrivateLedger？
[ ] 是否挂载了AgentAccountSystem？
[ ] 是否调用了 attach_accounts()？
[ ] 是否在测试结束时进行了对账验证？
```

#### **第5关：执行检查**
```
[ ] 是否使用完整的交易生命周期？（开仓→持仓→平仓）
[ ] 是否自动平仓（不手动修改capital）？
[ ] 是否使用完整的进化机制？（不省略任何步骤）
```

---

## ❌ **违反铁律的案例**

### **案例1：test_ultimate_1000x_COMPLETE.py（反面教材）**

**违反的铁律：**
- ❌ 铁律1：自己写循环，绕过Facade
- ❌ 铁律2：没有使用标准模板
- ❌ 铁律3：只开仓不平仓

**代码片段：**
```python
❌ 错误代码：
for i in range(1000):
    # 自己写循环
    supervisor.execute_cycle(...)
    # 只开仓，没有平仓逻辑
```

**后果：**
- 产生数千条空记录
- 账簿不一致
- 测试看似通过，数据完全不可信

---

### **案例2：test_v7_working_demo.py（刚才的错误）**

**违反的铁律：**
- ❌ 铁律1：没有通过v6 Facade
- ❌ 铁律2：没有基于标准模板
- ❌ 铁律3：创建了SimpleMockAgent（不是真实的AgentV5）

**代码片段：**
```python
❌ 错误代码：
class SimpleMockAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.total_roi = 0.0
        # ... 省略大量必需属性

# 为了快速通过测试而简化
agent = SimpleMockAgent("agent_001")
```

**后果：**
- Agent不完整
- 测试结果可信度存疑
- 可能掩盖真实问题

---

## ✅ **符合铁律的正确示例**

### **正确示例：基于标准模板的测试**

```python
✅ 正确代码：

# 1. 导入标准模板
from templates.STANDARD_TEST_TEMPLATE import StandardTest

# 2. 继承标准模板
class TestV7Integration(StandardTest):
    
    def test_full_cycle(self):
        # 3. 使用v6 Facade
        result = self.facade.run_scenario(
            market_type="bull",
            cycles=100,
            initial_agents=100
        )
        
        # 4. 自动包含：
        #    - 完整的Agent（真实的AgentV5）
        #    - 双账簿系统
        #    - 完整的交易生命周期
        #    - 自动对账
        
        # 5. 验证结果
        assert result['final_agents'] > 0
        assert result['ledger_consistent'] == True
```

---

## 🔍 **如何检查是否违反铁律？**

### **检查清单（代码审查时使用）**

```python
# 问题1：是否看到这种代码？
for cycle in range(N):
    supervisor.execute_cycle(...)
# ⚠️ 警告：可能违反铁律1

# 问题2：是否看到这种代码？
class SimpleMock...:
    ...
# ⚠️ 警告：可能违反铁律3

# 问题3：是否看到缺少这些？
# - v6 Facade
# - StandardTest模板
# - 双账簿系统
# ⚠️ 警告：可能违反铁律1+2

# 问题4：测试文件是否不在templates/目录下的模板？
# ⚠️ 警告：可能违反铁律2
```

---

## 📖 **延伸阅读**

- [AgentV5完整规范](../core_structures/agent_v5_spec.md) - 如何正确创建Agent
- [EvolutionManagerV5规范](../core_structures/evolution_manager_spec.md) - 如何正确管理进化
- [测试模式规范](../integration_patterns/testing_patterns.md) - 如何编写符合铁律的测试
- [v6 Facade使用规范](../integration_patterns/facade_usage.md) - 如何正确使用Facade

---

## 🎯 **执行标准**

### **每个测试必须过三关：**

1. ✅ **使用Facade入口**
2. ✅ **基于标准模板**
3. ✅ **对账验证无误**

### **如果有任何一关不过：**

```
立即停止 → 重新设计 → 严格遵守铁律
```

---

## 📝 **版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0 | 2025-12-07 | 初始制定，基于账簿问题的深刻教训 |
| v1.1 | 2025-12-10 | 添加详细的执行清单和案例分析 |

---

**⚠️ 最重要的提醒：**

```
三大铁律不是建议，是规则！
三大铁律不是指南，是红线！
三大铁律不可协商，不可妥协！

违反铁律 = 自毁长城
```

**记住：账簿一致性是金融系统的生命线！⭐⭐⭐**

