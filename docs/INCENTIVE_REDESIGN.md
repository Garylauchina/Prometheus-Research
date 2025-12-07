# Prometheus 激励机制重新设计
**日期**: 2025-12-07  
**问题**: 系统求盈利 vs Agent求生存 = 激励错位  
**目标**: 让生存=盈利，实现共赢

---

## 🎯 核心矛盾

```
当前系统：
  系统目标：盈利最大化（+835%）
  Agent目标：生存最大化（不被淘汰）
  
  矛盾：
  - 激进策略 = 高收益 + 高风险 → Agent选择保守
  - 长期持有 = 暴利 + 短期平淡 → Agent选择频繁交易
  - 跟随市场 = 正确 + 无差异化 → Agent选择反向
  
  结果：Agent为了生存，选择了不赚钱的策略！
```

---

## 🔧 解决方案

### 方案1：调整适应度函数（核心）

#### 现有问题

```python
# 当前适应度
fitness = (
    capital_ratio          # 资金比率（主要）
    * survival_bonus       # 生存加成（鼓励活得久）
    * stability_bonus      # 稳定性（鼓励不波动）
    * risk_adjustment      # 风险调整（惩罚回撤）
    * negativity_penalty   # 消极惩罚
)

问题：
1. survival_bonus：sqrt(生存天数/总天数) → 鼓励"熬"
2. stability_bonus：基于Sharpe → 惩罚波动，但高收益=高波动
3. risk_adjustment：1/(1+回撤) → 惩罚激进
```

#### 新设计：绝对收益导向

```python
# 新适应度（v6.0）
fitness = (
    absolute_return       # ⭐ 绝对收益（而非比率）
    * holding_bonus       # ⭐ 持仓奖励（持有越久越好）
    * patience_bonus      # ⭐ 耐心奖励（少交易）
    * trend_alignment     # ⭐ 趋势对齐（做对方向）
    * diversity_value     # ⭐ 多样性价值（保护独特策略）
)

详细：

1. absolute_return（绝对收益）
   = (current_capital - initial_capital) / initial_capital * 100
   
   不再乘以sqrt(生存时间)！
   → 赚得多=fitness高，不管活多久

2. holding_bonus（持仓奖励）
   = 1.0 + min(avg_holding_days / 30, 2.0)
   
   avg_holding_days = 每笔持仓的平均天数
   → 持有30天 = +100% fitness
   → 鼓励长期持有，而不是频繁交易

3. patience_bonus（耐心奖励）
   = 1.0 / (1.0 + trade_frequency)
   
   trade_frequency = trade_count / cycles_survived
   → 交易越少，奖励越高
   → 惩罚频繁交易

4. trend_alignment（趋势对齐）
   = 1.0 + (做多收益 if 市场上涨 else 做空收益)
   
   → 做对方向=加分，做错方向=减分
   → 鼓励顺势而为

5. diversity_value（多样性价值）
   = 1.0 + (基因独特性 * 0.3 if 种群多样性低 else 0)
   
   → 当种群同质化时，保护独特基因
   → 防止"一刀切"淘汰潜力股
```

---

### 方案2：延长评估周期

#### 现有问题

```python
每30周期进化一次
→ 长期策略没机会证明自己
→ 短期表现好的Agent占优
```

#### 新设计

```python
动态评估周期：
  - 前100周期：每50周期评估（给探索期）
  - 100-500周期：每100周期评估（稳定期）
  - 500周期后：每200周期评估（长期期）
  
效果：
  - 长期策略有足够时间展现价值
  - 不会因为短期波动被过早淘汰
```

---

### 方案3：引入"潜力股保护"机制

#### 核心思想

**不只看当前表现，也看潜在价值**

#### 具体实现

```python
# 识别"潜力股"
def is_potential_winner(agent):
    # 1. 持仓时间长（>平均值）
    if agent.avg_holding_days > population_avg * 1.5:
        return True
    
    # 2. 趋势对齐（做多在牛市）
    if agent.position_side == market_trend:
        return True
    
    # 3. 基因独特（与主流不同）
    if agent.gene_diversity_score > 0.7:
        return True
    
    return False

# 进化时保护
def evolve():
    # 识别潜力股
    potential_winners = [a for a in agents if is_potential_winner(a)]
    
    # 淘汰时：
    # - 90%按fitness淘汰
    # - 10%随机淘汰（包括精英，保持探索）
    # - 但绝不淘汰潜力股！
    
    protected = set(potential_winners)
    eliminate_candidates = [a for a in agents if a not in protected]
    # ... 从candidates中淘汰
```

---

### 方案4：团队奖励机制

#### 核心思想

**不只看个体，也看种群整体表现**

#### 具体实现

```python
# 计算种群整体表现
population_return = avg([agent.return for agent in agents])

# 个体fitness加入团队加成
def calculate_fitness_v3(agent):
    individual_return = agent.return
    
    # 团队加成
    if population_return > 0:
        team_bonus = 1.0 + (population_return / 100 * 0.2)  # 20%权重
    else:
        team_bonus = 1.0
    
    fitness = individual_return * team_bonus
    
    # 效果：
    # - 如果种群整体赚钱，每个Agent都受益
    # - 鼓励Agent做有利于集体的决策
    # - 减少"内卷"（互相竞争损害整体）
```

---

## 📊 预期效果对比

### 修改前

```
适应度 = 资金 × 生存 × 稳定 × 风险调整

Agent A（激进）：
  - 资金：1.5（+50%）
  - 生存：0.3（早期亏损被淘汰）
  - 稳定：0.7（波动大）
  - 风险：0.6（回撤高）
  → fitness = 1.5 × 0.3 × 0.7 × 0.6 = 0.189

Agent B（保守）：
  - 资金：1.0（0%）
  - 生存：1.0（活到最后）
  - 稳定：1.0（无波动）
  - 风险：1.0（无回撤）
  → fitness = 1.0 × 1.0 × 1.0 × 1.0 = 1.0

结果：B胜出！✅ 保守策略存活
```

### 修改后

```
适应度 = 绝对收益 × 持仓奖励 × 耐心奖励 × 趋势对齐

Agent A（激进，买入持有）：
  - 绝对收益：8.35（+835%）
  - 持仓奖励：3.0（持有2000天）
  - 耐心奖励：2.0（只交易1次）
  - 趋势对齐：1.5（做多在牛市）
  → fitness = 8.35 × 3.0 × 2.0 × 1.5 = 75.15

Agent B（保守，空仓观望）：
  - 绝对收益：0（+0%）
  - 持仓奖励：1.0（无持仓）
  - 耐心奖励：1.0（无交易）
  - 趋势对齐：1.0（无方向）
  → fitness = 0 × 1.0 × 1.0 × 1.0 = 0

结果：A胜出！✅ 激进策略存活
```

---

## 🎯 实施步骤

### 第1步：重写适应度函数（立即）

```python
# prometheus/core/evolution_manager_v5.py
def _calculate_fitness_v3(self, agent, total_cycles):
    """
    v3适应度：绝对收益导向
    核心：让生存=盈利
    """
    # 1. 绝对收益（不再乘以生存时间！）
    absolute_return = (agent.current_capital - agent.initial_capital) / agent.initial_capital
    
    if absolute_return <= 0:
        return 0.01  # 亏损或不赚=极低fitness
    
    # 2. 持仓奖励
    avg_holding_days = self._get_avg_holding_days(agent)
    holding_bonus = 1.0 + min(avg_holding_days / 30, 2.0)
    
    # 3. 耐心奖励
    trade_frequency = agent.trade_count / max(agent.cycles_survived, 1)
    patience_bonus = 1.0 / (1.0 + trade_frequency)
    
    # 4. 趋势对齐
    trend_alignment = self._calculate_trend_alignment(agent)
    
    # 5. 多样性价值
    diversity_value = self._calculate_diversity_value(agent)
    
    # 综合fitness
    fitness = (
        absolute_return 
        * holding_bonus 
        * patience_bonus 
        * trend_alignment 
        * diversity_value
    )
    
    return max(fitness, 0.01)
```

### 第2步：调整进化周期（中期）

```python
# prometheus/facade/v6_facade.py
def run_scenario(..., evo_interval=None):
    if evo_interval is None:
        # 动态调整
        if cycle < 100:
            evo_interval = 50
        elif cycle < 500:
            evo_interval = 100
        else:
            evo_interval = 200
```

### 第3步：引入潜力股保护（中期）

```python
# prometheus/core/evolution_manager_v5.py
def _evolve(self):
    # 识别潜力股
    potential_winners = self._identify_potential_winners()
    
    # 淘汰时保护
    protected = set(potential_winners)
    # ...
```

### 第4步：团队奖励（长期，可选）

```python
# 计算种群平均收益
population_avg = mean([a.return for a in agents])

# 加入team_bonus
fitness *= (1.0 + population_avg / 100 * 0.2)
```

---

## 🎯 验证标准

### 新标准

```
成功标准：
  - Agent平均收益 >= BTC收益 × 0.8
  - Agent持仓时间比例 >= 60%
  - Agent交易频率 <= 10%
  - 种群多样性 >= 0.4

终极目标：
  - 让Agent自然地"学会"买入持有
  - 而不是"强迫"它们这么做
```

---

## 📝 总结

### 核心理念转变

```
旧理念：生存 + 稳定 = 好Agent
新理念：盈利 + 耐心 = 好Agent

旧机制：鼓励"不亏"
新机制：鼓励"赚大钱"

旧结果：保守观望
新结果：激进持有
```

### 哲学思考

**"在市场中，不是活得久的赢，而是赚得多的赢。"**

但Agent不知道这一点，所以我们要通过激励机制告诉它：
- ✅ 赚钱=生存
- ❌ 不亏≠生存

**共赢的关键**：让Agent的生存策略=系统的盈利策略！

---

**记录人**: AI Assistant  
**审核人**: 用户 (刘刚)  
**状态**: 待实施

