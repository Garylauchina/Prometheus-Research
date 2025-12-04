# 明天工作清单（2025-12-06）

## 🎯 今日目标：优化生态位保护和参数调优

---

## ⏰ 时间规划（预计4-5小时）

### 上午（2-3小时）
**任务1：增强生态位保护系统** ⭐ P0

### 下午（1-2小时）
**任务2：动态压力响应优化** ⭐ P1

### 晚上（30分钟）
**任务3：验证测试** ⭐ P1

---

## 📝 详细任务

### ✅ 任务1：增强生态位保护系统（2-3小时）

**问题**：极端压力测试中基因熵从0.27降到0.057（-79%）

#### 子任务 1.1：修改 `niche_protection.py`

```python
# 需要调整的参数
class NicheProtectionSystem:
    def __init__(self):
        # 当前参数
        self.endangered_threshold = 0.1  # 10%
        self.dominant_threshold = 0.4    # 40%
        self.max_bonus = 0.3             # 30%奖励
        self.max_penalty = 0.5           # 50%惩罚
        
        # 建议优化为：
        self.endangered_threshold = 0.15  # 15% ⬆️
        self.dominant_threshold = 0.35    # 35% ⬇️
        self.max_bonus = 0.5              # 50%奖励 ⬆️
        self.max_penalty = 0.7            # 70%惩罚 ⬆️
```

**修改文件**：`prometheus/core/niche_protection.py`

#### 子任务 1.2：添加强制多样性机制

```python
# 在 evolution_manager_v5.py 中添加
def _check_diversity_crisis(self) -> bool:
    """检查多样性危机"""
    health = self.blood_lab.population_checkup(self.moirai.agents)
    return health.gene_entropy < 0.1  # 基因熵 < 0.1 触发危机

def _emergency_diversity_injection(self):
    """紧急多样性注入"""
    # 1. 强制创建3-5个随机新Agent
    # 2. 禁止相似度>90%的Agent交配
    # 3. 临时提高变异率到50%
```

**修改文件**：`prometheus/core/evolution_manager_v5.py`

#### 子任务 1.3：创建测试脚本

**创建文件**：`test_niche_enhanced.py`
- 测试新参数下的生态位保护
- 验证多样性是否改善

---

### ✅ 任务2：动态压力响应优化（1-2小时）

**问题**：压力测试中压力值恒定0.494537

#### 子任务 2.1：实现动态变异率

```python
# 在 evolution_manager_v5.py 中修改
def _calculate_mutation_rate(self, gene_entropy: float) -> float:
    """动态变异率：基因熵越低，变异率越高"""
    base_rate = 0.1
    entropy_boost = 0.5 * (1 - gene_entropy)  # 熵0时boost=0.5
    return min(base_rate + entropy_boost, 0.6)  # 最高60%
```

**修改文件**：`prometheus/core/evolution_manager_v5.py`

#### 子任务 2.2：压力响应Agent表现

```python
# 在 mastermind.py 中修改
def evaluate_environmental_pressure(self, ...):
    # 添加：如果Agent表现差，增加压力
    if agent_performance_stats:
        if agent_performance_stats['profitable_ratio'] < 0.1:
            pressure *= 1.2  # 增加20%压力
        elif agent_performance_stats['profitable_ratio'] > 0.7:
            pressure *= 0.8  # 降低20%压力
```

**修改文件**：`prometheus/core/mastermind.py`

---

### ✅ 任务3：验证测试（30分钟）

#### 子任务 3.1：重新运行压力测试

```powershell
python test_extreme_stress.py
```

**期望结果**：
- 基因熵下降 < 50%（当前79%）
- 最终基因熵 > 0.15（当前0.057）
- 健康状态不降到critical

#### 子任务 3.2：对比分析

```powershell
# 对比优化前后
python -c "
import pandas as pd
old = pd.read_csv('extreme_stress_test_results.csv')
new = pd.read_csv('extreme_stress_test_results_optimized.csv')
print('优化前基因熵:', old['gene_entropy'].iloc[-1])
print('优化后基因熵:', new['gene_entropy'].iloc[-1])
print('改善:', (new['gene_entropy'].iloc[-1] - old['gene_entropy'].iloc[-1]) / old['gene_entropy'].iloc[-1] * 100, '%')
"
```

---

## 🎯 成功标准

### 最低标准（必须达到）
- ✅ 基因熵最终值 > 0.15
- ✅ 健康状态不恶化到critical
- ✅ 代码无新增bug

### 理想标准（争取达到）
- ⭐ 基因熵最终值 > 0.20
- ⭐ 健康状态保持warning
- ⭐ 盈利率有所改善（>5%）

---

## 📁 需要修改的文件

1. `prometheus/core/niche_protection.py` - 参数调整
2. `prometheus/core/evolution_manager_v5.py` - 多样性机制+动态变异
3. `prometheus/core/mastermind.py` - 动态压力响应
4. `test_niche_enhanced.py` - 新测试脚本（创建）

---

## 🛠️ 开发命令速查

```powershell
# 运行测试
python test_niche_enhanced.py
python test_extreme_stress.py

# 查看结果
type extreme_stress_test_results_optimized.csv

# 对比分析
python load_and_analyze.py
```

---

## 💡 Tips

1. **小步快跑**：先改一个参数，测试，再改下一个
2. **保存旧版本**：修改前备份关键文件
3. **记录对比**：每次测试都保存结果CSV
4. **提交Git**：每完成一个任务就commit

---

## 📊 当前状态回顾

### 问题
- 基因熵：0.269 → 0.057 (-79%) 🚨
- 健康状态：warning → critical 🚨

### 目标
- 基因熵：保持 > 0.15 ✅
- 健康状态：保持 warning ✅

---

## ⏭️ 后续计划（如果明天完成快）

可选任务：
- [ ] 4年历史数据回测
- [ ] 多币种测试（ETH）
- [ ] 可视化图表生成

---

**预计完成时间**：明天晚上20:00前  
**难度评估**：中等（参数调优）  
**成功概率**：90%+

---

💪 加油！明天继续让Prometheus更强大！

