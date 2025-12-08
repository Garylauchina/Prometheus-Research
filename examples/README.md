# 📚 Prometheus v6.0 使用示例

本目录包含v6.0-Stage1的使用示例和训练脚本。

---

## 🚀 快速开始

### 1. 基因收集训练

```bash
# 收集牛市/熊市/震荡市的基因
python train_and_collect_genes.py

# 预计时间：3-5分钟
# 输出：experience/gene_collection_v6.db
```

**说明**：这个脚本会：
- 清空旧的经验数据库
- 训练3种市场环境（牛/熊/震荡）
- 每种市场1000周期
- 保存Top 100基因到数据库

---

### 2. 多轮训练

```bash
# 多轮训练，积累更多基因
python train_multi_rounds.py --rounds 2 --cycles 1000

# 参数：
#   --rounds: 训练轮数（默认3）
#   --cycles: 每轮周期数（默认1000）
```

**说明**：多轮训练可以：
- 积累更多样化的基因
- 验证基因的稳定性
- 观察基因的重复出现频率（稳定性指标）

---

### 3. 基因分析

```bash
# 分析收集的基因
python analyze_genes.py

# 输出：
#   - 各市场Top 10基因
#   - 基因参数分布
#   - ROI/Sharpe/MaxDrawdown统计
```

**说明**：分析会显示：
- 牛市最优基因（directional_bias → 1.0）
- 熊市最优基因（directional_bias → 0.22）
- 震荡市多样化基因

---

### 4. 跨轮对比

```bash
# 对比不同训练轮次的基因
python compare_rounds.py

# 输出：
#   - 各轮次基因特征
#   - 参数分布对比
#   - 稳定性分析
```

---

### 5. Agent行为诊断

```bash
# 诊断Agent的决策行为
python diagnose_agent_behavior.py

# 用于调试：
#   - Agent为什么不交易？
#   - 决策逻辑是否正确？
#   - 持仓管理是否合理？
```

---

## 📊 完整工作流

```bash
# 步骤1：收集基因（首次运行）
python train_and_collect_genes.py

# 步骤2：分析结果
python analyze_genes.py

# 步骤3：多轮训练（可选）
python train_multi_rounds.py --rounds 3

# 步骤4：对比分析
python compare_rounds.py

# 步骤5：如有问题，诊断
python diagnose_agent_behavior.py
```

---

## 🎯 训练目标

### Stage 1目标
- ✅ 产生100+条不同基因
- ✅ Top 20基因PF > 1.5
- ✅ 发现"可迁移基因"（在所有市场表现好）
- ✅ 发现"专用基因"（在特定市场表现优异）

### 预期结果
```
牛市：
  - directional_bias → 1.0（做多）
  - ROI: 28%+（市场+65%）

熊市：
  - directional_bias → 0.22（做空）
  - ROI: 50%+（市场-60%）

震荡市：
  - 多样化策略
  - ROI: 2-5%
```

---

## 📝 脚本说明

### train_and_collect_genes.py
- **功能**：基础的基因收集训练
- **时间**：3-5分钟
- **输出**：300条基因（100/市场）

### train_multi_rounds.py
- **功能**：多轮训练，增加基因多样性
- **时间**：可配置
- **输出**：累积的基因库

### analyze_genes.py
- **功能**：分析基因库
- **时间**：<1分钟
- **输出**：统计报告

### compare_rounds.py
- **功能**：跨轮对比分析
- **时间**：<1分钟
- **输出**：对比报告

### diagnose_agent_behavior.py
- **功能**：诊断工具
- **时间**：<1分钟
- **输出**：诊断报告

---

## 🔧 高级用法

### 自定义市场
```python
from prometheus.training.mock_training_school import MockTrainingSchool
from prometheus.facade.v6_facade import V6Facade

# 自定义市场数据
market_data = your_custom_market_data()

# 使用Facade训练
facade = V6Facade(instrument="BTC-USDT")
result = facade.run_mock_training(market_data, config)
```

### 自定义配置
```python
from prometheus.config.mock_training_config import MockTrainingConfig

config = MockTrainingConfig(
    cycles=2000,              # 增加周期
    total_system_capital=20000,  # 增加资金
    genesis_strategy='smart'  # 使用智能创世
)
```

---

## 💡 提示

1. **首次运行**：先运行`train_and_collect_genes.py`建立基因库
2. **智能创世**：有基因库后，使用`genesis_strategy='smart'`
3. **多样性**：多轮训练可以增加基因多样性
4. **稳定性**：重复出现的基因更稳定
5. **诊断**：遇到问题先运行`diagnose_agent_behavior.py`

---

## 📖 参考文档

- [Stage 1黄金规则](../docs/v6/STAGE1_GOLDEN_RULES.md)
- [实施计划](../docs/v6/STAGE1_IMPLEMENTATION_PLAN.md)
- [v6.0架构](../docs/v6/V6_ARCHITECTURE.md)
- [基因分析](../docs/v6/GENE_ANALYSIS_DEEP_DIVE.md)

---

## 🚀 下一步

完成基因收集后，可以：
1. 实施Stage 1.1改进（结构切换市场）
2. 进入Stage 2（Regime切换）
3. 实现Prophet的种群调度

详见：[实施计划](../docs/v6/STAGE1_IMPLEMENTATION_PLAN.md)

