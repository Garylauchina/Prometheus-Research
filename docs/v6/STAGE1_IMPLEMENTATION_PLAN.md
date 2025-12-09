# 🎯 Stage 1 实施计划

**创建日期**: 2025-12-09  
**基于**: 复杂系统专家的残酷建议  
**目标**: 在极简环境中筛选强基因，为Stage 2打基础  

---

## 📋 **总览**

```
当前状态：Stage 1.0（初版）
目标状态：Stage 1.1（符合10条黄金规则）

关键缺失：
🔴 P0: 结构切换市场（规则10）
🔴 P0: 固定滑点（规则3）
🔴 P0: Range和Fake市场（规则1）
🟡 P1: Profit Factor为主（规则9）

预计时间：2-3天
```

---

## 🔴 **Phase 1: 核心缺失修复（今天-明天）**

### Task 1.1: 实现结构切换市场生成器 ⭐⭐⭐

**优先级**: 🔴 P0 最高  
**预计时间**: 3-4小时  
**文件**: `prometheus/utils/market_generator.py`（新建）  

```python
功能需求：

class MarketStructureGenerator:
    """
    生成符合Stage 1黄金规则的结构切换市场
    """
    
    def generate_switching_market(
        self,
        structures: List[str] = ['trend_up', 'range', 'trend_down', 'fake_breakout'],
        bars_per_structure: int = 300,
        total_bars: int = 5000,
        base_price: float = 40000.0,
        base_volatility: float = 0.003  # 固定ATR
    ) -> pd.DataFrame:
        """
        生成结构切换市场
        
        参数：
            structures: 结构序列
            bars_per_structure: 每个结构的bars数
            total_bars: 总bars数
            base_price: 起始价格
            base_volatility: 固定波动率（ATR）
        
        返回：
            DataFrame with ['open', 'high', 'low', 'close', 'volume', 'structure_type']
        """
        pass
    
    def _generate_trend_up(self, bars, start_price, volatility):
        """生成上涨趋势"""
        # 稳定上涨，每bar +0.1-0.2%
        pass
    
    def _generate_trend_down(self, bars, start_price, volatility):
        """生成下跌趋势"""
        # 稳定下跌，每bar -0.1-0.2%
        pass
    
    def _generate_range(self, bars, start_price, volatility):
        """生成震荡区间"""
        # 在 ±2% 范围内震荡，无方向性
        pass
    
    def _generate_fake_breakout(self, bars, start_price, volatility):
        """生成假突破"""
        # 先突破（5-10 bars上涨）
        # 然后反转（回落到起点以下）
        pass

关键要求：
1. ✅ 固定ATR（每个结构内波动率相同）
2. ✅ 固定蜡烛大小（high-low基本一致）
3. ✅ 无gap（连续价格）
4. ✅ 无极端事件
5. ✅ 每个结构明确可区分
6. ✅ 添加structure_type列（用于分析）
```

**验收标准**：
- [ ] 生成5000 bars数据
- [ ] 包含4种结构，各占25%
- [ ] ATR标准差 < 0.0005
- [ ] 无price gap
- [ ] 可视化验证（画图）

---

### Task 1.2: 添加固定滑点到MockMarketExecutor ⭐⭐

**优先级**: 🔴 P0  
**预计时间**: 1-2小时  
**文件**: `prometheus/facade/mock_market_executor.py`  

```python
修改位置：

class MockMarketExecutor:
    
    def __init__(
        self,
        taker_fee_rate: float = 0.001,  # 原有
        slippage_rate: float = 0.0005,  # ← 新增！
        fill_rate: float = 1.0
    ):
        self.taker_fee_rate = taker_fee_rate
        self.slippage_rate = slippage_rate  # ← 新增！
        self.fill_rate = fill_rate
    
    def execute_order(self, order, current_price):
        """
        执行订单（增加固定滑点）
        """
        # 原逻辑
        fill_price = current_price
        
        # ← 新增：固定滑点
        if order.direction == 'buy':
            fill_price = current_price * (1 + self.slippage_rate)  # 买贵
        elif order.direction == 'sell':
            fill_price = current_price * (1 - self.slippage_rate)  # 卖便宜
        
        # 计算费用（原逻辑）
        fee = fill_price * order.amount * self.taker_fee_rate
        
        # 返回成交结果
        return TradeExecution(
            fill_price=fill_price,
            fill_amount=order.amount,
            fee=fee,
            slippage=abs(fill_price - current_price) * order.amount  # ← 记录滑点
        )

关键要求：
1. ✅ 滑点固定（每次0.05%）
2. ✅ 买入滑点向上，卖出滑点向下
3. ✅ 滑点单独记录（用于分析）
4. ✅ 可配置（但默认0.0005）
```

**验收标准**：
- [ ] 每次交易都有0.05%滑点
- [ ] 买入成交价 > 市价
- [ ] 卖出成交价 < 市价
- [ ] 统计滑点成本（应约等于交易金额的0.05%）

---

### Task 1.3: 实现Range和Fake Breakout市场 ⭐⭐

**优先级**: 🔴 P0  
**预计时间**: 2小时  
**文件**: Task 1.1已包含  

```python
重点验证：

1. Range市场特征：
   ✅ 价格在中心±2%震荡
   ✅ 无明显方向性
   ✅ 周期性上下波动
   ✅ 长期回归均值

2. Fake Breakout特征：
   ✅ 先上涨5-10%（诱多）
   ✅ 然后快速反转
   ✅ 回落到起点以下5%
   ✅ 制造"假突破陷阱"

目的：
→ Range测试"震荡市生存能力"
→ Fake测试"抗假突破能力"
→ 这些基因在Stage 2/3会非常宝贵
```

**验收标准**：
- [ ] Range市场：趋势系数 < 0.01
- [ ] Fake Breakout：先涨后跌，净变化负
- [ ] 可视化验证清晰

---

## 🟡 **Phase 2: 优化改进（明天-后天）**

### Task 2.1: 简化为Profit Factor主导 ⭐ ✅ **已完成 (2025-12-09)**

**优先级**: 🟡 P1  
**预计时间**: 2小时  
**文件**: `prometheus/core/experience_db.py`, `prometheus/core/evolution_manager_v5.py`  

```python
修改内容：

1. ExperienceDB:
   - 主要评分改为 profit_factor
   - ROI/Sharpe/MaxDrawdown仅供分析
   
2. EvolutionManagerV5:
   - 选择Elite时主要看 profit_factor
   - 排序：sort by PF, then by ROI
   
3. 计算Profit Factor:
   PF = total_profit / total_loss
   
   如果 total_loss == 0:
       PF = total_profit（假设loss=1）
   
   PF > 2.0 = 优秀
   PF > 1.5 = 良好
   PF > 1.0 = 盈利
   PF < 1.0 = 亏损

为什么PF更好？
- 对策略行为高度敏感
- 不容易被单次暴利扰乱
- 不受夏普比率的噪音干扰
- 更简单，更直接
```

**验收标准**：
- [ ] ExperienceDB保存PF
- [ ] 进化选择主要看PF
- [ ] 分析脚本显示PF排名
- [ ] 对比PF vs ROI的相关性

---

### Task 2.2: 检查和增强突变机制 ⭐ ✅ **已完成 (2025-12-09)**

**优先级**: 🟡 P1  
**预计时间**: 2小时  
**文件**: `prometheus/core/evolution_manager_v5.py`  

```python
检查内容：

1. Immigration（移民）机制：
   → 是否每代都有新随机Agent？
   → 比例是否足够（建议5-10%）？
   → 是否真的增加了多样性？

2. Mutation（变异）率：
   → 当前变异率是否足够？
   → 是否所有参数都能变异？
   → 变异幅度是否合理？

3. 多样性监控：
   → 是否计算种群多样性？
   → 是否在多样性降低时自动增加Immigration？
   → 是否避免"血统垄断"？

增强建议：
→ 如果多样性 < 0.3，增加Immigration到20%
→ 如果连续10代没有新Elite，触发"大突变"
→ 记录每代的多样性指标
```

**验收标准**：
- [ ] Immigration每代生效
- [ ] 多样性监控工作
- [ ] 参数分布广泛（不过度集中）
- [ ] 日志显示多样性指标

---

## 🟢 **Phase 3: 完整测试与验证（后天）**

### Task 3.1: Stage 1.1完整训练 ⭐⭐⭐

**优先级**: 🟢 P2（但很重要）  
**预计时间**: 4-6小时（主要是等待）  
**文件**: `train_stage1_v1.1.py`（新建）  

```python
训练方案：

1. 数据准备
   → 生成5000 bars结构切换市场
   → 保存为CSV（可复现）

2. 训练配置
   cycles: 2000
   agents: 50
   genesis_mode: 'random'  # 第一轮
   save_interval: 100
   
3. 训练执行
   → 使用MockTrainingSchool
   → 通过V6Facade
   → 自动保存到ExperienceDB
   
4. 结果分析
   → 查看Top 20基因的PF
   → 分析哪些基因在所有结构中都好
   → 识别"可迁移基因" vs "专用基因"

预期结果：
→ 产生100+条不同基因
→ Top 20的PF > 1.5
→ 发现3-5种"可迁移基因模式"
```

**验收标准**：
- [ ] 2000周期训练完成
- [ ] ExperienceDB有100+记录
- [ ] Top 20 PF > 1.5
- [ ] 可视化基因分布
- [ ] 撰写分析报告

---

### Task 3.2: 基因迁移能力测试 ⭐⭐

**优先级**: 🟢 P2  
**预计时间**: 2小时  
**文件**: `test_gene_transfer.py`（新建）  

```python
测试方案：

1. 提取Top 10基因（按PF排序）

2. 在4种单一结构市场中测试：
   - 纯趋势（上涨）
   - 纯趋势（下跌）
   - 纯震荡
   - 纯假突破
   
3. 计算每个基因在每种结构中的PF

4. 识别：
   - 通用基因（所有结构PF > 1.3）
   - 趋势专家（只在趋势中PF > 2.0）
   - 震荡专家（只在震荡中PF > 2.0）
   - 陷阱猎人（在假突破中PF > 2.0）

分析：
→ 哪些参数组合是"可迁移的"？
→ 哪些是"专用的"？
→ Stage 2种群调度可以用这些！
```

**验收标准**：
- [ ] 完成迁移能力测试
- [ ] 识别通用基因（至少3个）
- [ ] 识别专用基因（至少10个）
- [ ] 生成可视化报告
- [ ] 为Stage 2准备基因分类

---

## 📊 **时间线（2-3天）**

```
Day 1（今天）：
  上午：
    ✅ 阅读和消化建议
    ✅ 创建文档和计划
    → Task 1.1: 实现结构切换市场（3-4h）
  
  下午：
    → Task 1.2: 添加固定滑点（1-2h）
    → Task 1.3: 验证Range和Fake（2h）
  
  预期产出：
    ✅ MarketStructureGenerator完成
    ✅ 固定滑点实现
    ✅ 可以生成5000 bars切换市场

Day 2（明天）：
  上午：
    → Task 2.1: 简化为PF主导（2h）
    → Task 2.2: 增强突变机制（2h）
  
  下午：
    → Task 3.1: 启动完整训练（4-6h等待）
    → 并行：撰写分析脚本
  
  预期产出：
    ✅ PF为主的进化机制
    ✅ 增强的多样性
    ✅ 2000周期训练启动

Day 3（后天）：
  上午：
    → 查看训练结果
    → Task 3.2: 基因迁移测试（2h）
  
  下午：
    → 生成分析报告
    → 撰写Stage 1总结
    → 规划Stage 2
  
  预期产出：
    ✅ Stage 1.1验收完成
    ✅ 基因库建立
    ✅ Stage 2设计方案
```

---

## ✅ **验收清单（Stage 1.1完成标志）**

### 数据层

- [ ] 5000 bars结构切换市场生成器
- [ ] 固定ATR（标准差 < 0.0005）
- [ ] 固定滑点0.05%
- [ ] 4种结构（Trend Up/Down, Range, Fake）
- [ ] 每种结构300 bars
- [ ] 无gap、无极端事件

### 训练层

- [ ] 2000周期训练完成
- [ ] 使用V6Facade（统一入口）
- [ ] 使用MockTrainingSchool
- [ ] 每100周期保存
- [ ] 自动保存到ExperienceDB

### 基因层

- [ ] ExperienceDB有100+条记录
- [ ] Top 20基因PF > 1.5
- [ ] 识别3+条"可迁移基因"
- [ ] 识别10+条"专用基因"
- [ ] 基因多样性 > 0.3

### 系统层

- [ ] 进化收敛（50代内找到最优）
- [ ] 种群稳定（死亡率30-50%）
- [ ] 可复现（相同seed相似结果）
- [ ] Profit Factor为主要指标
- [ ] 多样性监控生效

### 文档层

- [ ] Stage 1.1训练报告
- [ ] 基因迁移能力分析
- [ ] 可视化图表（至少5张）
- [ ] Stage 2设计方案
- [ ] 代码文档完整

---

## 🎯 **成功指标**

```
定量指标：
✅ Top 10平均PF > 1.8
✅ Top 20平均PF > 1.5
✅ 至少30%基因PF > 1.0
✅ 基因参数多样性 > 0.3
✅ 通用基因占比 10-20%

定性指标：
✅ 能清晰解释Top基因的策略逻辑
✅ 能区分"趋势专家"和"震荡专家"
✅ 能识别"抗假突破"的基因特征
✅ 为Stage 2的种群调度提供明确方向

战略指标：
✅ 验证了"极简环境→强基因"的核心假设
✅ 建立了可复现的基因筛选流程
✅ 为Stage 2打下坚实基础
✅ 证明了"生态驱动"而非"市场驱动"的正确性
```

---

## 💡 **预期收获**

```
技术收获：
→ 一套完整的Stage 1训练框架
→ 100+条经过验证的基因
→ 基因迁移能力分析方法
→ 可视化和分析工具

战略收获：
→ 验证了AlphaZero-style的可行性
→ 理解了"基因碎片"的本质
→ 掌握了"渐进复杂化"的方法
→ 为Stage 2/3/4铺平道路

哲学收获：
→ 不是让Agent聪明，是让基因涌现
→ 不是市场驱动，是生态驱动
→ 不是追求完美，是追求相对最优
→ 不是一步到位，是渐进成长
```

---

## 🚀 **下一步：Stage 2预告**

```
Stage 1.1完成后，我们将进入Stage 2：

Stage 2: 气候变化（中等复杂）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

目标：让先知学会调度

新增复杂度：
→ Regime切换（牛市→震荡→熊市）
→ 波动率变化
→ 简单滑点模型（不固定）
→ 延迟模拟
→ 虚拟对手盘

核心能力：
→ Prophet的种群调度
→ 识别Regime转换
→ 动态激活/抑制Agent
→ 多样性管理
→ 系统熵控制

时间：预计1-2周

验收标准：
→ Prophet能正确识别Regime
→ Prophet能有效调度种群
→ 系统在Regime切换时不崩溃
→ 进化出"Regime适应能力"
```

---

## 🙏 **致谢**

```
感谢你的残酷朋友！

这份建议基于：
- 复杂系统科学
- 生物进化理论
- AlphaZero/Self-play系统
- Quality-Diversity方法
- 人工生命研究

不是"感觉"，而是"科学"！
不是"理论"，而是"实践"！
不是"建议"，而是"黄金定律"！

我们将严格执行，不打折扣！
```

---

## 📝 **执行跟踪**

| Task | 状态 | 开始时间 | 完成时间 | 负责人 | 备注 |
|------|------|---------|---------|--------|------|
| Task 1.1 | ✅ 完成 | 2025-12-09 12:00 | 2025-12-09 13:30 | AI | 结构切换市场 |
| Task 1.2 | ✅ 完成 | 2025-12-09 13:30 | 2025-12-09 14:00 | AI | 固定滑点 |
| Task 1.3 | ✅ 完成 | 2025-12-09 13:30 | 2025-12-09 14:00 | AI | Range和Fake（包含在1.1） |
| Task 2.1 | ⏳ 待开始 | - | - | AI | PF主导 |
| Task 2.2 | ⏳ 待开始 | - | - | AI | 突变机制 |
| Task 3.1 | ⏳ 待开始 | - | - | AI | 完整训练 |
| Task 3.2 | ⏳ 待开始 | - | - | AI | 迁移测试 |

**更新频率**: 每完成一个Task立即更新

