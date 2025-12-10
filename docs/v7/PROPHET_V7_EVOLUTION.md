# Prophet v7.0进化：从婴儿到大脑

> 💡 **核心理念**: Prophet是Prometheus的战略决策中心，Agent是战术执行单元

---

## 🧠 Prophet的使命

```
Prophet ≠ 简单的匹配器
Prophet = 系统的大脑

职责：
  1. 战略决策（资金分配、杠杆管理）
  2. 生态管理（多样性维护、健康监控）
  3. 资源调度（Immigration、干预）
  4. 风险控制（蓄水池、止损）

类比：
  🎖️  军队
     - 将军（Prophet）：战略决策、资源调度
     - 士兵（Agent）：战术执行、具体作战
  
  🏢 公司
     - CEO（Prophet）：战略方向、资源分配
     - 员工（Agent）：具体业务、执行任务
  
  💎 Prometheus
     - Prophet：战略层
     - Agent：战术层
     - Moirai：生命周期管理层
```

---

## 📋 Prophet v7.0：五大核心能力

### 能力1：方向分配引擎（Direction Allocation Engine）⭐⭐⭐

```python
# Prophet v7.0核心能力1

class DirectionAllocationEngine:
    """
    方向分配引擎（Prophet的核心大脑）
    
    职责：
      - 分析WorldSignature（市场状态）
      - 决定各生态位资金分配
      - 维护生态平衡
    """
    
    def __init__(self):
        # 10种生态位基础配置
        self.niche_configs = {
            'trend_following': {
                'base_allocation': 0.15,      # 基础15%
                'bull_multiplier': 1.5,       # 牛市×1.5
                'bear_multiplier': 0.5,       # 熊市×0.5
                'sideways_multiplier': 1.0,   # 震荡×1.0
            },
            'mean_reversion': {
                'base_allocation': 0.12,
                'bull_multiplier': 1.0,
                'bear_multiplier': 1.0,
                'sideways_multiplier': 1.5,   # 震荡市最优
            },
            'bull_specialist': {
                'base_allocation': 0.10,
                'bull_multiplier': 2.5,       # 牛市×2.5！
                'bear_multiplier': 0.1,       # 熊市几乎不用
                'sideways_multiplier': 0.5,
            },
            'bear_specialist': {
                'base_allocation': 0.10,
                'bull_multiplier': 0.1,       # 牛市几乎不用
                'bear_multiplier': 2.5,       # 熊市×2.5！
                'sideways_multiplier': 0.5,
            },
            'scalper': {
                'base_allocation': 0.10,
                'bull_multiplier': 1.2,
                'bear_multiplier': 1.2,
                'sideways_multiplier': 1.5,   # 震荡市适合
            },
            'arbitrage': {
                'base_allocation': 0.08,
                'bull_multiplier': 1.0,
                'bear_multiplier': 1.0,
                'sideways_multiplier': 1.0,   # 任何市场都行
            },
            'contrarian': {
                'base_allocation': 0.15,      # 基础15%（强制>15%）
                'bull_multiplier': 0.8,
                'bear_multiplier': 1.5,       # 熊市更重要
                'sideways_multiplier': 1.2,
            },
            'take_profit': {
                'base_allocation': 0.05,
                'bull_multiplier': 1.5,       # 牛市止盈重要
                'bear_multiplier': 0.5,
                'sideways_multiplier': 1.0,
            },
            'risk_manager': {
                'base_allocation': 0.05,
                'bull_multiplier': 0.5,
                'bear_multiplier': 2.0,       # 熊市风控重要
                'sideways_multiplier': 1.0,
            },
            'momentum': {
                'base_allocation': 0.10,
                'bull_multiplier': 1.8,       # 牛市动量强
                'bear_multiplier': 0.5,
                'sideways_multiplier': 0.8,
            },
        }
    
    def allocate_capital(
        self,
        world_signature: WorldSignatureSimple,
        niche_performance: Dict[str, float],
        total_capital: float
    ) -> Dict[str, float]:
        """
        资金分配（Prophet的核心算法）
        
        输入：
          - 市场状态（WorldSignature）
          - 各生态位历史表现（PF）
          - 总资金
        
        输出：
          - 各生态位资金分配
        
        算法：
          1. 基础分配（根据市场环境）
          2. 表现调整（奖励优秀生态位）
          3. 多样性保护（强制约束）⭐ 核心！
          4. 归一化
        """
        allocation = {}
        
        # ========== 步骤1：基础分配（根据市场环境）==========
        
        market_trend = world_signature.trend  # 'bull', 'bear', 'sideways'
        
        for niche, config in self.niche_configs.items():
            base = config['base_allocation']
            
            # 根据市场环境调整
            if market_trend == 'bull':
                multiplier = config['bull_multiplier']
            elif market_trend == 'bear':
                multiplier = config['bear_multiplier']
            else:  # sideways
                multiplier = config['sideways_multiplier']
            
            allocation[niche] = base * multiplier
        
        # ========== 步骤2：表现调整（奖励优秀生态位）==========
        
        for niche, perf in niche_performance.items():
            if perf > 2.0:  # PF>2.0，优秀
                allocation[niche] *= 1.5
            elif perf > 1.5:  # PF>1.5，良好
                allocation[niche] *= 1.2
            elif perf < 1.2:  # PF<1.2，一般
                allocation[niche] *= 0.8
            elif perf < 1.0:  # PF<1.0，亏损
                allocation[niche] *= 0.5
        
        # ========== 步骤3：多样性保护（强制约束）⭐ 核心！==========
        
        # 约束1：单一生态位<40%
        max_allocation = 0.40
        
        # 约束2：任一生态位>5%
        min_allocation = 0.05
        
        # 约束3：逆向生态位>15%（强制！）
        contrarian_min = 0.15
        
        for niche in allocation:
            # 应用最大最小约束
            allocation[niche] = max(min_allocation, min(max_allocation, allocation[niche]))
        
        # 强制逆向生态位>15%
        if allocation['contrarian'] < contrarian_min:
            allocation['contrarian'] = contrarian_min
        
        # ========== 步骤4：归一化 ==========
        
        total = sum(allocation.values())
        allocation = {k: v/total for k, v in allocation.items()}
        
        # ========== 步骤5：转换为资金数额 ==========
        
        capital_allocation = {k: v * total_capital for k, v in allocation.items()}
        
        return capital_allocation
    
    # ========== 示例输出 ==========
    
    """
    牛市场景（BTC稳定上涨）：
      bull_specialist:   25%  ← 牛市专家×2.5
      trend_following:   22%  ← 趋势追随×1.5
      momentum:          18%  ← 动量×1.8
      contrarian:        15%  ← 强制>15%
      mean_reversion:    10%
      其他:              10%
    
    熊市场景（BTC持续下跌）：
      bear_specialist:   25%  ← 熊市专家×2.5
      contrarian:        20%  ← 逆向×1.5
      risk_manager:      15%  ← 风控×2.0
      mean_reversion:    15%
      其他:              25%
    
    震荡市场（BTC横盘）：
      mean_reversion:    18%  ← 均值回归×1.5
      scalper:           15%  ← 短线×1.5
      contrarian:        15%  ← 强制>15%
      trend_following:   15%
      其他:              37%
    
    关键：
      ✅ 根据市场自动调整
      ✅ 强制多样性（逆向>15%）
      ✅ 奖励优秀生态位
      ✅ 但永不垄断（<40%）
    """
```

---

### 能力2：杠杆管理器（Leverage Manager）⭐⭐⭐

```python
# Prophet v7.0核心能力2

class LeverageManager:
    """
    杠杆管理器（Prophet的精确控制）
    
    职责：
      - 为每个Agent计算最优杠杆
      - 根据生态位、市场、表现动态调整
      - 波动率目标（Volatility Targeting）
    """
    
    def __init__(self):
        # 生态位基础杠杆
        self.niche_base_leverage = {
            'arbitrage': 15.0,      # 套利：低风险，高杠杆
            'mean_reversion': 10.0, # 均值回归：中低风险
            'scalper': 12.0,        # 短线：中风险
            'bull_specialist': 8.0, # 牛市专家：中风险
            'bear_specialist': 7.0, # 熊市专家：中风险
            'trend_following': 6.0, # 趋势：中风险
            'momentum': 5.0,        # 动量：中高风险
            'contrarian': 4.0,      # 逆向：高风险
            'take_profit': 6.0,     # 止盈：中风险
            'risk_manager': 3.0,    # 风控：低风险
        }
    
    def calculate_leverage(
        self,
        agent: AgentV7,
        market_volatility: float,
        world_signature: WorldSignatureSimple
    ) -> float:
        """
        计算Agent杠杆（Prophet的精确控制）
        
        算法：
          1. 生态位基础杠杆
          2. 市场波动率调整（波动率目标）⭐
          3. Agent表现调整
          4. 市场环境调整
          5. 限制范围（1x-20x）
        """
        # ========== 步骤1：生态位基础杠杆 ==========
        
        base_leverage = self.niche_base_leverage.get(agent.niche, 6.0)
        
        # ========== 步骤2：波动率目标（核心算法）⭐ ==========
        
        # 目标：组合年化波动率 = 12%
        target_volatility = 0.12
        
        # 波动率倍数
        volatility_multiplier = target_volatility / market_volatility
        
        leverage = base_leverage * volatility_multiplier
        
        # ========== 步骤3：Agent表现调整 ==========
        
        agent_pf = agent.get_profit_factor()
        
        if agent_pf > 2.5:
            performance_multiplier = 1.5      # 优秀Agent×1.5
        elif agent_pf > 2.0:
            performance_multiplier = 1.3
        elif agent_pf > 1.5:
            performance_multiplier = 1.0
        elif agent_pf > 1.2:
            performance_multiplier = 0.8
        else:
            performance_multiplier = 0.5      # 差Agent×0.5
        
        leverage *= performance_multiplier
        
        # ========== 步骤4：市场环境调整 ==========
        
        if world_signature.trend == 'crash':
            # 崩盘：大幅降低杠杆
            leverage *= 0.2
        elif world_signature.volatility == 'extreme':
            # 极端波动：降低杠杆
            leverage *= 0.5
        elif world_signature.trend == 'bull_stable':
            # 牛市稳定：可以提高杠杆
            leverage *= 1.2
        
        # ========== 步骤5：限制范围 ==========
        
        leverage = max(1.0, min(20.0, leverage))
        
        return leverage
    
    # ========== 示例输出 ==========
    
    """
    场景1：套利Agent，市场波动率6%，表现PF=2.8
      基础：      15x（套利高杠杆）
      波动率：    15 × (12%/6%) = 30x
      表现：      30 × 1.5 = 45x
      限制：      min(45, 20) = 20x  ← 最终杠杆
    
    场景2：趋势Agent，市场波动率15%，表现PF=1.8
      基础：      6x
      波动率：    6 × (12%/15%) = 4.8x
      表现：      4.8 × 1.0 = 4.8x
      市场：      4.8x（正常市场）
      最终：      4.8x
    
    场景3：逆向Agent，市场崩盘（波动率30%），表现PF=1.5
      基础：      4x
      波动率：    4 × (12%/30%) = 1.6x
      表现：      1.6 × 1.0 = 1.6x
      市场：      1.6 × 0.2 = 0.32x
      限制：      max(0.32, 1.0) = 1.0x  ← 崩盘强制1x
    
    关键：
      ✅ 低风险生态位 → 高杠杆
      ✅ 高波动市场 → 低杠杆
      ✅ 优秀Agent → 高杠杆
      ✅ 崩盘 → 强制1x
    """
```

---

### 能力3：生态系统监控器（Ecosystem Monitor）⭐⭐⭐

```python
# Prophet v7.0核心能力3

class EcosystemMonitor:
    """
    生态系统监控器（Prophet的眼睛）
    
    职责：
      - 监控生态健康度
      - 检测失衡风险
      - 触发干预机制
    """
    
    def __init__(self):
        # 健康阈值
        self.thresholds = {
            'directional_entropy_min': 0.5,     # 方向熵>0.5
            'monopoly_risk_max': 0.50,          # 垄断风险<50%
            'niche_entropy_min': 0.5,           # 生态位熵>0.5
            'health_score_warning': 0.5,        # 健康度警告
            'health_score_critical': 0.3,       # 健康度危急
        }
    
    def check_ecosystem_health(self, agents: List[AgentV7]) -> Dict:
        """
        检查生态系统健康度（Prophet的核心监控）
        
        返回：
          {
            'directional_entropy': 0.8,    # 方向熵
            'monopoly_risk': 0.3,          # 垄断风险
            'niche_entropy': 0.7,          # 生态位熵
            'health_score': 0.75,          # 整体健康度
            'warning': False,              # 是否警告
            'critical': False,             # 是否危急
            'intervention_needed': [],     # 需要的干预
          }
        """
        # ========== 指标1：方向熵 ==========
        
        long_count = sum(1 for a in agents if a.position_direction == 'long')
        short_count = sum(1 for a in agents if a.position_direction == 'short')
        neutral_count = len(agents) - long_count - short_count
        
        total = len(agents)
        p_long = long_count / total
        p_short = short_count / total
        p_neutral = neutral_count / total
        
        directional_entropy = -(
            p_long * np.log2(p_long + 1e-10) +
            p_short * np.log2(p_short + 1e-10) +
            p_neutral * np.log2(p_neutral + 1e-10)
        ) / np.log2(3)  # 归一化到[0,1]
        
        # ========== 指标2：垄断风险 ==========
        
        niche_counts = {}
        for agent in agents:
            niche = agent.niche
            niche_counts[niche] = niche_counts.get(niche, 0) + 1
        
        max_niche_ratio = max(niche_counts.values()) / len(agents)
        monopoly_risk = max_niche_ratio
        
        # ========== 指标3：生态位熵 ==========
        
        niche_entropy = 0.0
        for count in niche_counts.values():
            p = count / len(agents)
            niche_entropy -= p * np.log2(p + 1e-10)
        niche_entropy /= np.log2(10)  # 归一化（10个生态位）
        
        # ========== 指标4：整体健康度 ==========
        
        health_score = (
            directional_entropy * 0.30 +
            (1 - monopoly_risk) * 0.40 +
            niche_entropy * 0.30
        )
        
        # ========== 判断警告和危急 ==========
        
        warning = health_score < self.thresholds['health_score_warning']
        critical = health_score < self.thresholds['health_score_critical']
        
        # ========== 确定需要的干预 ==========
        
        intervention_needed = []
        
        if directional_entropy < 0.3:
            intervention_needed.append('direction')  # 方向垄断
        
        if monopoly_risk > 0.6:
            intervention_needed.append('diversity')  # 生态位垄断
        
        if niche_entropy < 0.3:
            intervention_needed.append('niche')  # 生态位灭绝
        
        if critical:
            intervention_needed.append('reset')  # 系统崩溃
        
        return {
            'directional_entropy': directional_entropy,
            'monopoly_risk': monopoly_risk,
            'niche_entropy': niche_entropy,
            'health_score': health_score,
            'niche_distribution': niche_counts,
            'warning': warning,
            'critical': critical,
            'intervention_needed': intervention_needed,
        }
    
    def intervene(self, health_report: Dict, moirai: Moirai):
        """
        生态干预（Prophet的行动）
        """
        if not health_report['intervention_needed']:
            return  # 健康，无需干预
        
        for intervention_type in health_report['intervention_needed']:
            if intervention_type == 'direction':
                self._intervene_direction(moirai, health_report)
            elif intervention_type == 'diversity':
                self._intervene_diversity(moirai, health_report)
            elif intervention_type == 'niche':
                self._intervene_niche(moirai, health_report)
            elif intervention_type == 'reset':
                self._intervene_reset(moirai)
    
    def _intervene_direction(self, moirai, health_report):
        """干预1：方向垄断"""
        logger.warning("🚨 Prophet干预：方向垄断！")
        
        # 强制淘汰垄断方向的弱Agent
        # 注入相反方向的Agent
        pass
    
    def _intervene_diversity(self, moirai, health_report):
        """干预2：生态位垄断"""
        logger.warning("🚨 Prophet干预：生态位垄断！")
        
        # 强制淘汰垄断生态位的弱Agent
        # 注入稀缺生态位的Agent
        pass
    
    def _intervene_niche(self, moirai, health_report):
        """干预3：生态位灭绝"""
        logger.warning("🚨 Prophet干预：生态位灭绝！")
        
        # 注入濒危生态位的Agent
        pass
    
    def _intervene_reset(self, moirai):
        """干预4：系统崩溃，紧急重置"""
        logger.error("💀 Prophet干预：系统崩溃！紧急重置！")
        
        # 大规模淘汰
        # 从ExperienceDB重新创世
        pass
```

---

### 能力4：战略Immigration（Strategic Immigration）⭐⭐

```python
# Prophet v7.0核心能力4

class StrategicImmigration:
    """
    战略Immigration（v6.0封存，v7.0激活）
    
    职责：
      - 多样性救援
      - 稀缺生态位补充
      - 黑天鹅应急
    """
    
    def inject_immigrants(
        self,
        moirai: Moirai,
        strategy: str,  # 'random', 'recall', 'legendary', 'niche_specific'
        target_niche: str = None,
        count: int = 5
    ):
        """
        注入移民（Prophet的战略工具）
        
        策略：
          1. random：随机创造（探索）
          2. recall：召回相似基因（ExperienceDB）
          3. legendary：召回传奇Agent（5奖章）
          4. niche_specific：定向补充特定生态位
        """
        if strategy == 'random':
            # 随机创造（纯探索）
            for _ in range(count):
                agent = moirai._clotho_create_single_agent()
                moirai.agents.append(agent)
        
        elif strategy == 'recall':
            # 召回相似基因
            similar_genomes = self.experience_db.query_similar_genomes(
                world_signature=self.current_world_signature,
                top_k=count
            )
            for genome_data in similar_genomes:
                agent = moirai._clotho_create_from_genome(genome_data)
                moirai.agents.append(agent)
        
        elif strategy == 'legendary':
            # 召回传奇Agent（5奖章）
            legendary_genomes = self.experience_db.query_by_awards(
                min_awards=5,
                top_k=count
            )
            for genome_data in legendary_genomes:
                agent = moirai._clotho_create_from_genome(genome_data)
                moirai.agents.append(agent)
        
        elif strategy == 'niche_specific':
            # 定向补充特定生态位
            if target_niche:
                # 召回该生态位的优秀基因
                niche_genomes = self.experience_db.query_by_niche(
                    niche=target_niche,
                    top_k=count
                )
                for genome_data in niche_genomes:
                    agent = moirai._clotho_create_from_genome(genome_data)
                    agent.niche = target_niche  # 强制生态位
                    moirai.agents.append(agent)
    
    # ========== 使用场景 ==========
    
    """
    场景1：生态位灭绝
      问题：逆向生态位只剩1个Agent
      干预：Prophet注入5个逆向Agent
      
      prophet.inject_immigrants(
          strategy='niche_specific',
          target_niche='contrarian',
          count=5
      )
    
    场景2：黑天鹅事件
      问题：市场暴跌，所有Agent亏损
      干预：Prophet召回历史上熊市的传奇Agent
      
      prophet.inject_immigrants(
          strategy='legendary',
          count=10
      )
    
    场景3：多样性崩溃
      问题：所有Agent都是趋势追随
      干预：Prophet注入随机Agent（探索）
      
      prophet.inject_immigrants(
          strategy='random',
          count=20
      )
    """
```

---

---

### 能力5：风控/审计系统（Risk Control & Audit System）⭐⭐⭐

```python
# Prophet v7.0核心能力5（新增！）

class RiskControlAndAuditSystem:
    """
    风控/审计系统（Prophet的最后一道防线）
    
    职责：
      - 系统级风险监控（不是单Agent风控）
      - 账簿审计（双账簿一致性）
      - 异常交易检测（发现作弊/Bug）
      - 合规检查（强制执行规则）
      - 紧急干预（系统性风险）
    
    定位：
      ✅ Prophet = 战略层风控
      ✅ RiskManager = 战术层风控
      ✅ Prophet是最后一道防线
    """
    
    def __init__(self):
        # 系统级风险限额
        self.system_limits = {
            'max_system_leverage': 500.0,       # 系统总杠杆<500x
            'max_daily_loss': 0.05,             # 单日亏损<5%
            'max_drawdown': 0.30,               # 最大回撤<30%
            'max_agent_count': 100,             # 最多100个Agent
            'min_agent_count': 20,              # 至少20个Agent
            'max_position_concentration': 0.30, # 单品种最多30%
        }
        
        # 审计历史
        self.audit_history = []
        
        # 异常记录
        self.anomaly_log = []
    
    # ========== 功能1：账簿审计 ==========
    
    def audit_ledgers(
        self,
        agents: List[AgentV7],
        public_ledger: PublicLedger
    ) -> Dict:
        """
        账簿审计（核心功能）
        
        检查：
          1. 双账簿一致性（PublicLedger vs PrivateLedger）
          2. 资金守恒（总资金不变）
          3. 持仓一致性（公共vs私有）
        
        返回：
          {
            'passed': True/False,
            'discrepancies': [],  # 不一致列表
            'total_discrepancy': 0.0,  # 总差异
          }
        """
        discrepancies = []
        total_discrepancy = 0.0
        
        for agent in agents:
            # 检查1：资金一致性
            public_capital = public_ledger.get_capital(agent.agent_id)
            private_capital = agent.account.private_ledger.virtual_capital
            
            capital_diff = abs(public_capital - private_capital)
            
            if capital_diff > 0.01:  # 容差0.01
                discrepancies.append({
                    'agent_id': agent.agent_id,
                    'type': 'capital_mismatch',
                    'public': public_capital,
                    'private': private_capital,
                    'diff': capital_diff,
                })
                total_discrepancy += capital_diff
            
            # 检查2：持仓一致性
            public_position = public_ledger.get_position(agent.agent_id)
            private_position = agent.account.private_ledger.get_position()
            
            if public_position != private_position:
                discrepancies.append({
                    'agent_id': agent.agent_id,
                    'type': 'position_mismatch',
                    'public': public_position,
                    'private': private_position,
                })
        
        # 检查3：资金守恒（系统级）
        total_system_capital = sum(a.account.private_ledger.virtual_capital for a in agents)
        expected_capital = self.capital_pool.total_invested
        
        system_diff = abs(total_system_capital - expected_capital)
        
        if system_diff > 1.0:  # 容差1.0
            discrepancies.append({
                'type': 'system_capital_mismatch',
                'actual': total_system_capital,
                'expected': expected_capital,
                'diff': system_diff,
            })
            total_discrepancy += system_diff
        
        # 判断是否通过
        passed = len(discrepancies) == 0
        
        audit_result = {
            'timestamp': datetime.now().isoformat(),
            'passed': passed,
            'discrepancies': discrepancies,
            'total_discrepancy': total_discrepancy,
        }
        
        self.audit_history.append(audit_result)
        
        if not passed:
            logger.error(f"💀 Prophet审计失败！发现{len(discrepancies)}处不一致")
            self._trigger_audit_alert(audit_result)
        
        return audit_result
    
    # ========== 功能2：系统级风险监控 ==========
    
    def check_system_risk(
        self,
        agents: List[AgentV7],
        current_drawdown: float,
        daily_loss: float
    ) -> Dict:
        """
        系统级风险监控（不是单Agent风控）
        
        检查：
          1. 系统总杠杆
          2. 单日亏损
          3. 最大回撤
          4. Agent数量
          5. 持仓集中度
        
        返回：
          {
            'risk_level': 'low'/'medium'/'high'/'critical',
            'violations': [],  # 违规列表
            'emergency_action': None/'reduce_leverage'/'close_all'/'shutdown',
          }
        """
        violations = []
        emergency_action = None
        
        # 检查1：系统总杠杆
        total_leverage = sum(a.current_leverage * a.position_size for a in agents if a.has_position())
        
        if total_leverage > self.system_limits['max_system_leverage']:
            violations.append({
                'type': 'system_leverage_exceeded',
                'current': total_leverage,
                'limit': self.system_limits['max_system_leverage'],
            })
            emergency_action = 'reduce_leverage'
        
        # 检查2：单日亏损
        if daily_loss > self.system_limits['max_daily_loss']:
            violations.append({
                'type': 'daily_loss_exceeded',
                'current': daily_loss,
                'limit': self.system_limits['max_daily_loss'],
            })
            emergency_action = 'close_all'  # 触发单日止损
        
        # 检查3：最大回撤
        if current_drawdown > self.system_limits['max_drawdown']:
            violations.append({
                'type': 'max_drawdown_exceeded',
                'current': current_drawdown,
                'limit': self.system_limits['max_drawdown'],
            })
            emergency_action = 'shutdown'  # 触发最大回撤，紧急关闭系统
        
        # 检查4：Agent数量
        agent_count = len(agents)
        if agent_count > self.system_limits['max_agent_count']:
            violations.append({
                'type': 'agent_count_exceeded',
                'current': agent_count,
                'limit': self.system_limits['max_agent_count'],
            })
        elif agent_count < self.system_limits['min_agent_count']:
            violations.append({
                'type': 'agent_count_too_low',
                'current': agent_count,
                'limit': self.system_limits['min_agent_count'],
            })
        
        # 检查5：持仓集中度
        position_concentration = self._calculate_position_concentration(agents)
        if position_concentration > self.system_limits['max_position_concentration']:
            violations.append({
                'type': 'position_concentration_exceeded',
                'current': position_concentration,
                'limit': self.system_limits['max_position_concentration'],
            })
        
        # 判断风险等级
        if emergency_action == 'shutdown':
            risk_level = 'critical'
        elif emergency_action == 'close_all':
            risk_level = 'high'
        elif len(violations) > 0:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        risk_report = {
            'timestamp': datetime.now().isoformat(),
            'risk_level': risk_level,
            'violations': violations,
            'emergency_action': emergency_action,
        }
        
        if risk_level in ['high', 'critical']:
            logger.error(f"🚨 Prophet风险监控：{risk_level}风险！")
            self._trigger_risk_alert(risk_report)
        
        return risk_report
    
    # ========== 功能3：异常交易检测 ==========
    
    def detect_anomaly(self, agent: AgentV7, cycle: int) -> Optional[Dict]:
        """
        异常交易检测（发现作弊/Bug）
        
        检查：
          1. 交易频率异常
          2. 仓位异常
          3. 盈亏异常
          4. 杠杆异常
        
        返回：
          None 或 {'type': '...', 'severity': '...'}
        """
        # 检查1：交易频率异常
        if agent.trade_count > 100 and cycle < 10:
            # 10个周期内交易100次？异常！
            return {
                'agent_id': agent.agent_id,
                'type': 'high_frequency_anomaly',
                'severity': 'medium',
                'details': f'交易{agent.trade_count}次/10周期',
            }
        
        # 检查2：仓位异常
        if agent.position_size > agent.current_capital * 10:
            # 仓位>10倍资金？异常！
            return {
                'agent_id': agent.agent_id,
                'type': 'position_size_anomaly',
                'severity': 'high',
                'details': f'仓位{agent.position_size} > 资金{agent.current_capital}×10',
            }
        
        # 检查3：盈亏异常
        cycle_pnl = agent.get_cycle_pnl()
        if cycle_pnl < -agent.current_capital * 0.5:
            # 单周期亏50%？异常！
            return {
                'agent_id': agent.agent_id,
                'type': 'extreme_loss_anomaly',
                'severity': 'high',
                'details': f'单周期亏损{cycle_pnl/agent.current_capital:.1%}',
            }
        
        if cycle_pnl > agent.current_capital * 2.0:
            # 单周期赚200%？异常！（可能是Bug）
            return {
                'agent_id': agent.agent_id,
                'type': 'extreme_profit_anomaly',
                'severity': 'medium',
                'details': f'单周期盈利{cycle_pnl/agent.current_capital:.1%}',
            }
        
        # 检查4：杠杆异常
        if agent.current_leverage > 100:
            # 杠杆>100x？异常！
            return {
                'agent_id': agent.agent_id,
                'type': 'leverage_anomaly',
                'severity': 'high',
                'details': f'杠杆{agent.current_leverage}x',
            }
        
        return None
    
    # ========== 功能4：合规检查 ==========
    
    def compliance_check(self, agents: List[AgentV7]) -> Dict:
        """
        合规检查（强制执行规则）
        
        检查：
          1. 多样性规则（单一生态位<40%）
          2. 杠杆规则（<20x）
          3. 仓位规则（单Agent<10%）
        
        返回：
          {
            'violations': [],
            'actions_taken': [],
          }
        """
        violations = []
        actions_taken = []
        
        # 检查1：多样性规则
        niche_counts = {}
        for agent in agents:
            niche = agent.niche
            niche_counts[niche] = niche_counts.get(niche, 0) + 1
        
        for niche, count in niche_counts.items():
            ratio = count / len(agents)
            if ratio > 0.40:
                violations.append({
                    'type': 'diversity_violation',
                    'niche': niche,
                    'ratio': ratio,
                })
                # 强制淘汰该生态位的弱Agent
                self._force_eliminate_weak_agents(agents, niche)
                actions_taken.append(f'强制淘汰{niche}弱Agent')
        
        # 检查2：杠杆规则
        for agent in agents:
            if agent.current_leverage > 20.0:
                violations.append({
                    'type': 'leverage_violation',
                    'agent_id': agent.agent_id,
                    'leverage': agent.current_leverage,
                })
                # 强制降低杠杆
                agent.current_leverage = 20.0
                actions_taken.append(f'强制降低Agent-{agent.agent_id}杠杆至20x')
        
        # 检查3：仓位规则
        total_capital = sum(a.current_capital for a in agents)
        for agent in agents:
            position_ratio = agent.position_size / total_capital
            if position_ratio > 0.10:
                violations.append({
                    'type': 'position_violation',
                    'agent_id': agent.agent_id,
                    'ratio': position_ratio,
                })
                # 强制减仓
                self._force_reduce_position(agent, 0.10)
                actions_taken.append(f'强制减少Agent-{agent.agent_id}仓位')
        
        return {
            'violations': violations,
            'actions_taken': actions_taken,
        }
    
    # ========== 功能5：紧急干预 ==========
    
    def emergency_intervention(
        self,
        action: str,  # 'reduce_leverage', 'close_all', 'shutdown'
        agents: List[AgentV7],
        okx_client: OKXClient
    ):
        """
        紧急干预（最后一道防线）
        """
        logger.error(f"💀💀💀 Prophet紧急干预：{action}")
        
        if action == 'reduce_leverage':
            # 全局降低杠杆
            for agent in agents:
                agent.current_leverage = max(1.0, agent.current_leverage * 0.5)
            logger.warning("⚠️  已将所有Agent杠杆减半")
        
        elif action == 'close_all':
            # 全部平仓
            for agent in agents:
                if agent.has_position():
                    okx_client.close_position(agent)
            logger.error("💀 已强制平仓所有Agent")
        
        elif action == 'shutdown':
            # 紧急关闭系统
            for agent in agents:
                if agent.has_position():
                    okx_client.close_position(agent)
            # 停止系统
            self._emergency_shutdown()
            logger.error("💀💀💀 系统已紧急关闭")
    
    # ========== 监控面板 ==========
    
    def get_risk_dashboard(self, agents, current_drawdown, daily_loss) -> Dict:
        """
        风控监控面板（实时显示）
        """
        return {
            'system_health': {
                'total_agents': len(agents),
                'active_agents': len([a for a in agents if a.state == 'active']),
                'total_capital': sum(a.current_capital for a in agents),
                'system_roi': self._calculate_system_roi(agents),
                'current_drawdown': current_drawdown,
                'daily_loss': daily_loss,
            },
            'risk_metrics': {
                'system_leverage': sum(a.current_leverage * a.position_size for a in agents if a.has_position()),
                'position_concentration': self._calculate_position_concentration(agents),
                'health_score': self.ecosystem_monitor.get_health_score(),
            },
            'audit_status': {
                'last_audit': self.audit_history[-1] if self.audit_history else None,
                'audit_passed': self.audit_history[-1]['passed'] if self.audit_history else True,
            },
            'recent_anomalies': self.anomaly_log[-10:],  # 最近10条异常
        }


# ========== 示例使用 ==========

"""
# Prophet每个周期自动执行风控/审计

prophet = ProphetV7()

for cycle in range(10000):
    # 1. 正常的资金分配、杠杆管理...
    prophet.allocate(agents, world_signature, market_data)
    
    # 2. 风控/审计（新增！）
    
    # 2.1 账簿审计
    audit_result = prophet.risk_control.audit_ledgers(agents, public_ledger)
    if not audit_result['passed']:
        # 账簿不一致！紧急处理
        prophet.risk_control.emergency_intervention('close_all', agents, okx_client)
    
    # 2.2 系统级风险监控
    risk_report = prophet.risk_control.check_system_risk(
        agents, current_drawdown, daily_loss
    )
    if risk_report['emergency_action']:
        # 触发紧急干预
        prophet.risk_control.emergency_intervention(
            risk_report['emergency_action'], agents, okx_client
        )
    
    # 2.3 异常交易检测
    for agent in agents:
        anomaly = prophet.risk_control.detect_anomaly(agent, cycle)
        if anomaly and anomaly['severity'] == 'high':
            # 发现高危异常，淘汰该Agent
            moirai.terminate_agent(agent, 'anomaly_detected')
    
    # 2.4 合规检查
    compliance_result = prophet.risk_control.compliance_check(agents)
    if compliance_result['violations']:
        logger.warning(f"⚠️  发现{len(compliance_result['violations'])}处违规")
    
    # 3. 继续正常交易...
"""
```

---

## 🏗️ Prophet v7.0架构

```python
# Prophet v7.0完整架构

class ProphetV7:
    """
    Prophet v7.0：Prometheus的大脑
    
    五大核心能力：
      1. 方向分配引擎（资金分配）
      2. 杠杆管理器（杠杆控制）
      3. 生态系统监控器（健康监控）
      4. 战略Immigration（多样性救援）
      5. 风控/审计系统（最后一道防线）⭐ 新增！
    """
    
    def __init__(
        self,
        experience_db: ExperienceDB,
        moirai: Moirai,
        capital_pool: CapitalPool
    ):
        # 四大核心组件
        self.direction_engine = DirectionAllocationEngine()
        self.leverage_manager = LeverageManager()
        self.ecosystem_monitor = EcosystemMonitor()
        self.immigration = StrategicImmigration(experience_db, moirai)
        
        # 依赖
        self.experience_db = experience_db
        self.moirai = moirai
        self.capital_pool = capital_pool
        
        # 状态
        self.current_world_signature = None
        self.health_history = []
    
    # ========== 对外唯一接口（极简！）==========
    
    def allocate(
        self,
        agents: List[AgentV7],
        world_signature: WorldSignatureSimple,
        market_data: Dict
    ):
        """
        Prophet的唯一对外接口（极简！）
        
        内部复杂：
          - 方向分配
          - 杠杆管理
          - 健康监控
          - 干预决策
        
        外部简单：
          - 一个方法搞定
        """
        self.current_world_signature = world_signature
        
        # 1. 计算各生态位表现
        niche_performance = self._calculate_niche_performance(agents)
        
        # 2. 方向分配（资金分配）
        capital_allocation = self.direction_engine.allocate_capital(
            world_signature=world_signature,
            niche_performance=niche_performance,
            total_capital=self.capital_pool.get_available_capital()
        )
        
        # 3. 根据分配调整各Agent资金
        self._redistribute_capital(agents, capital_allocation)
        
        # 4. 杠杆管理（为每个Agent计算杠杆）
        market_volatility = self._calculate_market_volatility(market_data)
        for agent in agents:
            leverage = self.leverage_manager.calculate_leverage(
                agent=agent,
                market_volatility=market_volatility,
                world_signature=world_signature
            )
            agent.current_leverage = leverage
        
        # 5. 生态系统监控
        health = self.ecosystem_monitor.check_ecosystem_health(agents)
        self.health_history.append(health)
        
        # 6. 干预（如果需要）
        if health['intervention_needed']:
            logger.warning(f"🧠 Prophet干预：{health['intervention_needed']}")
            self.ecosystem_monitor.intervene(health, self.moirai)
    
    # ========== 辅助方法 ==========
    
    def _calculate_niche_performance(self, agents) -> Dict[str, float]:
        """计算各生态位平均表现"""
        niche_agents = {}
        for agent in agents:
            niche = agent.niche
            if niche not in niche_agents:
                niche_agents[niche] = []
            niche_agents[niche].append(agent)
        
        niche_performance = {}
        for niche, agents_list in niche_agents.items():
            avg_pf = np.mean([a.get_profit_factor() for a in agents_list])
            niche_performance[niche] = avg_pf
        
        return niche_performance
    
    def _redistribute_capital(self, agents, capital_allocation):
        """根据分配重新分配各Agent资金"""
        # 简化：按生态位平均分配
        for niche, capital in capital_allocation.items():
            niche_agents = [a for a in agents if a.niche == niche]
            if niche_agents:
                capital_per_agent = capital / len(niche_agents)
                for agent in niche_agents:
                    agent.allocated_capital = capital_per_agent
    
    def _calculate_market_volatility(self, market_data) -> float:
        """计算市场波动率（20日滚动）"""
        returns = market_data['returns_20d']
        volatility = np.std(returns) * np.sqrt(252)  # 年化
        return volatility
    
    # ========== 监控接口 ==========
    
    def get_health_score(self) -> float:
        """获取当前健康度"""
        if self.health_history:
            return self.health_history[-1]['health_score']
        return 1.0
    
    def get_health_report(self) -> Dict:
        """获取完整健康报告"""
        if self.health_history:
            return self.health_history[-1]
        return {}
```

---

## 💡 Prophet设计哲学

### 1. 极简接口，复杂内部

```python
# 对外：极简
prophet.allocate(agents, world_signature, market_data)

# 内部：复杂
# - 方向分配（复杂算法）
# - 杠杆管理（波动率目标）
# - 健康监控（4大指标）
# - 干预决策（4种干预）

结果：
  ✅ 用户体验极简
  ✅ 内部功能强大
```

### 2. 战略决策，不是战术执行

```
Prophet = 将军
  - 决定资金分配（哪个方向多，哪个方向少）
  - 决定杠杆大小（风险控制）
  - 监控整体健康（生态平衡）
  - 但不决定具体交易（交给Agent）

Agent = 士兵
  - 具体交易决策
  - 执行买卖
  - 但不决定资金分配

分工：
  ✅ Prophet：战略层
  ✅ Agent：战术层
  ✅ 各司其职
```

### 3. 反脆弱优先

```
Prophet的首要任务：维护生态平衡

1. 强制多样性（最高优先级）
   - 单一生态位<40%
   - 逆向生态位>15%
   - 至少5个生态位存活

2. 生态监控（持续）
   - 健康度<0.5 → 警告
   - 健康度<0.3 → 紧急干预

3. 干预机制（4种）
   - 方向垄断 → 强制平衡
   - 生态位垄断 → 强制多样性
   - 生态位灭绝 → 定向补充
   - 系统崩溃 → 紧急重置

结果：
  💎 生态永不崩溃
  💎 多样性永存
  💎 反脆弱性极强
```

---

## 📋 Prophet开发路线图（更新：5大能力）

### Week 1-2：DirectionAllocationEngine

```
任务：
  ✅ 10种生态位配置
  ✅ allocate_capital()算法
  ✅ 多样性约束
  ✅ 测试：牛市/熊市/震荡市

代码量：
  ~600行
```

### Week 3-4：LeverageManager

```
任务：
  ✅ calculate_leverage()算法
  ✅ 波动率目标（Volatility Targeting）
  ✅ Agent表现调整
  ✅ 市场环境调整

代码量：
  ~400行
```

### Week 5-6：EcosystemMonitor

```
任务：
  ✅ check_ecosystem_health()
  ✅ 4大健康指标
  ✅ intervene()干预机制
  ✅ 测试：各种失衡场景

代码量：
  ~500行
```

### Week 7：StrategicImmigration

```
任务：
  ✅ inject_immigrants()
  ✅ 4种策略（random/recall/legendary/niche_specific）
  ✅ 与Moirai集成

代码量：
  ~200行
```

### Week 8-9：RiskControlAndAuditSystem ⭐ 新增！

```
任务：
  ✅ audit_ledgers()（账簿审计）
  ✅ check_system_risk()（系统级风险监控）
  ✅ detect_anomaly()（异常交易检测）
  ✅ compliance_check()（合规检查）
  ✅ emergency_intervention()（紧急干预）
  ✅ get_risk_dashboard()（监控面板）

代码量：
  ~800行

关键性：
  💎 这是Prophet的"最后一道防线"
  💎 防止系统性风险
  💎 保证账簿一致性（v6.0教训）
```

### Week 10：Prophet集成测试

```
任务：
  ✅ Prophet + Moirai + Agent完整流程
  ✅ 测试：生态平衡
  ✅ 测试：干预机制
  ✅ 测试：多样性维护
  ✅ 测试：风控/审计机制⭐ 新增！
  ✅ 测试：账簿一致性
  ✅ 测试：紧急干预

结果：
  💎 Prophet v7.0完成！
```

---

## 🎯 Prophet成功标准

```
功能标准：
  ✅ 方向分配有效（根据市场调整）
  ✅ 杠杆管理有效（波动率目标）
  ✅ 健康监控有效（准确识别失衡）
  ✅ 干预机制有效（恢复平衡）

反脆弱标准：
  ✅ 健康度>0.5（持续）
  ✅ 多样性永不崩溃
  ✅ 逆向生态位>15%（持续）
  ✅ 无单一生态位垄断（<40%）

性能标准：
  ✅ 系统ROI>基准
  ✅ 夏普比率>1.5
  ✅ 最大回撤<30%
```

---

## 💎 Prophet的终极使命

```
Prophet v1.0-v6.0：
  🐣 婴儿（功能有限）

Prophet v7.0：
  🧠 大脑（觉醒！）

Prophet的使命：
  1. 战略决策中心
  2. 生态系统管理者
  3. 多样性守护者
  4. 反脆弱性保证
  5. 风控/审计最后防线⭐ 新增！

Prophet的智慧：
  💡 不是控制每个Agent
  💡 而是维护生态平衡
  💡 让系统自组织
  💡 涌现智能行为

结果：
  💎 简单规则 → 复杂行为
  💎 多样性 → 反脆弱
  💎 生态平衡 → 稳定盈利

这就是Prophet v7.0的真正力量！
```

---

## 🚀 立即开始Prophet开发！

**第一步：DirectionAllocationEngine**

**时间：2周**

**代码：~600行**

**Prophet觉醒的时刻到了！** 🧠

