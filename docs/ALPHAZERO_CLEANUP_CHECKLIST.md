# AlphaZero重构 - 清理检查清单

## 📋 目标

系统性地清理所有遗留的过度设计引用，确保系统100%符合AlphaZero极简哲学。

---

## 🔴 **高优先级（阻塞测试）**

### 1. `agent.instinct` 引用
**错误**: `'AgentV5' object has no attribute 'instinct'`

**影响文件**（12个）:
- [ ] `prometheus/facade/v6_facade.py`
- [ ] `prometheus/core/moirai.py`
- [ ] `prometheus/core/inner_council.py`
- [ ] `prometheus/memory/memory_manager.py`
- [ ] `prometheus/core/diversity_monitor.py`
- [ ] `prometheus/trading/live_engine_full.py`
- [ ] `prometheus/trading/live_engine_fixed.py`
- [ ] `prometheus/trading/live_engine.py`
- [ ] `prometheus/backtest/historical_backtest.py`
- [ ] `prometheus/backtest/crazy_mode_backtest.py`
- [ ] `prometheus/core/diversity_protection.py`
- [ ] `prometheus/core/evolution_manager_v5.py`

**清理策略**:
- 替换为 `agent.strategy_params`
- 或删除相关逻辑（如果是diversity相关）

---

### 2. `metrics` 未定义
**错误**: `name 'metrics' is not defined`

**可能位置**:
- [ ] `prometheus/facade/v6_facade.py` (run_cycle方法中)
- [ ] `prometheus/core/evolution_manager_v5.py`

**清理策略**:
- 移除所有diversity metrics的引用
- 删除相关的监控逻辑

---

## 🟡 **中优先级（代码清理）**

### 3. `agent.emotion` 引用
**搜索命令**: `grep -r "agent\.emotion\|\.emotion\." --include="*.py" prometheus/`

**清理策略**:
- 移除所有emotion相关逻辑
- Agent已不再有emotion属性

---

### 4. Diversity相关文件（可选删除）
以下文件已不再使用，可考虑删除：
- [ ] `prometheus/core/diversity_monitor.py`
- [ ] `prometheus/core/diversity_protection.py`
- [ ] `prometheus/core/diversity_visualizer.py`
- [ ] `prometheus/core/dual_entropy.py`
- [ ] `prometheus/core/niche_protection.py`

**清理策略**:
- 暂时保留（不删除，避免import错误）
- 或添加文件头注释标记为"已废弃"

---

### 5. `Instinct` 类引用
**搜索命令**: `grep -r "from.*instinct import\|import.*Instinct" --include="*.py" prometheus/`

**清理策略**:
- 替换为 `from .strategy_params import StrategyParams`
- 或注释掉import

---

## 🟢 **低优先级（文档和测试）**

### 6. 更新文档
- [ ] 更新 `README.md` - 反映AlphaZero式架构
- [ ] 更新 `docs/ARCHITECTURE.md` - 移除diversity部分
- [ ] 创建 `docs/ALPHAZERO_PHILOSOPHY.md` - 说明设计理念

---

### 7. 更新测试
- [ ] 修复 `test_phase0_quick_verify.py`
- [ ] 修复其他测试文件中的instinct/emotion引用

---

## 📊 **清理进度**

### 已完成 ✅
```
✅ 创建StrategyParams（替代Instinct）
✅ 重构Agent（移除Instinct/Emotion/自杀/冥思/顿悟）
✅ 重构Daimon（2个voice：genome + strategy）
✅ 极简Fitness（只有绝对收益）
✅ 病毒式复制（替代交配）
✅ 移除双熵系统（血统熵+基因熵）
✅ 移除Immigration机制
✅ 清理evolution_manager_v5.py
✅ 清理v6_facade.py（部分）
```

### 进行中 🔄
```
🔄 清理所有instinct引用
🔄 清理所有metrics引用
```

### 待完成 ⏳
```
⏳ 清理emotion引用
⏳ 清理diversity文件
⏳ 更新文档
⏳ 更新测试
```

---

## 🛠️ **清理工具命令**

### 1. 搜索instinct引用
```bash
cd /Users/liugang/Cursor_Store/Prometheus-Quant
grep -r "\.instinct" --include="*.py" prometheus/ | grep -v "# " | wc -l
```

### 2. 搜索emotion引用
```bash
grep -r "\.emotion" --include="*.py" prometheus/ | grep -v "# " | wc -l
```

### 3. 搜索diversity引用
```bash
grep -ri "diversity_monitor\|diversity_protector\|blood_lab" --include="*.py" prometheus/ | wc -l
```

### 4. 搜索Immigration引用
```bash
grep -r "inject_immigrants\|immigration" --include="*.py" prometheus/ | grep -v "# " | wc -l
```

---

## 🎯 **清理目标**

### 代码统计目标
```
当前: ~15,000 行核心代码
目标: ~12,000 行核心代码（精简20%）
已精简: ~700 行
还需精简: ~2,300 行
```

### 文件数量目标
```
当前: ~80 个核心文件
目标: <70 个核心文件
已删除/废弃: 0
待处理: 5-10 个diversity相关文件
```

---

## 📝 **清理注意事项**

### ⚠️ **不要删除**
- ❌ 不要删除任何测试文件
- ❌ 不要删除任何文档
- ❌ 不要删除backward-compatible的入口

### ✅ **清理原则**
1. **注释而非删除** - 先注释掉，确认无影响后再删除
2. **逐个文件清理** - 每清理一个文件，立即测试
3. **保持兼容性** - 旧版本的文件（如agent_v4.py）可以保留
4. **提交频繁** - 每完成一个小步骤就提交

---

## 🚀 **下一步行动**

### 立即执行（今天）
1. [ ] 清理 `prometheus/facade/v6_facade.py` 中的 `instinct` 引用
2. [ ] 清理 `prometheus/core/moirai.py` 中的 `instinct` 引用
3. [ ] 修复 `metrics` 未定义错误
4. [ ] 运行 Phase 0 测试验证

### 明天执行
5. [ ] 清理其余10个文件的 `instinct` 引用
6. [ ] 清理所有 `emotion` 引用
7. [ ] 标记废弃文件
8. [ ] 更新文档

---

## 📈 **成功标准**

### 测试通过
- [ ] `test_phase0_quick_verify.py` 100%通过
- [ ] 无 `AttributeError` 错误
- [ ] 无 `NameError` 错误

### 代码质量
- [ ] 无 `instinct` 引用（除了被注释的代码）
- [ ] 无 `emotion` 引用（除了被注释的代码）
- [ ] 无 `diversity_monitor` 活跃引用
- [ ] 无 `Immigration` 活跃机制

### 系统运行
- [ ] 可以成功创建Agent
- [ ] 可以成功运行进化
- [ ] 可以成功进行病毒式复制
- [ ] Fitness计算正确

---

**最后更新**: 2025-12-08 03:35:00  
**负责人**: Cursor AI Assistant  
**状态**: 进行中 🔄

