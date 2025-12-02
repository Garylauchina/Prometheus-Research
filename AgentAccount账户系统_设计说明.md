# Agent账户系统 - 设计说明

## 📅 日期
2025-12-02

---

## 🎯 **设计理念**

> **"Agent必须记得自己的交易记录和持仓情况，才能向Supervisor正确提交申请。Supervisor还要与账户系统核查Agent的请求是否正确。"**
> 
> —— 用户核心理念

---

## 🏗️ **架构设计**

### **三层架构**

```
┌─────────────────────────────────────────┐
│  Agent (决策者)                          │
│  ├─ 拥有账户引用                          │
│  ├─ 查询账户状态                          │
│  ├─ 根据状态决策                          │
│  └─ 提交合法请求                          │
└──────────────┬──────────────────────────┘
               │ 访问
               ↓
┌─────────────────────────────────────────┐
│  AgentAccount (账户系统)                 │
│  ├─ 虚拟资金 (10,000 USDT)               │
│  ├─ 虚拟持仓 []                          │
│  ├─ 实际持仓 Position                    │
│  ├─ 交易历史 []                          │
│  ├─ 统计数据 (PnL, 胜率...)              │
│  ├─ 状态查询接口                          │
│  └─ 合法性检查                            │
└──────────────┬──────────────────────────┘
               │ 管理
               ↓
┌─────────────────────────────────────────┐
│  Supervisor (运营者+审核者)              │
│  ├─ 创建和管理所有账户                    │
│  ├─ 接收Agent请求                        │
│  ├─ 核查请求合法性 ⭐                    │
│  ├─ 执行交易                             │
│  └─ 更新账户状态                         │
└─────────────────────────────────────────┘
```

---

## 💻 **AgentAccount核心接口**

### **1. 状态查询**

```python
# Agent决策时调用
account.has_virtual_position() → bool
account.has_real_position() → bool
account.get_unrealized_pnl(current_price) → float
account.get_summary(current_price) → Dict
```

### **2. 合法性检查**

```python
# Supervisor验证请求时调用
account.can_buy(amount, price) → (bool, str)
account.can_sell() → (bool, str)
```

### **3. 交易记录**

```python
# Supervisor执行交易后调用
account.record_virtual_buy(amount, price, confidence)
account.record_virtual_sell(current_price, confidence) → pnl
account.record_real_buy(amount, price, confidence)
account.record_real_sell(current_price, confidence) → pnl
```

---

## 🔄 **完整工作流程**

### **周期N：Agent决策**

```python
class LiveAgentV4:
    def decide(self, current_price):
        """决策时查询账户"""
        
        # 1. 获取自己的账户状态
        account_status = self.account.get_summary(current_price)
        
        # 2. 根据状态决策
        if account_status['has_real_position']:
            # 已有持仓，考虑平仓
            unrealized_pnl = account_status['unrealized_pnl']
            
            # 止盈
            if unrealized_pnl > 100:
                return {
                    'signal': 'sell',
                    'confidence': 0.9,
                    'reason': f'止盈 (浮盈${unrealized_pnl:.2f})'
                }
            
            # 止损
            elif unrealized_pnl < -50:
                return {
                    'signal': 'sell',
                    'confidence': 1.0,
                    'reason': f'止损 (浮亏${unrealized_pnl:.2f})'
                }
            
            # 继续持有
            else:
                return {
                    'signal': None,
                    'confidence': 0.0,
                    'reason': f'持仓中 (浮盈${unrealized_pnl:.2f})'
                }
        else:
            # 无持仓，考虑开仓
            # 检查是否有足够资金
            can_buy, reason = self.account.can_buy(0.01, current_price)
            
            if not can_buy:
                return {
                    'signal': None,
                    'confidence': 0.0,
                    'reason': reason
                }
            
            # 分析市场
            market_analysis = self._analyze_market_from_bulletins()
            
            if market_analysis['should_buy']:
                return {
                    'signal': 'buy',
                    'confidence': market_analysis['confidence'],
                    'reason': market_analysis['reason']
                }
            else:
                return {
                    'signal': None,
                    'confidence': 0.0,
                    'reason': '市场条件不符'
                }
```

---

### **Supervisor接收并验证请求**

```python
class Supervisor:
    def receive_trade_request(self, agent_id, signal, confidence, current_price):
        """接收并验证交易请求"""
        
        # 1. 获取Agent账户
        account = self.agent_accounts.get(agent_id)
        if not account:
            logger.error(f"{agent_id}: 账户不存在")
            return False
        
        # 2. 验证请求合法性（核心！）
        if signal == 'buy':
            can_buy, reason = account.can_buy(0.01, current_price)
            if not can_buy:
                logger.warning(f"{agent_id}: 买入请求被拒绝 - {reason}")
                return False
            
            logger.info(f"✅ {agent_id}: 买入请求验证通过")
            return self._execute_buy_and_update(account, current_price, confidence)
        
        elif signal == 'sell':
            can_sell, reason = account.can_sell()
            if not can_sell:
                logger.warning(f"{agent_id}: 卖出请求被拒绝 - {reason}")
                return False
            
            logger.info(f"✅ {agent_id}: 卖出请求验证通过")
            return self._execute_sell_and_update(account, current_price, confidence)
        
        return False
    
    def _execute_buy_and_update(self, account, current_price, confidence):
        """执行买入并更新账户"""
        amount = 0.01
        
        # 1. 执行实际交易
        order = self.okx_trading.place_market_order(
            symbol='BTC/USDT:USDT',
            side='buy',
            amount=amount
        )
        
        if order:
            # 2. 更新虚拟账户
            account.record_virtual_buy(amount, current_price, confidence)
            
            # 3. 更新实际持仓
            account.record_real_buy(amount, current_price, confidence)
            
            logger.info(f"✅ {account.agent_id}: 交易执行成功，账户已更新")
            return True
        
        return False
```

---

## 📊 **数据流示例**

### **场景：Agent决策买入**

```
Step 1: Agent查询账户
────────────────────────────
Agent_01: account.get_summary(90500.0)
返回: {
    'virtual_capital': 10000.0,
    'has_real_position': False,  ← Agent知道自己没有持仓
    'unrealized_pnl': 0.0,
    ...
}

Step 2: Agent决策
────────────────────────────
Agent_01: 分析市场 → 上涨趋势
         检查账户 → 无持仓，有资金
         决定买入 → 返回 {'signal': 'buy', 'confidence': 0.75}

Step 3: 提交请求
────────────────────────────
supervisor.receive_trade_request(
    agent_id='Agent_01',
    signal='buy',
    confidence=0.75,
    current_price=90500.0
)

Step 4: Supervisor验证
────────────────────────────
account = agent_accounts['Agent_01']
can_buy, reason = account.can_buy(0.01, 90500.0)
→ 检查资金: 10000 >= 905 ✅
→ 检查持仓: has_real_position = False ✅
→ 检查冷却: 无最近交易 ✅
→ 返回: (True, "可以买入")

Step 5: 执行交易
────────────────────────────
okx.place_market_order('BTC/USDT:USDT', 'buy', 0.01)
→ ✅ 订单成功

Step 6: 更新账户
────────────────────────────
account.record_virtual_buy(0.01, 90500.0, 0.75)
→ virtual_positions.append(Position(...))
→ trade_count += 1

account.record_real_buy(0.01, 90500.0, 0.75)
→ real_position = Position(...)
→ has_real_position = True

Step 7: 下次决策
────────────────────────────
Agent_01: account.get_summary(90800.0)
返回: {
    'has_real_position': True,  ← Agent知道自己有持仓了
    'unrealized_pnl': 3.0,  ← (90800-90500) * 0.01 = 3
    ...
}

Agent_01: 看到有持仓且浮盈$3
         决定继续持有 → {'signal': None}
```

---

## 🎯 **核心优势**

### **1. Agent智能决策**

**修改前（盲目）**：
```python
Agent: 分析市场 → 决定买入
      (不知道自己是否已有持仓)
      → 提交买入请求
      → Supervisor拒绝（已有持仓）
      → 无效决策
```

**修改后（智能）**：
```python
Agent: 查询账户 → has_real_position = True
      → 不会提交买入请求
      → 考虑是否平仓
      → 有效决策
```

### **2. Supervisor严格验证**

```python
接收请求时:
  ✅ 检查账户是否存在
  ✅ 检查资金是否足够
  ✅ 检查持仓状态
  ✅ 检查冷却期
  ✅ 验证请求合法性
  
  只有通过所有检查才执行
```

### **3. 数据完整一致**

```
所有数据集中在AgentAccount:
  ├─ 虚拟交易
  ├─ 实际交易
  ├─ 持仓状态
  └─ 统计数据
  
  ✅ 单一数据源
  ✅ 不会不一致
  ✅ 易于查询
```

---

## 🚀 **实施计划**

### **第1步：Supervisor使用AgentAccount**

需要修改：
1. 用 `AgentAccount` 替代分散的字典
2. 更新 `receive_trade_request` 使用 `can_buy/can_sell`
3. 更新交易记录方法

### **第2步：Agent访问账户**

需要修改：
1. Agent初始化时接收账户引用
2. Agent决策时查询账户状态
3. Agent根据账户状态做决策

### **第3步：测试验证**

验证：
1. Agent能否正确查询账户
2. Supervisor能否正确验证请求
3. 账户状态是否正确更新

---

## 💡 **我的建议**

这是一个重要的架构改进，建议：

**立即实施？**
- ✅ **是** - 完善账户系统，实现正确的架构
- ⏸️ **稍后** - 先测试当前版本，确保基本功能正常

**您希望我立即实施AgentAccount集成吗？** 🚀
