"""
Moirai（摩伊莱/命运三女神）- Prometheus v5.0
===========================================

命运三女神，掌管所有Agent的生命周期：
- Clotho（克洛索）: 纺织生命之线 → 创建Agent
- Lachesis（拉刻西斯）: 分配命运 → 监督交易、执行指令
- Atropos（阿特洛波斯）: 剪断生命之线 → 淘汰失败的Agent

在希腊神话中，连众神都无法违抗命运三女神的裁决。
她们代表了最终的、不可改变的自然规律。

v5.0设计理念：
- 继承v4.0 Supervisor的核心功能
- 支持AgentV5的新架构
- 清晰的职责划分（三位女神）
- 向后兼容v4.0 AgentV4
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np

# 继承v4.0 Supervisor
from .supervisor import Supervisor, AgentHealthReport

# v5.0新模块
from .agent_v5 import AgentV5, AgentState, DeathReason
from .lineage import LineageVector
from .genome import GenomeVector
# AlphaZero式：移除Instinct
# from .instinct import Instinct

logger = logging.getLogger(__name__)


class TerminationReason:
    """
    Agent生命终结原因（v6.0 Stage 1.1）
    
    设计理念：
    - 明确区分终结原因
    - 决定是否载入史册
    - 决定最终状态
    """
    BANKRUPTCY = 'bankruptcy'              # 破产（资金<10%初始资金）
    POOR_PERFORMANCE = 'poor_performance'  # 性能淘汰（PF最低）
    RETIREMENT_HERO = 'retirement_hero'    # 光荣退休（5个奖章）✨
    RETIREMENT_AGE = 'retirement_age'      # 寿终正寝（10代）


class Moirai(Supervisor):
    """
    摩伊莱 - 命运三女神
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    三位女神的职责分工
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Clotho（克洛索）- 纺织生命之线
        🧵 genesis()           - 创世，诞生Agent
        🧵 _clotho_create_v5() - 创建AgentV5
        🧵 _clotho_weave()     - 纺织新Agent
    
    Lachesis（拉刻西斯）- 分配命运
        ⚖️ run_cycle()           - 运行周期，监督交易
        ⚖️ _lachesis_supervise() - 监督Agent决策
        ⚖️ _lachesis_execute()   - 执行交易指令
        ⚖️ _lachesis_validate()  - 验证风险
    
    Atropos（阿特洛波斯）- 剪断生命之线
        ✂️ _atropos_judge()     - 判断是否淘汰
        ✂️ _atropos_eliminate() - 淘汰Agent
        ✂️ _atropos_cut()       - 剪断生命之线
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    兼容性：
    - 完全继承v4.0 Supervisor的功能
    - 支持v4.0 AgentV4和v5.0 AgentV5
    - 通过agent_version参数切换
    """
    
    def __init__(self, 
                 bulletin_board=None,
                 num_families: int = 50,
                 exchange=None,
                 match_config: Optional[Dict] = None,
                 capital_pool=None,
                 experience_db=None,
                 **kwargs):
        """
        初始化命运三女神（v5.0专用，不向后兼容）
        
        Args:
            bulletin_board: 公告板系统
            num_families: 家族数量
            exchange: 交易所接口（OKXExchange或模拟交易所）
            match_config: 撮合配置
            capital_pool: 资金池（CapitalPool实例）
            experience_db: 经验数据库（ExperienceDB实例，用于智能创世）
            **kwargs: 其他参数传递给Supervisor
        """
        # 继承Supervisor的初始化
        super().__init__(bulletin_board=bulletin_board, **kwargs)
        
        # v6.0: 经验数据库（智能创世）
        self.experience_db = experience_db
        
        # v5.0配置
        self.num_families = num_families
        
        # 家族分配计数器（用于创世Agent）
        self._family_counter = 0
        
        # ✅ v6.0: 资金池（统一资金管理）
        self.capital_pool = capital_pool
        
        # 交易撮合配置
        self.exchange = exchange
        self.match_config = match_config or {
            # 回测配置
            "backtest_slippage": 0.0001,
            "backtest_fee": 0.0002,
            # Mock配置
            "mock_latency_min": 10,
            "mock_latency_max": 100,
            "mock_reject_rate": 0.05,
            "mock_fee": 0.0003,
            "mock_slippage_max": 0.005,
            # 虚拟盘配置
            "live_max_retries": 3,
            "live_timeout": 5.0,
            "live_cycle_interval": 3600,
            # 风控配置
            "max_position_ratio": 0.95,
            "max_trades_per_hour": 10,
            "min_trade_interval": 60,
        }
        
        logger.info(f"⚖️ Moirai（命运三女神）已初始化 [v5.0专用]")
        logger.info(f"   🧵 Clotho准备纺织新生命...")
        logger.info(f"   ⚖️ Lachesis准备分配命运...")
        logger.info(f"   ✂️ Atropos准备剪断失败者的生命之线...")
        logger.info(f"   📊 家族数量: {num_families}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Clotho（克洛索）- 纺织生命之线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _genesis_create_agents(self, agent_count, gene_pool, capital_per_agent, 
                               agent_factory=None, full_genome_unlock=False):
        """
        🧵 Clotho的职责：纺织新的生命之线（v5.0专用）
        
        覆盖Supervisor的方法，创建AgentV5
        
        Args:
            agent_count: Agent数量
            gene_pool: 基因池（v4.0格式，但我们不使用）
            capital_per_agent: 每个Agent的资金
            agent_factory: Agent工厂（忽略）
            full_genome_unlock: 是否解锁所有50个基因参数（激进模式）
        
        Returns:
            List[AgentV5]: 创建的AgentV5列表
        """
        return self._clotho_create_v5_agents(
            agent_count, gene_pool, capital_per_agent, full_genome_unlock
        )
    
    def _clotho_create_v5_agents(self, agent_count: int, gene_pool: List, 
                                  capital_per_agent: float,
                                  full_genome_unlock: bool = False) -> List[AgentV5]:
        """
        🧵 Clotho纺织v5.0 Agent
        
        为每个Agent纺织生命之线：
        1. 分配家族（Lineage）
        2. 创建基因组（Genome）- v6.0: 支持智能创世
        3. 赋予本能（Instinct）
        4. 初始化策略池（Strategy Pool）
        5. 赋予记忆（PersonalInsights）
        6. 注入守护神（Daimon）
        
        Args:
            agent_count: 要创建的Agent数量
            gene_pool: 基因池（v4.0格式，需要转换）
            capital_per_agent: 每个Agent的初始资金
            full_genome_unlock: 是否解锁所有50个基因参数（激进模式）
        
        Returns:
            List[AgentV5]: 创建的AgentV5列表
        """
        agents = []
        
        # ✨ v6.0: 智能创世（读取Prophet的创世策略）
        genesis_genomes = []  # 历史优秀基因组列表
        genesis_mode = "random"  # 默认随机创世
        
        if self.bulletin_board and self.experience_db:
            try:
                # 从公告板读取Prophet的创世策略
                strategy_bulletin = self.bulletin_board.get_latest_strategy()
                if strategy_bulletin:
                    genesis_strategy = strategy_bulletin.get("genesis_strategy", {})
                    genesis_mode = genesis_strategy.get("mode", "random")
                    
                    # 根据模式决定是否使用历史基因
                    if genesis_mode in ["adaptive", "mixed"]:
                        # 获取当前市场WorldSignature
                        world_sig = self.bulletin_board.get_current_world_signature()
                        if world_sig:
                            # 从ExperienceDB查询相似的优秀基因
                            similar_count = agent_count if genesis_mode == "adaptive" else agent_count // 2
                            genesis_genomes = self.experience_db.smart_genesis(
                                world_signature=world_sig,
                                top_k=similar_count,
                                similarity_threshold=0.7  # 相似度阈值
                            )
                            logger.info(
                                f"   ✨ 智能创世（{genesis_mode}）: "
                                f"从数据库匹配到{len(genesis_genomes)}个历史优秀基因"
                            )
                        else:
                            logger.warning("   ⚠️ 未找到WorldSignature，回退到随机创世")
                    else:
                        logger.info(f"   🎲 随机创世模式")
                        
            except Exception as e:
                logger.warning(f"   ⚠️ 智能创世失败（{e}），回退到随机创世")
        
        mode_msg = "🔥 激进模式（50参数）" if full_genome_unlock else "渐进模式（3参数）"
        logger.info(f"   🧵 Clotho开始纺织{agent_count}条生命之线...{mode_msg}")
        
        for i in range(agent_count):
            try:
                agent_id = f"Agent_{self.next_agent_id}"
                self.next_agent_id += 1
                
                # 1. 分配家族（循环分配，确保分布均匀）
                family_id = self._family_counter % self.num_families
                self._family_counter += 1
                
                # ✅ v6.0: 从资金池分配资金
                if self.capital_pool:
                    allocated_capital = self.capital_pool.allocate(
                        amount=capital_per_agent,
                        agent_id=agent_id,
                        reason="genesis"
                    )
                    if allocated_capital < capital_per_agent:
                        logger.warning(
                            f"      ⚠️ 资金池不足：期望${capital_per_agent:.2f}，"
                            f"实际${allocated_capital:.2f}"
                        )
                else:
                    # 如果没有资金池，使用默认值（向后兼容）
                    allocated_capital = capital_per_agent
                
                # 2. 创建AgentV5
                # ✨ v6.0: 如果有历史基因（策略参数），使用它；否则随机创建
                agent = AgentV5.create_genesis(
                    agent_id=agent_id,
                    initial_capital=allocated_capital,
                    family_id=family_id,
                    num_families=self.num_families,
                    full_genome_unlock=full_genome_unlock
                )
                
                if i < len(genesis_genomes):
                    # ✅ 使用历史优秀的策略参数（这才是真正控制行为的参数！）
                    historical_params = genesis_genomes[i]  # 这是一个字典
                    
                    # 更新Agent的策略参数
                    if hasattr(agent, 'strategy_params') and agent.strategy_params:
                        from prometheus.core.strategy_params import StrategyParams
                        agent.strategy_params = StrategyParams.from_dict(historical_params)
                        logger.debug(f"      ✨ {agent_id} 使用历史策略参数（智能创世）")
                    else:
                        logger.debug(f"      ⚠️ {agent_id} 无strategy_params，降级到随机基因")
                else:
                    # 随机创建（已在create_genesis中完成）
                    logger.debug(f"      🎲 {agent_id} 使用随机基因")
                
                # 确保血统携带family_id供多样性/移民统计使用
                agent.lineage.family_id = family_id
                
                agents.append(agent)
                
                logger.debug(
                    f"      ✅ {agent_id} | "
                    f"家族{family_id} | "
                    f"策略{[s.name for s in agent.strategy_pool]} | "
                    f"参数:{agent.strategy_params.get_display_string() if hasattr(agent, 'strategy_params') else 'N/A'}"
                )
                
            except Exception as e:
                logger.error(f"      ❌ 创建Agent失败: {e}")
                continue
        
        logger.info(f"   🧵 Clotho纺织完成: {len(agents)}个Agent诞生")
        
        # 显示家族分布
        family_dist = {}
        for agent in agents:
            families = agent.lineage.get_dominant_families(top_k=1)
            if families:
                family_id = families[0][0]
                family_dist[family_id] = family_dist.get(family_id, 0) + 1
        
        logger.info(f"      📊 家族分布: {len(family_dist)}个家族参与")
        
        return agents

    def _clotho_create_single_agent(self, allow_new_family: bool = False) -> AgentV5:
        """
        v5.3 移民机制需要的单Agent创建接口
        
        Args:
            allow_new_family: 是否允许创建新家族（用于移民注入）
        """
        agent_id = f"Agent_{self.next_agent_id}"
        self.next_agent_id += 1
        
        if allow_new_family:
            family_id = self.num_families  # 新家族
            self.num_families += 1
        else:
            family_id = self._family_counter % self.num_families
            self._family_counter += 1
        
        agent = AgentV5.create_genesis(
            agent_id=agent_id,
            initial_capital=self.initial_capital_per_agent if hasattr(self, 'initial_capital_per_agent') else 10000.0,
            family_id=family_id,
            num_families=self.num_families
        )
        # 确保血统携带family_id
        agent.lineage.family_id = family_id
        return agent
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Lachesis（拉刻西斯）- 分配命运
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _lachesis_collect_decisions(self, bulletins: Dict, market_data: Dict, 
                                     cycle_count: int) -> List[Dict]:
        """
        ⚖️ Lachesis收集Agent决策（v5.0专用）
        
        遍历所有AgentV5，收集他们的交易决策
        
        Args:
            bulletins: 公告板信息
            market_data: 市场数据
            cycle_count: 当前周期数
        
        Returns:
            List[Dict]: 所有Agent的决策列表
        """
        decisions = []
        
        for agent in self.agents:
            try:
                # 使用AgentV5的make_trading_decision
                decision = agent.make_trading_decision(
                    market_data=market_data,
                    bulletins=bulletins,
                    cycle_count=cycle_count
                )
                
                if decision:
                    decisions.append(decision)
                    
            except Exception as e:
                logger.error(f"   ❌ {agent.agent_id}决策失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        return decisions
    
    def _lachesis_validate_decision(self, decision: Dict) -> Tuple[bool, str]:
        """
        ⚖️ Lachesis验证决策的合规性
        
        检查：
        1. 资金是否充足
        2. 仓位是否合规
        3. 风险是否可控
        
        Args:
            decision: Agent的交易决策
        
        Returns:
            (是否通过, 原因)
        """
        # TODO: 实现风险验证逻辑
        return True, "通过"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Atropos（阿特洛波斯）- 剪断生命之线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _atropos_judge_agents(self) -> List[Tuple[AgentV5, str]]:
        """
        ✂️ Atropos判断哪些Agent应该被淘汰（v6.0 Stage 1.1版）
        
        ⚠️ 注意：这是**即时淘汰**机制（破产保护），不同于EvolutionManager的周期性淘汰
        
        判断标准：
        1. 资金耗尽（capital < 10%初始资金）→ 即时淘汰（破产保护）
        2. ❌ 移除"长期表现不佳"判断 → 由EvolutionManager基于PF周期性淘汰
        
        ✅ Stage 1.1一致性：
        - Moirai只负责"破产保护"（资金耗尽）
        - EvolutionManager负责"优胜劣汰"（基于Profit Factor）
        - 两者互补，不冲突
        
        Returns:
            List[(AgentV5, reason)]: 应该被淘汰的Agent列表
        """
        to_eliminate = []
        
        for agent in self.agents:
            try:
                # ✅ Stage 1.1: 只检查资金耗尽（破产保护）
                # 不检查表现（由EvolutionManager基于PF判断）
                if agent.current_capital < agent.initial_capital * 0.1:
                    to_eliminate.append((agent, "资金耗尽"))
                    
            except Exception as e:
                logger.error(f"   ❌ 判断{agent.agent_id}失败: {e}")
                continue
        
        return to_eliminate
    
    def retire_agent(
        self,
        agent: AgentV5,
        reason: str,  # 'hero' or 'age'
        current_price: float,
        awards: int = 0
    ) -> float:
        """
        🏆 Agent光荣退休（v6.0 Stage 1.1）
        
        💎 退休 ≠ 死亡
        - 退休是荣耀，死亡是终结
        - 退休载入史册，死亡被遗忘
        - 退休可被召回，死亡不可逆
        
        适用场景：
        - RETIREMENT_HERO: 光荣退休（5个奖章）🏆
        - RETIREMENT_AGE: 寿终正寝（10代）
        
        流程：
        1. Lachesis协助平仓（套现未实现盈亏）
        2. Atropos回收资金（100%回Pool）
        3. 载入史册（光荣退休）✨
        4. 标记状态（RETIRED_HERO/RETIRED_AGE）
        
        Args:
            agent: 要退休的AgentV5
            reason: 退休原因（'hero' or 'age'）
            current_price: 当前市场价格（用于平仓）
            awards: 获得的奖章数量（用于日志）
        
        Returns:
            float: 回收的资金数额
        """
        logger.info(f"\n🏆 ===== Agent光荣退休 =====")
        logger.info(f"   Agent: {agent.agent_id}")
        
        if reason == 'hero':
            logger.info(f"   🎖️ 荣誉: {awards}个奖章")
            logger.info(f"   原因: 光荣退休（5个奖章）")
        else:
            logger.info(f"   原因: 寿终正寝（10代）")
        
        # ✅ Step 1: Lachesis协助平仓
        final_capital = self._lachesis_force_close_all(
            agent=agent,
            current_price=current_price,
            reason=f"retire_{reason}"
        )
        
        # ✅ Step 2: Atropos回收资金到资金池
        reclaimed_amount = 0.0
        if self.capital_pool and final_capital > 0:
            self.capital_pool.reclaim(
                amount=final_capital,
                agent_id=agent.agent_id,
                reason=f'retirement_{reason}'
            )
            reclaimed_amount = final_capital
            logger.info(f"   💰 资金回收: ${reclaimed_amount:,.2f}")
        
        # ✅ Step 3: 载入史册（光荣退休必定载入）
        if hasattr(self, 'experience_db') and self.experience_db:
            try:
                # 获取当前WorldSignature
                world_sig = None
                if hasattr(self, 'prophet') and self.prophet:
                    world_sig = self.prophet.get_current_world_signature()
                
                # 保存到ExperienceDB
                self.experience_db.save_best_genomes(
                    agents=[agent],
                    world_signature=world_sig,
                    round_id=f"gen_{getattr(self, 'generation', 0)}"
                )
                
                # 计算ROI用于日志
                roi = (final_capital / agent.initial_capital - 1.0) \
                      if agent.initial_capital > 0 else 0.0
                
                if reason == 'hero':
                    logger.info(f"   📜 载入史册: ROI={roi*100:.2f}%")
                    logger.info(f"   🏆 {agent.agent_id}的荣光将永远传颂！")
                else:
                    logger.info(f"   📜 记录生平: ROI={roi*100:.2f}%")
            except Exception as e:
                logger.error(f"   ❌ 史册记录失败: {e}")
        
        # ✅ Step 4: 标记退休状态并移除
        if reason == 'hero':
            agent.state = AgentState.RETIRED_HERO
        else:
            agent.state = AgentState.RETIRED_AGE
        
        if agent in self.agents:
            self.agents.remove(agent)
        
        logger.info(f"   ✅ 退休完成 | 状态: {agent.state.value}")
        logger.info(f"🏆 ========================\n")
        
        return reclaimed_amount
    
    def terminate_agent(
        self,
        agent: AgentV5,
        reason: str,  # TerminationReason的值
        current_price: float
    ) -> float:
        """
        ✂️ Atropos剪断生命之线（v6.0 Stage 1.1）
        
        💀 死亡终结 - 三女神协作：
        1. Lachesis协助平仓（套现未实现盈亏）
        2. Atropos回收资金（100%回Pool）
        3. 标记状态（DEAD）
        
        适用场景：
        - BANKRUPTCY: 破产（资金<10%初始资金）
        - POOR_PERFORMANCE: 性能淘汰（PF最低）
        
        ⚠️ 注意：不载入史册（退休才载入）
        
        Args:
            agent: 要终结的AgentV5
            reason: 终结原因（TerminationReason的值）
            current_price: 当前市场价格（用于平仓）
        
        Returns:
            float: 回收的资金数额
        """
        logger.info(f"\n💀 ===== Agent生命终结 =====")
        logger.info(f"   Agent: {agent.agent_id}")
        logger.info(f"   原因: {reason}")
        
        # ✅ Step 1: Lachesis协助平仓
        final_capital = self._lachesis_force_close_all(
            agent=agent,
            current_price=current_price,
            reason=f"terminate_{reason}"
        )
        
        # ✅ Step 2: Atropos回收资金到资金池
        reclaimed_amount = 0.0
        if self.capital_pool and final_capital > 0:
            self.capital_pool.reclaim(
                amount=final_capital,
                agent_id=agent.agent_id,
                reason=reason
            )
            reclaimed_amount = final_capital
            logger.info(f"   💰 资金回收: ${reclaimed_amount:,.2f}")
        
        # ✅ Step 3: 标记死亡状态并移除
        agent.state = AgentState.DEAD
        
        if agent in self.agents:
            self.agents.remove(agent)
        
        logger.warning(f"   ✂️ Atropos剪断了{agent.agent_id}的生命之线")
        logger.info(f"   ✅ 生命终结完成 | 状态: {agent.state.value}")
        logger.info(f"💀 ========================\n")
        
        return reclaimed_amount
    
    def _atropos_eliminate_agent(self, agent: AgentV5, reason: str, current_price: float = 0):
        """
        ⚠️ 已废弃！请使用 retire_agent() 或 terminate_agent() 代替
        
        保留此方法仅为向后兼容性
        
        Args:
            agent: 要淘汰的AgentV5
            reason: 淘汰原因（例如："进化淘汰"/"资金耗尽"）
            current_price: 当前市场价格（用于平仓）
        """
        logger.warning(f"⚠️ _atropos_eliminate_agent已废弃，请使用retire_agent()或terminate_agent()")
        
        # 转换为新接口（只有死亡，不是退休）
        return self.terminate_agent(
            agent=agent,
            reason=reason,
            current_price=current_price
        )
    
    def _atropos_eliminate_agent_old(self, agent: AgentV5, reason: str, current_price: float = 0):
        """
        ✂️ Atropos剪断生命之线（v6.0 Stage 1.1版）- 旧实现
        
        ⚠️ 已废弃！保留用于参考
        
        ⚠️ 注意：这是**执行淘汰**，不负责判断（判断由调用者完成）
        
        调用者：
        1. EvolutionManager.run_evolution_cycle() → 基于Profit Factor淘汰弱者
        2. Moirai._atropos_check_and_eliminate() → 破产保护（资金耗尽）
        
        流程：
        1. 先平仓所有持仓（如果有）
        2. 平仓后资金归入virtual_capital
        3. 回收资金到资金池
        
        Args:
            agent: 要淘汰的AgentV5
            reason: 淘汰原因（例如："进化淘汰"/"资金耗尽"）
            current_price: 当前市场价格（用于平仓）
        """
        # ✅ v6.0: Step 1 - 先平仓所有持仓
        if hasattr(agent, 'account') and agent.account and current_price > 0:
            ledger = agent.account.private_ledger
            has_long = ledger.long_position and ledger.long_position.amount > 0
            has_short = ledger.short_position and ledger.short_position.amount > 0
            
            if has_long or has_short:
                logger.info(f"   💀 {agent.agent_id} 死亡前强制平仓...")
                
                # 平多头
                if has_long:
                    amount = ledger.long_position.amount
                    entry_price = ledger.long_position.entry_price  # ✅ 使用entry_price
                    pnl = (current_price - entry_price) * amount
                    
                    logger.info(
                        f"      📉 平多: {amount:.4f} @ ${entry_price:.2f} → "
                        f"${current_price:.2f} | PnL: ${pnl:+.2f}"
                    )
                    
                    # 调用账簿系统记录平仓
                    try:
                        from .ledger_system import Role
                        agent.account.record_trade(
                            trade_type='sell',
                            amount=amount,
                            price=current_price,
                            confidence=1.0,
                            caller_role=Role.MOIRAI
                        )
                    except Exception as e:
                        logger.error(f"      ❌ 平多失败: {e}")
                
                # 平空头
                if has_short:
                    amount = ledger.short_position.amount
                    entry_price = ledger.short_position.entry_price  # ✅ 使用entry_price
                    pnl = (entry_price - current_price) * amount
                    
                    logger.info(
                        f"      📈 平空: {amount:.4f} @ ${entry_price:.2f} → "
                        f"${current_price:.2f} | PnL: ${pnl:+.2f}"
                    )
                    
                    # 调用账簿系统记录平仓
                    try:
                        from .ledger_system import Role
                        agent.account.record_trade(
                            trade_type='cover',
                            amount=amount,
                            price=current_price,
                            confidence=1.0,
                            caller_role=Role.MOIRAI
                        )
                    except Exception as e:
                        logger.error(f"      ❌ 平空失败: {e}")
        elif hasattr(agent, 'account') and agent.account and current_price == 0:
            # 如果没有传入价格，发出警告
            ledger = agent.account.private_ledger
            has_position = (
                (ledger.long_position and ledger.long_position.amount > 0) or
                (ledger.short_position and ledger.short_position.amount > 0)
            )
            if has_position:
                logger.warning(
                    f"      ⚠️ Agent死亡时仍有持仓，但未传入current_price！"
                    f"未实现盈亏将丢失！"
                )
        
        # ✅ v6.0: Step 2 - 回收Agent剩余资金到资金池
        remaining_capital = 0.0
        if hasattr(agent, 'account') and agent.account:
            remaining_capital = agent.account.private_ledger.virtual_capital
            
            # 只有当有资金池时才回收
            if self.capital_pool and remaining_capital > 0:
                self.capital_pool.reclaim(
                    amount=remaining_capital,
                    agent_id=agent.agent_id,
                    reason=reason
                )
        
        logger.warning(
            f"   ✂️ Atropos剪断了{agent.agent_id}的生命之线 | "
            f"原因: {reason} | "
            f"资金剩余: ${remaining_capital:.2f}"
        )
        
        # 从活跃Agent列表中移除
        if agent in self.agents:
            self.agents.remove(agent)
        
        # 标记为死亡
        agent.state = AgentState.DEAD
        if reason == "自杀":
            agent.death_reason = DeathReason.SUICIDE
        elif reason == "资金耗尽":
            agent.death_reason = DeathReason.CAPITAL_DEPLETION
    
    # ========== 资金池生死线守护（v6.0新增）==========
    TARGET_RESERVE_RATIO = 0.20  # 目标：20%资金池（硬约束）
    FIXED_TAX_RATE = 0.10        # 固定税率：10%（可测试调整）
    
    def _lachesis_calculate_breeding_tax(self, elite_agent: AgentV5, current_price: float) -> float:
        """
        ⚖️ Lachesis计算繁殖税（v6.0 Stage 1.1版）
        
        ⚠️ 注意：税率**不基于Agent表现**，只基于系统资金池状态
        
        税率逻辑（AlphaZero式极简）：
        - 资金池 >= 20%：不征税（0%）
        - 资金池 < 20%：固定征税（10%）
        
        ✅ Stage 1.1一致性：
        - 税收是**系统级调控**，不涉及Agent表现评估
        - Elite选择由EvolutionManager基于Profit Factor完成
        - Moirai只负责执行税收，不判断"谁该繁殖"
        
        设计理念：
        - 不分级，不预判，让系统自然平衡
        - 如果10%不够，测试会告诉我们
        
        Args:
            elite_agent: 准备繁殖的精英Agent（由EvolutionManager基于PF选出）
            current_price: 当前市场价格
        
        Returns:
            float: 税额（绝对值）
        """
        if not self.capital_pool:
            return 0.0  # 无资金池，不征税
        
        # 1. 计算系统资金状态
        agent_total_capital = 0.0
        for agent in self.agents:
            if agent.state != AgentState.DEAD and hasattr(agent, 'account') and agent.account:
                realized = agent.account.private_ledger.virtual_capital
                # 繁殖时已经强制平仓，所以这里主要是realized，unrealized应该为0
                unrealized = 0.0
                if hasattr(agent, 'calculate_unrealized_pnl'):
                    try:
                        unrealized = agent.calculate_unrealized_pnl(current_price)
                    except:
                        unrealized = 0.0
                agent_total_capital += (realized + unrealized)
        
        pool_balance = self.capital_pool.available_pool
        system_total = agent_total_capital + pool_balance
        
        if system_total <= 0:
            logger.warning("   ⚠️ 系统总资金<=0，禁止繁殖")
            return float('inf')  # 返回无穷大，阻止繁殖
        
        reserve_ratio = pool_balance / system_total
        
        # 2. 极简税率逻辑
        if reserve_ratio >= self.TARGET_RESERVE_RATIO:
            tax_rate = 0.0
        else:
            tax_rate = self.FIXED_TAX_RATE
        
        # 3. 计算税额（基于已实现资金）
        if hasattr(elite_agent, 'account') and elite_agent.account:
            elite_capital = elite_agent.account.private_ledger.virtual_capital
        else:
            elite_capital = 0.0
        tax_amount = elite_capital * tax_rate
        
        logger.info(
            f"   💰 繁殖税: 资金池{reserve_ratio*100:.1f}% "
            f"(目标{self.TARGET_RESERVE_RATIO*100:.0f}%) "
            f"→ 税率{tax_rate*100:.0f}% "
            f"→ 税额${tax_amount:,.0f}"
        )
        
        return tax_amount
    
    def _lachesis_force_close_all(self, agent: AgentV5, current_price: float, reason: str = "breeding") -> float:
        """
        ⚖️ Lachesis强制清仓Agent所有持仓
        
        用于繁殖前套现，实现所有浮盈/浮亏
        
        Args:
            agent: 要平仓的Agent
            current_price: 当前市场价格
            reason: 平仓原因
        
        Returns:
            float: 平仓后的实盈资金
        """
        if not hasattr(agent, 'account') or not agent.account or current_price <= 0:
            return agent.account.private_ledger.virtual_capital if hasattr(agent, 'account') and agent.account else 0.0
        
        ledger = agent.account.private_ledger
        has_long = ledger.long_position and ledger.long_position.amount > 0
        has_short = ledger.short_position and ledger.short_position.amount > 0
        
        if not has_long and not has_short:
            # 无持仓，直接返回现金
            return ledger.virtual_capital
        
        logger.info(f"   🔄 {agent.agent_id} 繁殖前强制平仓...")
        
        # 平多头
        if has_long:
            amount = ledger.long_position.amount
            entry_price = ledger.long_position.entry_price
            pnl = (current_price - entry_price) * amount
            
            logger.info(f"      📉 平多: {amount:.4f} @ ${entry_price:.2f} → ${current_price:.2f} | PnL: ${pnl:+,.2f}")
            
            try:
                from .ledger_system import Role
                agent.account.record_trade(
                    trade_type='sell',
                    amount=amount,
                    price=current_price,
                    confidence=1.0,
                    caller_role=Role.MOIRAI
                )
            except Exception as e:
                logger.error(f"      ❌ 平多失败: {e}")
        
        # 平空头
        if has_short:
            amount = ledger.short_position.amount
            entry_price = ledger.short_position.entry_price
            pnl = (entry_price - current_price) * amount
            
            logger.info(f"      📈 平空: {amount:.4f} @ ${entry_price:.2f} → ${current_price:.2f} | PnL: ${pnl:+,.2f}")
            
            try:
                from .ledger_system import Role
                agent.account.record_trade(
                    trade_type='cover',
                    amount=amount,
                    price=current_price,
                    confidence=1.0,
                    caller_role=Role.MOIRAI
                )
            except Exception as e:
                logger.error(f"      ❌ 平空失败: {e}")
        
        # 返回平仓后的实盈资金
        final_capital = ledger.virtual_capital
        logger.info(f"      💰 平仓后资金: ${final_capital:,.2f}")
        
        return final_capital
    
    def _atropos_check_and_eliminate(self) -> int:
        """
        ✂️ Atropos执行淘汰检查（v6.0 Stage 1.1版）
        
        ⚠️ 注意：这是**即时淘汰**（破产保护），不同于EvolutionManager的周期性淘汰
        
        触发时机：
        - 每个交易周期后（可选）
        - 只淘汰资金耗尽的Agent（< 10%初始资金）
        
        ✅ Stage 1.1一致性：
        - 不基于Profit Factor（由EvolutionManager负责）
        - 只基于资金耗尽（破产保护）
        
        Returns:
            int: 淘汰的Agent数量
        """
        to_eliminate = self._atropos_judge_agents()
        
        if to_eliminate:
            logger.info(f"\n   ✂️ Atropos发现{len(to_eliminate)}个失败者需要淘汰")
            
            for agent, reason in to_eliminate:
                self._atropos_eliminate_agent(agent, reason)
            
            logger.info(f"   ✂️ Atropos淘汰完成 | 剩余Agent: {len(self.agents)}")
        
        return len(to_eliminate)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 公共方法
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_status_report(self) -> Dict:
        """
        获取Moirai状态报告（v5.0专用）
        
        Returns:
            Dict: 状态报告
        """
        report = {
            'agent_version': 'v5.0',
            'total_agents': len(self.agents),
            'num_families': self.num_families,
        }
        
        # v5.0统计
        family_dist = {}
        strategy_dist = {}
        
        for agent in self.agents:
            # 家族分布
            families = agent.lineage.get_dominant_families(top_k=1)
            if families:
                family_id = families[0][0]
                family_dist[family_id] = family_dist.get(family_id, 0) + 1
            
            # 策略分布
            if agent.current_strategy_name:
                strategy_dist[agent.current_strategy_name] = \
                    strategy_dist.get(agent.current_strategy_name, 0) + 1
        
        report['family_diversity'] = len(family_dist)
        report['strategy_distribution'] = strategy_dist
        
        return report
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Lachesis（拉刻西斯）- 交易撮合系统
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def match_trade(
        self,
        agent: AgentV5,
        decision: Dict,
        market_data: Dict,
        scenario: str = "backtest"
    ) -> Optional[Dict]:
        """
        ⚖️ Lachesis的职责：撮合交易
        
        场景差异：
        - backtest: 立即确定性成交，无延迟，精确滑点
        - mock: 模拟各种异常，可配置延迟/拒绝率
        - live_demo: 真实网络调用，异步处理，真实延迟
        
        Args:
            agent: 发起交易的Agent
            decision: Agent的交易决策
            market_data: 当前市场数据
            scenario: 场景类型
            
        Returns:
            成交回执 或 None(失败)
        """
        # 1. 风控检查
        if not self._risk_check(agent, decision, scenario):
            return None
        
        # 2. 场景化撮合
        if scenario == "backtest":
            trade_result = self._match_backtest(agent, decision, market_data)
        elif scenario == "mock":
            trade_result = self._match_mock(agent, decision, market_data)
        elif scenario == "live_demo":
            trade_result = self._match_live_demo(agent, decision, market_data)
        else:
            logger.error(f"未知场景: {scenario}")
            return None
        
        # 3. 记录账簿
        if trade_result and trade_result.get("success"):
            self._record_to_ledgers(agent, trade_result)
        
        return trade_result
    
    def _risk_check(self, agent: AgentV5, decision: Dict, scenario: str) -> bool:
        """风控检查"""
        try:
            # 1. 资金充足性
            required_capital = self._calculate_required_capital(decision, scenario)
            if not hasattr(agent, 'account') or not agent.account:
                logger.warning(f"Agent {agent.agent_id} 无账户系统")
                return False
            
            available_capital = agent.account.private_ledger.virtual_capital
            if required_capital > available_capital:
                logger.debug(f"资金不足: 需要{required_capital:.2f}, 可用{available_capital:.2f}")
                return False
            
            # 2. 持仓限制
            if not self._check_position_limit(agent, decision):
                logger.debug(f"超过持仓限制")
                return False
            
            # 3. 价格合理性
            if not self._check_price_sanity(decision):
                logger.debug(f"价格异常")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"风控检查失败: {e}")
            return False
    
    def _calculate_required_capital(self, decision: Dict, scenario: str) -> float:
        """计算所需资金"""
        amount = abs(decision.get("amount", 0))
        price = decision.get("price", 0)
        leverage = decision.get("leverage", 1.0)
        
        if amount <= 0 or price <= 0:
            return float('inf')  # 无效决策，返回无穷大
        
        # 保证金 = 名义价值 / 杠杆
        notional = amount * price
        margin = notional / leverage
        
        # 加上手续费和缓冲
        fee_rate = self.match_config.get(f"{scenario}_fee", 0.0003)
        buffer_rate = 0.01  # 1%缓冲
        
        total_required = margin * (1 + fee_rate + buffer_rate)
        
        return total_required
    
    def _check_position_limit(self, agent: AgentV5, decision: Dict) -> bool:
        """检查持仓限制"""
        # 简单实现：最大持仓不超过资金的95%
        max_ratio = self.match_config.get("max_position_ratio", 0.95)
        return True  # 暂时总是通过
    
    def _check_price_sanity(self, decision: Dict) -> bool:
        """检查价格合理性"""
        price = decision.get("price", 0)
        if price <= 0:
            return False
        # BTC价格应该在合理范围内
        if price < 1000 or price > 1000000:
            return False
        return True
    
    def _match_backtest(self, agent: AgentV5, decision: Dict, market_data: Dict) -> Dict:
        """回测撮合：确定性、同步、快速"""
        import time
        import uuid
        
        price = market_data.get("price", decision.get("price", 0))
        action = decision.get("action")
        amount = abs(decision.get("amount", 0))
        
        if price <= 0 or amount <= 0:
            return {"success": False, "error": "INVALID_PARAMS"}
        
        # 应用滑点
        slippage_rate = self.match_config.get("backtest_slippage", 0.0001)
        if action in ["buy", "long"]:
            fill_price = price * (1 + slippage_rate)
        else:
            fill_price = price * (1 - slippage_rate)
        
        # 手续费
        fee_rate = self.match_config.get("backtest_fee", 0.0002)
        fee = abs(amount * fill_price) * fee_rate
        
        return {
            "success": True,
            "action": action,
            "amount": amount,
            "fill_price": fill_price,
            "fee": fee,
            "timestamp": time.time(),
            "order_id": f"BT_{uuid.uuid4().hex[:8]}",
            "latency_ms": 0,
            "scenario": "backtest"
        }
    
    def _match_mock(self, agent: AgentV5, decision: Dict, market_data: Dict) -> Dict:
        """Mock撮合：可配置各种异常情况"""
        import random
        import time
        import uuid
        
        # 模拟网络延迟
        latency_ms = random.randint(
            self.match_config.get("mock_latency_min", 10),
            self.match_config.get("mock_latency_max", 100)
        )
        time.sleep(latency_ms / 1000.0)
        
        # 模拟订单拒绝
        reject_rate = self.match_config.get("mock_reject_rate", 0.05)
        if random.random() < reject_rate:
            return {
                "success": False,
                "error": "ORDER_REJECTED",
                "reason": "模拟订单拒绝",
                "latency_ms": latency_ms,
                "scenario": "mock"
            }
        
        price = market_data.get("price", decision.get("price", 0))
        action = decision.get("action")
        amount = abs(decision.get("amount", 0))
        
        if price <= 0 or amount <= 0:
            return {"success": False, "error": "INVALID_PARAMS"}
        
        # 动态滑点
        volatility = market_data.get("volatility", 0.01)
        slippage_rate = random.uniform(0, volatility * 2)
        
        if action in ["buy", "long"]:
            fill_price = price * (1 + slippage_rate)
        else:
            fill_price = price * (1 - slippage_rate)
        
        # 手续费
        fee_rate = self.match_config.get("mock_fee", 0.0003)
        fee = abs(amount * fill_price) * fee_rate
        
        return {
            "success": True,
            "action": action,
            "amount": amount,
            "fill_price": fill_price,
            "fee": fee,
            "timestamp": time.time(),
            "order_id": f"MOCK_{uuid.uuid4().hex[:8]}",
            "latency_ms": latency_ms,
            "slippage_bps": slippage_rate * 10000,
            "scenario": "mock"
        }
    
    def _match_live_demo(self, agent: AgentV5, decision: Dict, market_data: Dict) -> Dict:
        """虚拟盘撮合：真实网络调用"""
        import time
        
        start_time = time.time()
        action = decision.get("action")
        amount = abs(decision.get("amount", 0))
        
        if not hasattr(self, 'exchange') or not self.exchange:
            return {"success": False, "error": "NO_EXCHANGE"}
        
        # 调用OKX API
        max_retries = self.match_config.get("live_max_retries", 3)
        for retry in range(max_retries):
            try:
                order_result = self.exchange.place_order(
                    symbol="BTC-USDT-SWAP",
                    side=action,
                    order_type="market",
                    amount=amount,
                    agent_id=agent.agent_id
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                return {
                    "success": True,
                    "action": action,
                    "amount": amount,
                    "fill_price": order_result.get("avgPrice", 0),
                    "fee": order_result.get("fee", 0),
                    "timestamp": time.time(),
                    "order_id": order_result.get("orderId", ""),
                    "latency_ms": latency_ms,
                    "retries": retry,
                    "scenario": "live_demo"
                }
                
            except Exception as e:
                if retry == max_retries - 1:
                    return {
                        "success": False,
                        "error": "NETWORK_ERROR",
                        "reason": str(e),
                        "latency_ms": (time.time() - start_time) * 1000,
                        "scenario": "live_demo"
                    }
                time.sleep(0.5 * (retry + 1))
        
        return {"success": False, "error": "MAX_RETRIES_EXCEEDED"}
    
    def _record_to_ledgers(self, agent: AgentV5, trade_result: Dict):
        """记录到账簿系统"""
        from .ledger_system import Role
        
        try:
            if not hasattr(agent, 'account') or not agent.account:
                logger.error(f"Agent {agent.agent_id} 无账户系统，无法记录交易")
                return
            
            # 统一调用账簿系统记录交易
            agent.account.record_trade(
                trade_type=trade_result["action"],
                amount=trade_result["amount"],
                price=trade_result["fill_price"],
                confidence=1.0,
                caller_role=Role.MOIRAI  # ✅ 使用MOIRAI角色
            )
            
            logger.debug(f"✅ 交易已记录: Agent {agent.agent_id} {trade_result['action']} {trade_result['amount']:.4f} @ {trade_result['fill_price']:.2f}")
            
        except Exception as e:
            import traceback
            logger.error(f"记录交易到账簿失败: {e}")
            logger.error(f"详细堆栈:\n{traceback.format_exc()}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 辅助函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_moirai_summary(moirai: Moirai) -> str:
    """
    格式化Moirai摘要报告
    
    Args:
        moirai: Moirai实例
    
    Returns:
        str: 格式化的报告
    """
    report = moirai.get_status_report()
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚖️ Moirai（命运三女神）状态报告",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Agent版本: {report['agent_version']}",
        f"存活Agent: {report['total_agents']}",
    ]
    
    if report.get('family_diversity'):
        lines.append(f"家族多样性: {report['family_diversity']}个家族")
        
    if report.get('strategy_distribution'):
        lines.append("策略分布:")
        for strategy, count in report['strategy_distribution'].items():
            lines.append(f"  - {strategy}: {count}个")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)

