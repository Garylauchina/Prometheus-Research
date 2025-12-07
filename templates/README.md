# 📋 Prometheus 标准测试模板

## 🎯 目的

提供一个**完整架构**的测试模板，确保所有核心模块都被正确使用。

**架构完整性**: A (9/10)

## ✅ 包含的核心模块（9/10）

1. ✅ **Supervisor** - 监督层核心
2. ✅ **Mastermind** - 战略层核心
3. ✅ **BulletinBoard** - 信息架构
4. ✅ **PublicLedger** - 公共账簿（自动初始化）
5. ✅ **PrivateLedger** - 私有账簿（自动初始化）
6. ✅ **Moirai** - 生命周期（Supervisor内部）
7. ✅ **EvolutionManager** - 进化管理（Supervisor内部）
8. ✅ **AgentV5/AgentV4** - Agent
9. ✅ **OKXExchange/回测引擎** - 交易执行
10. ⚪ **WorldSignature** - 市场感知（可选）

## 📖 使用方法

### **方法1：直接运行模板**

```bash
python templates/STANDARD_TEST_TEMPLATE.py
```

### **方法2：基于模板创建新测试**

```bash
# 1. 复制模板
cp templates/STANDARD_TEST_TEMPLATE.py test_my_new_test.py

# 2. 修改配置
vim test_my_new_test.py  # 修改main()中的config

# 3. 运行测试
python test_my_new_test.py
```

### **方法3：在代码中导入**

```python
from templates.STANDARD_TEST_TEMPLATE import StandardTestRunner

config = {
    'trading_mode': 'okx_sandbox',
    'agent_count': 50,
    'duration_cycles': 1000,
}

runner = StandardTestRunner(config)
runner.run()
```

## ⚠️ 重要原则

### **不要省略核心模块！**

❌ **错误做法**：
```python
# 为了"简化"删除Supervisor
# agents = [Agent() for _ in range(10)]
# for agent in agents:
#     agent.current_capital *= (1 + return)  # 直接更新资金
```

✅ **正确做法**：
```python
# 使用Supervisor.genesis()自动初始化完整架构
supervisor = Supervisor(bulletin_board=bulletin_board)
genesis_result = supervisor.genesis(...)
# ✅ 自动初始化双账簿系统
# ✅ 自动挂载agent.account
```

### **始终使用账簿系统！**

❌ **错误做法**：
```python
# 直接修改agent.current_capital
agent.current_capital -= trade_cost
```

✅ **正确做法**：
```python
# 通过账簿系统记录交易
agent.account.record_trade(
    trade_type='buy',
    amount=size,
    price=price,
    confidence=0.8,
    is_real=True,
    caller_role='SUPERVISOR'
)
# 同步资金
agent.current_capital = agent.account.private_ledger.virtual_capital
```

## 🔧 配置说明

### **基本配置**

```python
config = {
    # 交易模式
    'trading_mode': 'okx_sandbox',  # okx_sandbox | okx_real | backtest
    
    # Agent配置
    'agent_count': 10,              # Agent数量
    'initial_capital_per_agent': 10000.0,  # 每个Agent初始资金
    
    # 测试配置
    'duration_cycles': 100,         # 测试周期数
    'cycle_delay': 1,               # 每周期延迟（秒）
    
    # 总资金
    'total_capital': 100000.0,
}
```

### **回测模式配置**

```python
config = {
    'trading_mode': 'backtest',
    'backtest_data_path': 'data/okx/BTC-USDT-SWAP_1h.csv',
    'backtest_start_date': '2023-01-01',
    'backtest_end_date': '2023-12-31',
    # ... 其他配置
}
```

## 📊 架构对比

### **模板架构（完整）**

```
StandardTestRunner
├── Supervisor (genesis)
│   ├── PublicLedger (自动)
│   ├── AgentAccountSystem (自动)
│   │   └── PrivateLedger (自动)
│   ├── Moirai (内部)
│   └── EvolutionManager (内部)
├── Mastermind
├── BulletinBoard
├── AgentV5 (多个)
│   └── account (自动挂载)
└── OKXExchange

评分：A (9/10)
```

### **典型错误架构（简化）**

```
简化测试
├── Moirai
├── EvolutionManager
└── AgentV5 (多个)
    └── current_capital (直接更新)

评分：D (3/10)
结果：不可信！
```

## 🎯 使用场景

### **场景1：性能评估测试**

使用完整架构评估系统真实性能：

```python
config = {
    'trading_mode': 'okx_sandbox',
    'agent_count': 50,
    'duration_cycles': 1000,
}
runner = StandardTestRunner(config)
runner.run()
```

### **场景2：历史回测**

使用历史数据验证策略：

```python
config = {
    'trading_mode': 'backtest',
    'backtest_data_path': 'data/okx/BTC-USDT-SWAP_1h.csv',
    'agent_count': 50,
}
runner = StandardTestRunner(config)
runner.run()
```

### **场景3：实盘前验证**

在实盘前进行完整验证：

```python
config = {
    'trading_mode': 'okx_sandbox',
    'agent_count': 20,
    'duration_cycles': 500,
}
runner = StandardTestRunner(config)
runner.run()
```

## 📚 相关文档

- **ARCHITECTURE_AUDIT_2025.md** - 架构审计报告
- **CODE_AUDIT_REPORT.md** - 代码审计报告
- **AUDIT_SUMMARY.md** - 审计总结

## ✅ 检查清单

使用此模板前，确认：

- [ ] 理解为什么需要完整架构
- [ ] 理解双账簿系统的重要性
- [ ] 不会为了"简化"删除核心模块
- [ ] 使用Supervisor.genesis()初始化
- [ ] 使用account.record_trade()记录交易
- [ ] 使用agent.account.private_ledger获取状态

## 🚨 常见错误

### **错误1：省略Supervisor**

```python
# ❌ 错误
moirai = Moirai()
agents = moirai._genesis_create_agents(...)
# 没有Supervisor，没有监督，没有风控
```

```python
# ✅ 正确
supervisor = Supervisor(bulletin_board=bulletin_board)
genesis_result = supervisor.genesis(...)
# 完整架构，自动初始化所有系统
```

### **错误2：省略双账簿**

```python
# ❌ 错误
agent.current_capital *= (1 + return)
# 没有交易记录，无法追踪，无法核对
```

```python
# ✅ 正确
agent.account.record_trade(...)
agent.current_capital = agent.account.private_ledger.virtual_capital
# 有完整的交易记录和核对机制
```

### **错误3：省略BulletinBoard**

```python
# ❌ 错误
decision = agent.decide(price)
# Agent"盲目"决策，没有市场信息，没有战略指导
```

```python
# ✅ 正确
# Supervisor发布市场分析 → BulletinBoard
# Mastermind发布战略 → BulletinBoard
decision = agent.decide(market_data)
# Agent基于完整信息做出明智决策
```

## 💡 最佳实践

1. **始终使用完整架构** - 即使测试简单功能
2. **始终使用账簿系统** - 即使只有1个Agent
3. **始终记录交易** - 即使是模拟交易
4. **定期审计测试** - 确保架构完整性
5. **不要追求"快速"** - 追求"正确"

---

**记住：完整架构 = 可信结果**  
**简化架构 = 浪费时间**

