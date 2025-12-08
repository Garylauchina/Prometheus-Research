# Mock训练架构重构进度
**日期**: 2025-12-08  
**目标**: 统一封装Mock训练，严格遵守"三大铁律"

---

## ✅ **已完成（Step 1-3）**

### **Step 1: Moirai封装税收机制** ✅
- 📍 **文件**: `prometheus/core/moirai.py`
- ✅ 添加 `TARGET_RESERVE_RATIO = 0.20` （硬约束）
- ✅ 添加 `FIXED_TAX_RATE = 0.10` （可测试调整）
- ✅ 实现 `_lachesis_calculate_breeding_tax()` 方法
  - 极简逻辑：资金池>=20%不征税，<20%征税10%
  - 自动保证20%资金池生死线
  - 完全封装，用户无感知

### **Step 2: 移除EvolutionManagerV5旧税率逻辑** ✅
- 📍 **文件**: `prometheus/core/evolution_manager_v5.py`
- ✅ 移除 `run_evolution_cycle()` 的 `breeding_tax_rate` 参数
- ✅ 移除 `use_dynamic_tax` 和相关逻辑
- ✅ 修改 `_viral_replicate()` 调用 `Moirai._lachesis_calculate_breeding_tax()`
- ✅ 删除 `_calculate_dynamic_tax_rate()` 方法（70行代码）
- ✅ 无lint错误

### **Step 3: 创建MockTrainingConfig** ✅
- 📍 **文件**: `prometheus/config/mock_training_config.py` （新建）
- ✅ `MockTrainingConfig` dataclass（完全自由参数）
- ✅ `MockTrainingResult` dataclass（完整结果封装）
- ✅ 移除 `breeding_tax_rate` 参数（税率由Moirai自动计算）
- ✅ 参数验证 `__post_init__()`

---

## 🚧 **待完成（Step 4-5）**

### **Step 4: V6Facade实现run_mock_training()** 
- 📍 **文件**: `prometheus/facade/v6_facade.py`
- ⏳ 添加 `run_mock_training(market_data, config)` 方法
- ⏳ 内部创建所有底层模块（Moirai/EvolutionManager/CapitalPool）
- ⏳ 严格封装，不对外暴露模块引用
- ⏳ 返回 `MockTrainingResult`

### **Step 5: 创建测试脚本** 
- 📍 **文件**: `test_mock_training_v6.py` （新建）
- ⏳ 使用 `build_facade()` + `run_mock_training()`
- ⏳ 验证数据封装正确性
- ⏳ 验证税收机制工作正常
- ⏳ 验证对账100%通过

---

## 📊 **核心改进**

### **税收机制（v6.0极简版）**
```python
# ❌ 旧版：用户可配置，复杂分级
config = MockTrainingConfig(
    breeding_tax_rate=0.15  # 用户配置
)

# ✅ 新版：Moirai自动，极简二元
# 用户完全无感知，Moirai自动保证20%生死线
# 资金池 >= 20%：税率 0%
# 资金池 < 20%：税率 10%
```

### **数据封装检查清单**
- [x] Agent资金计算正确（realized + unrealized）
- [x] CapitalPool balance正确
- [x] 税收 reclaim/allocate 正确
- [ ] 对账验证正常工作（待Step 5测试）
- [ ] 无底层模块泄漏（待Step 4完成）

---

## 🔧 **下一步行动**

1. **立即实现Step 4**: 在`V6Facade`中添加`run_mock_training()`方法
2. **数据封装核查**: 确保所有数据流清晰、一致
3. **创建测试脚本**: 验证完整流程
4. **运行1000周期**: 观察资金池变化，验证10%税率是否合适

---

## 📝 **关键设计决策记录**

### **为什么选择极简税率？**
- ❌ 分级税率（0%, 5%, 15%, 30%）= 过度设计
- ✅ 二元税率（0%, 10%）= 极简，可测试
- ✅ 让数据说话，而不是提前预判

### **为什么税率封装在Moirai？**
- ✅ Moirai是"命运女神"，掌管生死（包括繁殖）
- ✅ 税收是繁殖的一部分，自然属于Moirai
- ✅ 用户不应该配置税率，这是系统内部机制

### **为什么不处理极端回撤？**
- ✅ AlphaZero哲学：简单优先
- ✅ 测试驱动：问题驱动优化
- ✅ 先不管，让测试暴露问题

---

## 🎯 **成功标准**

1. ✅ 税率完全封装在Moirai，用户无感知
2. ✅ 无lint错误
3. ⏳ 测试脚本运行成功
4. ⏳ 对账100%通过
5. ⏳ 资金池稳定在15%~25%（测试1000周期）

---

**遵守三大铁律：**
1. ✅ 统一封装，统一调用，严禁旁路
2. ⏳ 严格执行测试规范（待Step 5）
3. ✅ 不可为测试通过而简化底层机制

