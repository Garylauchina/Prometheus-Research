# Instinct系统AlphaZero式重构方案
**日期**: 2025-12-08  
**目标**: 移除情绪化本能，改为纯粹理性的策略参数  
**原则**: 极简、理性、可进化

---

## 🎯 目标

```
从：模拟"人性"（恐惧、贪婪、绝望）
到：优化"策略"（仓位、持仓、方向）

从：情绪驱动决策
到：数据驱动决策

从：复杂的心理模型
到：简单的参数优化
```

---

## 📊 当前Instinct系统（待移除）

```python
# prometheus/core/instinct.py (当前)
@dataclass
class Instinct:
    # ❌ 情绪化本能（待移除）
    fear_of_death: float = 1.0         # 死亡恐惧
    reproductive_drive: float = 0.5    # 繁殖欲望
    loss_aversion: float = 0.5         # 损失厌恶
    risk_appetite: float = 0.5         # 风险偏好
    curiosity: float = 0.5             # 好奇心
    time_preference: float = 0.5       # 时间偏好

问题：
1. 死亡恐惧 → 过度保守，违背系统初心
2. 损失厌恶 → 不敢持亏损仓，错失反转
3. 好奇心 → 过度抽象，难以量化影响
4. 繁殖欲望 → 与交易决策无关

核心问题：这些是"人性模拟"，不是"交易策略"
```

---

## 🆕 新设计：StrategyParams（纯粹理性）

```python
# prometheus/core/strategy_params.py (新)
@dataclass
class StrategyParams:
    """
    策略参数 - AlphaZero式极简设计
    
    核心理念：
    1. 只保留"与盈利直接相关"的参数
    2. 所有参数都是"可观测、可量化"的
    3. 没有情绪，只有策略选择
    4. 完全可进化
    """
    
    # ========== 核心策略参数（6个） ==========
    
    # 1. 仓位策略（Position Sizing）
    position_size_base: float = 0.5
    # 基础仓位比例（0-1）
    # 0.1: 保守型（10%资金）
    # 0.5: 平衡型（50%资金）
    # 0.9: 激进型（90%资金）
    
    # 2. 持仓策略（Holding Period）
    holding_preference: float = 0.5
    # 持仓时长偏好（0-1）
    # 0: 短线（1-5个周期）
    # 0.5: 中线（5-20个周期）
    # 1: 长线（20+个周期）
    
    # 3. 方向策略（Direction Bias）
    directional_bias: float = 0.5
    # 方向偏好（0-1）
    # 0: 纯做多（只buy）
    # 0.5: 双向（buy + short）
    # 1: 纯做空（只short）
    
    # 4. 止损策略（Stop Loss）
    stop_loss_threshold: float = 0.1
    # 止损阈值（0-1）
    # 0.05: 紧止损（亏损5%止损）
    # 0.2: 松止损（亏损20%止损）
    # 1.0: 不止损（死扛）
    
    # 5. 止盈策略（Take Profit）
    take_profit_threshold: float = 0.2
    # 止盈阈值（0-1）
    # 0.05: 快止盈（盈利5%就跑）
    # 0.3: 慢止盈（盈利30%再跑）
    # 1.0: 永不止盈（持有到底）
    
    # 6. 趋势策略（Trend Following）
    trend_following_strength: float = 0.5
    # 趋势跟踪强度（0-1）
    # 0: 逆势（均值回归）
    # 0.5: 混合
    # 1: 顺势（趋势追踪）
    
    # ========== 元数据 ==========
    generation: int = 0
    parent_params: tuple = None
    
    def __post_init__(self):
        """确保所有参数在[0, 1]范围内"""
        self.position_size_base = np.clip(self.position_size_base, 0, 1)
        self.holding_preference = np.clip(self.holding_preference, 0, 1)
        self.directional_bias = np.clip(self.directional_bias, 0, 1)
        self.stop_loss_threshold = np.clip(self.stop_loss_threshold, 0, 1)
        self.take_profit_threshold = np.clip(self.take_profit_threshold, 0, 1)
        self.trend_following_strength = np.clip(self.trend_following_strength, 0, 1)
    
    # ========== 创世方法 ==========
    @classmethod
    def create_genesis(cls) -> 'StrategyParams':
        """创建创世策略参数"""
        return cls(
            position_size_base=np.random.beta(2, 2),
            holding_preference=np.random.beta(2, 2),
            directional_bias=np.random.beta(2, 2),
            stop_loss_threshold=np.random.beta(2, 2),
            take_profit_threshold=np.random.beta(2, 2),
            trend_following_strength=np.random.beta(2, 2),
            generation=0
        )
    
    # ========== 遗传方法 ==========
    @classmethod
    def crossover(cls, parent1: 'StrategyParams', parent2: 'StrategyParams') -> 'StrategyParams':
        """交叉遗传"""
        return cls(
            position_size_base=(parent1.position_size_base + parent2.position_size_base) / 2,
            holding_preference=(parent1.holding_preference + parent2.holding_preference) / 2,
            directional_bias=(parent1.directional_bias + parent2.directional_bias) / 2,
            stop_loss_threshold=(parent1.stop_loss_threshold + parent2.stop_loss_threshold) / 2,
            take_profit_threshold=(parent1.take_profit_threshold + parent2.take_profit_threshold) / 2,
            trend_following_strength=(parent1.trend_following_strength + parent2.trend_following_strength) / 2,
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_params=(parent1, parent2)
        )
    
    def mutate(self, mutation_rate: float = 0.1) -> 'StrategyParams':
        """突变"""
        mutated = StrategyParams(
            position_size_base=self.position_size_base + np.random.normal(0, mutation_rate),
            holding_preference=self.holding_preference + np.random.normal(0, mutation_rate),
            directional_bias=self.directional_bias + np.random.normal(0, mutation_rate),
            stop_loss_threshold=self.stop_loss_threshold + np.random.normal(0, mutation_rate),
            take_profit_threshold=self.take_profit_threshold + np.random.normal(0, mutation_rate),
            trend_following_strength=self.trend_following_strength + np.random.normal(0, mutation_rate),
            generation=self.generation,
            parent_params=self.parent_params
        )
        return mutated
```

---

## 🔧 Daimon决策逻辑重构

```python
# prometheus/core/inner_council.py (重构后)
class Daimon:
    """
    守护神 - AlphaZero式纯理性决策
    
    核心改变：
    1. 移除所有"情绪voice"（emotion_voice）
    2. 移除所有"恐惧机制"（fear_of_death）
    3. 只保留"理性评估"
    """
    
    def _strategy_voice(self, context: Dict) -> List[Vote]:
        """
        策略声音 - 基于StrategyParams的理性决策
        
        不再有：
        ❌ "死亡恐惧" → 提前平仓
        ❌ "损失厌恶" → 不敢止损
        ❌ "贪婪" → 不敢止盈
        
        只有：
        ✅ 策略参数 → 理性执行
        ✅ 市场状态 → 客观评估
        ✅ 风险收益 → 数学计算
        """
        votes = []
        params = self.agent.strategy_params
        
        # 获取当前状态
        position = context.get('position', {})
        has_position = position.get('amount', 0) != 0
        current_side = position.get('side')
        unrealized_pnl_pct = context.get('unrealized_pnl_pct', 0)
        
        # 1. 止损逻辑（纯粹理性）
        if has_position and unrealized_pnl_pct < -params.stop_loss_threshold:
            votes.append(Vote(
                action='close',
                confidence=0.95,
                voter_category='strategy',
                reason=f"止损触发: 亏损{unrealized_pnl_pct:.1%} > 阈值{params.stop_loss_threshold:.1%}"
            ))
            return votes  # 止损优先
        
        # 2. 止盈逻辑（纯粹理性）
        if has_position and unrealized_pnl_pct > params.take_profit_threshold:
            votes.append(Vote(
                action='close',
                confidence=0.90,
                voter_category='strategy',
                reason=f"止盈触发: 盈利{unrealized_pnl_pct:.1%} > 阈值{params.take_profit_threshold:.1%}"
            ))
        
        # 3. 持仓时长逻辑
        holding_periods = context.get('holding_periods', 0)
        expected_holding = params.holding_preference * 50  # 0-50个周期
        
        if has_position and holding_periods > expected_holding:
            votes.append(Vote(
                action='close',
                confidence=0.70,
                voter_category='strategy',
                reason=f"持仓时长达标: {holding_periods} > {expected_holding:.0f}"
            ))
        
        # 4. 开仓逻辑（基于趋势策略）
        if not has_position:
            market_trend = context.get('market_data', {}).get('trend', 'neutral')
            
            # 趋势跟踪 vs 均值回归
            if params.trend_following_strength > 0.5:
                # 顺势策略
                if market_trend == 'bullish' and params.directional_bias < 0.7:
                    votes.append(Vote(
                        action='buy',
                        confidence=params.trend_following_strength,
                        voter_category='strategy',
                        reason=f"顺势做多: 牛市({market_trend})"
                    ))
                elif market_trend == 'bearish' and params.directional_bias > 0.3:
                    votes.append(Vote(
                        action='short',
                        confidence=params.trend_following_strength,
                        voter_category='strategy',
                        reason=f"顺势做空: 熊市({market_trend})"
                    ))
            else:
                # 逆势策略（均值回归）
                if market_trend == 'bullish' and params.directional_bias > 0.3:
                    votes.append(Vote(
                        action='short',
                        confidence=1 - params.trend_following_strength,
                        voter_category='strategy',
                        reason=f"逆势做空: 牛市过热({market_trend})"
                    ))
                elif market_trend == 'bearish' and params.directional_bias < 0.7:
                    votes.append(Vote(
                        action='buy',
                        confidence=1 - params.trend_following_strength,
                        voter_category='strategy',
                        reason=f"逆势做多: 熊市超卖({market_trend})"
                    ))
        
        return votes
    
    def _make_decision(self, context: Dict) -> CouncilDecision:
        """
        做出最终决策 - AlphaZero式极简
        
        只有两个voice：
        1. genome_voice（基因参数）
        2. strategy_voice（策略参数）
        
        不再有：
        ❌ emotion_voice（情绪）
        ❌ instinct_voice（本能/恐惧）
        ❌ prophecy_voice（预言）
        ❌ experience_voice（经验）
        """
        all_votes = []
        
        # 1. 基因voice（市场感知）
        all_votes.extend(self._genome_voice(context))
        
        # 2. 策略voice（理性执行）
        all_votes.extend(self._strategy_voice(context))
        
        # 聚合votes（简单投票）
        if not all_votes:
            return CouncilDecision(action='hold', confidence=0.0, reasoning="无投票")
        
        # 按action分组，计算加权confidence
        action_scores = defaultdict(float)
        for vote in all_votes:
            action_scores[vote.action] += vote.confidence
        
        # 选择最高分的action
        best_action = max(action_scores.items(), key=lambda x: x[1])
        
        return CouncilDecision(
            action=best_action[0],
            confidence=best_action[1] / len(all_votes),
            reasoning=f"投票结果: {best_action[0]}({best_action[1]:.2f}分)"
        )
```

---

## 🗑️ 移除的模块

```
1. Emotion系统（emotion.py）
   - despair（绝望）
   - greed（贪婪）
   - fear（恐惧）
   - confidence（信心）
   → 全部移除！理性Agent不需要情绪

2. Instinct中的情绪化参数
   - fear_of_death（死亡恐惧）
   - loss_aversion（损失厌恶）
   - curiosity（好奇心）
   - reproductive_drive（繁殖欲望）
   → 全部移除！改为理性策略参数

3. Daimon中的情绪化voice
   - _emotion_voice（情绪投票）
   - _instinct_voice中的"死亡恐惧"逻辑
   → 全部移除！只保留理性评估

4. Agent中的自杀机制（可选移除）
   - should_commit_suicide()
   - commit_suicide()
   → 改为由EvolutionManager强制淘汰
   → Agent不需要"主动自杀"
```

---

## 📊 Fitness函数配套简化

```python
# prometheus/core/evolution_manager_v5.py
def _calculate_fitness_alphazero(self, agent: AgentV5, current_price: float = 0.0) -> float:
    """
    Fitness v4: AlphaZero式极简评分
    
    只有一个指标：绝对收益
    
    不再有：
    ❌ 持有奖励（鼓励不交易）
    ❌ 频率惩罚（惩罚探索）
    ❌ 趋势对齐（人为干预）
    ❌ 生存奖励（鼓励苟活）
    
    只有：
    ✅ 绝对收益 = (最终资金 - 初始资金) / 初始资金
    
    理由：
    - 盈利是唯一目标
    - 让进化自己找到最优策略
    - 不要人为干预演化方向
    """
    # 1. 计算最终资金
    current_liquid_capital = agent.account.private_ledger.virtual_capital if hasattr(agent, 'account') and agent.account else agent.current_capital
    unrealized_pnl = agent.calculate_unrealized_pnl(current_price) if current_price > 0 else 0.0
    effective_capital = current_liquid_capital + unrealized_pnl
    
    # 2. 计算绝对收益
    absolute_return = (effective_capital - agent.initial_capital) / agent.initial_capital
    
    # 就这么简单！
    return absolute_return
```

---

## ⏱️ 实施时间表

### Phase 1: 准备（1-2小时）

```
✅ 1. 创建新文件
   - prometheus/core/strategy_params.py
   - tests/test_strategy_params.py

✅ 2. 备份当前代码
   - git commit: "backup before alphazero redesign"
   - git tag: v6.0-before-alphazero-redesign
```

### Phase 2: 核心重构（3-4小时）

```
🔧 1. 重构Agent初始化
   - 用StrategyParams替换Instinct
   - 移除Emotion

🔧 2. 重构Daimon决策
   - 移除emotion_voice
   - 简化instinct_voice → strategy_voice
   - 只保留2个voice

🔧 3. 重构Fitness函数
   - _calculate_fitness_v3 → _calculate_fitness_alphazero
   - 只保留绝对收益

🔧 4. 移除自杀机制（可选）
   - 改为EvolutionManager强制淘汰
```

### Phase 3: 测试验证（1-2小时）

```
🧪 1. 单元测试
   - test_strategy_params.py
   - test_daimon_alphazero.py

🧪 2. 集成测试
   - 重新运行Phase 0（10 seeds × 50 cycles）
   - 验证系统稳定性

🧪 3. 对比测试
   - 对比v3 vs AlphaZero式
   - 看哪个收敛更好
```

### Phase 4: Phase 1大规模训练

```
🚀 如果Phase 0通过：
   - 立即进入Phase 1（100-200 runs）
   - 观察"殊途同归"程度
   - 提取最优策略模板
```

---

## ✅ 成功标准

```
Phase 0重新验证：
  ✅ 稳定性 ≥ 80%
  ✅ 种群健康 ≥ 50%
  ✅ 决策率 > 5%（不要太保守）
  
Phase 1收敛性：
  ✅ 同seed下，收益差异 < 10%（殊途同归）
  ✅ 不同seed下，能找到盈利策略
  
最终目标：
  ✅ 系统收益 > BTC（牛市）
  ✅ 系统收益 > +30%（熊市）
  ✅ 通过海量训练找到最优策略模板
```

---

## 🎯 关键理念

```
AlphaZero的成功秘诀：
1. 极简规则（围棋规则很简单）
2. 纯粹理性（没有情绪、恐惧、贪婪）
3. 海量训练（百万局博弈）
4. 数据驱动（从失败中学习）

Prometheus应该：
1. 极简参数（6个策略参数）
2. 纯粹理性（移除所有情绪化本能）
3. 海量训练（Phase 1-3大规模训练）
4. 数据驱动（从死亡中学习）

不忘初心，方得始终：
💰 盈利是唯一目标
💀→🌱 死亡是最大的馈赠
```

---

**现在立即开始实施？** 🚀

