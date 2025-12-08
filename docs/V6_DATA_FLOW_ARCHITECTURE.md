# v6.0 数据流架构设计
**日期**: 2025-12-08  
**版本**: v6.0 Final  
**核心原则**: 性能优化 + 数据封装 + 职责清晰

---

## 🎯 **核心设计决策**

### **关键问题：WorldSignature应该如何传递？**

经过深入讨论，确定了最优方案：

```
✅ Prophet计算并缓存（1次）
✅ BulletinBoard存储对象缓存（避免重复解析）
✅ Facade统一获取并分发（1次）
✅ Agent传递给Daimon
✅ Daimon保持独立（为未来神经网络替代做准备）

性能提升：125.8倍！
```

---

## 📊 **四层架构数据流（完整版）**

### **第0层：Memory Layer（系统记忆）**
```
ExperienceDB
├─ 存储：(WorldSignature, Genome, ROI, Sharpe, MaxDrawdown)
├─ 查询：query_similar_genomes(current_ws, top_k=100)
└─ 智能创世：smart_genesis(current_ws, count=50, strategy='adaptive')
```

### **第1层：Prophet（战略层）**
```
Prophet（先知）
├─ 输入：市场数据（market_data）
├─ 计算：WorldSignature（14维向量）
├─ 分析：市场状态（bull/bear/sideways）+ 风险等级
├─ 决策：战略建议（配资、杠杆、仓位）
└─ 输出：
   ├─ BulletinBoard.post(JSON) ← 发布JSON格式
   └─ BulletinBoard.cache_world_signature(对象) ← 缓存对象
```

### **第2层：Moirai（管理层）**
```
Moirai（命运三女神）
├─ 输入：BulletinBoard（Prophet的战略）+ ExperienceDB
├─ 创世：
│  ├─ 读取BulletinBoard（WorldSignature）
│  ├─ 查询ExperienceDB（匹配相似基因）
│  └─ 创建Agent（使用匹配的基因）
├─ 繁殖：
│  ├─ 克隆父代基因
│  ├─ 基因变异
│  └─ 创建子代Agent
└─ 淘汰：杀死表现差的Agent

一致性原则：创世和繁殖都由Moirai处理基因
```

### **第3层：Agent + Daimon（执行层）**
```
Agent（个体）
├─ 输入：market_data + world_signature（来自Facade）
├─ 准备context：
│  ├─ market_data
│  ├─ world_signature ← 从Facade传递
│  └─ agent自身信息（capital, position, pnl...）
└─ 调用Daimon：decision = daimon.guide(context)

Daimon（决策中枢）
├─ 输入：context（包含world_signature）
├─ 投票机制：
│  ├─ genome_voice（基因感知）
│  ├─ strategy_voice（策略执行）
│  └─ 未来可扩展：world_signature_voice, risk_voice...
└─ 输出：decision（buy/sell/hold + leverage + confidence）

保留Daimon的意义：
✅ 为未来神经网络替代做准备
✅ 投票机制模块化
✅ 可独立测试
```

---

## 🔄 **完整的信息流（创世阶段）**

```
第0周期（创世）：

1. Facade初始化
   └─ BulletinBoard初始化
   └─ Prophet初始化
   └─ Moirai初始化（传入ExperienceDB）

2. Prophet.genesis_strategy(initial_market_data)
   ├─ 计算WorldSignature（基于前100根K线）
   ├─ 分析市场状态（bull/bear/sideways）
   ├─ 评估风险等级（low/moderate/high/extreme）
   ├─ 制定战略建议（配资、杠杆、仓位）
   ├─ 发布到BulletinBoard：
   │  ├─ JSON格式：ws.to_dict()
   │  └─ 同时缓存对象：bulletin_board.cache_world_signature(ws)
   └─ 返回战略

3. Moirai._genesis_create_agents(bulletin_board, experience_db)
   ├─ 读取BulletinBoard（获取WorldSignature）
   ├─ 查询ExperienceDB：
   │  ├─ 计算相似度：current_ws.similarity(historical_ws)
   │  ├─ 过滤：similarity >= 0.7
   │  ├─ 排序：按(similarity, roi)降序
   │  └─ 返回前100个最相似的基因
   ├─ smart_genesis：
   │  ├─ 70%：直接使用最佳基因
   │  ├─ 20%：变异（mutation_rate=0.3）
   │  └─ 10%：随机探索
   └─ 创建Agent（使用匹配的基因）

4. Agent初始化
   └─ Daimon初始化
   └─ 账簿系统初始化
```

---

## 🔄 **完整的信息流（运行阶段）**

```
每个周期（第1周期开始）：

1. Prophet.update_strategy(current_market_data, cycle)
   ├─ 更新WorldSignature
   ├─ 更新市场状态和风险
   ├─ 发布到BulletinBoard（JSON + 缓存对象）
   └─ 返回战略

2. Facade.run_cycle(market_data)
   ├─ 获取缓存的WorldSignature（1次）← 性能优化！
   │  └─ ws = bulletin_board.get_current_world_signature()
   │
   ├─ 遍历所有Agent（50个）：
   │  └─ agent.make_decision(market_data, world_signature=ws)
   │     ├─ 准备context：
   │     │  ├─ market_data
   │     │  ├─ world_signature ← 从Facade传递
   │     │  └─ agent自身信息
   │     │
   │     └─ daimon.guide(context)
   │        ├─ genome_voice(context) ← 使用world_signature
   │        ├─ strategy_voice(context)
   │        └─ 综合决策
   │
   └─ 执行交易

3. 进化周期（每N周期）：
   └─ EvolutionManagerV5.run_evolution_cycle()
      ├─ 淘汰差的Agent
      └─ 精英繁殖：
         ├─ 克隆基因 ← Moirai处理基因（一致！）
         ├─ 变异
         └─ 创建子代
```

---

## ⚡ **性能优化总结**

### **传统方式（每个Agent解析）：**
```
50个Agent × 1000周期 = 50,000次调用

每次调用：
1. 读取BulletinBoard.get_recent() ← JSON查询
2. json.loads(bulletin.content) ← JSON解析
3. WorldSignatureSimple.from_dict() ← 对象创建

总耗时：~18ms × 1000周期 = 18秒
```

### **缓存方式（Facade统一获取）：**
```
1000周期 × 1次 = 1,000次调用

每次调用：
1. bulletin_board.get_current_world_signature() ← 直接返回对象

总耗时：~0.14ms × 1000周期 = 0.14秒

性能提升：128倍！
```

---

## 🎯 **数据封装总结**

| 层级 | 职责 | 读取BulletinBoard | 解析WorldSignature | 传递数据 |
|------|------|-----------------|------------------|---------|
| **Prophet** | 战略制定 | ❌ 不读取 | ✅ 计算并缓存 | ✅ 发布 |
| **Facade** | 系统协调 | ✅ 读取1次 | ❌ 使用缓存 | ✅ 分发给Agent |
| **Agent** | 个体决策 | ❌ 不读取 | ❌ 使用传递的对象 | ✅ 传递给Daimon |
| **Daimon** | 决策中枢 | ❌ 不读取 | ❌ 使用传递的对象 | ❌ 只输出决策 |

**封装原则：**
- ✅ Prophet负责生产数据
- ✅ BulletinBoard负责存储和缓存
- ✅ Facade负责协调和分发
- ✅ Agent/Daimon只消费数据

---

## 🏆 **Daimon保留的价值**

### **1. 为神经网络替代做准备**
```python
# 当前：基于规则
class RuleBasedDaimon:
    def guide(self, context):
        votes = self._genome_voice(context) + self._strategy_voice(context)
        return self._aggregate_votes(votes)

# 未来：神经网络
class NeuralDaimon:
    def __init__(self, agent):
        self.model = load_neural_network()  # ← 独立状态
    
    def guide(self, context):
        # 将context转换为特征向量
        features = self._prepare_features(context)
        # 神经网络推理
        decision = self.model.predict(features)
        return decision

# Agent不需要改动！
agent.daimon = NeuralDaimon(agent)  # ← 直接替换
```

### **2. 投票机制的模块化**
```python
class Daimon:
    def guide(self, context):
        all_votes = []
        
        # 当前的voice
        all_votes.extend(self._genome_voice(context))
        all_votes.extend(self._strategy_voice(context))
        
        # 未来可扩展（不需要修改Agent）
        all_votes.extend(self._world_signature_voice(context))
        all_votes.extend(self._risk_management_voice(context))
        all_votes.extend(self._social_learning_voice(context))
        
        return self._aggregate_votes(all_votes)
```

### **3. 测试和验证独立性**
```python
# 可以独立测试Daimon的决策逻辑
def test_daimon_decision():
    mock_agent = create_mock_agent()
    daimon = Daimon(mock_agent)
    
    context = {
        'world_signature': create_mock_ws(),
        'capital': 10000,
        # ...
    }
    
    decision = daimon.guide(context)
    assert decision.action in ['buy', 'sell', 'hold']
```

---

## 📝 **最终数据流设计**

### **创世阶段：**
```
V6Facade.run_mock_training(market_data, config)
  ↓
Prophet.genesis_strategy(initial_market_data)
  ├─ 计算WorldSignature
  ├─ BulletinBoard.post(JSON)
  └─ BulletinBoard.cache_world_signature(对象) ← 缓存
  ↓
Moirai._genesis_create_agents(bulletin_board, experience_db)
  ├─ 读取BulletinBoard（获取WorldSignature）
  ├─ ExperienceDB.smart_genesis(current_ws) ← 相似度匹配
  └─ 创建Agent（使用匹配的基因）
```

### **运行阶段：**
```
Facade.run_cycle(market_data, cycle)
  ↓
Prophet.update_strategy(market_data, cycle)
  ├─ 更新WorldSignature
  └─ 缓存到BulletinBoard
  ↓
ws = BulletinBoard.get_current_world_signature() ← 获取缓存（1次）
  ↓
for agent in agents:  # 50个Agent
  ↓
  agent.make_decision(market_data, world_signature=ws)
    ├─ context = {market_data, world_signature, agent_info}
    └─ daimon.guide(context)
       ├─ genome_voice(context) ← 使用world_signature
       ├─ strategy_voice(context)
       └─ aggregate_votes() → decision
```

---

## ✅ **设计优势总结**

| 维度 | 优势 | 数据 |
|------|------|------|
| **性能** | 每周期只解析1次 | 125.8x提升 |
| **封装** | 职责清晰分离 | 4层架构 |
| **扩展** | Daimon可替换 | 神经网络 |
| **测试** | 模块可独立测试 | 单元测试 |
| **一致性** | 创世=繁殖=Moirai处理基因 | 统一 |

---

## 🔧 **实现清单**

### **✅ 已完成：**
- [x] Prophet类创建（378行）
- [x] BulletinBoard缓存机制（+15行）
- [x] Prophet发布时自动缓存
- [x] 测试验证（性能提升125.8x）

### **⏳ 待实现：**
- [ ] Moirai集成ExperienceDB（智能创世）
- [ ] Facade集成Prophet
- [ ] Agent传递world_signature给Daimon
- [ ] 完整集成测试

---

## 🎓 **核心设计哲学**

### **1. 性能优化**
```
不要让50个Agent重复做同一件事
→ Facade统一做1次，然后分发
→ 性能提升：N倍（N=Agent数量）
```

### **2. 数据封装**
```
每一层只知道自己需要的信息
→ Daimon不知道BulletinBoard
→ Agent不知道Prophet
→ 降低耦合，提高可测试性
```

### **3. 职责清晰**
```
Prophet：看宏观，出战略
Moirai：管生死，管基因
Agent：接数据，做交易
Daimon：纯决策，可替换
```

### **4. 为未来做准备**
```
保留Daimon独立性
→ 未来可替换成神经网络
→ Agent代码不需要改动
→ AlphaZero式进化的基础
```

---

**不忘初心，方得始终！** 🎯

---

**状态：数据流架构设计完成** ✅

