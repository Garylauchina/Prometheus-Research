# 🧠 Memory Layer数据库设计

**日期**: 2025-12-06  
**主题**: 情境化知识库的完整数据结构

---

## 🎯 核心思想

### 你的洞察：Memory Layer应该记录

1. **WorldSignature** - 市场情境（在什么环境下）
2. **Agent基因组** - 策略特征（谁/什么策略）
3. **Agent行为** - 具体行动（做了什么）
4. **行为结果** - 最终结果（结果如何）

这形成了一个完整的**"情境→策略→行动→结果"**链条！

---

## 📊 完整的数据结构设计

### 核心表结构

#### 表1: Experience（经验记录）⭐核心表

```python
@dataclass
class Experience:
    """单次经验记录（原子级）"""
    
    # ============ 基本信息 ============
    experience_id: str          # 唯一ID
    timestamp: float            # 时间戳
    agent_id: str               # Agent ID
    
    # ============ 情境信息 ============
    world_signature: str        # 市场签名
    world_signature_detailed: Dict  # 详细特征
    market_raw_data: Dict       # 原始市场数据（可选）
    
    # ============ Agent特征 ============
    # 方案A: 完整基因组
    agent_genome: Dict          # 完整基因组
    agent_instinct: Dict        # 本能参数
    agent_lineage: Dict         # 家族信息
    
    # 方案B: 特征向量（更紧凑）
    agent_feature_vector: np.ndarray  # Agent特征向量
    agent_feature_dims: Dict    # 特征维度说明
    
    # ============ 行为信息 ============
    decision: Dict              # 决策内容
    """
    {
        'action': 'buy' / 'sell' / 'hold',
        'position': 0.5,      # 仓位
        'leverage': 5.0,      # 杠杆
        'confidence': 0.8,    # 决策信心
        'reasoning': {...}    # 决策原因（可选）
    }
    """
    
    # ============ 结果信息 ============
    immediate_result: Dict      # 立即结果
    """
    {
        'price_entry': 50000,
        'price_exit': 51000,
        'pnl': 100.0,
        'roi': 0.02,
        'holding_time': 3600
    }
    """
    
    short_term_result: Dict     # 短期结果（可选）
    long_term_result: Dict      # 长期结果（可选）
    
    # ============ 元数据 ============
    metadata: Dict              # 其他元数据
    """
    {
        'environment': 'mock' / 'vps' / 'production',
        'version': 'v5.5',
        'generation': 42,
        'parent_ids': [...]
    }
    """
```

---

### 设计讨论1: Agent特征的存储方式

#### 方案A: 完整基因组 ⭐推荐

```python
agent_genome = {
    'lineage': {
        'family_traits': {...},
        'ancestral_wisdom': {...}
    },
    'genome': {
        'risk_tolerance': 0.7,
        'learning_rate': 0.3,
        'exploration': 0.5,
        # ... 更多基因
    },
    'instinct': {
        'greed_level': 0.6,
        'fear_level': 0.4,
        # ... 更多本能
    }
}
```

**优点**：
- ✅ 完整信息
- ✅ 可以完全重现Agent
- ✅ 可以分析每个基因的影响

**缺点**：
- ❌ 存储空间大
- ❌ 查询可能慢

---

#### 方案B: 特征向量（紧凑）

```python
agent_feature_vector = np.array([
    0.7,  # risk_tolerance
    0.3,  # learning_rate
    0.5,  # exploration
    0.6,  # greed_level
    # ... 20-50个关键特征
])

agent_feature_dims = {
    0: 'risk_tolerance',
    1: 'learning_rate',
    # ...
}
```

**优点**：
- ✅ 紧凑
- ✅ 快速比较
- ✅ 支持向量相似度

**缺点**：
- ❌ 信息损失
- ❌ 不能完全重现Agent

---

#### 💡 推荐：混合方案

```python
@dataclass
class Experience:
    # 存储完整基因组
    agent_genome_full: Dict  # 完整信息（JSON）
    
    # 同时存储特征向量
    agent_feature_vector: np.ndarray  # 快速检索用
    
    # 最佳实践：
    # - 检索时用向量（快速）
    # - 分析时用完整基因组（准确）
```

---

### 设计讨论2: 行为的粒度

#### 级别1: 决策级（最细粒度）

```python
# 记录每个决策点
decision = {
    'action': 'buy',
    'position': 0.5,
    'leverage': 5.0,
    'confidence': 0.8,
    
    # 决策过程（可选，用于分析）
    'decision_process': {
        'base_signal': 0.6,         # 基础信号
        'prophet_influence': 0.1,   # Prophet影响
        'memory_influence': 0.2,    # 历史影响
        'peer_influence': 0.05,     # 同伴影响
        'final_decision': 0.75      # 最终决策
    }
}
```

**适用**: 详细分析、训练、研究

---

#### 级别2: 交易级（中粒度）⭐推荐

```python
# 记录完整交易
trade = {
    'entry': {
        'timestamp': 1234567890,
        'price': 50000,
        'position': 0.5,
        'leverage': 5.0
    },
    'exit': {
        'timestamp': 1234571490,
        'price': 51000,
        'reason': 'take_profit'
    },
    'result': {
        'pnl': 100.0,
        'roi': 0.02,
        'holding_time': 3600
    }
}
```

**适用**: 常规分析、性能评估

---

#### 级别3: 周期级（粗粒度）

```python
# 记录整个生命周期
lifecycle = {
    'birth': {
        'timestamp': ...,
        'initial_capital': 10000,
        'parents': [...]
    },
    'trades': [...],  # 所有交易摘要
    'death': {
        'timestamp': ...,
        'final_capital': 8000,
        'cause': 'bankruptcy',
        'age': 1000  # 存活周期数
    },
    'summary': {
        'total_trades': 50,
        'win_rate': 0.48,
        'total_roi': -0.2
    }
}
```

**适用**: 高层分析、种群研究

---

#### 💡 推荐：都记录，分表存储

```python
# 表1: Decisions（决策表）- 最细粒度
decisions = []  # 每个决策点

# 表2: Trades（交易表）- 中粒度
trades = []     # 每笔完整交易

# 表3: Lifecycles（生命周期表）- 粗粒度
lifecycles = [] # 每个Agent的一生

# 关联关系:
# Lifecycle -> Trades -> Decisions
```

---

### 设计讨论3: 结果的时间维度

#### 即时结果（Immediate Result）

```python
immediate_result = {
    'pnl': 100.0,           # 交易盈亏
    'roi': 0.02,            # 投资回报率
    'holding_time': 3600,   # 持有时间
    'slippage': 0.01,       # 实际滑点
    'fee': 0.05             # 手续费
}
```

**时间**: 交易完成时
**用途**: 评估单次交易

---

#### 短期结果（Short-term Result）

```python
short_term_result = {
    'next_3_trades_roi': 0.05,    # 后续3笔交易ROI
    'next_hour_capital': 10200,   # 1小时后资金
    'strategy_persistence': True   # 策略是否持续
}
```

**时间**: 交易后1小时-1天
**用途**: 评估策略连贯性

---

#### 长期结果（Long-term Result）

```python
long_term_result = {
    'lifecycle_impact': 0.15,     # 对整个生命周期的贡献
    'offspring_success': 0.8,     # 后代成功率
    'strategy_evolution': True,   # 策略是否进化
    'knowledge_value': 0.9        # 知识价值评分
}
```

**时间**: Agent死亡后
**用途**: 评估长期价值

---

#### 💡 推荐：分阶段记录

```python
@dataclass
class Experience:
    # 即时记录（必须）
    immediate_result: Dict
    
    # 延迟记录（可选，异步更新）
    short_term_result: Optional[Dict] = None
    long_term_result: Optional[Dict] = None
    
    # 更新标记
    result_status: str = 'immediate'  # 'immediate' -> 'short_term' -> 'long_term'
```

---

## 🗄️ 完整的数据库Schema

### 核心表设计

#### 表1: experiences（经验表）⭐核心

```sql
CREATE TABLE experiences (
    -- 基本信息
    experience_id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    agent_id TEXT NOT NULL,
    
    -- 情境信息
    world_signature TEXT NOT NULL,
    world_signature_level INTEGER,  -- 1:粗 2:中 3:细 4:向量
    world_features JSON,  -- 详细特征
    
    -- Agent特征
    agent_genome JSON,  -- 完整基因组
    agent_feature_vector BLOB,  -- numpy array
    agent_generation INTEGER,
    agent_age INTEGER,
    
    -- 行为信息
    action TEXT,  -- 'buy', 'sell', 'hold'
    position REAL,
    leverage REAL,
    confidence REAL,
    decision_detail JSON,
    
    -- 结果信息
    immediate_pnl REAL,
    immediate_roi REAL,
    holding_time REAL,
    
    short_term_roi REAL,
    long_term_value REAL,
    
    -- 元数据
    environment TEXT,  -- 'mock', 'vps', 'production'
    version TEXT,
    metadata JSON,
    
    -- 索引字段
    result_status TEXT,  -- 'immediate', 'short_term', 'long_term'
    created_at REAL,
    updated_at REAL
);

-- 索引
CREATE INDEX idx_world_sig ON experiences(world_signature);
CREATE INDEX idx_agent_id ON experiences(agent_id);
CREATE INDEX idx_timestamp ON experiences(timestamp);
CREATE INDEX idx_action ON experiences(action);
CREATE INDEX idx_roi ON experiences(immediate_roi);
```

---

#### 表2: world_signatures（签名表）

```sql
CREATE TABLE world_signatures (
    signature TEXT PRIMARY KEY,
    level INTEGER,  -- 粗中细
    
    -- 统计信息（快速查询用）
    occurrence_count INTEGER,
    avg_roi REAL,
    best_roi REAL,
    worst_roi REAL,
    success_rate REAL,
    
    -- 最佳策略（预计算）
    best_agent_features JSON,
    best_actions JSON,
    
    -- 元数据
    first_seen REAL,
    last_seen REAL,
    
    created_at REAL,
    updated_at REAL
);

CREATE INDEX idx_sig_occurrence ON world_signatures(occurrence_count DESC);
CREATE INDEX idx_sig_roi ON world_signatures(avg_roi DESC);
```

---

#### 表3: agent_genes（基因库）

```sql
CREATE TABLE agent_genes (
    gene_id TEXT PRIMARY KEY,
    agent_id TEXT,
    
    -- 基因信息
    genome JSON,
    feature_vector BLOB,
    
    -- 性能统计
    total_experiences INTEGER,
    avg_roi REAL,
    best_signature TEXT,  -- 最擅长的签名
    
    -- 演化信息
    generation INTEGER,
    parent_ids JSON,
    offspring_count INTEGER,
    
    -- 元数据
    born_at REAL,
    died_at REAL,
    lifespan REAL,
    
    created_at REAL,
    updated_at REAL
);

CREATE INDEX idx_gene_roi ON agent_genes(avg_roi DESC);
CREATE INDEX idx_gene_generation ON agent_genes(generation);
```

---

#### 表4: trades（交易表）

```sql
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    experience_id TEXT,  -- 关联到experience
    agent_id TEXT,
    
    -- 交易信息
    entry_timestamp REAL,
    entry_price REAL,
    entry_position REAL,
    
    exit_timestamp REAL,
    exit_price REAL,
    exit_reason TEXT,
    
    -- 结果
    pnl REAL,
    roi REAL,
    holding_time REAL,
    
    -- 上下文
    world_signature TEXT,
    
    created_at REAL
);

CREATE INDEX idx_trade_agent ON trades(agent_id);
CREATE INDEX idx_trade_sig ON trades(world_signature);
CREATE INDEX idx_trade_roi ON trades(roi DESC);
```

---

## 🔍 关键查询场景

### 场景1: 情境匹配查询

```python
def query_similar_experiences(signature: str, limit: int = 10):
    """
    查询相似情境下的历史经验
    
    返回：最相似的经验，按相似度和ROI排序
    """
    # SQL
    query = """
    SELECT e.*, 
           similarity(e.world_signature, ?) as sim_score
    FROM experiences e
    WHERE sim_score > 0.7
    ORDER BY sim_score DESC, e.immediate_roi DESC
    LIMIT ?
    """
    
    return db.execute(query, (signature, limit))
```

---

### 场景2: 最佳策略查询

```python
def get_best_strategy_for_signature(signature: str):
    """
    获取某情境下的最佳策略
    
    返回：历史上表现最好的Agent特征和行为
    """
    # SQL
    query = """
    SELECT 
        e.agent_genome,
        e.decision_detail,
        AVG(e.immediate_roi) as avg_roi,
        COUNT(*) as sample_count
    FROM experiences e
    WHERE e.world_signature = ?
    GROUP BY e.agent_genome
    HAVING sample_count > 5  -- 至少5个样本
    ORDER BY avg_roi DESC
    LIMIT 1
    """
    
    return db.execute(query, (signature,))
```

---

### 场景3: Agent特征分析

```python
def analyze_gene_performance(gene_feature_vector: np.ndarray):
    """
    分析某基因特征的表现
    
    返回：该基因在不同情境下的表现
    """
    # 找相似基因的所有经验
    similar_genes = find_similar_feature_vectors(gene_feature_vector, threshold=0.9)
    
    # 按签名分组统计
    query = """
    SELECT 
        e.world_signature,
        COUNT(*) as count,
        AVG(e.immediate_roi) as avg_roi,
        STDDEV(e.immediate_roi) as std_roi
    FROM experiences e
    WHERE e.agent_id IN (?)
    GROUP BY e.world_signature
    ORDER BY count DESC
    """
    
    return db.execute(query, (similar_genes,))
```

---

### 场景4: 情境演化预测

```python
def predict_next_phase(current_signature: str):
    """
    预测市场下一个阶段
    
    基于历史上该签名之后通常发生什么
    """
    # SQL
    query = """
    SELECT 
        e2.world_signature as next_signature,
        COUNT(*) as occurrence,
        AVG(e2.immediate_roi) as avg_roi
    FROM experiences e1
    JOIN experiences e2 
        ON e2.timestamp > e1.timestamp 
        AND e2.timestamp < e1.timestamp + 3600  -- 1小时内
    WHERE e1.world_signature = ?
    GROUP BY e2.world_signature
    ORDER BY occurrence DESC
    LIMIT 5
    """
    
    return db.execute(query, (current_signature,))
```

---

## 💡 关键设计决策

### 决策1: 完整性 vs 效率

**问题**: 存储完整基因组太大？

**解决**：
```python
# 方案A: 完整存储（推荐）
# - 磁盘便宜
# - 信息完整
# - 可以完全重现

# 方案B: 压缩存储
import zlib
compressed_genome = zlib.compress(json.dumps(genome).encode())

# 方案C: 引用存储
# - agent_genes表存完整基因
# - experiences表只存gene_id
```

**推荐**: 方案C（引用存储）
- ✅ 避免重复
- ✅ 节省空间
- ✅ 保持完整性

---

### 决策2: 实时 vs 批量

**问题**: 每个决策都立即写数据库？

**解决**：
```python
# 方案A: 实时写入
# 优点: 数据不丢失
# 缺点: 可能慢

# 方案B: 批量写入（推荐）
class MemoryLayer:
    def __init__(self):
        self.buffer = []
        self.buffer_size = 1000
    
    def record_experience(self, exp):
        self.buffer.append(exp)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        # 批量插入
        db.executemany("INSERT INTO ...", self.buffer)
        self.buffer = []
```

**推荐**: 批量写入 + 定期flush
- ✅ 高效
- ✅ 可以设置flush间隔（如每100个或每10秒）

---

### 决策3: 向量索引

**问题**: 如何快速找到相似的Agent特征？

**解决**：
```python
# 方案A: 使用Faiss（Facebook AI Similarity Search）
import faiss

class MemoryLayer:
    def __init__(self):
        self.index = faiss.IndexFlatL2(dimension)
    
    def add_agent_vector(self, vector):
        self.index.add(vector)
    
    def search_similar_agents(self, query_vector, k=10):
        distances, indices = self.index.search(query_vector, k)
        return indices

# 方案B: 使用专门的向量数据库
# - Milvus
# - Pinecone
# - Qdrant
```

**推荐**: 
- v5.5: 简单的numpy搜索（够用）
- v6.0: 集成Faiss（如果性能需要）

---

## 🎯 使用示例

### 示例1: 记录经验

```python
# Agent做了一个决策
experience = Experience(
    experience_id=generate_id(),
    timestamp=time.time(),
    agent_id=agent.agent_id,
    
    # 情境
    world_signature=current_sig.signature,
    world_signature_detailed=current_sig.features.__dict__,
    
    # Agent特征
    agent_genome=agent.get_genome(),
    agent_feature_vector=agent.get_feature_vector(),
    
    # 行为
    decision={
        'action': 'buy',
        'position': 0.5,
        'leverage': 5.0,
        'confidence': 0.8
    },
    
    # 结果（交易后更新）
    immediate_result={
        'pnl': 100.0,
        'roi': 0.02
    }
)

# 记录到Memory Layer
memory.record_experience(experience)
```

---

### 示例2: 查询最佳策略

```python
# 当前市场签名
current_sig = WorldSignature.encode(market_data)

# 查询历史相似情况
similar_cases = memory.query_similar_experiences(
    signature=current_sig.signature,
    limit=10
)

# 找出最成功的策略
best_strategies = [
    case for case in similar_cases
    if case.immediate_result['roi'] > 0.1
]

# 提取最佳Agent特征
if best_strategies:
    best_genes = [s.agent_genome for s in best_strategies]
    
    # Agent可以参考这些基因
    agent.blend_with_historical_genes(best_genes)
```

---

### 示例3: 分析Agent强项

```python
# 分析某个Agent最擅长什么情境
agent_experiences = memory.get_agent_experiences(agent_id)

# 按签名分组
sig_performance = defaultdict(list)
for exp in agent_experiences:
    sig_performance[exp.world_signature].append(exp.immediate_result['roi'])

# 找出最强签名
best_signatures = sorted(
    sig_performance.items(),
    key=lambda x: np.mean(x[1]),
    reverse=True
)[:5]

print(f"Agent最擅长的5种情境:")
for sig, rois in best_signatures:
    print(f"{sig}: 平均ROI {np.mean(rois):.2%}")
```

---

## 🎊 总结

### 你的设计思路是对的！⭐⭐⭐⭐⭐

Memory Layer应该记录：
1. ✅ WorldSignature（情境）
2. ✅ Agent基因组（策略特征）
3. ✅ Agent行为（具体行动）
4. ✅ 行为结果（immediate/short/long-term）

### 关键设计决策

1. **Agent特征**: 混合存储（完整基因组 + 特征向量）
2. **行为粒度**: 分层记录（决策/交易/生命周期）
3. **结果时间**: 分阶段更新（即时/短期/长期）
4. **存储方式**: 引用存储 + 批量写入
5. **查询优化**: 索引 + 向量搜索

### 数据库Schema

- `experiences` - 核心经验表
- `world_signatures` - 签名统计表
- `agent_genes` - 基因库表
- `trades` - 交易明细表

### 这个设计实现了

- ✅ 完整的知识记录
- ✅ 高效的查询检索
- ✅ 情境化的策略匹配
- ✅ 持续的学习积累

**这就是v6.0 Memory Layer的核心架构！** 🚀

---

**下一步**: 明天实现WorldSignature，为Memory Layer铺路！

---

**最后更新**: 2025-12-06 深夜
**设计者**: Prometheus开发团队

