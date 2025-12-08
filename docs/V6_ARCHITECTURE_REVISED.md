# Prometheus v6.0 架构文档（修订版）

**Version**: 6.0.0-revised  
**Date**: 2025-12-08  
**Status**: 融合专家审查意见  
**Philosophy**: 工程规范 + 进化自由度

---

## 📋 核心设计哲学

### 平衡两个维度

```
维度1：工程规范层（三大铁律）
  → 账簿、资金池、交易、Facade
  → 必须稳定、可靠、可审计
  → 这是"基础设施"

维度2：进化自由度层
  → 繁殖、变异、选择、对抗
  → 需要探索、创新、涌现
  → 这是"生命系统"

关键：通过封装实现"可控的自由度"
```

### 专家审查的核心洞察

```
✅ 你的v6.0是"优秀的工程架构"
❌ 但还不是"具有进化能力的生命系统"

需要增加：
  1. Self-Play对抗系统（最高优先级）
  2. MemoryLayer 2.0（知识系统，不是数据库）
  3. WorldSignature V4（压缩、投影、熵化）
  4. 多模态繁殖（不是单一病毒模式）
  5. 多目标fitness（盈利、风险、稳定性）
  6. 市场惊讶度（鲁棒性指标）
```

---

## 🏗️ 修订后的架构层次

```
┌─────────────────────────────────────────┐
│   用户/测试代码（三大铁律强制执行）       │
│   build_facade() + run_scenario()       │
└──────────────┬──────────────────────────┘
               │ 唯一入口
               ▼
┌─────────────────────────────────────────┐
│   V6Facade（统一封装层）                  │
│   - 工程规范强制执行                      │
│   - 进化策略可插拔                        │
└──────────────┬──────────────────────────┘
               │
      ┌────────┼────────┬────────┐
      ▼        ▼        ▼        ▼
┌──────────┐ ┌────┐ ┌──────┐ ┌─────────┐
│ Self-    │ │WS  │ │Memory│ │Evolution│
│ Play     │ │V4  │ │Layer │ │Manager  │
│ System⭐ │ │    │ │2.0⭐ │ │V6⭐     │
└──────────┘ └────┘ └──────┘ └─────────┘
      │         │        │          │
      └─────────┴────────┴──────────┘
                ▼
   ┌─────────────────────────┐
   │   工程规范层（三大铁律）   │
   │   - 账簿系统（自动对账）   │
   │   - 资金池（统一管理）     │
   │   - 交易生命周期           │
   └─────────────────────────┘
```

---

## 🆕 **核心新增组件**

### 1. Self-Play对抗系统（Level 1，最高优先级）⭐⭐⭐

**为什么是最高优先级？**
```
专家洞察："天才策略"的出现，几乎都依赖：
  - 对抗压力
  - 竞争博弈
  - 内部生态系统复杂性

没有Self-Play：
  → 永远无法产生"战略性策略"
  → 最多只有"统计套利策略"
```

**设计：**
```python
class SelfPlaySystem:
    """
    自我博弈对抗系统
    
    核心功能：
      1. Agent vs Agent（内部竞争）
      2. 对手盘生成器（模拟其他市场参与者）
      3. 压力调节器（动态调整竞争强度）
    """
    
    def __init__(self):
        self.adversarial_market = AdversarialMarket()
        self.agent_arena = AgentArena()
        self.pressure_controller = PressureController()
    
    # ===== 核心机制 =====
    
    def create_adversarial_agents(
        self,
        base_population: List[Agent],
        adversarial_ratio: float = 0.20
    ) -> List[Agent]:
        """
        创建对抗Agent
        
        策略：
          - 20%的Agent作为"对手盘"
          - 他们的目标是"打败"其他Agent
          - 不是为了盈利，而是为了制造压力
        """
        pass
    
    def simulate_competitive_market(
        self,
        agents: List[Agent],
        market_data: pd.DataFrame
    ):
        """
        竞争性市场模拟
        
        特点：
          - Agent之间会互相影响
          - 一个Agent的交易会影响价格
          - 流动性有限，大单会产生滑点
          - 对手盘会故意制造"陷阱"
        """
        pass
    
    def adjust_evolution_pressure(
        self,
        generation: int,
        diversity: float,
        average_fitness: float
    ) -> Dict:
        """
        动态压力调节
        
        规则：
          - 多样性高 → 增加竞争压力（加速进化）
          - 多样性低 → 减少压力（保护探索）
          - 平均fitness高 → 增加对手盘难度
          - 平均fitness低 → 降低难度（给喘息时间）
        """
        pass
```

**与Mock训练学校的结合：**
```
用户要求："增强型Mock训练学校，必须有完整的市场模拟"

实现：
  1. 市场摩擦（滑点、延迟、拒单）
  2. 对手盘（Self-Play的对抗Agent）
  3. 流动性模拟（订单簿深度）
  4. 价格冲击（大单影响价格）

封装：
  MockTrainingSchool = AdversarialMarket + SelfPlaySystem
```

---

### 2. MemoryLayer 2.0（知识系统）⭐⭐

**专家批评：**
```
❌ 当前设计：只是"成绩排行榜"
   - 存 ROI、Sharpe、Genome
   - 查询 topK
   - 提供智能创世

✅ 应该是：真正的"记忆系统"
   - 稀疏记忆（不是全存储）
   - 注意力机制（优先重要经验）
   - 遗忘机制（逐渐淘汰）
   - 压缩机制（State Embedding）
   - 迁移学习（策略间知识共享）
```

**重新设计：**
```python
class MemoryLayerV2:
    """
    记忆系统 2.0
    
    不是数据库，而是知识系统
    """
    
    def __init__(self):
        self.sparse_memory = SparseMemory()           # 稀疏记忆
        self.attention_index = AttentionIndex()       # 注意力索引
        self.experience_replay = PrioritizedReplay()  # 优先经验回放
        self.forgetting_curve = ForgettingCurve()     # 遗忘曲线
        self.state_encoder = StateEncoder()           # 状态编码器
        self.knowledge_transfer = KnowledgeTransfer() # 知识迁移
    
    # ===== 核心机制 =====
    
    def remember(
        self,
        experience: Experience,
        importance: float,
        novelty: float
    ):
        """
        记忆新经验
        
        不是"全部存储"，而是：
          1. 计算重要性（importance）
          2. 计算新颖性（novelty）
          3. 如果重要且新颖 → 强化记忆
          4. 如果平庸 → 不存储或低优先级
        """
        if importance * novelty > threshold:
            self.sparse_memory.store(experience, priority=importance * novelty)
            self.attention_index.add(experience, weight=importance)
    
    def forget(self, time_decay: float):
        """
        遗忘机制
        
        规则：
          - 低优先级经验逐渐衰减
          - 长时间未使用的经验逐渐淡化
          - 但"里程碑经验"永远不忘
        """
        self.sparse_memory.decay(time_decay)
        self.forgetting_curve.update()
    
    def retrieve_with_attention(
        self,
        query: WorldSignature,
        k: int = 10
    ) -> List[Experience]:
        """
        注意力式检索
        
        不是简单的"topK相似度"，而是：
          1. 计算query与所有经验的"注意力得分"
          2. 注意力得分 = 相似度 × 重要性 × 新鲜度
          3. 返回注意力得分最高的K个经验
        """
        attention_scores = self.attention_index.score(query)
        return self.sparse_memory.top_k(attention_scores, k)
    
    def compress_to_latent(
        self,
        experiences: List[Experience]
    ) -> np.ndarray:
        """
        压缩到隐空间
        
        使用AutoEncoder：
          - 输入：多个经验的原始特征
          - 输出：固定长度的latent vector
          - 目的：降维、去噪、提取本质
        """
        return self.state_encoder.encode(experiences)
    
    def transfer_knowledge(
        self,
        from_genome: Genome,
        to_genome: Genome
    ):
        """
        知识迁移
        
        不是"基因交叉"，而是"策略知识共享"：
          - 提取from_genome的"成功经验"
          - 压缩成"知识模块"
          - 注入到to_genome的"记忆"中
          - to_genome可以"借鉴"但不是"复制"
        """
        knowledge = self.knowledge_transfer.extract(from_genome)
        self.knowledge_transfer.inject(to_genome, knowledge)
```

**关键改进：**
```
1. 稀疏记忆：不是全存储，只存"重要+新颖"的经验
2. 注意力索引：检索时考虑"重要性"和"新鲜度"
3. 优先回放：高价值经验被反复学习
4. 遗忘曲线：平庸经验逐渐淡化
5. 状态编码：压缩到latent space
6. 知识迁移：策略间共享知识
```

---

### 3. WorldSignature V4（压缩、投影、熵化）⭐

**专家批评：**
```
❌ WS V3是"特征工程"，不是"世界建模"
   - 表达能力有限
   - 只能找"相似局部"
   - 无法认知"结构性格局"

✅ 应该加入：
   - 压缩机制（PCA / AutoEncoder）
   - 投影机制（latent vector）
   - 熵化机制（信息熵 = 世界复杂度）
   - 分段机制（regime clustering）
```

**重新设计：**
```python
@dataclass
class WorldSignature_V4:
    """
    世界签名 v4.0
    
    不是"特征提取"，而是"世界建模"
    """
    
    # ===== 基础信息（保留） =====
    id: str
    timestamp: float
    instrument: str
    
    # ===== 压缩表示（新增）⭐ =====
    latent_vector: np.ndarray       # 固定长度隐向量（512-dim）
    compression_ratio: float        # 压缩率（信息保留度）
    
    # ===== 熵化指标（新增）⭐ =====
    market_entropy: float           # 市场熵（复杂度）
    surprise_index: float           # 惊讶度（novelty）
    regime_stability: float         # 状态稳定性
    
    # ===== 分段聚类（新增）⭐ =====
    regime_cluster_id: int          # 所属regime
    regime_confidence: float        # 置信度
    regime_transition_prob: Dict    # 转换概率
    
    # ===== 原有维度（保留但降级）=====
    history: HistoryContext         # 历史背景
    present: PresentState           # 当前状态
    future_signals: FutureSignals   # 领先指标
    
    def compute_similarity(self, other: 'WorldSignature_V4') -> float:
        """
        相似度计算（升级版）
        
        不只是"向量余弦相似度"，而是：
          1. latent_vector相似度（权重0.5）
          2. regime_cluster相似度（权重0.3）
          3. market_entropy相似度（权重0.2）
        """
        latent_sim = cosine_similarity(self.latent_vector, other.latent_vector)
        regime_sim = 1.0 if self.regime_cluster_id == other.regime_cluster_id else 0.5
        entropy_sim = 1 - abs(self.market_entropy - other.market_entropy)
        
        return 0.5 * latent_sim + 0.3 * regime_sim + 0.2 * entropy_sim
```

**实现细节：**
```python
class WorldSignatureEncoder:
    """
    世界签名编码器
    
    使用AutoEncoder压缩市场信息
    """
    
    def __init__(self):
        self.autoencoder = AutoEncoder(
            input_dim=2048,   # 原始特征维度
            latent_dim=512    # 压缩后维度
        )
        self.regime_clusterer = RegimeClusterer(n_clusters=20)
        self.entropy_calculator = EntropyCalculator()
    
    def encode(self, market_data: pd.DataFrame) -> WorldSignature_V4:
        """
        编码市场数据到WorldSignature
        
        步骤：
          1. 提取原始特征（2048-dim）
          2. AutoEncoder压缩到latent vector（512-dim）
          3. 计算市场熵
          4. 计算惊讶度
          5. 进行regime聚类
        """
        # 1. 提取原始特征
        raw_features = self._extract_raw_features(market_data)
        
        # 2. 压缩
        latent_vector = self.autoencoder.encode(raw_features)
        compression_ratio = self.autoencoder.reconstruction_loss(latent_vector)
        
        # 3. 计算熵
        market_entropy = self.entropy_calculator.calculate(market_data)
        surprise_index = self.entropy_calculator.surprise(market_data, self.history)
        
        # 4. Regime聚类
        regime_id = self.regime_clusterer.predict(latent_vector)
        regime_conf = self.regime_clusterer.confidence(latent_vector)
        
        return WorldSignature_V4(
            latent_vector=latent_vector,
            compression_ratio=compression_ratio,
            market_entropy=market_entropy,
            surprise_index=surprise_index,
            regime_cluster_id=regime_id,
            regime_confidence=regime_conf,
            ...
        )
```

---

### 4. 多模态繁殖机制（EvolutionManagerV6）⭐

**专家批评：**
```
❌ 单一"病毒式复制"有灾难性隐患：
   - 极端加速基因同质化
   - Winner Take All → 系统死亡
   - 多样性依赖变异率 → 极易失控

✅ 应该加入"多模态繁殖"：
   - 病毒式复制（扩张优秀策略）
   - 混合交叉（生成新结构）
   - 随机重组（突发创新）
   - 深度突变（打破局部最优）
   - 结构大突变（天才碎片）
```

**重新设计：**
```python
class EvolutionManagerV6:
    """
    进化管理器 v6.0
    
    核心改进：多模态繁殖
    """
    
    def __init__(self):
        self.reproduction_strategies = {
            'viral': ViralReplication(),          # 病毒式复制
            'crossover': HybridCrossover(),       # 混合交叉
            'recombination': RandomRecombination(), # 随机重组
            'deep_mutation': DeepMutation(),      # 深度突变
            'structural': StructuralMutation()    # 结构突变
        }
        self.strategy_selector = StrategySelector()
    
    def run_evolution_cycle(
        self,
        agents: List[Agent],
        fitness_scores: List[float],
        diversity_index: float
    ) -> List[Agent]:
        """
        进化周期（多模态）
        
        不是单一繁殖方式，而是：
          1. 评估当前状态（多样性、fitness分布）
          2. 选择合适的繁殖策略组合
          3. 不同策略产生不同比例的后代
        """
        # 1. 选择精英
        elites = self._select_elites(agents, fitness_scores)
        
        # 2. 根据状态选择繁殖策略
        strategy_mix = self.strategy_selector.select(
            diversity=diversity_index,
            avg_fitness=np.mean(fitness_scores),
            generation=self.generation
        )
        
        # 3. 多模态繁殖
        offspring = []
        
        # 70%: 病毒式复制（扩张优秀策略）
        offspring.extend(
            self.reproduction_strategies['viral'].reproduce(
                elites,
                count=int(len(agents) * strategy_mix['viral'])
            )
        )
        
        # 15%: 混合交叉（生成新结构）
        offspring.extend(
            self.reproduction_strategies['crossover'].reproduce(
                elites,
                count=int(len(agents) * strategy_mix['crossover'])
            )
        )
        
        # 10%: 随机重组（突发创新）
        offspring.extend(
            self.reproduction_strategies['recombination'].reproduce(
                elites,
                count=int(len(agents) * strategy_mix['recombination'])
            )
        )
        
        # 4%: 深度突变（打破局部最优）
        offspring.extend(
            self.reproduction_strategies['deep_mutation'].reproduce(
                elites,
                count=int(len(agents) * strategy_mix['deep_mutation'])
            )
        )
        
        # 1%: 结构突变（天才碎片）
        offspring.extend(
            self.reproduction_strategies['structural'].reproduce(
                elites,
                count=int(len(agents) * strategy_mix['structural'])
            )
        )
        
        return offspring
```

**繁殖策略详解：**
```python
class ViralReplication:
    """病毒式复制：克隆+小变异"""
    def reproduce(self, elites, count):
        return [elite.clone().mutate(rate=0.05) for elite in random.choices(elites, k=count)]

class HybridCrossover:
    """混合交叉：有性繁殖"""
    def reproduce(self, elites, count):
        offspring = []
        for _ in range(count):
            parent1, parent2 = random.sample(elites, 2)
            child = parent1.crossover(parent2)
            offspring.append(child.mutate(rate=0.10))
        return offspring

class RandomRecombination:
    """随机重组：打乱基因顺序"""
    def reproduce(self, elites, count):
        offspring = []
        for _ in range(count):
            parent = random.choice(elites)
            child = parent.clone()
            child.genome.shuffle()  # 随机重组
            offspring.append(child.mutate(rate=0.20))
        return offspring

class DeepMutation:
    """深度突变：大幅度变异"""
    def reproduce(self, elites, count):
        offspring = []
        for _ in range(count):
            parent = random.choice(elites)
            child = parent.clone()
            child.mutate(rate=0.50)  # 高变异率
            offspring.append(child)
        return offspring

class StructuralMutation:
    """结构突变：改变基因结构"""
    def reproduce(self, elites, count):
        offspring = []
        for _ in range(count):
            parent = random.choice(elites)
            child = parent.clone()
            # 结构性改变：例如增加/删除基因段
            child.genome.structural_mutate()
            offspring.append(child)
        return offspring
```

---

### 5. 多目标Fitness（不再是单一绝对利润）⭐

**专家批评：**
```
❌ 绝对利润无法引导长期策略：
   - 倾向短周期赌博
   - 风险管理弱化
   - 优秀的低波动策略会被淘汰
   - 会从"侥幸"中学习
   - 极端行情下无防御能力

✅ 必须引入至少3个加权目标：
   1. 绝对利润（主要）
   2. 最大回撤（惩罚项）
   3. 尾部风险（VaR）
```

**重新设计：**
```python
class MultiObjectiveFitness:
    """
    多目标适应度函数
    
    不是单一"绝对利润"，而是加权组合
    """
    
    def __init__(self):
        self.weights = {
            'profit': 0.50,      # 50%: 绝对利润
            'drawdown': 0.25,    # 25%: 最大回撤（惩罚）
            'var': 0.15,         # 15%: 尾部风险（VaR）
            'stability': 0.10    # 10%: 长期稳定性
        }
    
    def calculate(
        self,
        agent: Agent,
        trades: List[Trade],
        current_price: float
    ) -> float:
        """
        计算多目标适应度
        
        公式：
        Fitness = w1 * profit 
                - w2 * drawdown_penalty 
                - w3 * var_penalty 
                + w4 * stability_bonus
        """
        # 1. 绝对利润（归一化）
        profit = agent.calculate_total_pnl(current_price)
        profit_normalized = profit / agent.initial_capital
        
        # 2. 最大回撤（惩罚）
        max_drawdown = agent.calculate_max_drawdown()
        drawdown_penalty = max(0, max_drawdown - 0.20)  # 超过20%开始惩罚
        
        # 3. 尾部风险（VaR 95%）
        returns = agent.get_returns_series()
        var_95 = np.percentile(returns, 5)  # 5%分位数
        var_penalty = max(0, -var_95 - 0.05)  # 超过5%开始惩罚
        
        # 4. 长期稳定性（奖励）
        stability = agent.calculate_stability_score()
        stability_bonus = stability if agent.age > 50 else 0
        
        # 综合
        fitness = (
            self.weights['profit'] * profit_normalized
            - self.weights['drawdown'] * drawdown_penalty
            - self.weights['var'] * var_penalty
            + self.weights['stability'] * stability_bonus
        )
        
        return fitness
    
    def adaptive_weights(
        self,
        market_regime: str,
        generation: int
    ):
        """
        自适应权重
        
        不同市场/阶段，权重不同：
          - 牛市：增加profit权重
          - 熊市：增加drawdown权重
          - 震荡市：增加stability权重
          - 早期：鼓励探索（降低惩罚）
          - 后期：强化风控（增加惩罚）
        """
        if market_regime == 'BULL':
            self.weights['profit'] = 0.60
            self.weights['drawdown'] = 0.20
        elif market_regime == 'BEAR':
            self.weights['profit'] = 0.40
            self.weights['drawdown'] = 0.35
        elif market_regime == 'SIDEWAYS':
            self.weights['profit'] = 0.45
            self.weights['stability'] = 0.20
        
        # 早期降低惩罚
        if generation < 10:
            self.weights['drawdown'] *= 0.5
            self.weights['var'] *= 0.5
```

---

### 6. 市场惊讶度（Surprise Index）

**专家建议：**
```
✅ 引入"市场惊讶度"作为核心指标
   - 能极大提升鲁棒性
   - 识别"异常市场状态"
   - 提前预警风险
```

**实现：**
```python
class SurpriseCalculator:
    """
    市场惊讶度计算器
    
    核心思想：
      - 基于历史分布，当前状态的"意外程度"
      - 高惊讶度 = 异常市场 = 高风险
    """
    
    def __init__(self):
        self.historical_distribution = HistoricalDistribution()
    
    def calculate_surprise(
        self,
        current_ws: WorldSignature_V4,
        history: List[WorldSignature_V4]
    ) -> float:
        """
        计算惊讶度
        
        方法：KL散度
        surprise = KL(current || historical)
        """
        # 1. 构建历史分布
        hist_dist = self.historical_distribution.fit(history)
        
        # 2. 计算当前状态的概率密度
        current_prob = hist_dist.pdf(current_ws.latent_vector)
        
        # 3. 惊讶度 = -log(prob)
        surprise = -np.log(current_prob + 1e-10)
        
        return surprise
    
    def risk_level(self, surprise: float) -> str:
        """
        风险等级
        
        surprise < 2: LOW（正常）
        2 <= surprise < 4: MEDIUM（轻微异常）
        4 <= surprise < 6: HIGH（异常）
        surprise >= 6: CRITICAL（极端异常）
        """
        if surprise < 2:
            return 'LOW'
        elif surprise < 4:
            return 'MEDIUM'
        elif surprise < 6:
            return 'HIGH'
        else:
            return 'CRITICAL'
```

---

## 🔒 **三大铁律的正确定位**

### 用户的明智修正

```
✅ 三大铁律 = 工程规范层（必须严格）
✅ 进化自由度 = 通过封装实现

不是"铁律 vs 自由度"的对立
而是"基础设施稳定 + 上层探索自由"的协同
```

### 铁律适用范围

**严格执行（工程层）：**
```
✅ 账簿系统（自动对账）
✅ 资金池（统一管理）
✅ 交易生命周期（原子操作）
✅ Facade统一入口（数据封装）
```

**封装的自由度（进化层）：**
```
✅ 繁殖策略（多模态，可插拔）
✅ 变异操作（可配置）
✅ 选择压力（动态调节）
✅ Fitness函数（多目标，自适应权重）
✅ Self-Play（对抗强度可调）
```

---

## 📋 **修订后的实施计划（6周）**

### Week 1: Self-Play对抗系统（Level 1，最高优先级）
```
Day 1-2: AdversarialMarket（对手盘生成器）
Day 3-4: AgentArena（Agent vs Agent竞技场）
Day 4-5: PressureController（压力调节器）
Day 6-7: 集成到MockTrainingSchool
```

### Week 2: MemoryLayer 2.0
```
Day 1-2: SparseMemory + AttentionIndex
Day 3-4: PrioritizedReplay + ForgettingCurve
Day 5: StateEncoder（AutoEncoder）
Day 6-7: KnowledgeTransfer
```

### Week 3: WorldSignature V4
```
Day 1-2: AutoEncoder训练
Day 3-4: EntropyCalculator + SurpriseCalculator
Day 5: RegimeClusterer
Day 6-7: 集成测试
```

### Week 4: 多模态繁殖 + 多目标Fitness
```
Day 1-3: 5种繁殖策略实现
Day 4-5: MultiObjectiveFitness
Day 6-7: 动态策略选择器
```

### Week 5: 迁移核心模块到v6/
```
Day 1-3: 迁移并重构核心模块
Day 4-5: 确保三大铁律强制执行
Day 6-7: 基础功能测试
```

### Week 6: 集成测试 + 验证
```
Day 1-3: 完整系统测试
Day 4-5: A/B对比（v5 vs v6）
Day 6-7: 性能优化
```

---

## 🎯 **成功标准（相对最优解）**

### 不是这些（完美解陷阱）：
```
❌ 预测准确率100%
❌ 永远不亏损
❌ 每笔交易都赚钱
```

### 而是这些（真正的成功）：
```
✅ 涌现出"天才策略"（非人工设计）
✅ 系统在Self-Play中持续进化
✅ 多样性保持在健康水平
✅ 长期跑赢BTC（夏普比率 > 1.5）
✅ 四种市场都能盈利（全天候）
✅ 极端行情下有防御能力（最大回撤 < 30%）
```

---

## 📌 **总结**

### v6.0的双重性格

```
左手：工程规范（三大铁律）
  → 稳定、可靠、可审计
  → 账簿、资金池、交易、Facade

右手：进化自由度（封装实现）
  → 探索、创新、涌现
  → Self-Play、多模态繁殖、MemoryLayer

平衡点：可控的自由度
```

### 核心价值观

```
1. 工程规范不是限制，而是基础
2. 进化自由不是混乱，而是封装的策略空间
3. Self-Play是涌现"天才策略"的关键
4. MemoryLayer是从"经验"到"知识"的桥梁
5. 多样性是系统生命力的保障
6. 相对最优解已经足够
```

---

**不忘初心，方得始终。**  
**在黑暗中寻找亮光，在混沌中寻找规则，在死亡中寻找生命。**  
**在对抗中寻找平衡，在进化中寻找涌现。** 💡📐💀🌱⚔️

