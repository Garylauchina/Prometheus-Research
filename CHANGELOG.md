# Changelog

所有重要的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [v6.0-Stage1] - 2025-12-09

### 🎉 重大变更（范式转变）

#### 核心理念转变
- **从"让Agent变聪明"到"在极简环境筛选强基因"**
  - v1.0-5.0的误区：试图通过复杂机制让Agent智能
  - v6.0的正确方向：在极简环境中让基因碎片自然涌现
- **从"市场驱动"到"生态驱动"**
  - 关注生死、淘汰、复制、多样性，而不是市场复杂度
- **从"个体智能"到"种群进化+中央调度"**
  - Agent是牺牲品（策略载体），不是智能体
  - Prophet（先知）负责中央调度

#### 架构简化
- **GenomeVector(50参数) → StrategyParams(6参数)**
  - 移除复杂的心理机制（恐惧、贪婪、FOMO）
  - 移除多层决策系统（三重投票）
  - 保留核心：方向偏好、仓位、持仓、止损、止盈、风险
- **Agent简化**
  - 从"试图理解市场"到"执行策略参数"
  - 决策逻辑极简化
  - 进化速度加快（50代→0-1代）

### ✨ 新增功能

#### V6Facade（统一入口）
- 严格封装，禁止直接调用底层模块
- 提供完整的生命周期管理
- 支持MockTrainingSchool（极简训练）

#### MockTrainingSchool（极简训练环境）
- 100%成交率
- 固定费率（0.1%）
- 无滑点（Stage 1.0，将在1.1中添加）
- 简化的市场数据生成器
- 快速验证进化机制

#### StrategyParams（6参数策略系统）
```python
- directional_bias: 方向偏好（0-1）
- position_size_base: 基础仓位（0-1）
- holding_preference: 持仓偏好（0-1）
- stop_loss_tolerance: 止损容忍度（0-1）
- take_profit_eagerness: 止盈积极度（0-1）
- risk_aversion: 风险厌恶度（0-1）
```

#### Prophet（战略层）
- 市场分析：计算WorldSignature
- 相似度匹配：查询历史最优基因
- 战略发布：通过BulletinBoard发布
- 智能创世：基于历史经验创建Agent

#### ExperienceDB（经验数据库）
- 保存历史最优基因（StrategyParams）
- 记录市场环境（WorldSignature）
- 记录性能指标（ROI, Sharpe, MaxDrawdown）
- 支持相似度查询
- 累积300+条基因

#### 相似度匹配系统
- **加权欧氏距离**（替代余弦相似度）
  - 牛市 vs 熊市：0.755 → 0.179（区分度提升）
  - 突出关键维度（trend, rsi, market_phase）
- **Prophet负责匹配逻辑**（架构清晰）
  - Prophet = 战略层（智慧）
  - ExperienceDB = 数据层（记忆）

#### 智能创世
- 基于当前市场环境（WorldSignature）
- 查询历史相似市场的最优基因
- 'smart'模式：使用历史基因
- 'random'模式：随机创建（用于积累基因）

### ⚡ 性能提升

- **进化收敛速度**：50代 → 0-1代找到最优基因
  - 牛市：directional_bias快速收敛到1.0（做多）
  - 熊市：directional_bias快速收敛到0.22（做空）
- **牛市ROI**：0.7% → 28%+（1000周期，市场+65%）
- **训练速度**：1000周期约2-3分钟（M4芯片）
- **基因积累**：300条（牛/熊/震荡各100条）

### 🐛 Bug修复

#### 进化机制
- **修复breeding_tax_rate参数错误**
  - V6Facade.run_cycle()错误传递breeding_tax_rate
  - EvolutionManagerV5不接受此参数
  - 导致进化无法执行
  - 修复后1000周期训练成功

#### 决策机制
- **修复Daimon的trend依赖bug**
  - 原逻辑依赖market_data.get('trend')
  - 但market_data没有提供trend字段
  - 导致Agent默认为'neutral'，从不交易
  - 修复：基于directional_bias和价格变化决策
  - ROI从0.7%提升到28%+

#### 数据保存
- **修复ExperienceDB的PF/ROI计算bug**
  - 原逻辑使用getattr(agent, 'roi', 0.0)
  - 但Agent对象没有roi属性
  - 导致保存的都是默认值0.0
  - 修复：从private_ledger和current_capital计算
  - 现在保存正确的性能指标

#### 突变机制
- **修复StrategyParams.mutate()返回值bug**
  - mutate()返回新对象，但未赋值
  - 导致变异不生效
  - 修复：child_strategy_params = child_strategy_params.mutate()
  - 现在变异正常工作

### 📚 文档新增

#### 核心文档
- `docs/STAGE1_GOLDEN_RULES.md` - Stage 1的10条黄金规则 ⭐
- `docs/STAGE1_IMPLEMENTATION_PLAN.md` - 详细实施计划
- `docs/SIMILARITY_ARCHITECTURE_V6.md` - 相似度匹配架构
- `docs/WORLDSIGNATURE_SIMILARITY.md` - 相似度计算详解
- `docs/V6_ARCHITECTURE.md` - 完整v6架构文档

#### 分析报告
- `docs/GENE_COLLECTION_SUCCESS.md` - 基因收集成功报告
- `docs/GENE_ANALYSIS_DEEP_DIVE.md` - 基因深度分析
- `docs/STABILITY_VS_PERFORMANCE.md` - 稳定性vs性能分析
- `docs/WORLDSIGNATURE_ANALYSIS.md` - WorldSignature数据分析

#### 修复记录
- `docs/CRITICAL_BUG_FIX_V6_EVOLUTION.md` - 进化bug修复记录
- `docs/TAX_MECHANISM_V6_SUMMARY.md` - 税收机制总结

### 🔄 变更内容

#### 废弃的功能（v5.0）
- ❌ GenomeVector（50参数）→ 改用StrategyParams（6参数）
- ❌ 复杂心理机制（恐惧、贪婪）→ 移除
- ❌ 多层决策系统（三重投票）→ 简化
- ❌ WorldView系统 → 移除
- ❌ 试图让Agent"聪明" → 改为让基因"涌现"

#### 保留但重构的功能
- ✅ Moirai（生死管理）→ 保留，增加智能创世
- ✅ EvolutionManagerV5（进化机制）→ 保留，修复bug
- ✅ AgentAccountSystem（双账簿）→ 保留不变
- ✅ BulletinBoard（公告板）→ 保留，增加缓存
- ✅ Supervisor（监督者）→ 保留，改用V6Facade

### 🎯 验收标准（已达成）

#### 数据层
- ✅ 1000 bars虚拟市场数据
- ✅ 固定费率0.1%
- ✅ 100%成交率
- ✅ 无极端事件

#### 训练层
- ✅ 1000周期训练成功
- ✅ 使用V6Facade统一入口
- ✅ 使用MockTrainingSchool
- ✅ 自动保存到ExperienceDB

#### 基因层
- ✅ ExperienceDB有300+条记录
- ✅ 牛市基因：directional_bias → 1.0
- ✅ 熊市基因：directional_bias → 0.22
- ✅ 震荡市基因：多样化

#### 系统层
- ✅ 进化收敛快（0-1代）
- ✅ 种群稳定（死亡率正常）
- ✅ 可复现（相同seed相似结果）
- ✅ Prophet战略层工作正常
- ✅ 相似度匹配准确（无误匹配）

### 🚀 下一步：v6.1-Stage1.1（计划中）

基于**复杂系统黄金规则**的改进：

#### P0：核心缺失（必须完成）
- 🔄 规则10：结构切换市场（Trend→Range→Fake Breakout，每300 bars切换）
- 🔄 规则3：固定滑点（0.05%，筛选成本敏感型基因）
- 🔄 规则1：扩展市场结构（Range震荡、Fake假突破）

#### P1：优化改进（重要）
- 🔄 规则9：简化为Profit Factor主导（PF = 总盈利/总亏损）
- 🔄 检查突变机制（Immigration、多样性监控）

#### P2：未来扩展（Stage 2准备）
- 🔄 增加bars数（1000→5000）
- 🔄 为Stage 2准备Regime切换机制

预计时间：2-3天

### 📖 参考资料

#### 理论基础
- AlphaZero/self-play系统
- 生物进化理论
- Quality-Diversity (QD)系统
- Evolvable Agent Systems
- 强化学习（Curriculum Learning）
- 人工生命（A-life）

#### 核心洞察
> **复杂智能只能从简化环境中首先出现**  
> （不在复杂环境中直接涌现）

#### Stage路线图
1. **Stage 1（极简）**：纯粹结构，清晰反馈，快速进化，产出基因碎片
2. **Stage 2（中等）**：Regime切换，波动率变化，延迟模拟，先知成熟
3. **Stage 3（复杂）**：历史数据，复杂滑点，极端事件，高频噪音
4. **Stage 4（实盘）**：真实世界验证

---

## [v5.0] - 2024-12-XX（已废弃）

v5.0的完全重构，但走错了方向。详见git历史记录。

---

## [v4.0及更早] - 历史版本

详见git历史记录。
