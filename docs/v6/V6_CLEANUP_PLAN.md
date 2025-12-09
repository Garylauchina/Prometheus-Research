# 🧹 v6.0 代码库清理方案

**创建日期**: 2025-12-09  
**目标**: 清理v1.0-5.0的旧代码，保持v6.0代码库整洁  
**原则**: 归档不删除，保留git历史  

---

## 📊 **当前状态**

```
根目录测试文件：104个
其中：
- v6.0相关：约20个 ✅ 保留
- v1.0-5.0旧测试：约80个 ⚠️ 需要归档
- 实验性测试：约4个 ⚠️ 需要归档
```

---

## 🎯 **清理目标**

### 根目录结构（清理后）
```
Prometheus-Quant/
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
│
├── prometheus/          # 核心代码
│   ├── core/
│   ├── facade/
│   ├── training/
│   ├── config/
│   └── v6/             # Stage 2-3预留
│
├── tests/              # 正式测试（新建）⭐
│   ├── test_v6_facade.py
│   ├── test_mock_training.py
│   ├── test_prophet.py
│   ├── test_experience_db.py
│   └── ...
│
├── examples/           # 使用示例（新建）⭐
│   ├── train_stage1.py
│   ├── analyze_genes.py
│   └── ...
│
├── scripts/            # 工具脚本（新建）⭐
│   ├── monitor_training.sh
│   └── ...
│
├── archive/            # 归档（新建）⭐
│   ├── v5/
│   │   ├── tests/
│   │   └── docs/
│   ├── v4/
│   └── experiments/
│
├── docs/               # 文档
│   ├── v6/            # v6.0文档（新建）⭐
│   │   ├── STAGE1_GOLDEN_RULES.md
│   │   ├── STAGE1_IMPLEMENTATION_PLAN.md
│   │   └── ...
│   ├── v5/            # v5.0文档（归档）
│   └── archive/       # 旧文档归档
│
└── experience/         # 经验数据库
    └── gene_collection_v6.db
```

---

## 📋 **清理清单**

### 🟢 保留（v6.0相关）

#### 测试文件
```
✅ test_mock_training_v6_1000cycles.py ⭐ 核心测试
✅ test_mock_training_v6_facade.py
✅ test_prophet_matching.py
✅ test_prophet_basic.py
✅ test_smart_genesis.py
✅ test_smart_genesis_comparison.py
✅ test_freedom_and_experience_db.py
✅ test_similarity_calculation.py
✅ test_tax_mechanism_v6.py
✅ test_bulletin_board_cache.py
✅ test_capital_investment_api.py
✅ test_capital_ledger_integration.py
✅ test_genesis_allocation_20pct.py
✅ test_phase1_20pct_genesis.py
```

#### 训练/分析脚本
```
✅ train_and_collect_genes.py ⭐ 核心训练
✅ train_multi_rounds.py
✅ analyze_genes.py
✅ compare_rounds.py
✅ diagnose_agent_behavior.py
```

#### 工具脚本
```
✅ monitor_training.sh
```

---

### 🟡 归档（v1.0-5.0相关）

#### 需要归档到 archive/v5/tests/
```
⚠️ test_v5_integration.py
⚠️ test_v53_*.py（所有v5.3测试）
⚠️ test_fear_*.py（旧的恐惧机制测试）
⚠️ test_genome_modes.py（旧的基因系统）
⚠️ test_daimon_improvement.py（旧的决策系统）
⚠️ test_mastermind_pressure.py
⚠️ test_diversity_*.py
⚠️ test_fitness_*.py
⚠️ test_evolution_*.py（非v6版本）
⚠️ test_training_school.py（旧版）
⚠️ test_extreme_stress*.py
⚠️ test_multi_regime.py（旧版）
⚠️ test_signature_integration.py（旧版）
⚠️ test_visualizer.py
⚠️ test_agent_directly.py
⚠️ test_trade_api_fix.py
⚠️ test_trading_frequency.py
⚠️ test_forced_dual_position.py
⚠️ ...（约80个文件）
```

#### 需要归档到 archive/experiments/
```
⚠️ test_quick_fix_verify.py
⚠️ diagnose_*.py（除了v6版本）
⚠️ fix_*.py
⚠️ 其他实验性脚本
```

---

### 🔴 可以删除（临时/重复文件）

```
❌ test_*.pyc
❌ __pycache__/
❌ *.log（除了重要的训练日志）
❌ 明确标记为"temp"的文件
```

---

## 🚀 **执行步骤**

### 第1步：创建归档目录结构

```bash
mkdir -p archive/v5/tests
mkdir -p archive/v5/docs
mkdir -p archive/v4
mkdir -p archive/experiments
mkdir -p tests
mkdir -p examples
mkdir -p scripts
mkdir -p docs/v6
mkdir -p docs/archive
```

### 第2步：移动v6.0测试到tests/目录

```bash
# 移动核心测试
mv test_mock_training_v6_*.py tests/
mv test_prophet_*.py tests/
mv test_smart_genesis*.py tests/
mv test_similarity_calculation.py tests/
mv test_tax_mechanism_v6.py tests/
mv test_bulletin_board_cache.py tests/
mv test_capital_*.py tests/
mv test_genesis_allocation_20pct.py tests/
mv test_phase1_20pct_genesis.py tests/
mv test_freedom_and_experience_db.py tests/
```

### 第3步：移动训练/分析脚本到examples/

```bash
mv train_and_collect_genes.py examples/
mv train_multi_rounds.py examples/
mv analyze_genes.py examples/
mv compare_rounds.py examples/
mv diagnose_agent_behavior.py examples/
```

### 第4步：移动工具脚本到scripts/

```bash
mv monitor_training.sh scripts/
```

### 第5步：归档v5测试到archive/v5/tests/

```bash
# 移动所有v5相关测试
mv test_v5*.py archive/v5/tests/
mv test_v53*.py archive/v5/tests/
mv test_fear*.py archive/v5/tests/
mv test_genome_modes.py archive/v5/tests/
mv test_daimon_improvement.py archive/v5/tests/
# ... 等等
```

### 第6步：归档v5文档到docs/archive/v5/

```bash
# 移动旧文档
mv docs/V5*.md docs/archive/v5/ 2>/dev/null || true
mv docs/OLD*.md docs/archive/ 2>/dev/null || true
# 保留V6*.md在docs/
```

### 第7步：整理v6.0文档到docs/v6/

```bash
mv docs/STAGE1*.md docs/v6/
mv docs/SIMILARITY*.md docs/v6/
mv docs/WORLDSIGNATURE*.md docs/v6/
mv docs/GENE*.md docs/v6/
mv docs/PROPHET*.md docs/v6/
mv docs/V6_ARCHITECTURE.md docs/v6/
mv docs/TAX_MECHANISM_V6*.md docs/v6/
```

### 第8步：创建README索引

在每个目录创建README.md说明。

---

## 📝 **清理后的目录结构**

```
Prometheus-Quant/
├── README.md                        ⭐ 项目主README
├── CHANGELOG.md                     ⭐ 更新日志
├── requirements.txt                 
│
├── prometheus/                      ⭐ 核心代码（不动）
│
├── tests/                           ⭐ 正式测试（14个）
│   ├── README.md                    "v6.0测试说明"
│   ├── test_mock_training_v6_1000cycles.py
│   └── ...
│
├── examples/                        ⭐ 使用示例（5个）
│   ├── README.md                    "如何使用v6.0"
│   ├── train_and_collect_genes.py
│   └── ...
│
├── scripts/                         ⭐ 工具脚本（1个）
│   ├── README.md                    "工具脚本说明"
│   └── monitor_training.sh
│
├── docs/                            ⭐ 文档
│   ├── v6/                          "v6.0文档"
│   │   ├── README.md
│   │   ├── STAGE1_GOLDEN_RULES.md
│   │   └── ...
│   ├── archive/                     "归档文档"
│   │   └── v5/
│   └── (其他通用文档)
│
├── archive/                         ⭐ 代码归档（不删除）
│   ├── v5/
│   │   ├── tests/                   "80+个v5测试"
│   │   └── docs/                    "v5文档"
│   ├── v4/
│   └── experiments/                 "实验性代码"
│
└── experience/                      ⭐ 数据（不动）
```

---

## ✅ **清理后的好处**

```
对新用户：
✅ 一眼就能看到v6.0的测试在tests/
✅ 知道从examples/开始学习
✅ 不会被104个测试文件吓到

对开发者：
✅ 清晰的代码组织
✅ 容易找到需要的文件
✅ 可以专注于v6.0开发

对项目：
✅ 专业的项目结构
✅ 符合Python最佳实践
✅ 保留了所有历史（archive/）
✅ Git历史完整
```

---

## ⚠️ **注意事项**

### 不要删除，只归档
```
❌ 不要: rm test_old.py
✅ 应该: mv test_old.py archive/v5/tests/
```

### 保留git历史
```
✅ 使用 git mv（会保留历史）
✅ 而不是 mv + git rm
```

### 创建README
```
每个目录都应该有README.md说明：
- tests/README.md
- examples/README.md
- scripts/README.md
- archive/README.md
```

### 更新引用
```
⚠️ 清理后需要更新：
- README.md中的文件路径
- docs/中的引用
- .gitignore（如果需要）
```

---

## 🚀 **执行计划**

### 今天（可选）
```
如果精力充足：
→ 创建目录结构
→ 移动v6.0核心文件
→ 创建各目录的README

如果太累：
→ 明天再做
→ 先休息
```

### 明天（推荐）
```
1. 执行第1-8步（约1小时）
2. 创建各目录README（约30分钟）
3. 更新主README（约15分钟）
4. 测试验证（约15分钟）
5. Git提交（v6.0-cleanup）
```

### 预计时间
```
总计：2-3小时
可以分多次完成
```

---

## 📋 **验收清单**

- [ ] 创建目录结构（tests/, examples/, scripts/, archive/）
- [ ] 移动v6.0测试到tests/（14个）
- [ ] 移动示例到examples/（5个）
- [ ] 移动脚本到scripts/（1个）
- [ ] 归档v5测试到archive/v5/tests/（80+个）
- [ ] 整理v6文档到docs/v6/（10+个）
- [ ] 创建各目录README（5个）
- [ ] 更新主README
- [ ] 测试验证（运行几个关键测试）
- [ ] Git提交

---

## 🎯 **成功标准**

```
清理后：
✅ 根目录干净（只有README、CHANGELOG等）
✅ tests/目录有14个v6测试
✅ examples/目录有5个示例
✅ archive/目录有80+个旧文件
✅ 所有文件都能找到
✅ Git历史完整
✅ 测试仍然能运行
```

---

## 💡 **建议**

```
我的建议：
→ 今天休息，明天清理
→ 清理是v6.0-Stage1的收尾工作
→ 完成后再发布v6.0.1（清理版）

或者：
→ 如果精力充足，今天可以快速完成
→ 创建目录结构（5分钟）
→ 移动关键文件（10分钟）
→ 其他的明天慢慢整理
```

