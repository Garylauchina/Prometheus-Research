# Prometheus AlphaZero式简化方案
## 2025-12-07 晚 - 回归本质

---

## 🎯 核心理念

```
AlphaZero的成功配方：
简单规则 + 海量博弈 = 涌现智能

我们的目标：
极简机制 + 海量训练 = 自然规律
```

---

## 📊 当前系统分析

### 当前机制清单（复杂度评估）

```
核心机制（必须保留）：
✅ 1. Agent（基因、决策）           - 本质
✅ 2. 交易执行（buy/sell/short/cover） - 本质
✅ 3. 账簿系统（盈亏计算）          - 本质
✅ 4. 自然选择（盈利者繁殖）        - 本质

中间机制（可简化）：
⚠️ 5. Fitness函数（v3复杂度：7-8个因素）
⚠️ 6. Daimon投票（5个voice）
⚠️ 7. Tier分级解锁（3→10→50）

外围机制（可去除）：
❌ 8. 多样性监控和保护（4-5个指标）
❌ 9. Immigration（周期性引入）
❌ 10. 死亡学习、成功经验（未实现）
❌ 11. 奖励系统（未实现）
```

### 训练量对比

```
AlphaZero: 数百万局博弈
我们当前: 10次 × 200周期 = 2,000次
差距:     1000倍！

结论：机制再好，训练量不够也无效！
```

---

## 🔧 简化方案（分5个阶段）

### 阶段1：评估和备份（1天）✅ 安全第一

```
任务：
1. ✅ 梳理当前机制（本文档）
2. ⬜ 备份当前代码（git branch: v6-before-simplification）
3. ⬜ 记录关键数据流（确保不破坏封装）
4. ⬜ 制定回滚策略

输出：
- 完整的机制清单
- 代码备份
- 数据流图
- 回滚计划
```

---

## 🛡️ 风险管理架构（三层防御）

### 核心理念：分层风险管理

```
AlphaZero的启示：
- 围棋是"完全信息博弈"（棋局 = 完整世界状态）
- 不需要担心"不可预测风险"

我们的现实：
- 市场是"不完全信息博弈"（WorldSignature ≠ 完整世界状态）
- 必须应对"不可预测风险"（黑天鹅、交易所宕机、监管突袭）

解决方案：三层架构
```

### Layer 1: 智能层（可优化）

```python
任务：基于可观测信息做最优决策
输入：WorldSignature（市场状态）+ Genome（基因）
处理：Daimon决策引擎
输出：交易决策（buy/sell/hold/close）
优化：通过演化和海量训练自动学习

→ 这是AlphaZero式的"智能优化"部分
→ 专注于"可观测范围内"的最优策略
```

### Layer 2: 监控层（部分可观测）

```python
任务：识别异常信号，提前预警
输入：WorldSignature异常指标
处理：
  - 订单簿突变检测（深度突然消失）
  - 流动性枯竭预警（滑点突然放大）
  - 价格跳空检测（价格不连续）
  - 多维异常评分（多项指标同时异常）
输出：
  - 提高danger_index
  - 降低仓位比例
  - 拒绝高风险交易

→ 这是"早期预警"部分
→ 处理"部分可观测的异常"
```

### Layer 3: 兜底层（硬性规则）🛡️

```python
任务：应对完全不可预测的黑天鹅
特点：
  ✅ 不依赖WorldSignature
  ✅ 不依赖Agent智能决策
  ✅ 硬性规则，强制执行
  ✅ 最后一道防线

1. Agent级别：
   MAX_POSITION_PCT = 0.8          # 最大仓位80%
   HARD_STOP_LOSS = -0.30          # 硬性止损-30%
   MAX_LEVERAGE = 3.0              # 最大杠杆3x
   MAX_CONSECUTIVE_LOSSES = 5      # 连续5次亏损停止交易

2. 系统级别：
   MAX_SYSTEM_POSITION_PCT = 0.7   # 系统最多70%开仓
   SYSTEM_DRAWDOWN_LIMIT = -0.50   # 系统最大回撤-50%
   CIRCUIT_BREAKER_THRESHOLD = -0.20  # 单周期亏损20%熔断
   MIN_ALIVE_AGENTS = 10           # 最少保留10个Agent

3. 执行级别：
   MAX_SLIPPAGE_PCT = 0.02         # 最大滑点2%
   MIN_ORDERBOOK_DEPTH = 10000     # 最小订单簿深度$10k
   MAX_PRICE_DEVIATION = 0.05      # 价格偏离5%拒绝交易

→ 这是"不可妥协的安全底线"
→ 保护系统不被黑天鹅摧毁
```

### 关键原则

```
原则1：智能优化 vs 硬性保护
  - Layer 1（智能层）：可以通过演化不断优化
  - Layer 3（兜底层）：不可优化，永久固定

原则2：完全不可预测的风险，交给最终的兜底措施
  - 不要指望Agent能"学会"应对黑天鹅
  - 硬性规则在Agent决策之外强制执行

原则3：保持简单，严格执行
  - 兜底规则要简单明确（不要复杂的if-else）
  - 一旦触发，立即执行（不给Agent任何"商量"余地）
```

---

### 阶段2：简化Fitness（2天）🎯 最小改动，最大效果

```
当前Fitness v3（复杂）：
def _calculate_fitness_v3(agent):
    score = 0
    # Part 1: 绝对收益（40%）
    score += absolute_return * 0.4
    # Part 2: 持有奖励（20%）
    score += holding_bonus * 0.2
    # Part 3: 交易频率惩罚（15%）
    score -= frequency_penalty * 0.15
    # Part 4: 趋势对齐（15%）
    score += trend_alignment * 0.15
    # Part 5: 生存基础分（10%）
    score += survival_bonus * 0.1
    return score

简化为AlphaZero式（极简）：
def _calculate_fitness_alphazero(agent):
    return agent.total_profit  # 就这么简单！

测试：
- 对比Fitness v3 vs AlphaZero式
- 看哪个收敛更好
```

### 阶段3：去除Tier分级（3天）🔓 完全自由

```
当前：
- 创世：3个参数
- 3-10代：解锁Tier 2
- 10+代：解锁Tier 3

简化为：
- 创世：全部50个参数
- 无分级，完全自由

修改：
1. GenomeVector.create_genesis(full_unlock=True) ✅ 已实现
2. 默认使用full_unlock=True
3. 去除mutate()中的Tier判断逻辑

风险：
- 维度灾难（需要更多Agent或更长训练）
- 收敛困难（需要验证）
```

### 阶段4：简化Daimon决策（2天）💭 从5个voice到1个

```
当前Daimon（复杂）：
class Daimon:
    def decide():
        votes = []
        votes += _genome_voice()      # 基因投票
        votes += _instinct_voice()    # 本能投票
        votes += _emotion_voice()     # 情绪投票
        votes += _experience_voice()  # 经验投票
        votes += _prophecy_voice()    # 预言投票
        return aggregate(votes)       # 聚合5个voice

简化为AlphaZero式（极简）：
class Daimon:
    def decide(market_data, agent_state):
        # 直接根据基因参数计算
        action = calculate_from_genome(
            genome=agent.genome,
            market=market_data,
            position=agent_state
        )
        return action  # 就这么简单！

优点：
- 决策完全由基因决定
- 相同基因+相同市场 = 相同决策
- 自然选择自动优化基因
```

### 阶段5：去除外围机制（1天）🗑️ 断舍离

```
去除：
1. ❌ 多样性监控（DiversityMonitor）
2. ❌ 多样性保护（DiversityProtection）
3. ❌ Immigration机制
4. ❌ 未实现的Memory Layer

保留：
1. ✅ 基本的选择淘汰（EvolutionManager核心）
2. ✅ 变异和繁殖（必要的随机性）

理由：
- AlphaZero没有这些，也能产生多样性
- 多样性应该是自然涌现的，不是人为保护的
- 让自然选择决定一切
```

---

## 🚀 执行计划（总共约8-10天）

### Week 1：评估和简化核心

```
Day 1: 阶段1 - 评估和备份 ✅
Day 2-3: 阶段2 - 简化Fitness
Day 4-6: 阶段3 - 去除Tier分级
```

### Week 2：简化决策和清理

```
Day 7-8: 阶段4 - 简化Daimon
Day 9: 阶段5 - 去除外围机制
Day 10: 验证和测试
```

### Week 3：海量训练

```
启动：1000个seed × 1000周期
预计时间：3-7天（取决于硬件）
```

---

## ⚠️ 风险控制

### 数据封装检查点

每个阶段完成后必须验证：

```
✅ 1. 账簿一致性（三大铁律第3关）
✅ 2. 交易记录完整性
✅ 3. Agent状态正确性
✅ 4. 结果可重复性（seed控制）
```

### 回滚策略

```
每个阶段前：
1. git commit（保存当前状态）
2. 运行基准测试（记录性能）
3. 如果新版性能下降>50%，立即回滚
```

---

## 💡 期待的结果

```
简化后：
- 代码量：减少30-50%
- 训练速度：提升2-3倍（机制更简单）
- 收敛性：更好（目标更清晰）
- 可解释性：更强（机制简单）

海量训练后：
- 发现真正的盈利规律（而非人为设计）
- 验证"在混沌中寻找规则"
- 实现"自由演化"的理想
```

---

## 🎓 哲学反思

```
我们一直在犯的错误：
❌ 过度设计（怕系统不够好）
❌ 手动调优（怕找不到最优解）
❌ 添加保护（怕Agent死光）

AlphaZero教给我们：
✅ 简单规则
✅ 信任进化
✅ 海量训练
✅ 让智能自然涌现

这才是"在混沌中寻找规则"的真谛！
```

---

## 📌 立即行动

**当前进度：阶段1 评估和备份**

下一步：
1. Git备份当前代码
2. 运行基准测试（记录当前性能）
3. 开始阶段2（简化Fitness）

准备好了吗？🚀

