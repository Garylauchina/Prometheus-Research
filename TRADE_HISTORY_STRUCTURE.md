# 交易历史记录结构说明

## ✅ 完整可追溯系统

### 数据结构

#### 1. 交易记录 (Trade Record)
```json
{
  "trade_id": 1,
  "type": "open_long",
  "side": "buy",
  "price": 87700.00,
  "amount": 0.001,
  "time": "2025-12-02T18:55:44",
  "timestamp": "2025-12-02 18:55:44",
  
  // ✅ 关键：可追溯到Agent
  "supporting_agents": [
    "LiveAgent_01",
    "LiveAgent_03",
    "LiveAgent_05"
  ],
  
  // ✅ 完整信号信息
  "all_signals": [
    {
      "agent_id": "LiveAgent_01",
      "signal": "buy",
      "confidence": 0.75
    },
    {
      "agent_id": "LiveAgent_03",
      "signal": "buy",
      "confidence": 0.80
    },
    {
      "agent_id": "LiveAgent_05",
      "signal": "buy",
      "confidence": 0.85
    }
  ],
  
  // ✅ 决策信息
  "consensus_confidence": 0.60,
  
  // ✅ 市场状态
  "market_state": {
    "trend": "上涨",
    "change_pct": 1.13,
    "volatility": 0.0009
  },
  
  // ✅ 交易所订单信息
  "order_info": {
    "id": "12345678",
    "status": "closed",
    "filled": 0.001
  }
}
```

#### 2. 平仓记录 (Close Position Record)
```json
{
  "trade_id": 2,
  "type": "close_position",
  "side": "sell",
  "price": 88200.00,
  "amount": 0.001,
  "time": "2025-12-02T19:15:44",
  "timestamp": "2025-12-02 19:15:44",
  
  "supporting_agents": ["LiveAgent_02", "LiveAgent_04"],
  "all_signals": [...],
  "consensus_confidence": 0.65,
  "market_state": {...},
  "order_info": {...},
  
  // ✅ 关联信息
  "related_open_trade_id": 1,
  "entry_price": 87700.00,
  "exit_price": 88200.00,
  "pnl": 50.00,
  "holding_time": 20.0  // 分钟
}
```

---

## 📊 可追溯性保证

### 能回答的问题

#### ✅ 1. 哪个Agent参与了这笔交易？
```python
trade = trade_history[0]
print(trade['supporting_agents'])
# ['LiveAgent_01', 'LiveAgent_03', 'LiveAgent_05']
```

#### ✅ 2. 各Agent的信心度是多少？
```python
for signal in trade['all_signals']:
    print(f"{signal['agent_id']}: {signal['confidence']}")
# LiveAgent_01: 0.75
# LiveAgent_03: 0.80
# LiveAgent_05: 0.85
```

#### ✅ 3. 当时的市场状态？
```python
print(trade['market_state'])
# {'trend': '上涨', 'change_pct': 1.13, 'volatility': 0.0009}
```

#### ✅ 4. 这笔交易盈亏如何？
```python
close_trade = trade_history[1]
print(f"盈亏: ${close_trade['pnl']:.2f}")
print(f"持仓时间: {close_trade['holding_time']:.1f}分钟")
```

#### ✅ 5. 某个Agent的所有交易？
```python
agent_trades = [
    t for t in trade_history 
    if 'LiveAgent_01' in t['supporting_agents']
]
```

---

## 📁 文件保存

### 自动保存
```
测试结束时自动保存：trade_history_20251202_185544.json
```

### 文件内容
```json
{
  "summary": {
    "total_signals": 150,
    "executed_trades": 10,
    "successful_trades": 6,
    "failed_trades": 4,
    "total_pnl": 125.50
  },
  
  "trades": [
    { /* 交易1 */ },
    { /* 交易2 */ },
    ...
  ],
  
  "agent_info": [
    {
      "agent_id": "LiveAgent_01",
      "personality": {
        "aggression": 0.8,
        "risk_tolerance": 0.9,
        "adaptability": 0.7
      }
    },
    ...
  ]
}
```

---

## 🔍 数据分析示例

### 分析Agent表现
```python
import json

# 加载数据
with open('trade_history_20251202_185544.json', 'r') as f:
    data = json.load(f)

# 统计各Agent参与次数
from collections import Counter
agent_participation = Counter()

for trade in data['trades']:
    for agent_id in trade['supporting_agents']:
        agent_participation[agent_id] += 1

print("Agent参与统计：")
for agent_id, count in agent_participation.most_common():
    print(f"  {agent_id}: {count}次")
```

### 分析盈亏来源
```python
# 统计每个Agent支持的交易盈亏
agent_pnl = {}

for trade in data['trades']:
    if trade['type'] == 'close_position':
        pnl = trade['pnl']
        for agent_id in trade['supporting_agents']:
            if agent_id not in agent_pnl:
                agent_pnl[agent_id] = []
            agent_pnl[agent_id].append(pnl)

for agent_id, pnls in agent_pnl.items():
    total_pnl = sum(pnls)
    win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
    print(f"{agent_id}: 盈亏${total_pnl:.2f}, 胜率{win_rate:.1f}%")
```

---

## 🛡️ 防丢失机制

### 1. 内存存储
```python
self.trade_history = []  # 实时存储
```

### 2. 自动保存
```python
# 测试结束自动保存
def _print_final_summary(self):
    if self.trade_history:
        self.save_trade_history()
```

### 3. 手动保存
```python
# 可随时调用
prometheus.save_trade_history('my_backup.json')
```

### 4. 关联性
```python
# 开仓和平仓通过trade_id关联
close_trade['related_open_trade_id'] = open_trade['trade_id']
```

---

## ✅ 总结

### 可追溯性：100%
- ✅ 每笔交易都记录参与的Agent
- ✅ 每个Agent的决策信心度都保留
- ✅ 市场状态完整记录
- ✅ 开仓平仓可关联
- ✅ 自动保存到文件

### 不会丢失的数据
- ✅ Agent ID列表
- ✅ 信号详情（signal + confidence）
- ✅ 市场状态
- ✅ 时间戳
- ✅ 盈亏信息
- ✅ 持仓时长

### 可回答的问题
- ✅ 谁参与了这笔交易？
- ✅ 为什么做出这个决策？
- ✅ 各Agent的贡献如何？
- ✅ 哪个Agent最赚钱？
- ✅ 哪个Agent最谨慎？

**完全可追溯，不会出现无法回溯的情况！** ✅

