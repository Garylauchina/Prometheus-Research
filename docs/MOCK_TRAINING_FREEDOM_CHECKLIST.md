# Mock训练完全自由度清单
**日期**: 2025-12-08  
**版本**: v6.0 Final

---

## ✅ **完全自由的参数（20个）**

### **核心参数（2个）**
```python
cycles: int                           # 训练周期数
total_system_capital: float           # 系统初始资金
```

### **进化参数（5个）**
```python
agent_count: int = 50                 # 创世Agent个数
genesis_allocation_ratio: float = 0.2 # 创世配资比例（20%给Agent，80%资金池）
evolution_interval: int = 10          # 进化周期（每N周期进化一次）
elimination_rate: float = 0.3         # 淘汰率（30%）
elite_ratio: float = 0.2              # 精英比例（20%）
```

### **创世参数（3个）**
```python
genesis_strategy: str = 'adaptive'    # 创世策略: 'pure_random', 'adaptive', 'hybrid'
genesis_seed: Optional[int] = None    # 创世随机种子（None=真随机）
full_genome_unlock: bool = False      # 是否解锁所有基因（渐进式/激进式）
```

### **交易参数（4个）**
```python
max_leverage: float = 100.0           # 最大杠杆倍数
max_position_pct: float = 0.8         # 单次开仓上限（占Agent总资金的%）
enable_short: bool = True             # 是否允许做空
fee_rate: float = 0.0005              # 手续费率（0.05% taker）
```

### **经验库参数（3个）**
```python
experience_db_path: Optional[str] = None  # 数据库路径（None=从0开始）
top_k_to_save: int = 10               # 保存最佳Agent数量
save_experience_interval: int = 50    # 保存经验间隔（每N周期保存一次）
```

### **验证参数（3个）**
```python
validation_data: Optional[pd.DataFrame] = None  # 验证集数据
validation_cycles: int = 1000         # 验证周期数
auto_validate: bool = False           # 是否训练后自动验证
```

---

## 🔒 **硬约束（系统保证，不可配置）**

### **税收机制（Moirai内部）**
```python
TARGET_RESERVE_RATIO = 0.20           # 20%流动资金生死线
FIXED_TAX_RATE = 0.10                 # 10%固定税率
```

**税率逻辑：**
- 资金池 >= 20%：税率 0%（不征税）
- 资金池 < 20%：税率 10%（保护生死线）

**设计理由：** AlphaZero哲学 - 极简规则，让测试暴露问题

---

## 📊 **ExperienceDB保存机制**

### **保存时机：**
1. **间隔保存：** 每`save_experience_interval`周期保存一次（例如：50, 100, 150...）
2. **最终保存：** 训练结束时再保存一次

### **保存内容：**
```python
{
    'run_id': '20251208_232226_cycle50',       # 运行ID + 周期标记
    'market_type': 'test',                     # 市场类型
    'world_signature': WorldSignatureSimple,   # 14维市场签名
    'genome': Agent.genome,                    # Agent基因
    'roi': float,                              # ROI
    'sharpe': float,                           # 夏普比率（如果有）
    'max_drawdown': float                      # 最大回撤（如果有）
}
```

### **查询机制：**
```python
# 智能创世时查询
best_genomes = experience_db.query_best_genomes(
    world_signature=current_ws,
    market_type='bull',
    top_k=10,
    similarity_threshold=0.8
)
```

---

## 🎯 **使用示例**

### **极简配置（只设置核心参数）**
```python
config = MockTrainingConfig(
    cycles=1000,
    total_system_capital=1_000_000
    # 其它全部使用默认值
)
```

### **完全自定义配置**
```python
config = MockTrainingConfig(
    # 核心
    cycles=2000,
    total_system_capital=10_000_000,
    
    # 进化
    agent_count=100,
    genesis_allocation_ratio=0.3,  # 30%给Agent
    evolution_interval=5,           # 每5周期进化
    elimination_rate=0.5,           # 淘汰50%
    elite_ratio=0.1,                # 保留10%精英
    
    # 创世
    full_genome_unlock=True,        # 激进模式
    genesis_strategy='adaptive',
    genesis_seed=42,
    
    # 交易
    max_leverage=50.0,              # 最大50x
    max_position_pct=0.6,           # 最大60%仓位
    enable_short=True,
    fee_rate=0.0002,                # 0.02%费率
    
    # 经验库
    experience_db_path='my_experience.db',
    top_k_to_save=20,
    save_experience_interval=100,   # 每100周期保存
    
    # 验证
    validation_data=validation_df,
    validation_cycles=500,
    auto_validate=True,
    
    # 日志
    log_interval=50,
    enable_debug_log=True
)
```

---

## 🔍 **参数验证规则**

```python
assert cycles > 0
assert total_system_capital > 0
assert agent_count > 0
assert 0 < genesis_allocation_ratio <= 1
assert 0 <= elimination_rate < 1
assert 0 < elite_ratio < 1
assert max_leverage >= 1
assert 0 < max_position_pct <= 1
assert validation_cycles > 0
if auto_validate:
    assert validation_data is not None
```

---

## ✅ **验证清单**

- [x] 所有20个参数可配置
- [x] elite_ratio和elimination_rate正确传递
- [x] full_genome_unlock正确传递
- [x] ExperienceDB间隔保存机制工作正常
- [x] 税收机制完全封装在Moirai内部
- [x] 对账100%通过
- [x] 0 ERROR日志
- [x] 严格遵守三大铁律

---

**状态：✅ 完全自由度已实现** ✅

