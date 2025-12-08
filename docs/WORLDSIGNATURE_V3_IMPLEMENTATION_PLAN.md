# WorldSignature V3 + MemoryLayer 实施计划

**制定时间**: 2025-12-08  
**目标**: 实现"过去+当下+未来"的完整WorldSignature + 智能创世  
**总工期**: 5天  
**哲学**: 不追求完美，追求"相对最优解"

---

## 📅 Day 1-2: 完善WorldSignature V3（增加History + Future Signals）

### 目标
让WorldSignature从"只有当下"变成"过去+当下+未来（领先指标）"

### 具体任务

#### Day 1 上午：增加History维度（历史背景）
**文件**: `prometheus/world_signature/signature.py`

**新增组件**: `HistoryContext`
```python
@dataclass
class HistoryContext:
    """历史背景信息"""
    # 价格位置
    price_percentile: float      # 当前价格在历史的百分位（0-1）
    historical_high: float       # 历史高点（过去200周期）
    historical_low: float        # 历史低点
    distance_from_high: float    # 距离高点的百分比（负数=低于高点）
    distance_from_low: float     # 距离低点的百分比
    
    # 波动率历史
    historical_avg_volatility: float  # 历史平均波动率
    volatility_ratio: float           # 当前波动率/历史平均（>1=偏高）
    
    # 成交量历史
    historical_avg_volume: float      # 历史平均成交量
    volume_ratio: float               # 当前成交量/历史平均
```

**修改**: `WorldSignature_V2` → `WorldSignature_V3`
```python
@dataclass
class WorldSignature_V3:
    # 新增
    history: HistoryContext
    
    # 已有
    macro_vec: np.ndarray  # 128-dim
    micro_vec: np.ndarray  # 256-dim
    regime: str
    scores: Dict[str, float]
    
    # 稍后增加（Day 1下午）
    future_signals: FutureSignals
```

#### Day 1 下午：增加Future Signals（领先指标）
**新增组件**: `FutureSignals`
```python
@dataclass
class FutureSignals:
    """领先指标（预警系统）"""
    # 趋势信号
    momentum_divergence: float       # 价格vs动量背离（-1到1，负数=背离）
    trend_weakening: bool            # 趋势减弱信号
    
    # 风险信号
    volatility_increasing: bool      # 波动率上升
    liquidity_decreasing: bool       # 流动性下降
    volume_divergence: float         # 价格vs成交量背离
    
    # 反转信号
    reversal_signal_strength: float  # 反转信号强度（0-1）
    exhaustion_signal: bool          # 趋势衰竭信号
    
    # 综合评估
    danger_level: str                # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
```

**计算逻辑**:
```python
def calculate_future_signals(df: pd.DataFrame, current_idx: int) -> FutureSignals:
    """
    计算领先指标
    
    参数:
        df: 市场数据（包含price, volume, 技术指标等）
        current_idx: 当前周期的索引
    """
    # 1. 动量背离
    # 价格新高，但RSI/MACD没有新高 → 背离
    momentum_divergence = calculate_momentum_divergence(df, current_idx)
    
    # 2. 成交量背离
    # 价格上涨，但成交量下降 → 缺乏支撑
    volume_divergence = calculate_volume_divergence(df, current_idx)
    
    # 3. 波动率变化
    # 波动率突然上升 → 市场不稳定
    volatility_increasing = check_volatility_increase(df, current_idx)
    
    # 4. 流动性变化
    # 订单簿深度下降 → 流动性枯竭
    liquidity_decreasing = check_liquidity_decrease(df, current_idx)
    
    # 5. 反转信号综合
    # 多个技术指标共振 → 反转概率高
    reversal_signal_strength = calculate_reversal_strength(
        momentum_divergence, volume_divergence, 
        volatility_increasing, liquidity_decreasing
    )
    
    # 6. 危险等级
    if reversal_signal_strength > 0.7:
        danger_level = 'CRITICAL'
    elif reversal_signal_strength > 0.5:
        danger_level = 'HIGH'
    elif reversal_signal_strength > 0.3:
        danger_level = 'MEDIUM'
    else:
        danger_level = 'LOW'
    
    return FutureSignals(...)
```

#### Day 2 上午：实现计算函数
**文件**: `prometheus/world_signature/indicators.py` (新建)

实现以下函数:
1. `calculate_momentum_divergence()` - 动量背离
2. `calculate_volume_divergence()` - 成交量背离
3. `check_volatility_increase()` - 波动率上升检测
4. `check_liquidity_decrease()` - 流动性下降检测
5. `calculate_reversal_strength()` - 反转信号综合

#### Day 2 下午：集成测试
**创建测试**: `test_worldsignature_v3.py`

验证:
1. History信息计算正确
2. Future Signals计算正确
3. WorldSignature_V3序列化/反序列化
4. 向量维度兼容（macro_vec 128-dim, micro_vec 256-dim保持不变）

---

## 📅 Day 3-4: 实现MemoryLayer（经验数据库 + 智能创世）

### Day 3 上午：ExperienceDB（经验数据库）
**文件**: `prometheus/memory/experience_db.py`

**核心类**: `ExperienceDB`
```python
class ExperienceDB:
    """
    经验数据库
    存储: (WorldSignature_V3, Genome, ROI, Sharpe, MaxDrawdown)
    查询: 基于WorldSignature相似度，返回历史最优Genome
    """
    
    def add_experience(
        self,
        ws: WorldSignature_V3,
        genome: GenomeVector,
        roi: float,
        sharpe: float,
        max_drawdown: float,
        segment_id: int,
        timestamp: float
    ):
        """记录经验"""
        pass
    
    def query_top_k_genomes(
        self,
        ws_current: WorldSignature_V3,
        k: int = 10,
        metric: str = 'roi',  # 'roi', 'sharpe', 'risk_adjusted'
        diversity_threshold: float = 0.3
    ) -> List[GenomeVector]:
        """
        查询最相似的WorldSignature下的Top-K个Genome
        
        相似度计算:
            1. macro_vec余弦相似度（权重0.4）
            2. micro_vec余弦相似度（权重0.3）
            3. History相似度（权重0.2）
            4. FutureSignals相似度（权重0.1）
        
        多样性保证:
            - 选出的K个Genome之间的距离 > diversity_threshold
            - 避免"10个几乎相同的基因"
        """
        pass
```

### Day 3 下午：IntelligentGenesis（智能创世）
**文件**: `prometheus/memory/intelligent_genesis.py`

**核心类**: `IntelligentGenesis`
```python
class IntelligentGenesis:
    """
    智能创世管理器
    根据初始市场环境和历史经验创建创世Agent
    """
    
    def create_genesis_agents(
        self,
        market_data: pd.DataFrame,
        n_total: int = 50,
        elite_ratio: float = 0.30,     # 30%精英复制体（高ROI/高Sharpe）
        diverse_ratio: float = 0.40,   # 40%多样性Agent（不同策略）
        random_ratio: float = 0.30,    # 30%随机探索
        n_elite_genomes: int = 5,
        n_diverse_genomes: int = 10,
        elite_mutation_rate: float = 0.05,
        diverse_mutation_rate: float = 0.10
    ) -> List[AgentV5]:
        """
        创建创世Agent
        
        步骤:
            1. 计算初始WorldSignature_V3（使用前100周期数据）
            2. 冷启动检查（ExperienceDB是否为空）
            3. 查询历史最优Genome
            4. 创建Agent:
               - 30%: 精英复制体（ROI最高、Sharpe最高）
               - 40%: 多样性Agent（不同策略组合）
               - 30%: 随机探索（完全随机基因）
        """
        pass
```

### Day 4 上午：分段记录机制
**文件**: `prometheus/facade/v6_facade.py`

**修改**: `run_cycle()` 方法

增加逻辑:
```python
def run_cycle(self, ...):
    for cycle_num in range(start_cycle, target_cycle):
        # ... 现有逻辑 ...
        
        # 每50周期记录一次经验
        if cycle_num % 50 == 0 and cycle_num > 0:
            self._record_segment_experience(
                start_cycle=cycle_num - 50,
                end_cycle=cycle_num,
                current_price=current_price
            )
```

**新增方法**: `_record_segment_experience()`
```python
def _record_segment_experience(
    self,
    start_cycle: int,
    end_cycle: int,
    current_price: float
):
    """
    记录分段经验
    
    计算:
        1. 该分段的WorldSignature_V3（统计特征）
        2. 每个Agent的表现（ROI, Sharpe, MaxDrawdown）
        3. 记录到ExperienceDB
    """
    # 1. 计算分段WorldSignature
    segment_data = self.market_data[start_cycle:end_cycle]
    ws_segment = self.prophet.calculate_world_signature_segment(segment_data)
    
    # 2. 记录每个Agent的表现
    for agent in self.moirai.agents:
        if agent.state != AgentState.ALIVE:
            continue
        
        roi = agent.calculate_roi_segment(start_cycle, end_cycle)
        sharpe = agent.calculate_sharpe_segment(start_cycle, end_cycle)
        max_dd = agent.calculate_max_drawdown_segment(start_cycle, end_cycle)
        
        self.experience_db.add_experience(
            ws=ws_segment,
            genome=agent.genome,
            roi=roi,
            sharpe=sharpe,
            max_drawdown=max_dd,
            segment_id=start_cycle // 50,
            timestamp=time.time()
        )
```

### Day 4 下午：集成到V6Facade
**文件**: `prometheus/facade/v6_facade.py`

**修改**: `build_facade()`
```python
def build_facade(
    market_data: pd.DataFrame,
    config: SystemCapitalConfig,
    scenario: str,
    seed: Optional[int] = None,
    use_intelligent_genesis: bool = True,  # 新增参数
    experience_db_path: str = "data/experience_db.json"  # 新增参数
) -> V6Facade:
    """
    构建Facade实例
    
    如果use_intelligent_genesis=True:
        - 从ExperienceDB加载历史经验
        - 使用IntelligentGenesis创建Agent
    否则:
        - 使用随机创世（当前方式）
    """
    # 初始化ExperienceDB
    experience_db = ExperienceDB(db_path=experience_db_path)
    
    # 创建Agent
    if use_intelligent_genesis and not experience_db.is_empty():
        intelligent_genesis = IntelligentGenesis(experience_db)
        initial_agents = intelligent_genesis.create_genesis_agents(
            market_data=market_data,
            n_total=config.agent_count
        )
        logger.info(f"✅ 使用智能创世（基于{len(experience_db.records)}条历史经验）")
    else:
        initial_agents = [
            AgentV5(genome=GenomeVector.create_random())
            for _ in range(config.agent_count)
        ]
        logger.info("⚠️ 使用随机创世（ExperienceDB为空或未启用）")
    
    # ... 其余逻辑不变 ...
```

---

## 📅 Day 5: 验证对比（A/B测试）

### 目标
验证"智能创世"是否比"随机创世"更接近"相对最优解"

### 测试脚本
**文件**: `test_intelligent_genesis_comparison.py`

```python
"""
对比测试：随机创世 vs 智能创世

测试环境：
  - 市场数据：2023年BTC数据（牛市）
  - 训练周期：500周期
  - Agent数量：50
  - Seed：固定（7001）确保可重复

对比指标：
  1. 系统ROI
  2. Agent平均ROI
  3. 夏普比率
  4. 最大回撤
  5. 收敛速度（多少周期后稳定）
"""

# 测试A：随机创世（baseline）
results_random = run_scenario(
    market_data=btc_data,
    config=capital_config,
    scenario='backtest',
    seed=7001,
    use_intelligent_genesis=False,  # 关键
    max_cycles=500
)

# 测试B：智能创世（新系统）
results_intelligent = run_scenario(
    market_data=btc_data,
    config=capital_config,
    scenario='backtest',
    seed=7001,
    use_intelligent_genesis=True,  # 关键
    max_cycles=500
)

# 对比分析
print("=" * 80)
print("对比结果")
print("=" * 80)
print(f"随机创世:")
print(f"  系统ROI: {results_random['system_roi']:.2%}")
print(f"  Agent平均ROI: {results_random['agent_avg_roi']:.2%}")
print(f"  夏普比率: {results_random['sharpe']:.2f}")
print(f"  最大回撤: {results_random['max_drawdown']:.2%}")
print()
print(f"智能创世:")
print(f"  系统ROI: {results_intelligent['system_roi']:.2%}")
print(f"  Agent平均ROI: {results_intelligent['agent_avg_roi']:.2%}")
print(f"  夏普比率: {results_intelligent['sharpe']:.2f}")
print(f"  最大回撤: {results_intelligent['max_drawdown']:.2%}")
print()
print(f"改进:")
print(f"  系统ROI提升: {(results_intelligent['system_roi'] - results_random['system_roi']):.2%}")
print(f"  夏普比率提升: {(results_intelligent['sharpe'] - results_random['sharpe']):.2f}")
```

### 成功标准
```
相对最优解的验证：
  ✅ 智能创世系统ROI > 随机创世系统ROI + 10%
  ✅ 智能创世夏普比率 > 随机创世夏普比率 + 0.2
  ✅ 智能创世最大回撤 < 随机创世最大回撤
  ✅ 收敛速度更快（例如100周期 vs 200周期）

如果达到以上标准 → 智能创世成功
如果未达到 → 分析原因，迭代改进
```

---

## 📋 检查清单（确保不遗漏）

### Day 1-2
- [ ] `HistoryContext` 类实现
- [ ] `FutureSignals` 类实现
- [ ] `WorldSignature_V3` 类实现
- [ ] 所有计算函数实现（indicators.py）
- [ ] 单元测试通过
- [ ] 向量维度兼容性测试

### Day 3-4
- [ ] `ExperienceDB` 类实现
- [ ] 相似度计算正确（余弦相似度）
- [ ] 多样性保证机制
- [ ] `IntelligentGenesis` 类实现
- [ ] 分段记录机制
- [ ] 集成到V6Facade
- [ ] 数据封装正确（无信息泄露）

### Day 5
- [ ] 对比测试脚本完成
- [ ] 随机创世baseline运行
- [ ] 智能创世运行
- [ ] 结果分析
- [ ] 文档更新

---

## ⚠️ 关键注意事项

### 1. 数据封装（严格执行）
- WorldSignature_V3只能通过Prophet计算，不能手动构造
- ExperienceDB的查询只返回Genome，不泄露ROI等敏感信息给Agent
- Agent不能直接访问ExperienceDB

### 2. 向后兼容
- WorldSignature_V3需要能序列化为JSON
- 需要提供`from_dict()`和`to_dict()`方法
- 确保与现有代码兼容

### 3. 性能考虑
- 相似度计算可能耗时，考虑缓存
- ExperienceDB可能很大，考虑分页加载
- 向量计算使用NumPy加速

### 4. 遵守三大铁律
- 统一封装：所有创世都通过build_facade()
- 严格测试：所有测试基于标准模板
- 完整机制：包含对账、交易费用、市场信息评估

---

## 🎯 预期成果

完成后，系统应该能够：
1. ✅ WorldSignature包含"过去+当下+未来"三个维度
2. ✅ 通过ExperienceDB积累历史经验
3. ✅ 智能创世从历史最优策略开始
4. ✅ 不断逼近"相对最优解"
5. ✅ 在四种市场环境下都表现优于baseline

**核心哲学**: 不追求完美，追求"更好"。Done is better than perfect.

