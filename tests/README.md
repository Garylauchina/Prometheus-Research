# 🧪 Prometheus v6.0 测试

本目录包含v6.0-Stage1的所有测试文件。

---

## ⭐ 核心测试（必看）

### MockTrainingSchool测试
```bash
# 1000周期完整训练测试（推荐）
python test_mock_training_v6_1000cycles.py

# Facade集成测试
python test_mock_training_v6_facade.py

# Phase 1测试
python test_mock_training_phase1.py
```

### Prophet（先知）测试
```bash
# 基础测试
python test_prophet_basic.py

# 智能匹配测试
python test_prophet_matching.py
```

### 智能创世测试
```bash
# 智能创世基础测试
python test_smart_genesis.py

# 智能创世对比测试
python test_smart_genesis_comparison.py
```

---

## 🔧 系统测试

### 税收机制
```bash
python test_tax_mechanism_v6.py
```

### 资金管理
```bash
python test_capital_investment_api.py
python test_capital_ledger_integration.py
python test_genesis_allocation_20pct.py
python test_phase1_20pct_genesis.py
```

### ExperienceDB
```bash
python test_freedom_and_experience_db.py
```

### BulletinBoard
```bash
python test_bulletin_board_cache.py
```

### 相似度计算
```bash
python test_similarity_calculation.py
```

---

## 📊 测试覆盖

- ✅ MockTrainingSchool（极简训练环境）
- ✅ Prophet（战略层）
- ✅ ExperienceDB（经验数据库）
- ✅ 智能创世
- ✅ 相似度匹配
- ✅ 税收机制
- ✅ 资金管理
- ✅ BulletinBoard

---

## 🚀 快速开始

```bash
# 1. 运行核心1000周期测试
cd /path/to/Prometheus-Quant
python tests/test_mock_training_v6_1000cycles.py

# 2. 查看结果
# 输出会显示训练进度和最终结果

# 3. 查看经验数据库
ls experience/gene_collection_v6.db
```

---

## 📝 测试说明

所有测试都基于v6.0-Stage1架构：
- 使用V6Facade统一入口
- 使用MockTrainingSchool极简环境
- 使用StrategyParams（6参数）
- 遵循三大铁律（统一封装、测试规范、不可简化）

---

## 🔍 旧版本测试

v5.0及更早版本的测试已归档到：
```
../archive/v5/tests/
```

共90+个旧测试文件，仅供参考，不推荐运行。

