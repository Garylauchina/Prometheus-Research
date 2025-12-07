# Daimon决策信息流完整核查
**日期**: 2025-12-07  
**版本**: v6.0  
**目的**: 确保Daimon获得所有必要信息

---

## 📊 完整信息流图

```
┌─────────────────────────────────────────────────────────────┐
│  外部环境                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Prophet（先知）                                       │  │
│  │  → WorldSignature                                    │  │
│  │  → 市场洞察                                          │  │
│  │  → 战略建议                                          │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        │ 发布到                            │
│                        ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ BulletinBoard（公告板）                               │  │
│  │  → WorldSignature                                    │  │
│  │  → Bulletins                                         │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        │ 读取                              │
└────────────────────────┼───────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Memory Layer（记忆层）                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MemoryManager                                        │  │
│  │  → Death Records（死亡记录）                          │  │
│  │  → Success Records（成功记录）                        │  │
│  │  → Survival Lessons（生存教训）                       │  │
│  │  → Champion Strategies（冠军策略）                    │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        │ 继承/查询                         │
└────────────────────────┼───────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Agent + Daimon（决策单元）                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Agent收集Context:                                      ││
│  │                                                        ││
│  │  1. 自身特征:                                         ││
│  │     - Instinct（本能）                                ││
│  │     - Genome（基因）                                  ││
│  │     - Emotion（情绪）                                 ││
│  │     - Strategy（策略）                                ││
│  │                                                        ││
│  │  2. 外部信息:                                         ││
│  │     - market_data（市场数据）                         ││
│  │     - bulletins（公告板）                             ││
│  │     - world_signature（世界签名）⭐                   ││
│  │                                                        ││
│  │  3. 状态信息:                                         ││
│  │     - position（持仓）                                ││
│  │     - capital（资金）                                 ││
│  │     - recent_pnl（最近盈亏）                          ││
│  │     - personal_stats（个人统计）                      ││
│  │                                                        ││
│  │  4. 记忆/经验:                                        ││
│  │     - inherited_wisdom（继承智慧）⭐NEW               ││
│  │                                                        ││
│  │  5. 时间上下文:  ⚠️ NEW                               ││
│  │     - current_cycle                                   ││
│  │     - holding_periods                                 ││
│  │     - time_since_last_trade                           ││
│  │                                                        ││
│  │  6. 风险评估:  ⚠️ NEW                                 ││
│  │     - max_drawdown                                    ││
│  │     - risk_exposure                                   ││
│  │     - margin_health                                   ││
│  └────────────────────────────────────────────────────────┘│
│                         ↓                                   │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Daimon.guide(context) - 7个Voice:                     ││
│  │                                                        ││
│  │  1. instinct_voice（本能之声）                        ││
│  │     输入: instinct, capital_ratio, position           ││
│  │                                                        ││
│  │  2. genome_voice（基因之声）                          ││
│  │     输入: genome, market_data.trend                   ││
│  │                                                        ││
│  │  3. experience_voice（经验之声）                      ││
│  │     输入: personal_stats, recent_pnl                  ││
│  │                                                        ││
│  │  4. emotion_voice（情绪之声）                         ││
│  │     输入: emotion, consecutive_losses                 ││
│  │                                                        ││
│  │  5. strategy_voice（策略之声）                        ││
│  │     输入: strategy_signals                            ││
│  │                                                        ││
│  │  6. prophecy_voice（先知之声）                        ││
│  │     输入: bulletins（从BulletinBoard）               ││
│  │                                                        ││
│  │  7. world_signature_voice（世界感知）⭐              ││
│  │     输入: world_signature（从BulletinBoard）         ││
│  │                                                        ││
│  │  8. ancestor_voice（祖先之声）⭐NEW                   ││
│  │     输入: inherited_wisdom（从Memory Layer）         ││
│  │                                                        ││
│  │  9. risk_voice（风险之声）⚠️ NEW                      ││
│  │     输入: risk_assessment                             ││
│  └────────────────────────────────────────────────────────┘│
│                         ↓                                   │
│  ┌────────────────────────────────────────────────────────┐│
│  │ 投票 → 决策 → 安全检查 → 最终决策                      ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                         ↓
              返回给Agent → 提交给Moirai
```

---

## ✅ 已实现的输入

### 1. Agent特征（4个Voice）

| Voice | 输入 | 来源 | 状态 |
|-------|------|------|------|
| instinct_voice | Instinct对象 | Agent.instinct | ✅ 完整 |
| genome_voice | GenomeVector | Agent.genome | ✅ 完整 |
| emotion_voice | EmotionalState | Agent.emotion | ✅ 完整 |
| strategy_voice | strategy_signals | Agent.策略系统 | ✅ 完整 |

### 2. 外部信息（3个Voice）

| Voice | 输入 | 来源 | 状态 |
|-------|------|------|------|
| experience_voice | personal_stats | Agent.personal_insights | ✅ 完整 |
| prophecy_voice | bulletins | BulletinBoard | ✅ 完整 |
| world_signature_voice | world_signature | BulletinBoard | ✅ 完整 |

### 3. 状态信息

| 信息 | 字段 | 来源 | 状态 |
|------|------|------|------|
| 持仓 | position | Ledger系统 | ✅ 完整 |
| 资金 | capital, capital_ratio | Agent | ✅ 完整 |
| 盈亏 | recent_pnl | Agent | ✅ 完整 |
| 统计 | personal_stats | PersonalInsights | ✅ 完整 |

---

## ⚠️ 需要补充的输入

### 1. Memory Layer（高优先级）

```python
# 新增：ancestor_voice
def _ancestor_voice(self, context: Dict) -> List[Vote]:
    """
    祖先之声 - 基于继承的智慧
    
    输入：
      - inherited_wisdom.survival_lessons
      - inherited_wisdom.success_patterns
      - inherited_wisdom.warnings
    
    输出：
      - 避免历史错误的投票
      - 模仿成功策略的投票
    """
    wisdom = context.get('inherited_wisdom')
    if not wisdom:
        return []
    
    votes = []
    
    # 从生存教训中学习
    for lesson in wisdom.survival_lessons:
        if '避免做空' in lesson and market_trend == 'bullish':
            votes.append(Vote('buy', 0.7, 'ancestor', lesson))
    
    # 从成功模式中学习
    for pattern in wisdom.success_patterns:
        if '长期持有' in pattern and has_position:
            votes.append(Vote('hold', 0.6, 'ancestor', pattern))
    
    return votes

状态：✅ 已设计，待实施
```

### 2. 时间上下文（中优先级）

```python
# 补充context
context['time_context'] = {
    'current_cycle': self.cycles_survived,
    'holding_periods': self._calc_holding_periods(),
    'time_since_last_trade': self._time_since_last_trade(),
    'market_phase': self._estimate_market_phase(cycle),
}

# 影响的Voice：
# - instinct_voice：新手保护期
# - genome_voice：耐心判断
# - experience_voice：时间止损

状态：⚠️ 需要实现
```

### 3. 风险评估（中优先级）

```python
# 新增：risk_voice
def _risk_voice(self, context: Dict) -> List[Vote]:
    """
    风险之声 - 基于风险评估
    
    输入：
      - max_drawdown（最大回撤）
      - current_drawdown（当前回撤）
      - risk_exposure（风险敞口）
      - leverage（杠杆）
    
    输出：
      - 风险过高时建议减仓/平仓
      - 风险可控时允许加仓
    """
    risk_assessment = context.get('risk_assessment', {})
    
    current_dd = risk_assessment.get('current_drawdown', 0)
    max_dd_threshold = 0.2  # 20%
    
    votes = []
    
    # 回撤过大 → 建议平仓
    if current_dd > max_dd_threshold and has_position:
        votes.append(Vote(
            'close',
            0.8,
            'risk',
            f"回撤过大({current_dd:.1%})，风险控制"
        ))
    
    return votes

状态：⚠️ 需要实现
```

### 4. 社交信息（低优先级，可选）

```python
# 补充context（可选）
context['social_context'] = {
    'population_sentiment': self._get_population_sentiment(),
    'family_performance': self._get_family_performance(),
    'peer_comparison': self._compare_with_peers(),
}

# 新增：social_voice（可选）
def _social_voice(self, context: Dict) -> List[Vote]:
    """
    社交之声 - 基于种群行为
    
    输入：
      - population_sentiment（大家都在做什么）
      - family_performance（家族表现）
    
    输出：
      - 逆向/从众建议
    """
    pass

状态：⏸️ 可选，暂不实施
```

---

## 🔄 信息流核查清单

### Context准备（Agent._prepare_decision_context）

```python
✅ market_data: 市场数据
✅ bulletins: 公告板信息
✅ capital: 资金状态
✅ position: 持仓状态
✅ recent_pnl: 最近盈亏
✅ personal_stats: 个人统计
✅ strategy_signals: 策略信号
⭐ inherited_wisdom: 继承智慧（NEW）
⚠️ time_context: 时间上下文（待补充）
⚠️ risk_assessment: 风险评估（待补充）
⏸️ social_context: 社交信息（可选）
```

### Daimon Voices

```python
✅ 1. instinct_voice
✅ 2. genome_voice
✅ 3. experience_voice
✅ 4. emotion_voice
✅ 5. strategy_voice
✅ 6. prophecy_voice
✅ 7. world_signature_voice
⭐ 8. ancestor_voice（NEW，待实施）
⚠️ 9. risk_voice（待实施）
⏸️ 10. social_voice（可选）
```

### 信息来源检查

```python
✅ Agent自身: instinct, genome, emotion, capital, position
✅ BulletinBoard: bulletins, world_signature
✅ PersonalInsights: personal_stats
⭐ Memory Layer: inherited_wisdom（NEW）
⚠️ Time tracking: cycles, holding_periods（待补充）
⚠️ Risk tracking: drawdown, exposure（待补充）
```

---

## 📋 实施优先级

### 🔴 Phase 1：Memory Layer（立即）

1. ✅ 实现MemoryManager
2. ⭐ 在Agent中添加inherited_wisdom
3. ⭐ 在Daimon中添加ancestor_voice
4. ⭐ 集成到创世和进化流程

### 🟡 Phase 2：时间和风险（本周）

5. ⚠️ 补充time_context到context
6. ⚠️ 实现risk_voice
7. ⚠️ 在Agent中跟踪time/risk指标

### 🟢 Phase 3：社交信息（可选，下周）

8. ⏸️ 实现social_context（如果有价值）
9. ⏸️ 实现social_voice

---

## 🎯 验证标准

### 完整性检查

```python
def verify_context_completeness(context: Dict) -> Dict:
    """验证context完整性"""
    
    required_fields = [
        'market_data',
        'bulletins',
        'capital',
        'position',
        'recent_pnl',
        'personal_stats',
    ]
    
    optional_fields = [
        'inherited_wisdom',  # Memory Layer
        'time_context',      # 时间
        'risk_assessment',   # 风险
    ]
    
    missing = []
    for field in required_fields:
        if field not in context:
            missing.append(field)
    
    return {
        'complete': len(missing) == 0,
        'missing_required': missing,
        'has_optional': [f for f in optional_fields if f in context]
    }
```

### 信息流验证

```python
def verify_information_flow():
    """验证信息流正确性"""
    
    # 1. BulletinBoard → Agent
    assert agent can read bulletins
    assert agent can read world_signature
    
    # 2. Memory Layer → Agent
    assert agent.inherited_wisdom is not None
    assert wisdom comes from MemoryManager
    
    # 3. Agent → Daimon
    assert context has all required fields
    assert context['inherited_wisdom'] is passed
    
    # 4. Daimon → Decision
    assert all voices can access their inputs
    assert ancestor_voice uses inherited_wisdom
    
    # 5. Decision → Moirai
    assert decision is complete
```

---

## 💡 设计原则总结

### 1. 信息完整性

```
Daimon应该获得所有影响决策的信息：
  ✅ 内部特征（instinct, genome, emotion）
  ✅ 外部环境（market, world_signature）
  ✅ 历史经验（wisdom, personal_stats）
  ⚠️ 时间因素（cycle, holding_period）
  ⚠️ 风险状态（drawdown, exposure）
```

### 2. 信息流清晰

```
单向流动：
  BulletinBoard → Agent → Daimon → Decision → Moirai
  Memory Layer → Agent → Daimon
  
不跨层：
  ❌ Daimon不直接访问BulletinBoard
  ❌ Daimon不直接访问Memory Layer
```

### 3. 职责分离

```
Agent: 收集context
Daimon: 基于context做决策
Moirai: 执行决策并记录到Memory
```

---

**记录人**: AI Assistant  
**审核人**: 用户 (刘刚)  
**状态**: 信息流已核查，待补充

