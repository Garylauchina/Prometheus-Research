"""
Evolution Manager V5.0 - v5.0专用进化系统
=========================================

完全重构的进化系统，支持AgentV5的Lineage/Genome/Instinct遗传

核心改进：
1. 使用LineageVector进行血统继承
2. 使用GenomeVector进行基因交叉
3. 使用Instinct进行本能遗传
4. 生殖隔离检查（基于Lineage）
5. 双熵监控（Lineage Entropy + Gene Entropy）
"""

from typing import List, Tuple, Dict, Optional
import logging
import numpy as np
import random  # v5.2: 用于变异率随机化

from .agent_v5 import AgentV5
from .lineage import LineageVector
from .genome import GenomeVector
# AlphaZero式：移除所有diversity相关import
# from .instinct import Instinct
# from .dual_entropy import PrometheusBloodLab
# from .diversity_monitor import DiversityMonitor
# from .diversity_protection import DiversityProtector

logger = logging.getLogger(__name__)


class EvolutionManagerV5:
    """
    v6.0 AlphaZero式进化管理器
    
    核心职责：
    1. 评估种群表现（纯Fitness）
    2. 淘汰最差Agent
    3. 病毒式复制（克隆精英+变异）
    
    移除：
    ❌ 生殖隔离检查
    ❌ 双熵监控
    ❌ Immigration
    ❌ 多样性保护
    """
    
    def __init__(self, 
                 moirai,  # Moirai实例（替代supervisor）
                 elite_ratio: float = 0.2,
                 elimination_ratio: float = 0.3,
                 num_families: int = 50,
                 capital_pool=None,
                 fitness_mode: str = 'profit_factor'):
        """
        初始化进化管理器
        
        Args:
            moirai: Moirai实例
            elite_ratio: 精英比例
            elimination_ratio: 淘汰比例
            num_families: 家族数量
            capital_pool: 资金池（CapitalPool实例）
            fitness_mode: Fitness计算模式
                - 'profit_factor': Profit Factor主导（Stage 1.1默认）
                - 'absolute_return': 绝对收益（v6.0原版）
        """
        self.moirai = moirai
        self.elite_ratio = elite_ratio
        self.elimination_ratio = elimination_ratio
        self.num_families = num_families
        self.fitness_mode = fitness_mode  # ✅ Stage 1.1: 添加fitness模式
        
        # ✅ v6.0: 资金池（统一资金管理）
        self.capital_pool = capital_pool
        
        # AlphaZero式：极简统计
        self.generation = 0
        self.total_births = 0
        self.total_deaths = 0
        
        logger.info(f"🦠 EvolutionManagerV5已初始化 (v6.0 AlphaZero式)")
        logger.info(f"   精英比例: {elite_ratio:.0%}")
        logger.info(f"   淘汰比例: {elimination_ratio:.0%}")
        logger.info(f"   繁殖方式: 病毒式复制（固定变异率0.1）")
        logger.info(f"   Fitness模式: {fitness_mode}  ✅ Stage 1.1")
    
    def _calculate_dynamic_mutation_rate(self, gene_entropy: float) -> float:
        """
        计算动态变异率（v5.1.1新增）
        
        基因熵越低，变异率越高，防止种群趋同
        
        Args:
            gene_entropy: 当前基因熵（0-1）
        
        Returns:
            float: 动态变异率（0.1-0.6）
        """
        if gene_entropy >= self.gene_entropy_threshold:
            # 基因熵健康，使用基础变异率
            return self.base_mutation_rate
        else:
            # 基因熵过低，提高变异率
            # 熵越低，变异率越高（线性映射）
            entropy_deficit = self.gene_entropy_threshold - gene_entropy
            boost = (self.max_mutation_rate - self.base_mutation_rate) * (entropy_deficit / self.gene_entropy_threshold)
            mutation_rate = self.base_mutation_rate + boost
            
            logger.warning(
                f"⚠️  基因熵过低({gene_entropy:.3f} < {self.gene_entropy_threshold:.3f})，"
                f"提高变异率: {self.base_mutation_rate:.1%} → {mutation_rate:.1%}"
            )
            
            return min(mutation_rate, self.max_mutation_rate)
    
    def run_evolution_cycle(self, current_price: float = 0):
        """
        🧬 执行一轮进化周期 - AlphaZero式极简版（v6.0）
        
        流程：
        1. 评估Agent表现（纯Fitness）
        2. 淘汰最差的
        3. 计算动态税率（系统级调控）⭐
        4. 让最好的繁殖（含税收机制）
        5. 固定变异率（0.1）
        
        税收机制（系统级调控）：
        ✅ 动态税率：根据资金利用率自动调整
        ✅ 目标：维持80%资金利用率
        ✅ 繁殖时强制父代平仓（套现浮盈）
        ✅ 收取税收 → 资金池
        ✅ 父代保留剩余资金
        ✅ 子代从资金池获得配资
        
        移除：
        ❌ 双熵健康检查
        ❌ 动态变异率
        ❌ 多样性危机检测
        ❌ Immigration
        ❌ 多样性保护
        
        Args:
            current_price: 当前市场价格（用于强制平仓和税收计算）
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🧬 开始进化周期 - 第{self.generation + 1}代 (AlphaZero式)")
        logger.info(f"{'='*70}")
        
        # AlphaZero式：固定变异率
        mutation_rate = 0.1
        
        # ✅ v6.0极简税率：Moirai自动保证20%资金池生死线
        logger.info(f"💰 税率机制: Moirai自动计算（保证{self.moirai.TARGET_RESERVE_RATIO*100:.0f}%资金池生死线）")
        
        # 1. 评估Agent表现（纯Fitness排序）
        rankings = self._rank_agents(current_price=current_price)
        
        if not rankings:
            logger.warning("无Agent可进化")
            return
        
        total_agents = len(rankings)
        
        # 2. 识别精英、存活者和淘汰者（AlphaZero式：纯实力）
        elite_count = max(1, int(total_agents * self.elite_ratio))
        eliminate_count = max(1, int(total_agents * self.elimination_ratio))
        
        elite_agents = rankings[:elite_count]
        survivors = rankings[:-eliminate_count] if eliminate_count < total_agents else []
        to_eliminate = rankings[-eliminate_count:]
        
        # AlphaZero式：没有多样性保护，纯实力淘汰
        
        logger.info(f"📊 种群评估:")
        logger.info(f"   总数: {total_agents}")
        logger.info(f"   精英: {elite_count} (永久保留)")
        logger.info(f"   存活: {len(survivors)}")
        logger.info(f"   淘汰: {eliminate_count}")
        
        # 4. ✂️ Atropos淘汰失败者
        logger.info(f"\n✂️ Atropos开始淘汰失败者...")
        eliminated_ids = []
        
        for agent, pnl in to_eliminate:
            eliminated_ids.append(agent.agent_id)
            logger.info(f"   💀 {agent.agent_id} (PnL=${pnl:+.2f})")
            
            # 标记死亡（传入current_price以便平仓）
            self.moirai._atropos_eliminate_agent(
                agent=agent, 
                reason="进化淘汰",
                current_price=current_price  # ✅ 传入当前价格
            )
            self.total_deaths += 1
        
        # 3. 🦠 病毒式复制（Viral Replication）
        logger.info(f"\n🦠 病毒式复制：精英自我克隆 + 随机变异...")
        
        new_agents = []
        target_replication_count = eliminate_count  # 淘汰多少，复制多少
        
        logger.info(f"📊 目标复制数: {target_replication_count}")
        logger.info(f"🧬 变异率: {mutation_rate:.1%}")
        
        # 🦠 病毒式复制：从精英中选择，克隆并变异
        for i in range(target_replication_count):
            try:
                # 1. 选择一个精英（按fitness加权随机）
                elite = self._select_elite_weighted(elite_agents)
                
                if not elite:
                    logger.warning(f"   无法选择精英，跳过本次复制")
                    continue
                
                # 2. 病毒式复制：克隆 + 变异 + 税收（v6.0极简版）
                # Moirai会自动计算税率，保证20%资金池生死线
                child = self._viral_replicate(
                    elite=elite, 
                    mutation_rate=mutation_rate,
                    current_price=current_price  # ✅ 传入当前价格用于平仓和税收计算
                )
                
                # 子代创建成功
                if child is None:
                    logger.warning(f"   ⚠️ {elite.agent_id} 繁殖失败")
                    continue
                
                new_agents.append(child)
                self.total_births += 1
                
                # 日志
                lineage_type = child.lineage.classify_purity()
                logger.info(
                    f"   🦠 {child.agent_id} | "
                    f"精英父本: {elite.agent_id} | "
                    f"第{child.generation}代 | "
                    f"{lineage_type}"
                )
                
            except Exception as e:
                logger.error(f"   ❌ 繁殖失败（尝试{i+1}/{target_replication_count}）: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        # v5.2：种群波动分析
        actual_breeding_ratio = len(new_agents) / eliminate_count if eliminate_count > 0 else 1.0
        population_change = len(new_agents) - eliminate_count  # 正数=增长，负数=萎缩
        emergency_threshold = int(eliminate_count * 0.9)  # 90%阈值
        
        if len(new_agents) >= target_replication_count:
            # 达到目标
            if population_change > 0:
                logger.info(f"   ✅ 繁殖成功：{len(new_agents)}/{eliminate_count} ({actual_breeding_ratio:.1%})")
                logger.info(f"   📈 种群增长+{population_change}个（v5.2特性：自然波动）")
            elif population_change < 0:
                logger.info(f"   ✅ 繁殖成功：{len(new_agents)}/{eliminate_count} ({actual_breeding_ratio:.1%})")
                logger.info(f"   📉 种群萎缩{population_change}个（v5.2特性：可控波动）")
            else:
                logger.info(f"   ✅ 繁殖成功：{len(new_agents)}/{eliminate_count} ({actual_breeding_ratio:.1%})")
                logger.info(f"   ⚖️ 种群平衡")
        elif len(new_agents) >= emergency_threshold:
            # 达到90%阈值，可接受
            logger.warning(f"   ⚠️ 繁殖偏低：{len(new_agents)}/{eliminate_count} ({actual_breeding_ratio:.1%})")
            logger.warning(f"   📉 种群萎缩{-population_change}个，接近紧急阈值")
        else:
            # 低于90%，触发紧急措施
            logger.error(f"   🚨 繁殖严重不足：{len(new_agents)}/{eliminate_count} ({actual_breeding_ratio:.1%})")
            logger.error(f"   💀 种群萎缩{-population_change}个，已触发紧急阈值！")
            # 未来可以在这里添加紧急恢复机制
        
        # 6. 添加新Agent到Moirai
        self.moirai.agents.extend(new_agents)
        # 为新生Agent挂载账簿，防止后续对账缺失
        try:
            from prometheus.ledger.attach_accounts import attach_accounts
            public_ledger = getattr(self.moirai, "public_ledger", None)
            attach_accounts(new_agents, public_ledger)
        except Exception as e:
            logger.warning(f"新Agent挂账簿失败: {e}")
        
        # 7. ✅ Stage 1.1: Immigration检查（维护多样性）
        immigrants = self.maybe_inject_immigrants(allow_new_family=True, force=False)
        if immigrants:
            logger.info(f"   🚁 Immigration: 注入{len(immigrants)}个移民")
            # 为移民挂载账簿
            try:
                from prometheus.ledger.attach_accounts import attach_accounts
                public_ledger = getattr(self.moirai, "public_ledger", None)
                attach_accounts(immigrants, public_ledger)
            except Exception as e:
                logger.warning(f"移民挂账簿失败: {e}")
        
        # 8. 记录统计
        self.generation += 1
        
        logger.info(f"\n🧬 进化周期完成:")
        logger.info(f"   新生: {len(new_agents)}个")
        if immigrants:
            logger.info(f"   移民: {len(immigrants)}个  ✅ Stage 1.1")
        logger.info(f"   当前种群: {len(self.moirai.agents)}个")
        logger.info(f"   累计出生: {self.total_births}")
        logger.info(f"   累计死亡: {self.total_deaths}")
        logger.info(f"{'='*70}")
    
    def _calculate_fitness_v2(self, agent: AgentV5, total_cycles: int) -> float:
        """
        计算Agent的综合适应度（v5.2: 完整版）
        
        核心理念：
        1. 活着的Agent才是好Agent（必要条件）
        2. 盈利的Agent才是好Agent（充分条件）
        3. 活跃的Agent才是好Agent（不过度消极）
        
        Args:
            agent: 要评估的Agent
            total_cycles: 总周期数（用于归一化）
        
        Returns:
            float: 适应度分数
        """
        import numpy as np
        
        # ============================================================
        # Part 1: 基础分数（当前资金比率）
        # ============================================================
        capital_ratio = agent.current_capital / agent.initial_capital
        base_score = capital_ratio
        
        # ============================================================
        # Part 2: 生存加成（活得久 = 好）
        # ============================================================
        cycles_survived = agent.cycles_survived if hasattr(agent, 'cycles_survived') else 1
        if total_cycles > 0:
            survival_bonus = np.sqrt(cycles_survived / total_cycles)
        else:
            survival_bonus = 1.0
        
        # ============================================================
        # Part 3: 稳定性加成（波动小 = 好）
        # ============================================================
        stability_bonus = 1.0
        if agent.trade_count > 5:
            sharpe = agent.get_sharpe_ratio() if hasattr(agent, 'get_sharpe_ratio') else 0
            stability_bonus = 1 + min(sharpe * 0.2, 0.5)  # 最多+50%
        
        # ============================================================
        # Part 4: 濒死惩罚（险些破产 = 差）
        # ============================================================
        if capital_ratio < 0.3:
            near_death_penalty = 0.3  # 严重惩罚
        elif capital_ratio < 0.5:
            near_death_penalty = 0.7
        else:
            near_death_penalty = 1.0
        
        # ============================================================
        # Part 5: 风险调整（回撤大 = 差）
        # ============================================================
        max_drawdown = agent.max_drawdown if hasattr(agent, 'max_drawdown') else 0
        risk_adjustment = 1 / (1 + max_drawdown)
        
        # ============================================================
        # Part 6: 消极惩罚（太保守 = 差）
        # ============================================================
        negativity_penalty = 1.0
        
        # 6.1 交易频率过低
        expected_min_trades = cycles_survived * 0.3
        if agent.trade_count < expected_min_trades:
            negativity_penalty *= 0.7
        
        # 6.2 长期低收益（活很久但不赚钱）
        if cycles_survived > 20:
            total_return = capital_ratio - 1
            if total_return < 0.05:  # 只赚5%
                negativity_penalty *= 0.5
            elif total_return < 0.10:
                negativity_penalty *= 0.8
        
        # 6.3 远低于市场平均（机会成本）
        alive_agents = [a for a in self.moirai.agents if a.current_capital > a.initial_capital * 0.2]
        if len(alive_agents) > 1:
            market_avg_return = np.mean([
                (a.current_capital / a.initial_capital - 1) 
                for a in alive_agents
            ])
            
            if market_avg_return > 0.1:  # 市场有明显机会
                relative_performance = (capital_ratio - 1) / market_avg_return
                
                if relative_performance < 0.3:  # 不到市场平均的30%
                    negativity_penalty *= 0.5
                elif relative_performance < 0.5:
                    negativity_penalty *= 0.7
        
        # 6.4 持仓时间过少（总是空仓观望）- ⭐ 加强惩罚！
        if hasattr(agent, 'cycles_with_position') and cycles_survived > 0:
            position_time_ratio = agent.cycles_with_position / cycles_survived
            if position_time_ratio < 0.1:  # 90%时间空仓 - 极严重！
                negativity_penalty *= 0.3  # ⭐ 从0.7→0.3，严厉惩罚！
            elif position_time_ratio < 0.2:  # 80%时间空仓
                negativity_penalty *= 0.5  # ⭐ 从0.7→0.5
            elif position_time_ratio < 0.4:  # 60%时间空仓
                negativity_penalty *= 0.7  # ⭐ 从0.9→0.7
            elif position_time_ratio < 0.6:  # 40%时间空仓
                negativity_penalty *= 0.9  # ⭐ 新增：适度惩罚
        
        # ============================================================
        # Final: 综合Fitness（v5.2：6个维度）
        # ============================================================
        fitness = (
            base_score 
            * survival_bonus 
            * stability_bonus 
            * near_death_penalty 
            * risk_adjustment
            * negativity_penalty
        )
        
        return fitness
    
    def _calculate_fitness_v3(self, agent: AgentV5, total_cycles: int, current_price: float = 0.0, btc_return: float = 0.0) -> float:
        """
        ⚔️ 计算Agent的适应度（v3: 绝对收益导向，鼓励"买入持有"）
        
        **核心理念转变**：
        - ❌ 旧版v2：survival_bonus（活得久就好）→ 导致保守观望
        - ✅ 新版v3：绝对收益（赚钱就好）→ 激励积极交易并长期持有
        
        **关键修改**：
        1. 不再乘以survival_bonus（去除"活得久"奖励）
        2. 强力奖励长期持有（holding_duration_bonus）
        3. 严厉惩罚频繁交易（trade_frequency_penalty）
        4. 奖励趋势对齐（做对方向）
        
        Args:
            agent: 要评估的Agent
            total_cycles: 总周期数
            current_price: 当前市场价格（用于计算未实现盈亏）✨ 关键修复！
            btc_return: BTC的收益率（用于对比）
        
        Returns:
            float: 适应度分数
        """
        import numpy as np
        
        # ============================================================
        # Part 1: 绝对收益（核心！）+ 未实现盈亏（v6修复）
        # ============================================================
        # ✅ v6修复：包含未实现盈亏！使用真实的当前市场价格！
        current_capital = agent.current_capital
        
        # 计算未实现盈亏（使用传入的当前市场价格）
        unrealized_pnl = 0.0
        if current_price > 0:  # ✨ 使用真实的当前价格
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
        
        # 有效资金 = 已实现资金 + 未实现盈亏
        effective_capital = current_capital + unrealized_pnl
        capital_ratio = effective_capital / agent.initial_capital
        absolute_return = capital_ratio - 1  # -1 = -100%, 0 = 0%, 1 = +100%
        
        # 如果亏损，fitness极低
        if absolute_return <= -0.5:  # 亏损50%以上
            return 0.001  # 接近淘汰
        elif absolute_return <= 0:  # 任何亏损
            return 0.1 + absolute_return * 0.2  # 0~0.1之间
        
        # 如果盈利，base_score = 1 + 收益率
        base_score = 1.0 + absolute_return  # 0%收益=1.0, 100%收益=2.0
        
        # ============================================================
        # Part 2: 持仓时间奖励（关键！鼓励长期持有）
        # ============================================================
        holding_duration_bonus = 1.0
        
        if hasattr(agent, 'cycles_with_position') and hasattr(agent, 'cycles_survived'):
            if agent.cycles_survived > 0:
                holding_ratio = agent.cycles_with_position / agent.cycles_survived
                
                # 强力奖励持仓！
                if holding_ratio >= 0.9:  # 90%时间持仓
                    holding_duration_bonus = 3.0  # 3倍！
                elif holding_ratio >= 0.7:  # 70%时间持仓
                    holding_duration_bonus = 2.0  # 2倍
                elif holding_ratio >= 0.5:  # 50%时间持仓
                    holding_duration_bonus = 1.5
                elif holding_ratio >= 0.3:  # 30%时间持仓
                    holding_duration_bonus = 1.2
                else:  # <30%时间持仓
                    holding_duration_bonus = 0.5  # 严厉惩罚空仓观望！
        
        # ============================================================
        # Part 3: 交易频率惩罚（关键！惩罚频繁交易）
        # ============================================================
        trade_frequency_penalty = 1.0
        
        if hasattr(agent, 'cycles_survived') and agent.cycles_survived > 0:
            # 理想：每20个周期交易1次（0.05）
            ideal_frequency = 0.05
            # 使用private_ledger的trade_count
            actual_trade_count = agent.account.private_ledger.trade_count if hasattr(agent, 'account') else 0
            actual_frequency = actual_trade_count / agent.cycles_survived
            
            if actual_frequency > ideal_frequency * 5:  # 超过理想的5倍（太频繁！）
                trade_frequency_penalty = 0.3  # 严厉惩罚！
            elif actual_frequency > ideal_frequency * 3:  # 超过3倍
                trade_frequency_penalty = 0.5
            elif actual_frequency > ideal_frequency * 2:  # 超过2倍
                trade_frequency_penalty = 0.7
            elif actual_frequency > ideal_frequency * 1.5:  # 超过1.5倍
                trade_frequency_penalty = 0.9
            # else: 频率合理或偏低，不惩罚
        
        # ============================================================
        # Part 4: 趋势对齐奖励（做对方向）
        # ============================================================
        trend_alignment_bonus = 1.0
        
        # 如果有BTC基准收益，且Agent跑赢BTC
        if btc_return > 0 and absolute_return > btc_return:
            outperformance = (absolute_return - btc_return) / btc_return
            trend_alignment_bonus = 1.0 + min(outperformance, 1.0)  # 最多2倍
        
        # ============================================================
        # Part 5: 稳定性调整（可选，适度影响）
        # ============================================================
        stability_bonus = 1.0
        max_drawdown = getattr(agent, 'max_drawdown', 0)
        if max_drawdown > 0:
            stability_bonus = 1 / (1 + max_drawdown * 0.5)  # 适度惩罚回撤
        
        # ============================================================
        # Final: 综合Fitness（v3：4个关键维度）
        # ============================================================
        fitness = (
            base_score                    # 绝对收益
            * holding_duration_bonus      # 持仓时间（3倍奖励！）
            * trade_frequency_penalty     # 交易频率（严厉惩罚！）
            * trend_alignment_bonus       # 趋势对齐
            * stability_bonus             # 稳定性
        )
        
        return max(fitness, 0.001)  # 确保非负
    
    # ✅ v6.0已移除：_calculate_dynamic_tax_rate()
    # 税率计算已统一封装到 Moirai._lachesis_calculate_breeding_tax()
    # 严格遵守"统一封装，严禁旁路"原则
    
    def _calculate_fitness_alphazero(self, agent: AgentV5, current_price: float = 0.0) -> float:
        """
        ⚔️ AlphaZero式极简Fitness v2 - 绝对收益 + 参与惩罚
        
        核心原则：
        ✅ 绝对收益是主要指标
        ✅ 惩罚不参与交易（资金闲置是浪费！）
        
        理由：
        - 盈利是唯一目标
        - 但"不交易"不等于"持有"
        - 不交易 = 资金闲置 = 应该被淘汰
        - 让进化鼓励"积极参与"而非"消极观望"
        
        Args:
            agent: 待评估的Agent
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            float: Fitness分数（绝对收益，不交易则惩罚）
        """
        # ✅ v6.0: 处理initial_capital为0的情况（资金池耗尽时）
        if agent.initial_capital <= 0:
            logger.warning(f"⚠️ Agent {agent.agent_id} initial_capital={agent.initial_capital}, 返回最低fitness")
            return -1.0  # 返回最低fitness，将被淘汰
        
        # 1. 计算最终资金（现金 + 未实现盈亏）
        current_liquid_capital = agent.account.private_ledger.virtual_capital if hasattr(agent, 'account') and agent.account else agent.current_capital
        unrealized_pnl = agent.calculate_unrealized_pnl(current_price) if current_price > 0 else 0.0
        effective_capital = current_liquid_capital + unrealized_pnl
        
        # 2. 计算绝对收益
        absolute_return = (effective_capital - agent.initial_capital) / agent.initial_capital
        
        # 3. ✨ 惩罚不交易（关键修改！）
        trade_count = agent.account.private_ledger.trade_count if hasattr(agent, 'account') and agent.account else 0
        
        if trade_count == 0:
            # 从未交易 = 资金闲置 = 严厉惩罚
            return -1.0  # 负分！必死无疑！
        
        # 如果有交易，直接返回绝对收益
        return absolute_return
    
    def _calculate_fitness_profit_factor(self, agent: AgentV5, current_price: float = 0.0) -> float:
        """
        ⚔️ Stage 1.1: Profit Factor主导的Fitness计算
        
        核心原则：
        ✅ Profit Factor是主要指标（盈利交易/亏损交易）
        ✅ 对策略行为高度敏感
        ✅ 不容易被单次暴利扰乱
        ✅ 更简单，更直接
        
        计算公式：
            PF = total_profit / abs(total_loss)
            
            如果 total_loss == 0:
                PF = total_profit（假设loss=1）
            
            PF > 2.0 = 优秀
            PF > 1.5 = 良好
            PF > 1.0 = 盈利
            PF < 1.0 = 亏损
        
        Args:
            agent: 待评估的Agent
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            float: Fitness分数（基于Profit Factor）
        """
        # 1. 检查初始资本
        if agent.initial_capital <= 0:
            logger.warning(f"⚠️ Agent {agent.agent_id} initial_capital={agent.initial_capital}")
            return -1.0
        
        # 2. 检查交易记录
        if not hasattr(agent, 'account') or not agent.account:
            return -1.0  # 无账户，淘汰
        
        trade_count = agent.account.private_ledger.trade_count
        if trade_count == 0:
            return -1.0  # 从未交易，淘汰
        
        # 3. 计算Profit Factor
        total_profit = 0.0
        total_loss = 0.0
        
        for trade in agent.account.private_ledger.trade_history:
            pnl = getattr(trade, 'pnl', 0.0)
            if pnl is None:
                pnl = 0.0  # ✅ 防止None值
            if pnl > 0:
                total_profit += pnl
            elif pnl < 0:
                total_loss += abs(pnl)
        
        # 4. 计算PF
        if total_loss > 0:
            profit_factor = total_profit / total_loss
        elif total_profit > 0:
            # 无亏损交易，PF = 总盈利（假设loss=1）
            profit_factor = total_profit
        else:
            # 无盈利无亏损（异常情况）
            profit_factor = 0.0
        
        # 5. 如果PF < 1.0，返回负值（加速淘汰）
        if profit_factor < 1.0:
            return profit_factor - 1.0  # 例如 PF=0.8 → fitness=-0.2
        
        # 如果PF >= 1.0，直接返回PF
        return profit_factor
    
    def _rank_agents(self, current_price: float = 0.0) -> List[Tuple[AgentV5, float]]:
        """
        ⚔️ 评估并排序Agent（Stage 1.1: 支持多种Fitness模式）
        
        评估标准（根据fitness_mode）：
        - 'profit_factor': Profit Factor主导（默认）
        - 'absolute_return': 纯绝对收益
        
        Args:
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            List[(agent, fitness)]: 按表现排序的Agent列表（从优到劣）
        """
        rankings = []
        
        for agent in self.moirai.agents:
            # ✅ Stage 1.1: 根据配置选择Fitness计算方法
            if self.fitness_mode == 'profit_factor':
                fitness = self._calculate_fitness_profit_factor(agent, current_price)
            else:  # 默认使用absolute_return
                fitness = self._calculate_fitness_alphazero(agent, current_price)
            
            rankings.append((agent, fitness))
        
        # 按fitness排序（从高到低）
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def _select_elite_weighted(self, elite_agents: List[Tuple[AgentV5, float]]) -> Optional[AgentV5]:
        """
        🦠 病毒式复制：按fitness加权选择精英
        
        规则：fitness越高，被选中概率越大（轮盘赌选择）
        
        Args:
            elite_agents: 精英Agent列表 [(agent, fitness), ...]
        
        Returns:
            被选中的精英Agent
        """
        if not elite_agents:
            return None
        
        agents = [agent for agent, _ in elite_agents]
        fitnesses = [fitness for _, fitness in elite_agents]
        
        # 如果所有fitness都<=0，均等概率选择
        if all(f <= 0 for f in fitnesses):
            return random.choice(agents)
        
        # 调整负数fitness为0
        fitnesses = [max(0, f) for f in fitnesses]
        total = sum(fitnesses)
        
        if total == 0:
            return random.choice(agents)
        
        # 轮盘赌选择
        probabilities = [f / total for f in fitnesses]
        return random.choices(agents, weights=probabilities, k=1)[0]
    
    def _viral_replicate(
        self, 
        elite: AgentV5, 
        mutation_rate: float, 
        current_price: float = 0
    ) -> AgentV5:
        """
        🦠 病毒式复制：克隆精英 + 随机变异 + 税收机制（v6.0极简版）
        
        流程：
        1. 强制父代全仓平仓（浮盈→实盈）
        2. Moirai自动计算繁殖税（保证20%资金池生死线）
        3. 收取繁殖税 → 资金池
        4. 父代保留剩余资金
        5. 克隆所有基因（Genome, StrategyParams, Lineage）
        6. 应用随机变异
        7. 子代从资金池获得配资
        8. 创建新Agent
        
        Args:
            elite: 被复制的精英Agent
            mutation_rate: 变异率（0.0-1.0）
            current_price: 当前市场价格（用于强制平仓和税收计算）
        
        Returns:
            复制的子代Agent
        """
        child_id = f"Agent_{self.moirai.next_agent_id}"
        self.moirai.next_agent_id += 1
        child_generation = elite.generation + 1
        
        # 1. 克隆Lineage
        import copy
        child_lineage = copy.deepcopy(elite.lineage)
        
        # 2. 克隆Genome并变异
        child_genome = copy.deepcopy(elite.genome)
        child_genome.mutate(mutation_rate=mutation_rate, generation=child_generation)
        
        # 3. 克隆StrategyParams并变异
        from prometheus.core.strategy_params import StrategyParams
        sp = elite.strategy_params
        child_strategy_params = StrategyParams(
            position_size_base=sp.position_size_base,
            holding_preference=sp.holding_preference,
            directional_bias=sp.directional_bias,
            stop_loss_threshold=sp.stop_loss_threshold,
            take_profit_threshold=sp.take_profit_threshold,
            trend_following_strength=sp.trend_following_strength,
            generation=child_generation,
            parent_params=(sp.to_dict(),)  # 记录父代参数
        )
        # ✅ 关键修复：mutate返回新对象，必须赋值回去！
        child_strategy_params = child_strategy_params.mutate(mutation_rate=mutation_rate)
        
        # 4. 克隆MetaGenome（如果有）
        child_meta_genome = None
        if hasattr(elite, 'meta_genome') and elite.meta_genome:
            child_meta_genome = copy.deepcopy(elite.meta_genome)
            # MetaGenome的mutate可能不需要generation参数，捕获异常
            try:
                child_meta_genome.mutate(mutation_rate=mutation_rate, generation=child_generation)
            except TypeError:
                child_meta_genome.mutate(mutation_rate=mutation_rate)
        
        # 5. 创建子代（含税收机制）
        # ✅ v6.0税收机制: 强制平仓 → 收税 → 父代保留 → 子代配资
        
        # Step 1: 强制父代全仓平仓（浮盈→实盈）
        parent_capital_before = 0.0
        if current_price > 0 and hasattr(elite, 'account') and elite.account:
            try:
                parent_capital_before = elite.account.private_ledger.virtual_capital
                parent_capital_after = self.moirai._lachesis_force_close_all(
                    agent=elite,
                    current_price=current_price,
                    reason="breeding_tax_settlement"
                )
                logger.debug(f"      🔄 强制平仓: {elite.agent_id[:8]} ${parent_capital_before:,.2f} → ${parent_capital_after:,.2f}")
            except Exception as e:
                logger.warning(f"      ⚠️ 强制平仓失败: {e}，使用当前资金")
                parent_capital_after = parent_capital_before
        else:
            # 如果没有价格或账户，使用当前资金
            parent_capital_after = elite.account.private_ledger.virtual_capital if hasattr(elite, 'account') and elite.account else elite.initial_capital
        
        # Step 2: Moirai自动计算繁殖税（v6.0极简版）
        breeding_tax = self.moirai._lachesis_calculate_breeding_tax(
            elite_agent=elite,
            current_price=current_price
        )
        
        # 检查是否允许繁殖（税额为无穷大表示资金池耗尽）
        if breeding_tax == float('inf'):
            logger.error(f"      ❌ 资金池耗尽，无法繁殖")
            return None
        
        parent_remaining = parent_capital_after - breeding_tax
        
        if parent_remaining < 0:
            logger.error(f"      ❌ {elite.agent_id} 资金不足以支付繁殖税")
            return None
        
        # Step 3: 收取繁殖税 → 资金池
        if self.capital_pool and breeding_tax > 0:
            try:
                self.capital_pool.reclaim(
                    amount=breeding_tax,
                    agent_id=elite.agent_id,
                    reason="breeding_tax"
                )
                logger.info(
                    f"      💰 [繁殖税收] {elite.agent_id[:8]} "
                    f"${parent_capital_after:,.2f} → "
                    f"税${breeding_tax:,.2f} + "
                    f"保留${parent_remaining:,.2f}"
                )
            except Exception as e:
                logger.error(f"      ❌ 税收回收失败: {e}")
                # 如果回收失败，不扣税
                parent_remaining = parent_capital_after
                breeding_tax = 0
        
        # Step 3: 父代保留剩余资金
        if hasattr(elite, 'account') and elite.account:
            elite.account.private_ledger.virtual_capital = parent_remaining
        
        # Step 4: 子代从资金池获得配资
        default_child_capital = 2000.0  # 固定配资
        
        if self.capital_pool:
            try:
                child_capital = self.capital_pool.allocate(
                    amount=default_child_capital,
                    agent_id=child_id,
                    reason="breeding_allocation"
                )
                logger.info(f"      💰 [资金池配资] 子代{child_id[:8]} ← ${child_capital:,.2f}")
            except Exception as e:
                logger.error(f"      ❌ 资金池配资失败: {e}")
                # 如果资金池耗尽，使用最小配资
                child_capital = 100.0
                logger.warning(f"      ⚠️ 资金池不足，使用最小配资: ${child_capital:,.2f}")
        else:
            # 无资金池时，使用默认值（不应该发生）
            child_capital = default_child_capital
            logger.warning(f"      ⚠️ 无资金池，使用默认配资: ${child_capital:,.2f}")
        
        # Step 5: 创建子代（使用从资金池分配的资金）
        child = AgentV5(
            agent_id=child_id,
            initial_capital=child_capital,  # ✅ 从资金池分配的资金
            lineage=child_lineage,
            genome=child_genome,
            strategy_params=child_strategy_params,
            generation=child_generation,
            meta_genome=child_meta_genome
        )
        
        logger.debug(f"   🦠 {elite.agent_id[:8]} → {child_id[:8]} (G{child_generation}, ${child_capital:,.2f})")
        self.total_births += 1
        return child
    
    def _select_parents_simple(
        self, 
        elite_agents: List[Tuple[AgentV5, float]]
    ) -> Tuple[Optional[AgentV5], Optional[AgentV5]]:
        """
        AlphaZero式极简父母选择
        
        规则：
        1. 从精英中随机选择两个
        2. 确保不是同一个Agent
        
        Args:
            elite_agents: 精英Agent列表
        
        Returns:
            (parent1, parent2): 父母Agent
        """
        if not elite_agents or len(elite_agents) < 2:
            return None, None
        
        # 随机选择两个不同的精英
        elite_only = [agent for agent, _ in elite_agents]
        parent1 = random.choice(elite_only)
        
        # 确保parent2不是parent1
        available_parents = [a for a in elite_only if a.agent_id != parent1.agent_id]
        if not available_parents:
            return parent1, parent1  # 如果只有1个精英，只能自交
        
        parent2 = random.choice(available_parents)
        return parent1, parent2
    
    def _select_parents_relaxed(
        self, 
        survivors: List[Tuple[AgentV5, float]]
    ) -> Tuple[Optional[AgentV5], Optional[AgentV5]]:
        """
        选择父母（放宽的版本 - 优先保证繁殖成功）
        
        规则：
        1. 如果存活者 < 5个，完全不检查生殖隔离
        2. 否则，尝试10次后放宽
        3. 确保不选同一个Agent
        
        Args:
            survivors: 存活的Agent列表
        
        Returns:
            (parent1, parent2): 父母Agent
        """
        if not survivors:
            return None, None
        
        # 如果存活者太少，直接选择
        if len(survivors) < 5:
            parent1 = self._select_parent_roulette(survivors)
            parent2 = self._select_parent_roulette(survivors)
            # 确保不是同一个
            attempts = 0
            while parent1 and parent2 and parent1.agent_id == parent2.agent_id and attempts < 20:
                parent2 = self._select_parent_roulette(survivors)
                attempts += 1
            return parent1, parent2
        
        # 尝试找到低亲缘度的父母
        for attempt in range(10):
            parent1 = self._select_parent_roulette(survivors)
            parent2 = self._select_parent_roulette(survivors)
            
            if not parent1 or not parent2:
                continue
            
            # 不能是同一个
            if parent1.agent_id == parent2.agent_id:
                continue
            
            # 检查亲缘度
            kinship = parent1.lineage.compute_kinship(parent2.lineage)
            
            if kinship < self.kinship_threshold:
                return parent1, parent2
        
        # 10次失败后，放宽限制，直接选择
        parent1 = self._select_parent_roulette(survivors)
        parent2 = self._select_parent_roulette(survivors)
        
        # 确保不是同一个
        attempts = 0
        while parent1 and parent2 and parent1.agent_id == parent2.agent_id and attempts < 20:
            parent2 = self._select_parent_roulette(survivors)
            attempts += 1
        
        return parent1, parent2
    
    def _select_parent_roulette(
        self, 
        survivors: List[Tuple[AgentV5, float]]
    ) -> Optional[AgentV5]:
        """
        轮盘赌选择父母
        
        适应度高的Agent有更高概率被选中
        
        Args:
            survivors: 存活的Agent列表
        
        Returns:
            AgentV5: 选中的父母
        """
        if not survivors:
            return None
        
        # 计算选择权重（基于PnL）
        weights = []
        for agent, pnl in survivors:
            # 将PnL转换为正权重
            weight = max(pnl + 1000, 1)  # 偏移确保为正
            weights.append(weight)
        
        # 归一化
        total_weight = sum(weights)
        if total_weight == 0:
            # 如果所有权重为0，均匀选择
            probabilities = [1.0 / len(survivors)] * len(survivors)
        else:
            probabilities = [w / total_weight for w in weights]
        
        # 轮盘赌选择
        idx = np.random.choice(len(survivors), p=probabilities)
        parent, _ = survivors[idx]
        
        return parent
    
    def _clotho_weave_child(
        self, 
        parent1: AgentV5, 
        parent2: AgentV5,
        mutation_rate: float = 0.1
    ) -> AgentV5:
        """
        🧵 Clotho纺织新的生命之线
        
        继承：
        1. Lineage（血统）- 混合父母血统
        2. Genome（基因组）- 交叉+变异
        3. Instinct（本能）- 遗传+随机强化/削弱
        4. MetaGenome（元基因组）- 决策风格遗传 ✨[v5.1新增]
        
        Args:
            parent1: 父母1
            parent2: 父母2
        
        Returns:
            AgentV5: 新生儿
        """
        # 生成子代ID
        child_id = f"Agent_{self.moirai.next_agent_id}"
        self.moirai.next_agent_id += 1
        
        # 1. 🧬 继承血统（Lineage）
        child_lineage = LineageVector.create_child(
            parent1.lineage,
            parent2.lineage
        )
        
        # 2. 🧬 继承基因组（Genome）
        child_genome = GenomeVector.crossover(
            parent1.genome,
            parent2.genome
        )
        
        # 计算子代代数
        child_generation = max(parent1.generation, parent2.generation) + 1
        
        # 3. 🧬 继承策略参数（StrategyParams）- AlphaZero式
        from prometheus.core.strategy_params import StrategyParams
        child_strategy_params = parent1.strategy_params.crossover(
            parent2.strategy_params,
            generation=child_generation
        )
        
        # 4. 🧬 继承元基因组（MetaGenome）- v5.1新增
        from prometheus.core.meta_genome import MetaGenomeEvolution
        
        if hasattr(parent1, 'meta_genome') and hasattr(parent2, 'meta_genome'):
            child_meta_genome = MetaGenomeEvolution.crossover_and_mutate(
                parent1.meta_genome,
                parent2.meta_genome,
                crossover_rate=0.5,
                mutation_rate=mutation_rate  # 使用动态变异率
            )
        else:
            # 向后兼容：创建新的元基因组
            from prometheus.core.meta_genome import MetaGenome
            child_meta_genome = MetaGenome.create_genesis()
        
        # 5. 创建子代Agent - AlphaZero式
        child = AgentV5(
            agent_id=child_id,
            initial_capital=parent1.initial_capital,  # 继承父母的初始资金
            lineage=child_lineage,
            genome=child_genome,
            strategy_params=child_strategy_params,  # AlphaZero式：使用StrategyParams
            generation=child_generation,
            meta_genome=child_meta_genome
        )
        # 确保血统携带family_id（优先父母的dominant family）
        if hasattr(child_lineage, "family_id"):
            child.lineage.family_id = child_lineage.family_id
        else:
            dom_family = child_lineage.get_dominant_family()
            child.lineage.family_id = dom_family
        
        # 🔧 修复：为新Agent设置初始fitness（多样性保护器需要）
        # 新生儿还没有交易记录，使用基准fitness = 1.0
        child.fitness = 1.0
        
        return child
    
    def inject_immigrants(self, 
                          count: Optional[int] = None,
                          allow_new_family: bool = True,
                          reason: Optional[str] = None) -> List[AgentV5]:
        """
        ✅ Stage 1.1: 简化Immigration机制（维护多样性）
        
        作用：防止"方向垄断崩溃"（Monopoly Lineage Collapse）
        
        Args:
            count: 注入数量（None=自动计算）
            allow_new_family: 是否允许新家族
            reason: 触发原因
        
        Returns:
            List[AgentV5]: 注入的移民
        """
        if not hasattr(self, 'immigration_enabled'):
            self.immigration_enabled = True  # ✅ Stage 1.1: 默认启用
        
        if not self.immigration_enabled:
            return []
        
        # 自动计算注入数量（10%种群）
        if count is None:
            count = max(1, len(self.moirai.agents) // 10)
        
        immigrants = []
        logger.info(f"🚁 Immigration触发: 注入{count}个移民 | 原因: {reason or '未知'}")
        
        for i in range(count):
            # ✅ Stage 1.1: 使用Moirai的创世方法创建移民
            immigrant = self.moirai._create_random_agent(
                agent_id_suffix=f"immigrant_{i}",
                generation=0  # 移民从第0代开始
            )
            immigrants.append(immigrant)
        
        # 将移民添加到种群
        self.moirai.agents.extend(immigrants)
        self.total_births += len(immigrants)
        
        logger.info(f"✅ Immigration完成: 成功注入{len(immigrants)}个移民")
        logger.info(f"   当前种群: {len(self.moirai.agents)}个Agent")
        
        return immigrants

    def maybe_inject_immigrants(self,
                                metrics: Optional['DiversityMetrics'] = None,
                                allow_new_family: bool = True,
                                force: bool = False) -> List[AgentV5]:
        """
        ✅ Stage 1.1: 简化Immigration触发逻辑
        
        触发条件（任一满足）：
        - force=True 强制
        - 种群过小（<初始种群的50%）
        - 进化代数过高（平均代数>10，易出现方向垄断）
        
        Args:
            metrics: 多样性指标（暂时不使用）
            allow_new_family: 是否允许新家族
            force: 是否强制注入
        
        Returns:
            List[AgentV5]: 实际注入的移民列表
        """
        if not hasattr(self, 'immigration_enabled'):
            self.immigration_enabled = True
        
        if not self.immigration_enabled:
            return []
        
        # 1. 强制触发
        if force:
            return self.inject_immigrants(
                count=None,
                allow_new_family=allow_new_family,
                reason="强制Immigration"
            )
        
        # 2. 检查种群大小（低于初始50%）
        current_pop = len(self.moirai.agents)
        initial_pop = getattr(self.moirai, 'initial_population_size', 50)
        
        if current_pop < initial_pop * 0.5:
            logger.warning(f"⚠️ 种群过小: {current_pop} < {initial_pop * 0.5:.0f}")
            return self.inject_immigrants(
                count=max(1, initial_pop // 10),
                allow_new_family=allow_new_family,
                reason=f"种群过小({current_pop})"
            )
        
        # 3. 检查平均代数（>10代，易方向垄断）
        if self.moirai.agents:
            generations = [agent.generation for agent in self.moirai.agents]
            avg_gen = np.mean(generations)
            
            if avg_gen > 10:
                logger.warning(f"⚠️ 平均代数过高: {avg_gen:.1f} > 10")
                return self.inject_immigrants(
                    count=max(1, current_pop // 10),
                    allow_new_family=allow_new_family,
                    reason=f"平均代数过高({avg_gen:.1f})"
                )
        
        # 不触发
        return []
    
    def get_population_stats(self) -> Dict:
        """
        获取种群统计信息
        
        Returns:
            Dict: 种群统计
        """
        if not self.moirai.agents:
            return {}
        
        # AlphaZero式：极简统计（移除熵计算）
        generations = [agent.generation for agent in self.moirai.agents]
        
        return {
            'population_size': len(self.moirai.agents),
            'avg_generation': np.mean(generations) if generations else 0,
            'max_generation': max(generations) if generations else 0,
            'total_births': self.total_births,
            'total_deaths': self.total_deaths,
        }
