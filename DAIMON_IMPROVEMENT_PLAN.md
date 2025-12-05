# Daimon决策系统改进计划

**日期**: 2025-12-05  
**目标**: 让Agent更容易开仓，让fear_of_death在真实环境中发挥作用

---

## 🔍 当前问题诊断

### 问题1：Daimon太保守
```python
# 当前：如果没有任何投票，默认hold
if not all_votes:
    return CouncilDecision(action='hold', ...)
```

**后果**：
- 如果6个声音都不投票，就永远hold
- Agent从不开仓
- fear_of_death无法发挥作用（需要持仓才能触发）

---

### 问题2：缺少"探索"机制
- 当前设计：等待明确信号才行动
- 问题：在模拟测试中，信号可能不够强
- 需要：基于好奇心/风险偏好的探索行为

---

### 问题3：instinct_voice只在"危险时"投票
```python
# instinct_voice当前逻辑：
if fear_level > 1.5 and has_position:
    # 只有濒死+持仓才投票
```

**问题**：
- 如果Agent从不开仓，fear_level永远是0
- instinct_voice从不投票
- risk_appetite和curiosity没有充分利用

---

## 💊 改进方案

### 改进1：增加"探索性开仓"逻辑

**在instinct_voice中添加**：
```python
# 3. 风险偏好 - 探索性开仓（v5.2改进）
if not has_position and capital_ratio > 0.8:
    # 资金充足时，根据风险偏好尝试开仓
    if instinct.risk_appetite > 0.6:
        # 高风险偏好：60%以上，倾向开仓
        votes.append(Vote(
            action='buy',  # 默认做多
            confidence=instinct.risk_appetite * 0.6,
            voter_category='instinct',
            reason=f"风险偏好({instinct.risk_appetite:.1%}): 探索性开仓"
        ))
```

**效果**：
- 高risk_appetite的Agent会主动开仓
- 低risk_appetite的Agent保持观望
- fear_of_death现在有机会发挥作用

---

### 改进2：增加"好奇心"驱动

**在instinct_voice中添加**：
```python
# 4. 好奇心 - 尝试新策略（v5.2改进）
if instinct.curiosity > 0.7 and not has_position:
    # 高好奇心：偶尔尝试新方向
    action = random.choice(['buy', 'sell'])
    votes.append(Vote(
        action=action,
        confidence=instinct.curiosity * 0.4,
        voter_category='instinct',
        reason=f"好奇心({instinct.curiosity:.1%}): 尝试{action}"
    ))
```

**效果**：
- 高curiosity的Agent会尝试不同方向
- 增加行为多样性

---

### 改进3：降低fear_of_death触发阈值

**当前阈值太高**：
```python
if fear_level > 1.5 and has_position:
    # 需要资金<30%才触发
```

**改进：动态阈值**：
```python
# v5.2改进：根据fear_of_death动态调整阈值
fear_threshold = 2.5 - instinct.fear_of_death
# 高恐惧(1.8): threshold=0.7 → 资金<65%就触发
# 低恐惧(0.3): threshold=2.2 → 资金<20%才触发

if fear_level > fear_threshold and has_position:
    # 高恐惧者更早平仓
    votes.append(Vote(...))
```

**效果**：
- 高fear_of_death的Agent更容易触发平仓
- 低fear_of_death的Agent很难触发
- **明确的行为差异**

---

### 改进4：增加"无聊惩罚"

**问题**：Agent可能长期hold，没有任何action

**改进**：
```python
# 5. 无聊惩罚 - 鼓励交易（v5.2改进）
idle_cycles = context.get('idle_cycles', 0)
if idle_cycles > 5 and not has_position:
    # 5轮没交易，降低hold吸引力
    boredom_factor = min(idle_cycles / 10, 0.5)
    votes.append(Vote(
        action='buy',  # 尝试开仓
        confidence=boredom_factor,
        voter_category='instinct',
        reason=f"无聊{idle_cycles}轮: 尝试交易"
    ))
```

**效果**：
- 防止Agent永远hold
- 鼓励探索和交易

---

## 🎯 实施顺序

### Phase 1：核心改进（立即）
1. ✅ **改进3**：降低fear_of_death触发阈值
   - 最关键：让高低恐惧有差异
   - 风险低：只改阈值

2. ✅ **改进1**：增加探索性开仓
   - 让Agent基于risk_appetite开仓
   - 中等风险：需要平衡参数

### Phase 2：增强改进（可选）
3. **改进2**：好奇心驱动
   - 增加多样性
   - 低风险：可选功能

4. **改进4**：无聊惩罚
   - 防止永远hold
   - 低风险：可选功能

---

## 📝 代码修改清单

### 文件1：`prometheus/core/inner_council.py`

#### 修改位置：`_instinct_voice`方法

```python
def _instinct_voice(self, context: Dict) -> List[Vote]:
    votes = []
    instinct = self.agent.instinct
    
    capital_ratio = context.get('capital_ratio', 1.0)
    recent_pnl = context.get('recent_pnl', 0)
    consecutive_losses = context.get('consecutive_losses', 0)
    position = context.get('position', {})
    has_position = position.get('amount', 0) != 0
    
    # 1. 死亡恐惧（v5.2改进：动态阈值）
    fear_level = instinct.calculate_death_fear_level(capital_ratio, consecutive_losses)
    fear_threshold = 2.5 - instinct.fear_of_death  # 新增！
    
    if fear_level > fear_threshold and has_position:  # 修改！
        # 高恐惧者更容易触发
        votes.append(Vote(
            action='close',
            confidence=min(fear_level / 3.0, 0.95),
            voter_category='instinct',
            reason=f"死亡恐惧({fear_level:.1f}>阈值{fear_threshold:.1f}): 资金仅剩{capital_ratio:.1%}"
        ))
    
    # 2. 损失厌恶（保持不变）
    if recent_pnl < -0.05 and has_position:
        loss_aversion_strength = instinct.loss_aversion
        votes.append(Vote(...))
    
    # 3. 风险偏好 - 探索性开仓（新增！v5.2）
    if not has_position and capital_ratio > 0.8:
        if instinct.risk_appetite > 0.6:
            # 高风险偏好：主动开仓
            votes.append(Vote(
                action='buy',
                confidence=instinct.risk_appetite * 0.6,
                voter_category='instinct',
                reason=f"风险偏好({instinct.risk_appetite:.1%}): 探索性开仓"
            ))
        elif instinct.risk_appetite < 0.3:
            # 低风险偏好：强化观望
            votes.append(Vote(
                action='hold',
                confidence=(1 - instinct.risk_appetite) * 0.6,
                voter_category='instinct',
                reason=f"风险偏好({instinct.risk_appetite:.1%}): 保守观望"
            ))
    
    return votes
```

---

## 🧪 验证测试

### 测试1：重新运行v2测试
```bash
python test_fear_extreme_market_v2.py
```

**期待结果**：
- Agent不再全都hold
- 高risk_appetite的Agent会开仓
- 高fear_of_death的Agent会更早平仓
- 低fear_of_death的Agent会更晚平仓

---

### 测试2：新的对比测试
创建一个测试，对比：
- 高恐惧+高风险 vs 低恐惧+低风险
- 观察开仓率和平仓时机的差异

---

## 🎯 成功标准

### 最低标准
- ✅ Agent能够开仓（不再全都hold）
- ✅ 高恐惧Agent更早平仓
- ✅ 低恐惧Agent更晚平仓（或不平仓）

### 理想标准
- ⭐ 开仓率与risk_appetite正相关
- ⭐ 平仓时机与fear_of_death负相关
- ⭐ fear_of_death在真实Daimon决策中发挥作用

---

## 📊 风险评估

### 风险1：过度开仓
- **问题**：如果所有Agent都疯狂开仓
- **缓解**：设置confidence较低（0.6），其他声音可以抵消

### 风险2：破坏现有平衡
- **问题**：改动Daimon可能影响其他功能
- **缓解**：只修改instinct_voice，不影响其他声音

### 风险3：参数需要调优
- **问题**：阈值和confidence可能需要调整
- **缓解**：从保守参数开始，逐步调整

---

## 🎊 预期影响

### 对fear_of_death实验的影响
- ✅ fear_of_death将在真实Daimon决策中发挥作用
- ✅ 高低恐惧的差异将在真实环境中显现
- ✅ 完成"路径B实验"的最后一步

### 对整个系统的影响
- ✅ Agent行为更多样化
- ✅ 交易更活跃
- ✅ 进化压力更明显

---

**开始实施时间**: 现在  
**预计完成时间**: 30分钟  
**实施者**: AI助手

Let's do it! 💪

