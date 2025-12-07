# Memory Layer集成指南
**日期**: 2025-12-07  
**版本**: v6.0  
**原则**: 统一封装，统一调用，严禁旁路

---

## 🎯 核心设计原则

### 1. 单一入口

```python
❌ 错误：直接访问内部组件
from prometheus.memory.death_registry import DeathRegistry
death_reg = DeathRegistry()
death_reg.record(...)  # 禁止！

✅ 正确：通过MemoryManager统一入口
from prometheus.memory import get_memory_manager
memory = get_memory_manager()
memory.record_death(...)  # 正确！
```

### 2. 清晰分层

```
Level 0: Memory Layer
  ↑ 记录     ↓ 指导
  
Level 1: Prophet
  ↑ 汇报     ↓ 战略
  
Level 2: Moirai
  ↑ 请求     ↓ 执行
  
Level 3: Agent

信息流：单向，不跨层！
```

### 3. 职责分离

```
Memory Layer: 只负责记忆、分析、指导
Moirai: 负责执行、记录事件到Memory
Agent: 负责交易、从Memory获取智慧
```

---

## 📦 完整的集成流程

### 步骤1：初始化Memory Layer

```python
# prometheus/facade/v6_facade.py

from prometheus.memory import get_memory_manager

class V6Facade:
    def __init__(self, ...):
        # 初始化Memory Layer（系统唯一）
        self.memory = get_memory_manager()
        
        # 传递给需要的组件
        self.moirai = Moirai(
            ...,
            memory=self.memory  # ⭐ 注入
        )
        
        self.evolution = EvolutionManagerV5(
            ...,
            memory=self.memory  # ⭐ 注入
        )
```

---

### 步骤2：Moirai记录事件

```python
# prometheus/core/moirai.py

class Moirai:
    def __init__(self, ..., memory=None):
        self.memory = memory  # Memory Layer引用
    
    def _atropos_cut(self, agent: AgentV5, reason: DeathReason):
        """剪断生命之线 - 记录死亡"""
        
        # 1. 先记录到Memory Layer
        if self.memory:
            market_state = self._get_current_market_state()
            self.memory.record_death(
                agent=agent,
                reason=reason.value,
                market_state=market_state,
                cycle=self.current_cycle
            )
        
        # 2. 然后执行死亡
        agent.state = AgentState.DEAD
        self.agents.remove(agent)
        
        logger.info(f"✂️ Atropos剪断了{agent.agent_id}的生命之线")
    
    def _clotho_spin_thread(self, ...):
        """纺织生命之线 - 创建Agent"""
        
        # 1. 从Memory获取智慧
        wisdom = None
        if self.memory:
            wisdom = self.memory.get_wisdom_for_newborn(
                parent1=parent1,
                parent2=parent2,
                family_id=family_id
            )
        
        # 2. 创建Agent
        agent = AgentV5(...)
        
        # 3. 注入智慧
        if wisdom:
            agent.inherited_wisdom = wisdom
        
        return agent
    
    def _check_milestone(self, agent: AgentV5):
        """检查Agent是否达成里程碑"""
        total_return = (agent.current_capital / agent.initial_capital - 1)
        
        # 记录成功事件
        if total_return > 0.5 and not getattr(agent, '_milestone_50', False):
            if self.memory:
                self.memory.record_success(
                    agent=agent,
                    milestone="首次盈利50%",
                    cycle=self.current_cycle
                )
            agent._milestone_50 = True
        
        if total_return > 1.0 and not getattr(agent, '_milestone_100', False):
            if self.memory:
                self.memory.record_success(
                    agent=agent,
                    milestone="盈利翻倍",
                    cycle=self.current_cycle
                )
            agent._milestone_100 = True
```

---

### 步骤3：Agent使用智慧

```python
# prometheus/core/agent_v5.py

class AgentV5:
    def __init__(self, ...):
        self.inherited_wisdom: Optional[WisdomPackage] = None
        # 在创建时，Moirai会注入wisdom
    
    def make_trading_decision(self, ...):
        # 决策前，Daimon会考虑inherited_wisdom
        context = self._prepare_decision_context(...)
        
        # 传递wisdom给Daimon
        if self.inherited_wisdom:
            context['wisdom'] = self.inherited_wisdom
        
        decision = self.daimon.guide(context)
        return decision
```

---

### 步骤4：Daimon考虑智慧

```python
# prometheus/core/inner_council.py

class Daimon:
    def guide(self, context: Dict) -> CouncilDecision:
        # 收集所有投票
        all_votes = []
        
        # 1. 现有的voices
        all_votes.extend(self._instinct_voice(context))
        all_votes.extend(self._genome_voice(context))
        all_votes.extend(self._emotion_voice(context))
        
        # 2. ⭐ 新增：ancestor_voice（基于Memory）
        if 'wisdom' in context:
            all_votes.extend(self._ancestor_voice(context))
        
        # 3. 投票决策
        decision = self._vote(all_votes)
        
        # 4. ⭐ 新增：决策安全检查（基于Memory）
        if hasattr(self.agent, 'memory_ref'):
            is_safe, warning = self.agent.memory_ref.check_decision_safety(
                self.agent, decision, context['market_data']
            )
            if not is_safe:
                logger.warning(f"{self.agent.agent_id}: {warning}")
                decision.confidence *= 0.3  # 降低置信度
        
        return decision
    
    def _ancestor_voice(self, context: Dict) -> List[Vote]:
        """
        祖先的声音 - 基于继承的智慧
        """
        votes = []
        wisdom: WisdomPackage = context.get('wisdom')
        
        if not wisdom:
            return votes
        
        # 从生存教训中学习
        for lesson in wisdom.survival_lessons:
            if '避免在牛市中做空' in lesson:
                market_trend = context['market_data'].get('long_term_trend')
                if market_trend == 'bullish':
                    votes.append(Vote(
                        action='buy',
                        confidence=0.7,
                        voter_category='ancestor',
                        reason=f"祖先智慧: {lesson}"
                    ))
        
        # 从成功模式中学习
        for pattern in wisdom.success_patterns:
            if '长期持有' in pattern:
                if context['position']['amount'] > 0:
                    votes.append(Vote(
                        action='hold',
                        confidence=0.6,
                        voter_category='ancestor',
                        reason=f"成功模式: {pattern}"
                    ))
        
        return votes
```

---

### 步骤5：Evolution记录进化事件

```python
# prometheus/core/evolution_manager_v5.py

class EvolutionManagerV5:
    def __init__(self, ..., memory=None):
        self.memory = memory
    
    def run_evolution_cycle(self, ...):
        """运行进化周期"""
        
        # 进化前记录
        if self.memory:
            self.memory.record_event(MemoryEvent(
                event_type=EventType.EVOLUTION,
                agent_id='system',
                timestamp=datetime.now(),
                cycle=cycle,
                agent_state={},
                market_state={},
                event_data={
                    'generation': self.generation,
                    'population_size': len(self.moirai.agents)
                }
            ))
        
        # 执行进化
        # ...
```

---

## 🔒 严格的访问控制

### 允许的调用链

```
✅ Moirai → memory.record_death()
✅ Moirai → memory.get_wisdom_for_newborn()
✅ Moirai → memory.record_success()
✅ Daimon → memory.check_decision_safety()
✅ Evolution → memory.record_event()
✅ Prophet → memory.query_wisdom()
```

### 禁止的调用

```
❌ Agent → memory.record_death()  # 越权！
❌ Daimon → memory._death_registry  # 直接访问内部！
❌ 任何地方 → DeathRegistry()  # 绕过MemoryManager！
```

---

## 📊 信息流示例

### 场景1：Agent死亡

```
1. Agent亏损 → 资金<0
   ↓
2. Moirai检测到 → 调用 _atropos_cut()
   ↓
3. Moirai → memory.record_death(agent, reason, ...)
   ↓
4. MemoryManager:
   - 分析死因
   - 更新统计
   - 生成警示
   - 存储到DB
   ↓
5. Memory Layer智慧更新
```

### 场景2：创建新Agent

```
1. Evolution需要新Agent
   ↓
2. Moirai → _clotho_spin_thread()
   ↓
3. Moirai → memory.get_wisdom_for_newborn(parent1, parent2, family_id)
   ↓
4. MemoryManager:
   - 查询死亡教训
   - 查询成功模式
   - 查询冠军策略
   - 合成智慧包
   ↓
5. 返回 WisdomPackage
   ↓
6. Agent.inherited_wisdom = wisdom
   ↓
7. Daimon决策时使用wisdom
```

### 场景3：Daimon决策

```
1. Agent收到市场数据
   ↓
2. Agent → daimon.guide(context)
   ↓
3. Daimon收集votes:
   - instinct_voice
   - genome_voice
   - ⭐ ancestor_voice（基于inherited_wisdom）
   ↓
4. 投票 → 生成decision
   ↓
5. Daimon → memory.check_decision_safety(agent, decision, market)
   ↓
6. MemoryManager:
   - 检查是否匹配危险模式
   - 返回(is_safe, warning)
   ↓
7. 如果不安全 → 调整decision
   ↓
8. 返回final decision
```

---

## 🧪 测试验证

### 测试1：Memory初始化

```python
def test_memory_initialization():
    from prometheus.memory import get_memory_manager
    
    memory = get_memory_manager()
    assert memory is not None
    assert memory.generation == 0
    assert memory.total_events == 0
    
    # 验证单例
    memory2 = get_memory_manager()
    assert memory is memory2  # 同一个实例
```

### 测试2：事件记录

```python
def test_event_recording():
    memory = get_memory_manager()
    
    # 创建mock agent
    agent = create_mock_agent()
    
    # 记录死亡
    memory.record_death(
        agent=agent,
        reason="破产",
        market_state={'trend': 'bullish'},
        cycle=100
    )
    
    # 验证记录
    stats = memory.get_statistics()
    assert stats['total_deaths'] == 1
```

### 测试3：智慧传承

```python
def test_wisdom_inheritance():
    memory = get_memory_manager()
    
    # 记录一些死亡
    for i in range(10):
        agent = create_mock_agent()
        memory.record_death(agent, "做空失败", ...)
    
    # 获取智慧
    wisdom = memory.get_wisdom_for_newborn()
    
    # 验证智慧内容
    assert len(wisdom.survival_lessons) > 0
    assert any('做空' in lesson for lesson in wisdom.survival_lessons)
```

---

## 📋 实施Checklist

- [ ] 创建 `prometheus/memory/` 目录
- [ ] 实现 `memory_manager.py`（统一入口）
- [ ] 实现 `death_registry.py`（死亡记录）
- [ ] 实现 `success_registry.py`（成功记录）
- [ ] 实现 `experience_db.py`（经验数据库）
- [ ] 实现 `strategy_analyzer.py`（策略分析）
- [ ] 修改 `Moirai` 注入memory
- [ ] 修改 `EvolutionManagerV5` 注入memory
- [ ] 修改 `Daimon` 增加ancestor_voice
- [ ] 修改 `AgentV5` 增加inherited_wisdom
- [ ] 修改 `V6Facade` 初始化memory
- [ ] 编写集成测试
- [ ] 验证信息流正确性

---

## 🎯 验证标准

### 成功标准

```
✅ Memory是系统唯一实例（单例）
✅ 所有死亡都被记录
✅ 所有成功都被记录
✅ 新Agent都继承智慧
✅ Daimon决策考虑祖先智慧
✅ 没有直接访问内部组件
✅ 信息流清晰单向
```

### 失败标志

```
❌ 出现 from prometheus.memory.death_registry import ...
❌ 出现 memory._death_registry.xxx
❌ 跨层调用（Agent → Memory）
❌ 双向信息流
❌ 多个Memory实例
```

---

**记录人**: AI Assistant  
**审核人**: 用户 (刘刚)  
**状态**: 架构设计完成，待实施

