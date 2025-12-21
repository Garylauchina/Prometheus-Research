# Prometheus-Quant 开发铁律

> ⚠️ 项目根目录约束文件，开发前必读！AI助手接到任务时先阅读本文件！

---

## 🎯 核心原则

**质量优先于速度，完整性优先于便利性，长期价值优先于短期捷径**

---

## 📐 架构层面

### ⚠️ 铁律1：统一封装，严禁旁路

**必须：** 通过统一入口/接口访问系统  
**禁止：** 自己写循环直接调用底层模块

```python
# ✅ 正确
from prometheus.xxx import SystemEntry
entry = SystemEntry(config)
result = entry.run()

# ❌ 错误
from prometheus.v9.system import SystemManager
manager = SystemManager(config)  # 绕过封装
```

**例外：** 封装层本身的实现、底层单元测试（需注释说明）

---

### ⚠️ 铁律2：向后兼容，渐进演进

**必须：** 新功能用开关控制  
**禁止：** 删除现有接口、破坏性修改

```python
# ✅ 正确
class Config:
    use_new_feature: bool = False  # 默认关闭

# ❌ 错误
def calculate():
    return new_method()  # 直接替换旧逻辑
```

**重大变更：** 保留旧接口（标记deprecated）+ 迁移文档 + CHANGELOG记录

---

## 🧪 测试层面

### ⚠️ 铁律3：严格测试规范

**必须：** 使用标准测试模板  
**禁止：** 自创简化版测试

```python
# ✅ 正确：基于标准模板
from tests.STANDARD_TEST_TEMPLATE import StandardTestBase

class TestFeature(StandardTestBase):
    def test_complete(self):
        self.setup()
        self.run()
        self.verify()

# ❌ 错误：临时脚本
def quick_test():
    agent = Agent()
    agent.trade()  # 无验证
```

**临时调试：** 可以写脚本（放`scripts/debug/`），提交前转为标准测试

---

### ⚠️ 铁律4：不为测试妥协完整性

**必须：** 完整生命周期（开仓→持仓→平仓）+ 资金守恒验证  
**禁止：** 为了测试快而跳过关键步骤

```python
# ✅ 正确
def test_trading():
    initial = agent.capital.total
    agent.open_position()
    agent.hold_position()
    agent.close_position()
    assert_capital_conservation(initial, agent.capital.total)

# ❌ 错误
def test_trading():
    agent.open_position()
    # 跳过平仓和验证
```

**原则：** 测试慢→优化实现，测试难→改进设计

---

## 💰 业务层面

### ⚠️ 铁律5：资金管理必须封装

**必须：** 通过CapitalManager执行事务  
**禁止：** 直接修改capital属性

```python
# ✅ 正确
manager = CapitalManager(agent.capital)
manager.execute_transaction(transaction)

# ❌ 错误
agent.capital.balance = 21000
agent.capital.available += 1000
```

**唯一例外：** 初始化构造函数、测试setup（需注释）

---

### ⚠️ 铁律6：配置驱动，参数可控

**必须：** 所有业务参数从config读取  
**禁止：** 硬编码业务逻辑

```python
# ✅ 正确
threshold = config.evolution.elimination_threshold

# ❌ 错误
threshold = 0.01  # 魔法数字
```

**必须配置化：** 阈值、周期、比例、开关、模式  
**可以硬编码：** 物理常量、数学常数、枚举定义

---

## 📚 文档层面

### ⚠️ 铁律7：重要决策文档化

**必须记录：**
- 架构决策 → `ARCHITECTURE.md`
- 设计权衡 → 对应设计文档
- 变更历史 → `CHANGELOG.md`
- 已知问题 → `KNOWN_ISSUES.md`
- 实验结果 → `experiments/`

**何时记录：** 6个月后可能忘记的决策

---

## 🔍 提交前检查清单

**架构：**
- [ ] 通过统一入口？
- [ ] 向后兼容？

**测试：**
- [ ] 基于标准模板？
- [ ] 完整生命周期？
- [ ] 资金守恒验证？

**业务：**
- [ ] 资金通过Manager？
- [ ] 参数从config读取？

**文档：**
- [ ] 重要决策记录？
- [ ] CHANGELOG更新？

---

## ⚡ 快速自检

开发时问自己：

1. **统一入口？** 99%情况要通过
2. **破坏兼容？** 添加开关
3. **测试完整？** 完整生命周期+资金守恒
4. **直接改capital？** 用Manager
5. **硬编码参数？** 移到config
6. **决策能记住？** 不确定就写文档

---

## 💡 记住

> **规则是自由的边界，遵守它们才能更快、更好、更长久地开发**

**违反铁律？** 
1. 先确认真的需要
2. 与团队讨论
3. 记录决策
4. 必要时修改铁律（不要悄悄违反）

---

*版本：v1.0 | 更新：2024-12-18*
