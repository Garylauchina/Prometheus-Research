# v6.0封装检查清单（为v7.0预留）

## 🎯 目标

确保v6.0的核心结构封装良好，v7.0开发时能"信手拈来"。

---

## ✅ 已封装良好的部分

### 1. Moirai三女神架构

```python
# ✅ Clotho（创造）
moirai._clotho_create_single_agent()  # 创建单个Agent

# ✅ Lachesis（行为）
moirai._lachesis_force_close_all(agent, price, reason)  # 强制平仓

# ✅ Atropos（终结）
moirai.retire_agent(agent, reason, price, awards)  # 光荣退休
moirai.terminate_agent(agent, reason, price)  # 终结生命
```

**v7.0使用场景：**
- Prophet召回传奇Agent → 使用`_clotho_create_single_agent`基础
- Prophet淘汰表现差的Agent → 使用`terminate_agent`
- Prophet管理Agent生命周期 → 使用Moirai接口

---

### 2. 退休机制

```python
# ✅ 奖章颁发
evolution_manager._award_top_performers(ranked_agents, top_k=5)

# ✅ 退休检查
evolution_manager._check_and_retire_agents(current_price)

# ✅ 奖章统计
awards = sum(1 for m in agent.meta_genome.milestones 
            if m.get('type') == 'top_performer')
```

**v7.0使用场景：**
- 不同生态位独立颁发奖章
- 不同生态位不同退休条件
- Prophet管理退休Agent池

---

### 3. Immigration机制

```python
# ✅ Immigration注入（已标注v7.0 Prophet专用）
evolution_manager.inject_immigrants(count=10, reason="Prophet战略注入")

# ✅ Immigration触发检查
evolution_manager.maybe_inject_immigrants(force=True)
```

**v7.0使用场景：**
- Prophet分析市场环境 → 决定注入哪些生态位
- Prophet维护多样性 → 触发Immigration
- Prophet响应方向熵 → 动态注入

---

### 4. ExperienceDB

```python
# ✅ 保存退休英雄
experience_db.save_retired_agent(
    agent=agent,
    world_signature=ws,
    awards=5,
    retirement_reason='hero',
    generation=100,
    run_id='v7_phase1',
    market_type='bull'
)

# ✅ 查询相似基因
candidates = experience_db.query_similar_genomes(
    world_signature=current_ws,
    top_k=50,
    similarity_threshold=0.6
)
```

**v7.0使用场景：**
- Prophet召回v6.0基因 → 按WorldSignature匹配
- Prophet按生态位召回 → 需要增强（见优化建议）
- Prophet复活传奇Agent → 按奖章数查询

---

### 5. AgentState扩展

```python
# ✅ 退休状态已定义
class AgentState(Enum):
    RETIRED_HERO = "retired_hero"    # 光荣退休（5个奖章，可召回）
    RETIRED_AGE = "retired_age"      # 寿终正寝（10代，可召回但优先级低）
```

**v7.0使用场景：**
- Prophet管理退休Agent池
- Prophet优先召回RETIRED_HERO
- Prophet区分不同退休原因

---

## ⚠️ 需要优化的部分

### 1. 离开→新生机制（立即优化）⭐

#### 当前实现（不够封装）

```python
# ⚠️ 当前在run_evolution_cycle中直接实现
departed_count = 0
if hasattr(self, 'retirement_enabled') and self.retirement_enabled:
    departed_agents = self._check_and_retire_agents(current_price)
    departed_count = len(departed_agents)

# 直接创建新生
new_births = []
if departed_count > 0:
    for i in range(departed_count):
        new_agent = self.moirai._clotho_create_single_agent()
        new_births.append(new_agent)
    
    self.moirai.agents.extend(new_births)
    # ... 挂载账簿
```

#### 优化方案（抽取为独立方法）

```python
# ✅ 抽取为独立方法
def _replace_departed_agents(
    self, 
    departed_count: int, 
    reason: str = "补充离开者"
) -> List[AgentV5]:
    """
    🧵 Clotho创造新生（v6.0极简主义）
    
    作用：1:1补充离开者（退休/死亡）
    
    v7.0可复用：
    - Prophet可以调用此方法补充特定生态位
    - 支持不同的创建策略（随机 vs 召回历史基因）
    
    Args:
        departed_count: 离开者数量
        reason: 创建原因（用于日志）
    
    Returns:
        List[AgentV5]: 新创建的Agent列表
    """
    if departed_count <= 0:
        return []
    
    logger.info(f"🧵 Clotho创造新生: 补充{departed_count}个离开者")
    
    new_births = []
    for i in range(departed_count):
        new_agent = self.moirai._clotho_create_single_agent()
        new_births.append(new_agent)
        self.total_births += 1
    
    # 添加到种群
    self.moirai.agents.extend(new_births)
    
    # 挂载账簿
    try:
        from prometheus.ledger.attach_accounts import attach_accounts
        public_ledger = getattr(self.moirai, "public_ledger", None)
        attach_accounts(new_births, public_ledger)
    except Exception as e:
        logger.warning(f"新Agent挂账簿失败: {e}")
    
    logger.info(f"✅ 新生完成: {len(new_births)}个Agent")
    return new_births
```

**v7.0使用场景：**
```python
# Prophet按生态位补充
departed_trend_followers = 5
new_agents = evolution_manager._replace_departed_agents(
    departed_count=departed_trend_followers,
    reason="补充Trend Follower生态位"
)

# Prophet为新Agent分配生态位
for agent in new_agents:
    agent.niche = 'trend_follower'
```

---

### 2. 生态位接口（为v7.0预留）⭐

#### 需要在Agent中预留

```python
# ⚠️ 当前Agent缺少niche属性
# ✅ v7.0需要添加

@dataclass
class AgentV5:
    # ... 现有属性
    
    # ✅ v7.0预留：生态位
    niche: Optional[str] = None  # 'trend_follower', 'bull_holder', etc.
    
    def assign_niche(self, niche: str):
        """
        🏷️ 分配生态位（v7.0 Prophet专用）
        
        10大生态位：
        1. trend_follower      - 趋势跟随
        2. mean_reversion      - 均值回归
        3. bull_holder         - 牛市持仓
        4. bear_shorter        - 熊市做空
        5. scalper             - 短线交易
        6. arbitrageur         - 套利交易
        7. contrarian          - 逆向交易
        8. profit_taker        - 止盈专家
        9. risk_manager        - 风险管理
        10. momentum_trader    - 动量交易
        """
        self.niche = niche
```

#### 需要在EvolutionManager中预留

```python
# ✅ v7.0预留：按生态位查询Agent

def get_agents_by_niche(self, niche: str) -> List[AgentV5]:
    """
    🏷️ 按生态位查询Agent（v7.0 Prophet专用）
    
    用途：
    - Prophet统计各生态位Agent数量
    - Prophet分析各生态位表现
    - Prophet调整资金分配
    
    Args:
        niche: 生态位名称
    
    Returns:
        List[AgentV5]: 该生态位的所有Agent
    """
    return [agent for agent in self.moirai.agents 
            if getattr(agent, 'niche', None) == niche]

def get_niche_statistics(self) -> Dict[str, int]:
    """
    📊 统计各生态位Agent数量（v7.0 Prophet专用）
    
    Returns:
        Dict[str, int]: {niche_name: agent_count}
    """
    stats = {}
    for agent in self.moirai.agents:
        niche = getattr(agent, 'niche', 'unknown')
        stats[niche] = stats.get(niche, 0) + 1
    return stats
```

**v7.0使用场景：**
```python
# Prophet分析生态位分布
niche_stats = evolution_manager.get_niche_statistics()
# {'trend_follower': 10, 'bull_holder': 8, ...}

# Prophet调整资金分配
if niche_stats['bear_shorter'] < 5:  # 空头太少
    # 注入更多空头Agent
    prophet.inject_bear_shorters(count=5)
```

---

### 3. Prophet召回接口（增强）⭐

#### 当前实现（功能单一）

```python
# ⚠️ 当前只有基础的相似度查询
candidates = experience_db.query_similar_genomes(
    world_signature=ws,
    top_k=50,
    similarity_threshold=0.6
)
```

#### 优化方案（增加多种召回策略）

```python
# ✅ ExperienceDB增强

def query_by_awards(
    self, 
    min_awards: int = 5, 
    top_k: int = 50
) -> List[Dict]:
    """
    🏆 按奖章数查询（v7.0 Prophet专用）
    
    用途：
    - Prophet召回传奇Agent（5奖章英雄）
    - Prophet优先召回高奖章Agent
    
    Args:
        min_awards: 最低奖章数
        top_k: 返回数量
    
    Returns:
        List[Dict]: 基因列表
    """
    query = """
        SELECT genome, profit_factor, awards, retirement_reason
        FROM best_genomes
        WHERE awards >= ?
        ORDER BY awards DESC, profit_factor DESC
        LIMIT ?
    """
    cursor = self.conn.execute(query, (min_awards, top_k))
    # ... 返回结果

def query_by_niche(
    self, 
    world_signature: WorldSignatureSimple,
    niche: str,
    top_k: int = 50
) -> List[Dict]:
    """
    🏷️ 按生态位查询（v7.0 Prophet专用）
    
    用途：
    - Prophet按生态位召回基因
    - 牛市 → 召回Bull Holder基因
    - 熊市 → 召回Bear Shorter基因
    
    Args:
        world_signature: 当前市场环境
        niche: 生态位名称
        top_k: 返回数量
    
    Returns:
        List[Dict]: 该生态位的基因列表
    
    注意：
    - v6.0数据库没有niche字段
    - 需要通过directional_bias推断生态位
    - 或者v7.0重新训练时记录niche
    """
    # 根据directional_bias推断生态位
    if niche == 'bull_holder':
        direction_min = 0.7
        direction_max = 1.0
    elif niche == 'bear_shorter':
        direction_min = -1.0
        direction_max = -0.7
    # ... 其它生态位
    
    # 查询符合条件的基因
    # ...

def query_legendary_agents(
    self, 
    retirement_reason: str = 'hero',
    top_k: int = 20
) -> List[Dict]:
    """
    ✨ 查询传奇Agent（v7.0 Prophet专用）
    
    用途：
    - Prophet复活传奇Agent
    - Prophet优先召回光荣退休的英雄
    
    Args:
        retirement_reason: 'hero' or 'age'
        top_k: 返回数量
    
    Returns:
        List[Dict]: 传奇Agent列表
    """
    query = """
        SELECT genome, profit_factor, awards, agent_id, generation
        FROM best_genomes
        WHERE retirement_reason = ?
        ORDER BY awards DESC, profit_factor DESC
        LIMIT ?
    """
    cursor = self.conn.execute(query, (retirement_reason, top_k))
    # ... 返回结果
```

**v7.0使用场景：**
```python
# Prophet根据市场环境召回基因
if market_type == 'bull':
    # 牛市 → 召回Bull Holder基因
    bull_genes = experience_db.query_by_niche(
        world_signature=current_ws,
        niche='bull_holder',
        top_k=20
    )
    prophet.revive_agents(bull_genes)

elif market_type == 'bear':
    # 熊市 → 召回Bear Shorter基因
    bear_genes = experience_db.query_by_niche(
        world_signature=current_ws,
        niche='bear_shorter',
        top_k=20
    )
    prophet.revive_agents(bear_genes)

# Prophet复活传奇Agent
legends = experience_db.query_legendary_agents(
    retirement_reason='hero',
    top_k=10
)
prophet.revive_legendary_agents(legends)
```

---

### 4. 寿命管理接口（为v7.0 Phase 3预留）

#### 需要在MetaGenome中预留

```python
# ⚠️ 当前MetaGenome缺少lifespan_counter
# ✅ v7.0 Phase 3添加

@dataclass
class MetaGenome:
    # ... 现有字段
    milestones: List[Dict] = field(default_factory=list)  # 🏅 奖章记录
    
    # ✅ v7.0 Phase 3预留：寿命管理
    lifespan_counter: int = 300  # 当前剩余寿命（cycles）
    max_lifespan: int = 300      # 最大寿命（用于重置）
    
    def age(self, cycles: int = 1):
        """
        ⏱️ 老化（v7.0 Phase 3）
        
        每cycle递减寿命计数器
        """
        self.lifespan_counter -= cycles
    
    def is_expired(self) -> bool:
        """
        💀 检查是否寿命耗尽（v7.0 Phase 3）
        """
        return self.lifespan_counter <= 0
    
    def reset_lifespan(self):
        """
        🔄 重置寿命（v7.0 Phase 3）
        
        用途：
        - Prophet召回传奇Agent时重置寿命
        - Prophet给优秀Agent延寿
        """
        self.lifespan_counter = self.max_lifespan
```

#### 需要在EvolutionManager中预留

```python
# ✅ v7.0 Phase 3预留：寿命检查

def _check_lifespan_expiration(self, current_price: float) -> List[AgentV5]:
    """
    💀 检查寿命耗尽（v7.0 Phase 3）
    
    用途：
    - 替代或补充10代死亡机制
    - 不同生态位配置不同寿命
    
    Returns:
        List[AgentV5]: 寿命耗尽的Agent列表
    """
    expired_agents = []
    
    for agent in list(self.moirai.agents):
        if agent.state != AgentState.ACTIVE:
            continue
        
        if hasattr(agent, 'meta_genome') and agent.meta_genome:
            if agent.meta_genome.is_expired():
                # 寿命耗尽 → 终结
                self.moirai.terminate_agent(
                    agent=agent,
                    reason='lifespan_expired',
                    current_price=current_price
                )
                expired_agents.append(agent)
    
    return expired_agents

def _age_all_agents(self):
    """
    ⏱️ 所有Agent老化（v7.0 Phase 3）
    
    每cycle调用一次
    """
    for agent in self.moirai.agents:
        if hasattr(agent, 'meta_genome') and agent.meta_genome:
            agent.meta_genome.age(cycles=1)
```

**v7.0 Phase 3使用场景：**
```python
# Prophet为不同生态位配置不同寿命
NICHE_LIFESPAN = {
    'scalper': 100,         # 短线：极短寿命
    'trend_follower': 300,  # 趋势：中等寿命
    'bull_holder': 500,     # 牛市持仓：长寿命
}

# 创建Agent时分配寿命
def create_agent_with_niche(niche: str):
    agent = moirai._clotho_create_single_agent()
    agent.niche = niche
    agent.meta_genome.max_lifespan = NICHE_LIFESPAN[niche]
    agent.meta_genome.lifespan_counter = NICHE_LIFESPAN[niche]
    return agent

# 每cycle检查寿命
def run_cycle():
    # ... 交易逻辑
    
    # 所有Agent老化
    evolution_manager._age_all_agents()
    
    # 检查寿命耗尽
    expired = evolution_manager._check_lifespan_expiration(current_price)
    
    # 补充离开者
    if expired:
        evolution_manager._replace_departed_agents(len(expired))
```

---

## 📋 实施计划

### Phase 1：立即优化（不影响v6.0功能）⭐

```
优先级：高
时间：1-2小时
影响：无（只是代码重构）

任务：
1. ✅ 抽取_replace_departed_agents()方法
2. ✅ 添加注释说明v7.0可复用
3. ✅ 单元测试验证

完成标准：
- run_evolution_cycle调用_replace_departed_agents
- 代码更清晰
- v6.0功能不变
```

### Phase 2：预留接口（为v7.0准备）

```
优先级：中
时间：2-3小时
影响：无（只是预留字段和方法）

任务：
1. ⚠️ Agent.niche属性预留（Optional[str]）
2. ⚠️ ExperienceDB增强查询方法
3. ⚠️ EvolutionManager生态位查询方法
4. ⚠️ 添加注释说明v7.0使用场景

完成标准：
- 接口预留完成
- 注释清晰
- v6.0不调用（保持极简）
```

### Phase 3：寿命接口（为v7.0 Phase 3准备）

```
优先级：低
时间：1-2小时
影响：无（只是预留字段）

任务：
1. ⚠️ MetaGenome.lifespan_counter预留
2. ⚠️ 寿命管理方法预留
3. ⚠️ 添加注释说明v7.0 Phase 3使用

完成标准：
- 字段预留完成
- v6.0不使用（保持极简）
```

---

## 💡 封装原则

### 1. 极简主义

```
v6.0原则：
  - 只实现必要功能
  - 预留接口但不使用
  - 注释说明v7.0用途

避免：
  - 过度设计
  - 实现不需要的功能
  - 增加v6.0复杂度
```

### 2. 信手拈来

```
v7.0目标：
  - 调用v6.0接口即可
  - 无需重构底层代码
  - 快速实现新功能

举例：
  # v7.0开发时
  evolution_manager._replace_departed_agents(count=5)  # 直接调用
  experience_db.query_by_niche(niche='bull_holder')   # 直接查询
  agent.assign_niche('trend_follower')                # 直接分配
```

### 3. 向后兼容

```
确保：
  - v6.0功能不变
  - v6.0测试全部通过
  - v7.0开发不影响v6.0

验证：
  - 重新运行v6.0所有测试
  - 确认基因池不变
  - 确认数据纯净100%
```

---

## ✅ 检查清单

### v6.0封装完成标准

```
☑️ 1. 核心方法封装清晰
  - Moirai三女神方法
  - 退休机制方法
  - Immigration方法

☑️ 2. 接口预留完整
  - 生态位接口（Agent.niche）
  - 召回接口（ExperienceDB增强）
  - 寿命接口（MetaGenome.lifespan_counter）

☑️ 3. 注释说明充分
  - 每个方法标注v7.0用途
  - 每个接口说明使用场景
  - 每个预留字段说明目的

☑️ 4. v6.0功能不变
  - 所有测试通过
  - 基因池数据不变
  - 数据纯净100%

☑️ 5. v7.0可复用
  - 调用接口即可
  - 无需重构底层
  - 快速实现新功能
```

---

## 💰 不忘初心，方得始终

```
v6.0目标：筛选优秀基因 ✅ 已完成（24,412个）
v7.0目标：BTC市场盈利 ← 下一步！

封装原则：
  ✅ 为v7.0预留接口
  ✅ 保持v6.0极简稳定
  ✅ 避免过度设计
  ✅ 信手拈来
```

---

*文档创建时间：2025-12-10*  
*v6.0-Stage1完成后的封装检查*  
*确保v7.0开发时"信手拈来"！*

