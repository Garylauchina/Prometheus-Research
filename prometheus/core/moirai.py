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
from .instinct import Instinct

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
                 **kwargs):
        """
        初始化命运三女神（v5.0专用，不向后兼容）
        
        Args:
            bulletin_board: 公告板系统
            num_families: 家族数量
            **kwargs: 其他参数传递给Supervisor
        """
        # 继承Supervisor的初始化
        super().__init__(bulletin_board=bulletin_board, **kwargs)
        
        # v5.0配置
        self.num_families = num_families
        
        # 家族分配计数器（用于创世Agent）
        self._family_counter = 0
        
        logger.info(f"⚖️ Moirai（命运三女神）已初始化 [v5.0专用]")
        logger.info(f"   🧵 Clotho准备纺织新生命...")
        logger.info(f"   ⚖️ Lachesis准备分配命运...")
        logger.info(f"   ✂️ Atropos准备剪断失败者的生命之线...")
        logger.info(f"   📊 家族数量: {num_families}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Clotho（克洛索）- 纺织生命之线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _genesis_create_agents(self, agent_count, gene_pool, capital_per_agent, 
                               agent_factory=None):
        """
        🧵 Clotho的职责：纺织新的生命之线（v5.0专用）
        
        覆盖Supervisor的方法，创建AgentV5
        
        Args:
            agent_count: Agent数量
            gene_pool: 基因池（v4.0格式，但我们不使用）
            capital_per_agent: 每个Agent的资金
            agent_factory: Agent工厂（忽略）
        
        Returns:
            List[AgentV5]: 创建的AgentV5列表
        """
        return self._clotho_create_v5_agents(
            agent_count, gene_pool, capital_per_agent
        )
    
    def _clotho_create_v5_agents(self, agent_count: int, gene_pool: List, 
                                   capital_per_agent: float) -> List[AgentV5]:
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
        
        Returns:
            List[AgentV5]: 创建的AgentV5列表
        """
        agents = []
        
        logger.info(f"   🧵 Clotho开始纺织{agent_count}条生命之线...")
        
        for i in range(agent_count):
            try:
                agent_id = f"Agent_{self.next_agent_id}"
                self.next_agent_id += 1
                
                # 1. 分配家族（循环分配，确保分布均匀）
                family_id = self._family_counter % self.num_families
                self._family_counter += 1
                
                # 2. 创建AgentV5
                agent = AgentV5.create_genesis(
                    agent_id=agent_id,
                    initial_capital=capital_per_agent,
                    family_id=family_id,
                    num_families=self.num_families
                )
                
                agents.append(agent)
                
                logger.debug(
                    f"      ✅ {agent_id} | "
                    f"家族{family_id} | "
                    f"策略{[s.name for s in agent.strategy_pool]} | "
                    f"本能:{agent.instinct.describe_personality()}"
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
                # Agent自主判断
                if agent.should_commit_suicide():
                    to_eliminate.append((agent, "自杀"))
                elif agent.current_capital < agent.initial_capital * 0.1:
                    to_eliminate.append((agent, "资金耗尽"))
                    
            except Exception as e:
                logger.error(f"   ❌ 判断{agent.agent_id}失败: {e}")
                continue
        
        return to_eliminate
    
    def _atropos_eliminate_agent(self, agent: AgentV5, reason: str):
        """
        ✂️ Atropos剪断生命之线（v5.0专用）
        
        无情地淘汰失败的Agent
        
        Args:
            agent: 要淘汰的AgentV5
            reason: 淘汰原因
        """
        logger.warning(
            f"   ✂️ Atropos剪断了{agent.agent_id}的生命之线 | "
            f"原因: {reason} | "
            f"资金剩余: ${agent.current_capital:.2f}"
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
        
        # TODO: 是否需要记录到某个"亡者名单"？
    
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

