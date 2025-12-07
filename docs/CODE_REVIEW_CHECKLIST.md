# Prometheus 代码审查清单

**版本**: v6.0  
**生效日期**: 2025-12-07  
**强制执行**: 所有新代码必须通过此清单检查

---

## 🔒 三大铁律检查 (必须100%通过)

### 铁律1: 统一封装,统一调用,严禁旁路 ✅

**检查项**:
- [ ] 是否使用了 `v6 Facade` 统一入口? (`run_scenario` 或 `build_facade`)
- [ ] 是否避免了自己写循环直接调用底层模块?
- [ ] 是否避免了绕过 Facade 直接 import Supervisor/Moirai?
- [ ] 所有交易是否通过 `agent.account.record_trade` 记录?
- [ ] 是否避免了直接调用 `exchange.place_order`?

**反面案例**:
```python
# ❌ 错误: 自己写循环,绕过 Facade
for step in range(2000):
    supervisor.run_cycle()
    evolution_manager.evolve()
```

**正确做法**:
```python
# ✅ 正确: 使用 Facade 统一入口
facade = run_scenario(
    mode="backtest",
    total_cycles=2000,
    ...
)
```

---

### 铁律2: 严格执行测试规范 ✅

**检查项**:
- [ ] 是否基于标准模板? (`test_ultimate_v6_CORRECT.py` 或 `STANDARD_TEST_TEMPLATE.py`)
- [ ] 是否包含完整的组件初始化?
  - [ ] Supervisor/Moirai
  - [ ] EvolutionManagerV5
  - [ ] BulletinBoard
  - [ ] PublicLedger (通过 Facade 自动)
  - [ ] PrivateLedger (通过 attach_accounts 自动)
- [ ] 是否包含双账簿验证? (`attach_accounts` + 断言检查)
- [ ] 是否包含对账验证? (`facade.reconcile()`)
- [ ] 是否包含结果归档? (results/backtest/<date>/<run_id>/)

**反面案例**:
```python
# ❌ 错误: 自创简化版,省略关键模块
agents = [Agent(...) for _ in range(50)]
for step in range(2000):
    for agent in agents:
        agent.trade()  # 没有账簿!
```

**正确做法**:
```python
# ✅ 正确: 使用完整模板
facade = run_scenario(...)  # 自动初始化所有模块
reconcile_summary = facade.reconcile()  # 对账验证
assert all(len(v) == 0 for v in reconcile_summary.values())
```

---

### 铁律3: 不可为测试通过而简化底层机制 ✅

**检查项**:
- [ ] 交易是否包含完整生命周期? (开仓 → 持仓 → 平仓)
  - [ ] 有开多 (`buy`) 就要有平多 (`sell`)
  - [ ] 有开空 (`short`) 就要有平空 (`cover`)
- [ ] 是否避免了手动修改资金?
  - [ ] 不直接修改 `agent.current_capital`
  - [ ] 不直接修改 `account.private_ledger.virtual_capital`
- [ ] 是否由账簿系统自动计算资金?
  - [ ] 盈亏通过 `record_trade` 自动计算
  - [ ] 资金从 `account.private_ledger.virtual_capital` 读取
- [ ] 进化机制是否完整?
  - [ ] 使用 `EvolutionManagerV5.run_evolution_cycle`
  - [ ] 不省略 Immigration
  - [ ] 不省略 DiversityMonitor

**反面案例**:
```python
# ❌ 错误1: 只开仓不平仓
trade_type = 'buy' if signal > 0 else 'short'
account.record_trade(trade_type=trade_type, ...)  # 从不 sell/cover!

# ❌ 错误2: 手动修改资金
agent.current_capital = new_capital  # 绕过账簿!
account.private_ledger.virtual_capital = new_capital

# ❌ 错误3: 简化进化
# 完全不调用 evolution_manager
```

**正确做法**:
```python
# ✅ 正确1: 完整开平仓
if decision['action'] == 'buy':
    account.record_trade(trade_type='buy', ...)
elif decision['action'] == 'sell':
    account.record_trade(trade_type='sell', ...)  # 平仓!

# ✅ 正确2: 从账簿读取资金
agent.current_capital = account.private_ledger.virtual_capital

# ✅ 正确3: 完整进化
facade.run_cycle(...)  # 自动包含进化
```

---

## 📋 账簿系统检查 (金融系统生命线)

### 账簿一致性 ✅

**检查项**:
- [ ] 每笔交易是否同时写入私账和公账?
- [ ] 是否调用了 `attach_accounts(agents, public_ledger)`?
- [ ] 是否验证了每个 Agent 都有 `agent.account`?
- [ ] 是否验证了每个 `account` 都有 `private_ledger`?
- [ ] 测试结束后是否调用了 `facade.reconcile()`?
- [ ] 对账结果是否全部通过? (无不一致记录)

**代码检查**:
```python
# ✅ 必须在 genesis 后立即执行
attach_accounts(agents, public_ledger)

# ✅ 必须验证账簿挂载
for agent in agents:
    assert hasattr(agent, 'account'), f"Agent {agent.agent_id} 缺少account"
    assert hasattr(agent.account, 'private_ledger'), f"缺少private_ledger"

# ✅ 必须在测试结束后对账
reconcile_summary = facade.reconcile()
has_issues = any(len(v) > 0 for v in reconcile_summary.values())
if has_issues:
    raise Exception("❌ 账簿不一致!")
```

### 交易记录 ✅

**检查项**:
- [ ] 是否通过 `account.record_trade` 记录交易?
- [ ] `amount` 是否 > 0?
- [ ] `price` 是否 > 0?
- [ ] `trade_type` 是否正确? (`buy`/`sell`/`short`/`cover`)
- [ ] 是否避免了创建空记录?

**代码检查**:
```python
# ✅ 正确的交易记录
if amount > 0 and price > 0:
    account.record_trade(
        trade_type='buy',  # 明确的交易类型
        amount=amount,     # > 0
        price=price,       # > 0
        confidence=0.8,
        is_real=False,
        caller_role=Role.SUPERVISOR
    )
```

---

## 🏗️ 架构检查

### v6 Facade 使用 ✅

**检查项**:
- [ ] 是否使用 `run_scenario` 或 `build_facade`?
- [ ] `mode` 参数是否正确? (`backtest`/`okx_paper`/`mock`)
- [ ] `market_feed` 是否提供正确的数据?
- [ ] 是否使用 `facade.run(total_cycles=...)`?
- [ ] 是否使用 `facade.reconcile()` 对账?

### 模块依赖 ✅

**检查项**:
- [ ] 是否避免了循环 import?
- [ ] 是否使用了正确的 import 路径?
```python
# ✅ 正确
from prometheus.facade.v6_facade import run_scenario
from prometheus.core.ledger_system import Role

# ❌ 错误
from prometheus.core.supervisor import Supervisor  # 不应该直接 import
```

---

## 📊 测试质量检查

### 可重复性 ✅

**检查项**:
- [ ] 是否设置了随机种子?
- [ ] 是否保存了完整配置?
- [ ] 是否归档了测试结果?
- [ ] 结果目录是否使用标准格式? (`results/<mode>/<date>/<run_id>/`)

### 错误处理 ✅

**检查项**:
- [ ] 是否捕获了关键异常?
- [ ] 是否在异常时进行了对账?
- [ ] 是否记录了失败原因?
- [ ] 是否避免了静默失败?

**代码检查**:
```python
# ✅ 正确的错误处理
try:
    facade.run(total_cycles=2000)
except Exception as e:
    logger.error(f"测试失败: {e}")
    # 即使失败也要对账
    reconcile_summary = facade.reconcile()
    raise
```

---

## 📝 文档检查

### 代码注释 ✅

**检查项**:
- [ ] 关键决策是否有注释?
- [ ] 复杂逻辑是否有说明?
- [ ] 是否标注了三大铁律的遵守情况?

### 测试文档 ✅

**检查项**:
- [ ] 是否有 docstring 说明测试目的?
- [ ] 是否说明了使用的架构?
- [ ] 是否说明了预期结果?
- [ ] 是否说明了对账标准?

---

## ✅ 审查清单总结

**通过标准**: 所有 ✅ 项目必须 100% 符合

**快速自检**:
1. ⚠️ 我是否使用了 v6 Facade? 
2. ⚠️ 我是否基于标准模板?
3. ⚠️ 我是否包含完整的开平仓逻辑?
4. ⚠️ 我是否避免了手动修改资金?
5. ⚠️ 我是否进行了对账验证?

**如果任何一项答案是"否"**:
- 🛑 **立即停止**
- 📖 重新阅读三大铁律
- 🔧 修改代码直到所有项都是"是"
- ✅ 重新提交审查

---

## 📚 参考文档

- [三大铁律详解](./LEDGER_ISSUES_AND_FIXES.md)
- [V6 Facade 设计](./V6_FACADE_PLAN.md)
- [标准测试模板](../templates/STANDARD_TEST_TEMPLATE.py)
- [正确测试示例](../test_ultimate_v6_CORRECT.py)

---

## 💡 记住

> **"在金融系统中,账簿一致性是不可妥协的底线!"**  
> **"任何小问题都可能导致灾难性后果!"**  
> **"不能为了测试通过就忽略账簿警告!"**

---

**审查人签字**: _______________  
**审查日期**: _______________  
**通过/不通过**: _______________

