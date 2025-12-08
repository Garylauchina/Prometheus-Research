# Self-Play对抗系统设计文档

**Priority**: Level 1（最高优先级）  
**Rationale**: 专家洞察 - "没有Self-Play，v6不可能超过v5"  
**Status**: 设计阶段  
**Date**: 2025-12-08

---

## 🎯 **为什么是最高优先级？**

### 专家的残酷诊断

```
当前系统：
  Agent 对 Market
  ❌ 不是 Agent 对 Market 对 Agent

结果：
  → 永远无法产生"战略性策略"
  → 最多只有"统计套利策略"
  → 缺少第二层对抗压力

"天才策略"的出现，几乎都依赖：
  ✅ 对抗压力
  ✅ 竞争博弈
  ✅ 内部生态系统复杂性
```

### AlphaZero的核心启示

```
AlphaZero不是靠"特征工程"战胜人类：
  而是靠"无数次自我对弈"

自我对弈 = 自我施压
自我施压 = 自我进化
自我进化 = 涌现智慧
```

---

## 🏗️ **系统架构**

```
┌─────────────────────────────────────────┐
│   SelfPlaySystem（统一入口）              │
│   - 协调对抗训练                          │
│   - 动态压力调节                          │
└──────────────┬──────────────────────────┘
               │
      ┌────────┼────────┬────────┐
      ▼        ▼        ▼        ▼
┌──────────┐┌──────┐┌──────┐┌──────┐
│Adversarial││Agent ││Market││Pressure│
│Market    ││Arena ││Impact││Controller│
│          ││      ││Model ││        │
└──────────┘└──────┘└──────┘└──────┘
      │         │        │        │
      └─────────┴────────┴────────┘
                 ▼
   ┌─────────────────────────┐
   │   MockTrainingSchool    │
   │   - 完整市场模拟         │
   │   - 市场摩擦             │
   │   - 对手盘               │
   └─────────────────────────┘
```

---

## 🧩 **核心组件**

### 1. AdversarialMarket（对手盘生成器）

**设计理念：**
```
真实市场中，不是所有参与者都是"理性"的：
  - 做市商（提供流动性）
  - 套利者（消除价差）
  - 趋势跟随者（追涨杀跌）
  - 对冲基金（复杂策略）
  - 散户（情绪化交易）

我们需要模拟这些"对手盘"
让Agent学会"博弈"，而不只是"统计"
```

**实现：**
```python
class AdversarialMarket:
    """
    对手盘市场模拟器
    
    生成各种类型的"对手盘Agent"，让主Agent与之竞争
    """
    
    def __init__(self):
        self.adversary_types = {
            'market_maker': MarketMakerAdversary(),
            'arbitrageur': ArbitrageurAdversary(),
            'trend_follower': TrendFollowerAdversary(),
            'contrarian': ContrarianAdversary(),
            'noise_trader': NoiseTraderAdversary()
        }
        
        self.order_book = OrderBook()
        self.price_impact_model = PriceImpactModel()
    
    # ===== 核心方法 =====
    
    def create_adversarial_population(
        self,
        base_agents: List[Agent],
        adversary_ratio: float = 0.20
    ) -> List[Agent]:
        """
        创建对手盘种群
        
        参数：
          - base_agents: 主Agent群体
          - adversary_ratio: 对手盘占比（默认20%）
        
        返回：
          - 混合种群（主Agent + 对手盘Agent）
        
        策略：
          - 60%是主Agent（进化学习）
          - 20%是对手盘（固定策略）
          - 20%是"影子对手"（克隆主Agent的策略）
        """
        population = base_agents.copy()
        n_adversaries = int(len(base_agents) * adversary_ratio)
        
        # 1. 固定策略对手盘（10%）
        for i in range(n_adversaries // 2):
            adv_type = random.choice(list(self.adversary_types.keys()))
            adversary = self.adversary_types[adv_type].create_agent()
            adversary.role = 'adversary'
            adversary.type = adv_type
            population.append(adversary)
        
        # 2. 影子对手（10%，克隆主Agent）
        for i in range(n_adversaries // 2):
            target = random.choice(base_agents)
            shadow = target.clone()
            shadow.role = 'shadow_adversary'
            shadow.genome.mutate(rate=0.30)  # 变异，避免完全相同
            population.append(shadow)
        
        return population
    
    def simulate_order_matching(
        self,
        orders: List[Order],
        current_price: float
    ) -> Tuple[List[Trade], float]:
        """
        订单撮合模拟
        
        不同于简化的"即时成交"，这里模拟真实的订单簿：
          1. 订单进入订单簿
          2. 按价格-时间优先匹配
          3. 大单会产生价格冲击
          4. 流动性不足会导致部分成交或拒单
        
        返回：
          - 成交列表
          - 新的市场价格
        """
        # 1. 订单进入订单簿
        for order in orders:
            self.order_book.add(order)
        
        # 2. 撮合
        trades = []
        for order in orders:
            if order.type == 'market':
                # 市价单：立即成交，但有价格冲击
                trade, price_impact = self.order_book.match_market_order(order)
                if trade:
                    trades.append(trade)
                    current_price += price_impact
            elif order.type == 'limit':
                # 限价单：等待匹配
                trade = self.order_book.match_limit_order(order)
                if trade:
                    trades.append(trade)
        
        # 3. 价格冲击模型
        net_order_flow = sum([o.amount * o.side for o in orders])
        price_impact = self.price_impact_model.calculate(
            net_order_flow,
            self.order_book.liquidity()
        )
        new_price = current_price + price_impact
        
        return trades, new_price
    
    def calculate_slippage(
        self,
        order: Order,
        ideal_price: float,
        actual_price: float
    ) -> float:
        """
        计算滑点
        
        滑点 = (实际成交价 - 理想价格) / 理想价格
        """
        return (actual_price - ideal_price) / ideal_price


class MarketMakerAdversary:
    """
    做市商对手盘
    
    策略：
      - 在买卖两侧挂单
      - 赚取买卖价差
      - 提供流动性
    """
    def create_agent(self) -> Agent:
        agent = Agent(
            genome=self._create_market_maker_genome()
        )
        agent.strategy = 'market_maker'
        return agent
    
    def _create_market_maker_genome(self) -> Genome:
        """
        做市商基因：
          - 高频交易
          - 低风险偏好
          - 快速平仓
        """
        return Genome(
            max_position_pct=0.10,
            hold_time_preference=0.05,  # 极短持仓
            risk_tolerance=0.20,
            ...
        )


class TrendFollowerAdversary:
    """
    趋势跟随者
    
    策略：
      - 追涨杀跌
      - 动量交易
      - 制造"羊群效应"
    """
    def create_agent(self) -> Agent:
        agent = Agent(
            genome=self._create_trend_follower_genome()
        )
        agent.strategy = 'trend_follower'
        return agent
    
    def _create_trend_follower_genome(self) -> Genome:
        """
        趋势跟随者基因：
          - 高仓位
          - 长持仓时间
          - 对动量敏感
        """
        return Genome(
            max_position_pct=0.80,
            hold_time_preference=0.60,
            momentum_sensitivity=0.90,
            ...
        )


class ContrarianAdversary:
    """
    逆向交易者
    
    策略：
      - 在高点做空
      - 在低点做多
      - "别人贪婪我恐惧"
    """
    def create_agent(self) -> Agent:
        agent = Agent(
            genome=self._create_contrarian_genome()
        )
        agent.strategy = 'contrarian'
        return agent


class NoiseTraderAdversary:
    """
    噪音交易者（散户模拟）
    
    策略：
      - 随机交易
      - 情绪化
      - 制造市场噪音
    """
    def create_agent(self) -> Agent:
        agent = Agent(
            genome=self._create_noise_genome()
        )
        agent.strategy = 'noise_trader'
        return agent
```

---

### 2. AgentArena（竞技场）

**设计理念：**
```
不只是"Agent vs Market"
而是"Agent vs Agent"的直接对抗

竞技场提供：
  1. 1v1对决（直接竞争）
  2. 小组赛（5-10个Agent竞争）
  3. 锦标赛（全员淘汰赛）
```

**实现：**
```python
class AgentArena:
    """
    Agent竞技场
    
    提供多种对抗模式，让Agent在竞争中进化
    """
    
    def __init__(self):
        self.match_history = []
        self.leaderboard = Leaderboard()
    
    # ===== 对抗模式 =====
    
    def duel_1v1(
        self,
        agent1: Agent,
        agent2: Agent,
        market_data: pd.DataFrame
    ) -> Dict:
        """
        1v1对决
        
        规则：
          - 相同的市场数据
          - 相同的初始资金
          - 最终PnL高者胜
        
        意义：
          - 直接对比策略优劣
          - 胜者获得"繁殖优先权"
        """
        # 初始化
        agent1.reset(initial_capital=10000)
        agent2.reset(initial_capital=10000)
        
        # 运行
        for i in range(len(market_data)):
            context = market_data.iloc[i]
            
            # 两个Agent同时决策
            action1 = agent1.decide(context)
            action2 = agent2.decide(context)
            
            # 执行（可能相互影响）
            self._execute_with_interaction(action1, action2, context)
        
        # 结算
        pnl1 = agent1.calculate_total_pnl(market_data.iloc[-1].close)
        pnl2 = agent2.calculate_total_pnl(market_data.iloc[-1].close)
        
        winner = agent1 if pnl1 > pnl2 else agent2
        loser = agent2 if pnl1 > pnl2 else agent1
        
        return {
            'winner': winner,
            'loser': loser,
            'winner_pnl': max(pnl1, pnl2),
            'loser_pnl': min(pnl1, pnl2),
            'margin': abs(pnl1 - pnl2)
        }
    
    def group_battle(
        self,
        agents: List[Agent],
        market_data: pd.DataFrame,
        group_size: int = 5
    ) -> List[Agent]:
        """
        小组赛
        
        规则：
          - 随机分组（每组5个Agent）
          - 每组前2名晋级
          - 组内竞争激烈
        
        意义：
          - 模拟"资源竞争"
          - 多样性得以保留（不同组的策略可能不同）
        """
        groups = self._split_into_groups(agents, group_size)
        winners = []
        
        for group in groups:
            # 小组内竞争
            results = []
            for agent in group:
                agent.reset(initial_capital=10000)
                pnl = self._run_agent(agent, market_data)
                results.append((agent, pnl))
            
            # 排序，取前2名
            results.sort(key=lambda x: x[1], reverse=True)
            winners.extend([r[0] for r in results[:2]])
        
        return winners
    
    def tournament(
        self,
        agents: List[Agent],
        market_data: pd.DataFrame
    ) -> Agent:
        """
        锦标赛（淘汰赛）
        
        规则：
          - 单败淘汰
          - 1v1对决
          - 最后一个存活者获胜
        
        意义：
          - 找到"最强策略"
          - 但可能损失多样性
        """
        remaining = agents.copy()
        
        while len(remaining) > 1:
            # 配对
            pairs = self._pair_agents(remaining)
            next_round = []
            
            for agent1, agent2 in pairs:
                result = self.duel_1v1(agent1, agent2, market_data)
                next_round.append(result['winner'])
            
            remaining = next_round
        
        return remaining[0]  # 冠军
    
    # ===== 辅助方法 =====
    
    def _execute_with_interaction(
        self,
        action1: Action,
        action2: Action,
        context: Dict
    ):
        """
        执行交易，考虑Agent间的相互影响
        
        例如：
          - 如果两个Agent同时买入，价格会上涨
          - 如果一个买、一个卖，价格影响抵消
        """
        # 计算净订单流
        net_flow = action1.amount - action2.amount
        
        # 价格冲击
        price_impact = net_flow * 0.001  # 简化模型
        adjusted_price = context['close'] + price_impact
        
        # 执行
        action1.execute(price=adjusted_price)
        action2.execute(price=adjusted_price)
```

---

### 3. PressureController（压力调节器）

**设计理念：**
```
进化压力不是固定的，而是动态调节的：
  - 多样性高 → 增加压力（加速进化）
  - 多样性低 → 减少压力（保护探索）
  - Fitness高 → 增加难度（防止过拟合）
  - Fitness低 → 降低难度（给喘息时间）
```

**实现：**
```python
class PressureController:
    """
    进化压力调节器
    
    动态调整竞争强度，避免"过度竞争"或"竞争不足"
    """
    
    def __init__(self):
        self.pressure_level = 0.50  # 初始压力（50%）
        self.history = []
    
    def adjust_pressure(
        self,
        generation: int,
        diversity_index: float,
        avg_fitness: float,
        fitness_variance: float
    ) -> Dict:
        """
        调整进化压力
        
        考虑因素：
          1. 多样性（diversity_index）
          2. 平均适应度（avg_fitness）
          3. 适应度方差（fitness_variance）
          4. 代数（generation）
        
        返回：
          - pressure_level: 0-1之间
          - adversary_ratio: 对手盘比例
          - competition_mode: 竞争模式
        """
        # 1. 基于多样性
        if diversity_index < 0.30:
            # 多样性过低 → 降低压力，鼓励探索
            diversity_factor = 0.50
        elif diversity_index > 0.70:
            # 多样性高 → 增加压力，加速进化
            diversity_factor = 1.50
        else:
            diversity_factor = 1.0
        
        # 2. 基于适应度
        if avg_fitness > 0.50:
            # Fitness高 → 增加对手盘难度
            fitness_factor = 1.30
        elif avg_fitness < 0.10:
            # Fitness低 → 降低难度
            fitness_factor = 0.70
        else:
            fitness_factor = 1.0
        
        # 3. 基于方差
        if fitness_variance < 0.10:
            # 方差小（趋同） → 增加扰动
            variance_factor = 1.20
        else:
            variance_factor = 1.0
        
        # 4. 基于代数（早期宽松，后期严格）
        if generation < 10:
            generation_factor = 0.60
        elif generation < 50:
            generation_factor = 1.0
        else:
            generation_factor = 1.20
        
        # 综合
        new_pressure = self.pressure_level * diversity_factor * fitness_factor * variance_factor * generation_factor
        new_pressure = np.clip(new_pressure, 0.1, 1.0)
        
        self.pressure_level = new_pressure
        self.history.append({
            'generation': generation,
            'pressure': new_pressure,
            'diversity': diversity_index,
            'avg_fitness': avg_fitness
        })
        
        return {
            'pressure_level': new_pressure,
            'adversary_ratio': 0.10 + 0.30 * new_pressure,  # 10%-40%
            'competition_mode': self._select_competition_mode(new_pressure)
        }
    
    def _select_competition_mode(self, pressure: float) -> str:
        """
        选择竞争模式
        
        pressure < 0.3: 'relaxed'（放松，自由进化）
        0.3 <= pressure < 0.7: 'moderate'（适中，小组赛）
        pressure >= 0.7: 'intense'（激烈，锦标赛）
        """
        if pressure < 0.3:
            return 'relaxed'
        elif pressure < 0.7:
            return 'moderate'
        else:
            return 'intense'
```

---

### 4. MarketImpactModel（市场冲击模型）

**设计理念：**
```
真实市场中，大单会影响价格：
  - 买入大量 → 价格上涨
  - 卖出大量 → 价格下跌
  - 影响程度取决于流动性

模拟这个机制，让Agent学会：
  - 控制仓位大小
  - 分批建仓
  - 避免价格冲击
```

**实现：**
```python
class PriceImpactModel:
    """
    价格冲击模型
    
    模拟订单对价格的影响
    """
    
    def __init__(self):
        self.impact_coefficient = 0.001  # 冲击系数
    
    def calculate(
        self,
        net_order_flow: float,
        liquidity: float
    ) -> float:
        """
        计算价格冲击
        
        公式：
        impact = k * (net_order_flow / liquidity)^0.5
        
        其中：
          - k: 冲击系数
          - net_order_flow: 净订单流（买-卖）
          - liquidity: 流动性（订单簿深度）
        """
        if liquidity <= 0:
            return 0.0
        
        normalized_flow = net_order_flow / liquidity
        impact = self.impact_coefficient * np.sign(normalized_flow) * np.sqrt(abs(normalized_flow))
        
        return impact
    
    def permanent_impact(self, temporary_impact: float) -> float:
        """
        永久冲击
        
        不是所有冲击都会消失：
          - 临时冲击：订单完成后价格回归
          - 永久冲击：订单包含信息，价格不回归
        
        假设：50%是永久的
        """
        return temporary_impact * 0.50
```

---

## 🔗 **与MockTrainingSchool的集成**

### 用户要求

```
"原计划的增强型Mock训练学校，必须有完整的市场模拟，
包括市场摩擦和对手盘。"
```

### 集成设计

```python
class MockTrainingSchool:
    """
    Mock训练学校（增强版）
    
    集成Self-Play对抗系统
    """
    
    def __init__(self):
        self.self_play_system = SelfPlaySystem()
        self.market_friction = MarketFriction()
        self.slippage_model = SlippageModel()
        self.latency_simulator = LatencySimulator()
    
    def run_training_session(
        self,
        agents: List[Agent],
        market_data: pd.DataFrame,
        config: Dict
    ):
        """
        训练会话
        
        完整的市场模拟：
          1. 市场摩擦（滑点、延迟、拒单）
          2. 对手盘（Self-Play）
          3. 价格冲击
          4. 流动性约束
        """
        # 1. 创建对手盘
        full_population = self.self_play_system.adversarial_market.create_adversarial_population(
            agents,
            adversary_ratio=0.20
        )
        
        # 2. 运行对抗训练
        for cycle in range(config['num_cycles']):
            # 所有Agent同时决策
            orders = []
            for agent in full_population:
                context = self._get_context(agent, market_data, cycle)
                action = agent.decide(context)
                if action:
                    order = self._create_order(agent, action)
                    orders.append(order)
            
            # 3. 市场摩擦
            orders = self.market_friction.apply(orders)  # 部分订单被拒绝
            orders = self.latency_simulator.delay(orders)  # 延迟
            
            # 4. 撮合（考虑价格冲击）
            trades, new_price = self.self_play_system.adversarial_market.simulate_order_matching(
                orders,
                current_price=market_data.iloc[cycle].close
            )
            
            # 5. 更新Agent状态
            for trade in trades:
                trade.agent.update(trade)
        
        # 6. 评估（只评估主Agent，不评估对手盘）
        main_agents = [a for a in full_population if a.role != 'adversary']
        return self._evaluate(main_agents)


class MarketFriction:
    """
    市场摩擦模拟
    
    真实市场中的各种"摩擦"：
      - 订单被拒绝（资金不足、风控限制）
      - 部分成交（流动性不足）
      - 延迟成交（网络延迟）
    """
    
    def apply(self, orders: List[Order]) -> List[Order]:
        """
        应用市场摩擦
        
        返回：过滤后的订单列表
        """
        valid_orders = []
        for order in orders:
            # 1. 检查资金
            if not self._check_capital(order):
                order.status = 'REJECTED_INSUFFICIENT_CAPITAL'
                continue
            
            # 2. 检查风控
            if not self._check_risk_control(order):
                order.status = 'REJECTED_RISK_LIMIT'
                continue
            
            # 3. 随机拒单（模拟交易所故障）
            if random.random() < 0.01:  # 1%概率
                order.status = 'REJECTED_EXCHANGE_ERROR'
                continue
            
            valid_orders.append(order)
        
        return valid_orders


class SlippageModel:
    """
    滑点模型
    
    模拟实际成交价与预期价的偏差
    """
    
    def calculate(
        self,
        order: Order,
        market_price: float,
        liquidity: float
    ) -> float:
        """
        计算滑点
        
        因素：
          1. 订单大小（大单滑点更大）
          2. 流动性（流动性低滑点更大）
          3. 市场波动（波动大滑点更大）
        """
        size_factor = order.amount / liquidity
        slippage = market_price * size_factor * 0.002  # 0.2%基础滑点
        
        # 买入正滑点，卖出负滑点
        if order.side == 'buy':
            return market_price + slippage
        else:
            return market_price - slippage


class LatencySimulator:
    """
    延迟模拟器
    
    模拟网络延迟、撮合延迟
    """
    
    def delay(self, orders: List[Order]) -> List[Order]:
        """
        给订单加上时间戳，模拟延迟
        
        延迟分布：
          - 90%: 100ms内
          - 9%: 100-500ms
          - 1%: > 500ms（网络问题）
        """
        for order in orders:
            delay_ms = self._sample_delay()
            order.timestamp += delay_ms / 1000.0  # 转换为秒
        
        # 按时间戳排序（先到先得）
        orders.sort(key=lambda o: o.timestamp)
        return orders
    
    def _sample_delay(self) -> float:
        """
        采样延迟（毫秒）
        """
        r = random.random()
        if r < 0.90:
            return random.uniform(10, 100)
        elif r < 0.99:
            return random.uniform(100, 500)
        else:
            return random.uniform(500, 2000)
```

---

## 📋 **实施计划（Week 1，7天）**

### Day 1-2: AdversarialMarket核心
```
✅ OrderBook（订单簿）
✅ PriceImpactModel（价格冲击）
✅ 5种对手盘Agent（MarketMaker, TrendFollower, Contrarian, Arbitrageur, NoiseTrader）
✅ 单元测试
```

### Day 3-4: AgentArena
```
✅ duel_1v1（1v1对决）
✅ group_battle（小组赛）
✅ tournament（锦标赛）
✅ Leaderboard（排行榜）
✅ 集成测试
```

### Day 5: PressureController
```
✅ adjust_pressure（动态压力调节）
✅ select_competition_mode（竞争模式选择）
✅ 压力历史记录
```

### Day 6-7: MockTrainingSchool集成
```
✅ MarketFriction（市场摩擦）
✅ SlippageModel（滑点）
✅ LatencySimulator（延迟）
✅ 完整流程测试
✅ A/B对比（有/无Self-Play）
```

---

## 🎯 **成功标准**

### 定量指标
```
✅ 对手盘Agent能够正常交易（成交率 > 80%）
✅ 价格冲击模型合理（大单冲击 > 小单冲击）
✅ 市场摩擦正常（拒单率 < 5%）
✅ 延迟分布符合预期（90% < 100ms）
```

### 定性指标
```
✅ 主Agent在对抗环境中能够学习
✅ 不同对手盘导致不同策略涌现
✅ Self-Play训练的Agent > 非Self-Play训练的Agent（A/B测试）
✅ 多样性保持在健康水平
```

---

## 📌 **关键洞察**

### Self-Play的本质

```
不是"模拟真实市场"
而是"创造进化压力"

真实市场太复杂，无法完全模拟
但我们可以创造一个"竞争生态"
让Agent在竞争中自我进化
```

### 封装的重要性

```
用户强调："放开自由度的方式，同样需要进行封装"

Self-Play系统虽然复杂，但对外接口简单：
  - build_facade() 自动初始化
  - run_scenario(use_self_play=True) 一键开启
  - 内部细节完全封装

三大铁律依然有效
```

---

**Self-Play是v6.0的灵魂。**  
**没有对抗，就没有进化。**  
**没有进化，就没有涌现。** ⚔️🧬💡

