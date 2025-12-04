# 滑点模型集成指南

## 概述

滑点模型已完成开发和测试，现在需要集成到交易执行系统中。

---

## 集成位置

**主要集成点：`Supervisor._execute_agent_decision()`**

这是Agent决策被执行为实际交易的地方。

```
Agent决策 → Supervisor验证 → [滑点计算] → 实际成交 → 更新账户
```

---

## 集成步骤

### 1. 在Supervisor中初始化滑点模型

```python
# prometheus/core/supervisor.py

from .slippage_model import create_slippage_model, MarketCondition, OrderSide, OrderType

class Supervisor:
    def __init__(self, ...):
        # ... 现有初始化 ...
        
        # 添加滑点模型
        self.slippage_model = create_slippage_model("realistic")
        logger.info("滑点模型已启用（真实市场模式）")
```

### 2. 在执行交易时应用滑点

```python
def _execute_agent_decision(self, agent, decision, market_data):
    """执行Agent的交易决策（应用滑点）"""
    
    # 1. 获取决策参数
    action = decision['action']
    size_usd = decision['size']
    expected_price = market_data['close'].iloc[-1]
    
    # 2. 构建市场条件
    market_condition = MarketCondition(
        price=expected_price,
        volume=market_data['volume'].iloc[-1],
        volatility=self._calculate_volatility(market_data),  # 需要实现
        liquidity_depth=self._estimate_liquidity(market_data),  # 需要实现
        spread=self._calculate_spread(market_data)  # 需要实现
    )
    
    # 3. 计算滑点
    if action == 'buy':
        order_side = OrderSide.BUY
    elif action == 'sell':
        order_side = OrderSide.SELL
    else:
        return  # hold/close 不需要滑点
    
    slippage_result = self.slippage_model.calculate_slippage(
        order_side=order_side,
        order_size_usd=size_usd,
        order_type=OrderType.MARKET,  # 假设都是市价单
        market_condition=market_condition
    )
    
    # 4. 使用实际成交价格（包含滑点）
    actual_price = slippage_result.actual_price
    slippage_cost = slippage_result.slippage_amount
    
    # 5. 执行交易（使用实际价格）
    # ... 现有交易执行逻辑，但使用actual_price ...
    
    # 6. 记录滑点成本
    agent.total_slippage_cost += slippage_cost
    
    logger.debug(
        f"{agent.agent_id} {action} | "
        f"预期价=${expected_price:.2f} | "
        f"实际价=${actual_price:.2f} | "
        f"滑点={slippage_result.slippage_rate:.3%}"
    )
```

### 3. 添加市场条件计算辅助方法

```python
def _calculate_volatility(self, market_data, window=20):
    """计算市场波动率"""
    returns = market_data['close'].pct_change().dropna()
    if len(returns) < window:
        return 0.02  # 默认2%
    return returns.tail(window).std()

def _estimate_liquidity(self, market_data):
    """估算市场流动性深度"""
    avg_volume = market_data['volume'].tail(20).mean()
    # 假设流动性深度 = 平均成交量 × 当前价格
    current_price = market_data['close'].iloc[-1]
    return avg_volume * current_price

def _calculate_spread(self, market_data):
    """计算买卖价差"""
    # 如果有high/low数据，可以估算
    if 'high' in market_data.columns and 'low' in market_data.columns:
        recent_hl_diff = (market_data['high'] - market_data['low']).tail(20).mean()
        current_price = market_data['close'].iloc[-1]
        return recent_hl_diff / current_price
    else:
        return 0.0002  # 默认0.02%
```

### 4. 在Agent中记录滑点成本

```python
# prometheus/core/agent_v5.py

class AgentV5:
    def __init__(self, ...):
        # ... 现有属性 ...
        
        # 添加滑点成本追踪
        self.total_slippage_cost = 0.0  # 累计滑点成本
```

---

## 测试集成

创建测试脚本验证集成：

```python
# test_slippage_integration.py

from prometheus.core.supervisor import Supervisor
from prometheus.core.agent_v5 import AgentV5
import pandas as pd

# 1. 创建Supervisor（应该自动初始化滑点模型）
supervisor = Supervisor(...)

# 2. 创建测试Agent
agent = AgentV5.create_genesis(...)

# 3. 模拟交易决策
decision = {
    'action': 'buy',
    'size': 10000,
    'agent_id': agent.agent_id
}

# 4. 执行决策（应该自动应用滑点）
market_data = pd.DataFrame(...)  # 模拟市场数据
supervisor._execute_agent_decision(agent, decision, market_data)

# 5. 检查滑点成本
print(f"滑点成本: ${agent.total_slippage_cost:.2f}")
assert agent.total_slippage_cost > 0, "滑点成本应该>0"
```

---

## 配置选项

可以通过配置文件选择滑点模型：

```python
# config.py

SLIPPAGE_MODEL = "realistic"  # "realistic", "low", "base", "none"
```

```python
# supervisor.py

if config.SLIPPAGE_MODEL == "none":
    self.slippage_model = None  # 禁用滑点
else:
    self.slippage_model = create_slippage_model(config.SLIPPAGE_MODEL)
```

---

## 影响评估

启用滑点后，Agent会面临：
1. ✅ **更真实的市场环境**
2. ✅ **交易成本增加** - Agent必须学会减少不必要的交易
3. ✅ **大单惩罚** - Agent必须学会仓位管理
4. ✅ **进化压力增加** - 只有真正优秀的策略才能盈利

---

## 下一步

1. 实现Supervisor中的集成代码
2. 添加市场条件计算方法
3. 更新Agent类添加滑点成本追踪
4. 运行集成测试
5. 运行完整进化测试（500+代）观察影响

---

## 注意事项

- **回测数据兼容性**: 确保历史数据有足够信息计算波动率和流动性
- **性能影响**: 滑点计算很快（<1ms），不会影响性能
- **参数调优**: 可能需要根据实际交易结果调整滑点模型参数

