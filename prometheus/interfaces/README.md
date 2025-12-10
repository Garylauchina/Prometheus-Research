# Prometheus v8.0 Interfaces ⭐⭐⭐

> **设计理念：v7.0是核心，v8.0是外壳**  
> v7.0专注于策略进化，v8.0提供标准化接口与外部世界交互

---

## 📚 三大接口

### 1. MarketDataInterface - 市场数据接口

**职责：** 为Prophet提供统一的市场数据获取接口

**三种实现：**
- `LiveMarketData` - 实盘（从交易所API获取）
- `BacktestMarketData` - 回测（从历史数据文件读取）
- `SimulatedMarketData` - 模拟（生成模拟数据）

**使用示例：**

```python
from prometheus.interfaces import create_market_data

# 实盘
market_data = create_market_data(
    mode='live',
    exchange='okx',
    symbol='BTC-USDT'
)

# 回测
market_data = create_market_data(
    mode='backtest',
    data_file='btc_2024.csv',
    symbol='BTC-USDT'
)

# 模拟
market_data = create_market_data(
    mode='simulation',
    symbol='BTC-USDT',
    scenario='bull'
)

# 获取市场快照
snapshot = market_data.get_current_snapshot()
print(f"价格: {snapshot.price}, 波动率: {snapshot.volatility}")
```

**数据结构：**
```python
@dataclass
class MarketSnapshot:
    timestamp: datetime
    symbol: str
    price: float
    price_change: float
    volatility: float
    volume: float
    # ... 更多字段
```

---

### 2. ExecutionInterface - 交易执行接口

**职责：** 为Moirai提供统一的交易执行接口

**两种实现：**
- `LiveExecution` - 实盘（通过交易所API执行）
- `SimulatedExecution` - 模拟（内存模拟）

**使用示例：**

```python
from prometheus.interfaces import create_execution, OrderSide, OrderType

# 实盘
execution = create_execution(
    mode='live',
    exchange='okx',
    api_key='your_key',
    api_secret='your_secret'
)

# 模拟
execution = create_execution(
    mode='simulation',
    initial_balance=10000.0
)

# 提交订单
order = execution.submit_order(
    agent_id='agent_1',
    symbol='BTC-USDT',
    side=OrderSide.BUY,
    quantity=0.1,
    order_type=OrderType.MARKET
)

# 查询持仓
positions = execution.get_all_positions(agent_id='agent_1')

# 平仓
execution.close_position(agent_id='agent_1', symbol='BTC-USDT')
```

**数据结构：**
```python
@dataclass
class Order:
    order_id: str
    agent_id: str
    symbol: str
    side: OrderSide
    quantity: float
    status: OrderStatus
    # ... 更多字段

@dataclass
class Position:
    symbol: str
    agent_id: str
    quantity: float
    entry_price: float
    unrealized_pnl: float
    # ... 更多字段
```

---

### 3. TrainingInterface - 对抗训练接口

**职责：** 生成对抗性训练场景，测试系统鲁棒性

**实现：**
- `AdversarialTraining` - 对抗训练器

**使用示例：**

```python
from prometheus.interfaces import (
    AdversarialTraining,
    ScenarioType,
    get_standard_test_suite
)

# 创建训练器
trainer = AdversarialTraining()

# 创建单个场景
black_swan = trainer.create_scenario(ScenarioType.BLACK_SWAN)
print(f"场景: {black_swan.name}, 难度: {black_swan.difficulty}/10")

# 获取标准测试套件
scenarios = get_standard_test_suite()
print(f"标准测试: {len(scenarios)}个场景")

# 运行场景（TODO: 需要实现）
# result = trainer.run_scenario(black_swan, your_v7_system)
```

**场景类型：**
- `BULL_MARKET` - 牛市（测试盈利能力）
- `BEAR_MARKET` - 熊市（测试做空和防御）
- `BLACK_SWAN` - 黑天鹅（测试风险控制）
- `FLASH_CRASH` - 闪崩（测试紧急响应）
- `LIQUIDITY_CRISIS` - 流动性枯竭（测试滑点处理）
- `WHIPSAW` - 来回打脸（测试频繁转换）
- `WORST_CASE` - 最坏情况（综合压力测试）

---

## 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Prometheus v7.0 Core                    │
│                    （策略进化核心）                          │
│                                                             │
│  Prophet ←→ Moirai ←→ Agent                                │
│     ↓          ↓         ↓                                  │
│  自省+聆听   种群管理   交易决策                             │
└─────────────────────────────────────────────────────────────┘
         ↓ (只依赖接口)         ↓ (只依赖接口)
┌─────────────────────┐    ┌─────────────────────┐
│  MarketDataInterface│    │  ExecutionInterface │
│  （市场数据）        │    │  （交易执行）        │
└─────────────────────┘    └─────────────────────┘
         ↓                          ↓
┌────────────────────────────────────────────────────────────┐
│               Prometheus v8.0 Interfaces                   │
│               （标准化外壳）                                │
│                                                            │
│  • LiveMarketData      • BacktestMarketData                │
│  • SimulatedMarketData                                     │
│  • LiveExecution       • SimulatedExecution                │
│  • AdversarialTraining                                     │
└────────────────────────────────────────────────────────────┘
         ↓                          ↓
┌─────────────────────┐    ┌─────────────────────┐
│   OKX / Binance     │    │  Historical Data    │
│   （真实交易所）     │    │  （历史数据文件）    │
└─────────────────────┘    └─────────────────────┘
```

---

## 🎯 设计原则

### 1. 依赖倒置原则 (DIP)
- v7.0核心只依赖接口（抽象）
- v8.0实现具体功能
- 可以轻松切换实现，不影响核心

### 2. 开闭原则 (OCP)
- 对扩展开放：新增交易所只需实现接口
- 对修改封闭：v7.0代码不需要修改

### 3. 单一职责原则 (SRP)
- MarketDataInterface：只管数据获取
- ExecutionInterface：只管交易执行
- TrainingInterface：只管训练场景

---

## 📝 实现状态

### ✅ 已完成
- [x] 接口设计（3个接口）
- [x] 数据结构定义（MarketSnapshot, Order, Position等）
- [x] 模拟实现（SimulatedMarketData, SimulatedExecution）
- [x] 场景定义（7种训练场景）
- [x] 工厂函数（create_market_data, create_execution）

### 🚧 待实现（v8.0后续工作）
- [ ] LiveMarketData完整实现（OKX/Binance API）
- [ ] LiveExecution完整实现（真实交易）
- [ ] BacktestMarketData完整实现（历史数据加载）
- [ ] TrainingInterface完整实现（场景运行+结果收集）
- [ ] 更多交易所支持
- [ ] 更多训练场景

---

## 🚀 快速开始

### 场景1：模拟训练（最简单）

```python
# 1. 创建模拟接口
from prometheus.interfaces import create_market_data, create_execution

market_data = create_market_data('simulation', symbol='BTC-USDT')
execution = create_execution('simulation', initial_balance=10000.0)

# 2. 将接口传给v7.0系统
# your_v7_system.set_market_data(market_data)
# your_v7_system.set_execution(execution)

# 3. 运行系统
# your_v7_system.run()
```

### 场景2：历史回测

```python
# 1. 准备历史数据文件（CSV格式）
# timestamp, price, volume, ...

# 2. 创建回测接口
market_data = create_market_data(
    'backtest',
    data_file='data/btc_2024.csv',
    symbol='BTC-USDT'
)
execution = create_execution('simulation')

# 3. 运行回测
# your_v7_system.set_market_data(market_data)
# your_v7_system.set_execution(execution)
# your_v7_system.run_backtest()
```

### 场景3：实盘交易（最谨慎）

```python
# 1. 配置API密钥（⚠️ 谨慎！）
market_data = create_market_data(
    'live',
    exchange='okx',
    symbol='BTC-USDT',
    api_key='your_key'
)
execution = create_execution(
    'live',
    exchange='okx',
    api_key='your_key',
    api_secret='your_secret'
)

# 2. 先小额测试！！！
# your_v7_system.set_market_data(market_data)
# your_v7_system.set_execution(execution)
# your_v7_system.run(capital=100)  # 先用100U测试！
```

---

## 💡 最佳实践

### 1. 测试顺序
1. **模拟训练**（SimulatedMarketData + SimulatedExecution）
2. **历史回测**（BacktestMarketData + SimulatedExecution）
3. **模拟盘测试**（LiveMarketData + SimulatedExecution）
4. **小额实盘**（LiveMarketData + LiveExecution，100U）
5. **逐步加仓**（确认稳定后再增加资金）

### 2. 风险控制
- ⚠️ **永远不要在未经测试的情况下使用LiveExecution**
- ⚠️ **先用SimulatedExecution验证逻辑**
- ⚠️ **实盘初期只用小额资金**
- ⚠️ **设置止损和最大亏损限制**

### 3. 接口选择
- **开发阶段**：SimulatedMarketData + SimulatedExecution
- **回测阶段**：BacktestMarketData + SimulatedExecution
- **实盘阶段**：LiveMarketData + LiveExecution

---

## 📊 接口对比

| 特性 | Simulated | Backtest | Live |
|------|-----------|----------|------|
| 数据来源 | 生成 | 历史文件 | 交易所API |
| 执行速度 | 极快 | 快 | 实时 |
| 成本 | 免费 | 免费 | 手续费 |
| 风险 | 无 | 无 | 高 |
| 真实性 | 低 | 中 | 高 |
| 适用场景 | 开发+训练 | 策略验证 | 真实交易 |

---

## 🔮 未来扩展

### v8.1: 更多交易所
- Binance
- Bybit
- Coinbase

### v8.2: 更多数据源
- TradingView
- CryptoCompare
- CoinGecko

### v8.3: 更多训练场景
- 对冲场景
- 套利场景
- 做市场景

---

## 📞 联系

有问题或建议？欢迎提Issue！

**设计日期：** 2025-12-11  
**设计者：** Prometheus Team  
**版本：** v8.0-alpha

---

**🌟 记住：架构的威力在于分离关注点！v7.0专注策略，v8.0专注交互！**

