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
                 **kwargs):
        """
        初始化命运三女神（v5.0专用，不向后兼容）
        
        Args:
            bulletin_board: 公告板系统
            num_families: 家族数量
            exchange: 交易所接口（OKXExchange或模拟交易所）
            match_config: 撮合配置
            capital_pool: 资金池（CapitalPool实例）
            **kwargs: 其他参数传递给Supervisor
        """
        # 继承Supervisor的初始化
        super().__init__(bulletin_board=bulletin_board, **kwargs)
        
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
        2. 创建基因组（Genome）
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
                agent = AgentV5.create_genesis(
                    agent_id=agent_id,
                    initial_capital=allocated_capital,  # ✅ 使用从资金池分配的资金
                    family_id=family_id,
                    num_families=self.num_families,
                    full_genome_unlock=full_genome_unlock  # ✨ 传递参数
                )
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
        ✂️ Atropos判断哪些Agent应该被淘汰（v5.0专用）
        
        判断标准：
        1. Agent主动自杀（should_commit_suicide）
        2. 资金耗尽（capital < 阈值）
        3. 长期表现不佳
        
        Returns:
            List[(AgentV5, reason)]: 应该被淘汰的Agent列表
        """
        to_eliminate = []
        
        for agent in self.agents:
            try:
                # AlphaZero式：只基于客观指标判断淘汰
                # 移除"自杀"机制，由EvolutionManager强制淘汰
                if agent.current_capital < agent.initial_capital * 0.1:
                    to_eliminate.append((agent, "资金耗尽"))
                    
            except Exception as e:
                logger.error(f"   ❌ 判断{agent.agent_id}失败: {e}")
                continue
        
        return to_eliminate
    
    def _atropos_eliminate_agent(self, agent: AgentV5, reason: str, current_price: float = 0):
        """
        ✂️ Atropos剪断生命之线（v5.0专用）
        
        无情地淘汰失败的Agent，并回收其剩余资金
        
        流程：
        1. 先平仓所有持仓（如果有）
        2. 平仓后资金归入virtual_capital
        3. 回收资金到资金池
        
        Args:
            agent: 要淘汰的AgentV5
            reason: 淘汰原因
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
        ✂️ Atropos执行淘汰检查
        
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

