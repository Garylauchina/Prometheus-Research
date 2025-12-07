# Prometheus 海量训练计划
**日期**: 2025-12-07  
**目标**: 通过海量碰撞找到最优演化规律（AlphaZero哲学）  
**原则**: 先放开限制，让系统自由探索，从数据中提取规律

---

## 🎯 总体思路

```
AlphaZero的成功之道：
  简单规则 + 海量博弈 = 涌现智能

我们的训练策略：
  极简机制 + 海量训练 = 自然规律
  
关键改变：
  ❌ 不要手动调参（过拟合陷阱）
  ❌ 不要过早优化（限制探索空间）
  ✅ 放开限制，让系统自由碰撞
  ✅ 记录完整数据（WorldSignature + Genome + 结果）
  ✅ 从数据中提取规律
```

---

## 📊 三阶段渐进式训练

### Phase 0: 快速验证（30-60分钟）⚡

```
目标：确保"放开限制"后系统能稳定运行
配置：10 seeds × 50 cycles = 500次实验

改动：
  ✅ full_genome_unlock=True（50个参数全开）
  ✅ 简化Fitness（纯绝对收益，去除持有奖励/频率惩罚）
  ✅ 关闭Immigration（纯自然选择）
  ⚠️ 保留账簿一致性检查（不能完全去掉）

成功标准：
  ✅ 稳定性 ≥ 80%（至少8/10个seed不崩溃）
  ✅ 种群健康（至少50% Agent存活）
  ✅ 交易活跃（至少10笔交易）
  ℹ️ 不要求盈利（现阶段）

执行：
  python3 test_phase0_quick_verify.py

如果失败：
  🛠️ 修复稳定性问题，重新运行
  
如果成功：
  ✅ 进入Phase 1
```

### Phase 1: 同Seed探索（1天）🔬

```
目标：验证"殊途同归" - 相同创世条件，不同演化路径，是否收敛
配置：1个固定seed × 100-200次独立运行 × 200 cycles

核心问题：
  "相同的初始条件，会演化出相同的结果吗？"
  
实验设计：
  genesis_seed = 7001（固定）
  evolution_seed = None（每次真随机）
  
  运行100-200次独立实验，观察：
  - 最终系统收益的分布（均值、方差）
  - 最佳Agent的基因分布（是否收敛到相似基因？）
  - 交易行为的相似性（频率、持仓、方向）
  
期望结果：
  理想：5-10%的差异（殊途同归）✅
  可接受：10-20%的差异（部分收敛）⚠️
  警告：>30%的差异（完全发散）❌
  
如果完全发散：
  说明演化系统太随机，需要增加Agent数量或周期数
  
如果完全相同：
  说明演化系统太确定，检查random seed是否正确
  
执行：
  python3 test_phase1_same_seed.py

数据记录：
  - 每次实验的完整WorldSignature序列
  - 每个Agent的基因快照（每10代）
  - 所有交易决策的context（基因+市场状态+决策）
```

### Phase 2: 多Seed探索（2-3天）🚀

```
目标：大规模碰撞，找到普遍规律
配置：1000个不同seed × 1000 cycles ≈ 100万次实验

核心问题：
  "什么样的初始条件+演化路径能产生最优结果？"
  
实验设计：
  genesis_seed = 7001-8000（1000个）
  evolution_seed = None（真随机）
  cycles = 1000（长期演化）
  
  分批执行：
  - Batch 1: seed 7001-7100（100个）
  - Batch 2: seed 7101-7200（100个）
  - ...
  - Batch 10: seed 7901-8000（100个）
  
  每个batch完成后，立即分析：
  - Top 10%的实验，基因有什么共同点？
  - 不同市场环境（牛/熊/震荡/崩盘），哪些基因更优？
  - 是否出现"超级基因"（多个环境都表现好）？
  
期望输出：
  1. 基因-环境适应矩阵
     | 基因类型 | 牛市 | 熊市 | 震荡 | 崩盘 |
     |---------|------|------|------|------|
     | 趋势型   | +++  | --   | +    | --   |
     | 均值回归 | +    | +    | ++   | -    |
     | 波动捕捉 | ++   | ++   | +    | +++  |
  
  2. 最优基因模板
     根据市场环境，推荐初始基因配置
  
  3. 演化规律
     - 盈利Agent的基因演化轨迹
     - 亏损Agent的基因演化陷阱
  
执行：
  python3 test_phase2_multi_seed.py --batch 1
  python3 test_phase2_multi_seed.py --batch 2
  ...
  python3 test_phase2_multi_seed.py --batch 10

数据存储：
  SQLite数据库（方便查询）+ JSONL文件（详细记录）
  
  表结构：
  - experiments: 实验元数据
  - cycles: 每周期的WorldSignature
  - agents: Agent基因和状态
  - trades: 交易决策和结果
  - analysis: 分析结果
```

### Phase 3: Mock压力测试（1天）💥

```
目标：极端环境测试，验证系统鲁棒性
配置：多种Mock场景 × 100 seeds

核心问题：
  "在极端/异常市场下，系统是否稳定？"
  
Mock场景设计：
  1. 超级牛市（+500% in 6个月）
  2. 极端熊市（-80% in 3个月）
  3. 闪崩事件（-30% in 1小时）
  4. 高波动震荡（±20%每天）
  5. 流动性枯竭（订单簿深度1/10）
  6. 高滑点环境（2-5%滑点）
  7. 多空转换频繁（每天切换）
  
每个场景：
  - 100个不同seed
  - 200 cycles
  - 观察：崩溃率、最大回撤、系统盈利
  
期望结果：
  稳健系统的特征：
  ✅ 在所有场景下稳定性 ≥ 80%
  ✅ 最大回撤 ≤ 50%（无Layer 3保护下）
  ✅ 至少在3/7个场景中盈利
  
如果大量崩溃：
  🛠️ 需要增加Layer 3兜底风控
  
执行：
  python3 test_phase3_mock_stress.py
```

---

## 📊 数据记录方案（关键！）

### 三层数据记录

```python
Layer 0: 市场环境（WorldSignature）
  每个cycle记录：
  {
    "cycle": 1,
    "price": 9524.0,
    "world_signature": {
      "macro_vec": [...],      # 宏观向量
      "micro_vec": [...],      # 微观向量
      "human_tags": ["牛市初期", "低波动"],
      "regime": "early_bull",
      "danger_index": 0.2,
      "opportunity_index": 0.8
    }
  }

Layer 1: Agent表现（Gene-Environment）
  每10代记录Agent快照：
  {
    "agent_id": "Agent_61",
    "generation": 10,
    "genome": {...},         # 完整基因
    "capital": 12500.0,
    "return": 0.25,
    "trades_count": 15,
    
    # 分环境表现（关键！）
    "performance_by_regime": {
      "bull": {"cycles": 50, "return": 0.35},
      "bear": {"cycles": 30, "return": -0.05},
      "sideways": {"cycles": 20, "return": 0.10}
    }
  }

Layer 2: 决策-环境关联（Decision-WorldSignature）
  每笔成功交易记录：
  {
    "agent_id": "Agent_61",
    "cycle": 25,
    "action": "buy",
    "amount": 0.5,
    "price": 10234.0,
    
    # 决策时的市场状态（关键！）
    "world_signature_snapshot": {...},
    
    # 决策时的基因状态（关键！）
    "genome_snapshot": {...},
    
    # Daimon的推理过程
    "reasoning": "趋势偏好(75%): 顺势做多",
    
    # 结果
    "profit": 2025.43,
    "holding_periods": 12
  }
```

### 存储架构

```
prometheus-training-data/
├── experiments/
│   ├── phase1_same_seed/
│   │   ├── seed_7001_run_001.jsonl
│   │   ├── seed_7001_run_002.jsonl
│   │   └── ...
│   ├── phase2_multi_seed/
│   │   ├── batch_01/
│   │   │   ├── seed_7001.jsonl
│   │   │   ├── seed_7002.jsonl
│   │   │   └── ...
│   │   └── batch_02/
│   │       └── ...
│   └── phase3_mock/
│       ├── super_bull/
│       ├── extreme_bear/
│       └── ...
├── analysis/
│   ├── gene_environment_matrix.csv
│   ├── optimal_gene_templates.json
│   ├── evolution_patterns.md
│   └── top_agents.json
└── training.db  # SQLite数据库（快速查询）
```

---

## 🔍 数据分析方案

### Analysis 1: 基因-环境适应矩阵

```python
问题：什么基因在什么环境下表现最好？

方法：
1. 提取所有实验中的Agent表现
2. 按WorldSignature.regime分组
3. 按Genome参数聚类（K-means，10个类）
4. 计算每个基因类在每个环境下的平均收益

输出：
  gene_environment_matrix.csv
  
用途：
  - 创世时根据预期市场环境选择基因模板
  - 进化时根据当前环境调整选择压力
```

### Analysis 2: 最优基因模板

```python
问题：如果重新开始，应该用什么基因初始化？

方法：
1. 提取Top 10%盈利Agent的基因
2. 分析基因参数的分布（均值、方差）
3. 识别"关键参数"（高相关性）

输出：
  optimal_gene_templates.json
  {
    "bull_market": {
      "trend_preference": 0.85,
      "risk_appetite": 0.65,
      "patience": 0.40,
      ...
    },
    "bear_market": {...},
    "sideways": {...}
  }

用途：
  - 指导创世Agent的基因初始化
  - 指导Immigration的基因配置
```

### Analysis 3: 演化轨迹分析

```python
问题：成功Agent的基因如何演化？失败Agent陷入什么陷阱？

方法：
1. 提取每个Agent的基因演化序列
2. 按最终结果分组（Top 10% vs Bottom 10%）
3. 可视化基因演化轨迹

输出：
  evolution_patterns.md（含图表）
  
用途：
  - 识别有害突变（避免）
  - 识别有益突变（鼓励）
```

### Analysis 4: WorldSignature重要性排序

```python
问题：WorldSignature的哪些维度最影响决策？

方法：
1. 提取所有成功交易的WorldSignature
2. 特征重要性分析（Random Forest）
3. 排序并可视化

输出：
  worldsignature_importance.csv
  
用途：
  - 简化WorldSignature（去除无用维度）
  - 优化Prophet计算（重点计算重要维度）
```

---

## ⏱️ 时间估算

```
Phase 0: 快速验证
  时间：30-60分钟
  计算：10 seeds × 50 cycles
  
Phase 1: 同Seed探索
  时间：6-12小时（分批执行）
  计算：100-200 runs × 200 cycles
  
Phase 2: 多Seed探索
  时间：2-3天（分10批）
  计算：1000 seeds × 1000 cycles
  估算：每批10-12小时（可并行）
  
Phase 3: Mock压力测试
  时间：6-8小时
  计算：7个场景 × 100 seeds × 200 cycles
  
数据分析：
  时间：1-2天
  
总计：4-6天（如果24小时不停运行）
```

---

## 🚀 开始执行

### 现在就开始？

```bash
# Step 1: 运行Phase 0快速验证
python3 test_phase0_quick_verify.py

# 如果通过，继续创建Phase 1脚本
# 如果失败，先修复问题
```

### 并行化建议

```
如果有多台机器：
  - 机器1：Phase 2 Batch 1-3
  - 机器2：Phase 2 Batch 4-6
  - 机器3：Phase 2 Batch 7-10
  - VPS：Phase 3 Mock测试
  
可以将4-6天缩短到2-3天
```

---

## ❓ 关键决策点

### 1. 是否简化Fitness？

```
当前Fitness v3：
  score = 绝对收益(40%) + 持有奖励(20%) + 频率惩罚(15%) + ...

AlphaZero式：
  score = 绝对收益(100%)

您的选择？
A: 立即简化（更纯粹，但可能频繁交易）
B: 保留v3（更稳定，但可能过拟合）
```

### 2. 是否关闭Immigration？

```
当前：每20代Immigration一次（注入新基因）

AlphaZero式：纯自然选择（无外部干预）

您的选择？
A: 关闭Immigration（更纯粹）
B: 保留Immigration（防止基因单一化）
```

### 3. 是否保留多样性监控？

```
当前：监控基因熵、血统熵，低于阈值警告

AlphaZero式：不管多样性，让自然选择决定

您的选择？
A: 关闭监控（更纯粹）
B: 保留监控（防止过早收敛）
```

---

**建议：先运行Phase 0，根据结果再决定是否需要调整**

**您觉得这个计划可行吗？现在开始Phase 0？** 🚀

