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
from .instinct import Instinct
from .dual_entropy import PrometheusBloodLab
from .diversity_monitor import DiversityMonitor  # v5.2 Day 3
from .diversity_protection import DiversityProtector  # v5.2 Day 3

logger = logging.getLogger(__name__)


class EvolutionManagerV5:
    """
    v5.0进化管理器（不向后兼容）
    
    职责：
    1. 评估种群表现
    2. 选择优秀父母
    3. 繁殖新Agent（Lineage/Genome/Instinct遗传）
    4. 生殖隔离检查
    5. 监控双熵健康度
    """
    
    def __init__(self, 
                 moirai,  # Moirai实例（替代supervisor）
                 elite_ratio: float = 0.2,
                 elimination_ratio: float = 0.3,
                 num_families: int = 50):
        """
        初始化进化管理器
        
        Args:
            moirai: Moirai实例
            elite_ratio: 精英比例
            elimination_ratio: 淘汰比例
            num_families: 家族数量
        """
        self.moirai = moirai
        self.elite_ratio = elite_ratio
        self.elimination_ratio = elimination_ratio
        self.num_families = num_families
        
        # 双熵监控系统
        self.blood_lab = PrometheusBloodLab(num_families=num_families)
        
        # v5.2 Day 3: 多样性监控和保护系统
        self.diversity_monitor = DiversityMonitor()
        self.diversity_protector = DiversityProtector(
            protection_ratio=0.1,
            min_niche_size=3,
            max_protection_count=5
        )
        
        # 进化统计
        self.generation = 0
        self.total_births = 0
        self.total_deaths = 0
        
        # 生殖隔离阈值（降低以减少限制）
        self.kinship_threshold = 0.8  # 提高阈值，减少限制
        
        # v5.3：提高变异率，强化多样性
        self.base_mutation_rate = 0.2   # v5.3: 基础变异率提升到20%
        self.max_mutation_rate = 0.7    # v5.3: 最大变异率提升到70%
        self.gene_entropy_threshold = 0.3  # v5.3: 提高阈值，更积极触发高变异
        
        # v5.3：移民机制配置
        self.immigration_enabled = True  # v5.3: 启用移民机制
        self.immigration_interval = 10   # v5.3: 每10轮注入移民
        self.immigrants_per_wave = 2     # v5.3: 每次2个移民
        
        logger.info(f"🧬 EvolutionManagerV5已初始化 (v5.3)")
        logger.info(f"   精英比例: {elite_ratio:.0%}")
        logger.info(f"   淘汰比例: {elimination_ratio:.0%}")
        logger.info(f"   生殖隔离阈值: {self.kinship_threshold}")
    
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
        执行一轮进化周期（v5.0专用）
        
        流程：
        1. 双熵健康检查
        2. 评估Agent表现
        3. 淘汰表现最差的
        4. 选择优秀父母
        5. 🧵 Clotho纺织新生命（Lineage/Genome/Instinct遗传）
        6. 记录统计
        
        Args:
            current_price: 当前市场价格
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🧬 开始进化周期 - 第{self.generation + 1}代")
        logger.info(f"{'='*70}")
        
        # 1. 双熵健康检查
        health = self.blood_lab.population_checkup(self.moirai.agents)
        logger.info(f"🩺 种群健康检查:")
        logger.info(f"   血统熵: {health.lineage_entropy_normalized:.3f}")
        logger.info(f"   基因熵: {health.gene_entropy:.3f}")
        logger.info(f"   总体健康: {health.overall_health}")
        
        # 1.1 计算动态变异率（v5.1.1）
        base_mutation_rate = self._calculate_dynamic_mutation_rate(health.gene_entropy)
        
        # v5.2：引入随机噪声（±20%）
        noise_factor = random.uniform(0.8, 1.2)
        dynamic_mutation_rate = base_mutation_rate * noise_factor
        
        logger.info(f"🧬 基础变异率: {base_mutation_rate:.1%}")
        logger.info(f"🎲 噪声系数: ×{noise_factor:.2f}")
        logger.info(f"🧬 实际变异率: {dynamic_mutation_rate:.1%} (v5.2: 随机化)")
        
        # 1.2 检查多样性危机（v5.1.1）
        diversity_crisis = health.gene_entropy <= 0.1  # 修改为<=，包含边界值
        if diversity_crisis:
            logger.error(f"🚨 多样性危机！基因熵={health.gene_entropy:.3f} ≤ 0.1")
            logger.error(f"   启动紧急多样性恢复机制...")
        
        # 2. 评估Agent表现
        rankings = self._rank_agents()
        
        if not rankings:
            logger.warning("无Agent可进化")
            return
        
        total_agents = len(rankings)
        
        # 2.1 【v5.2 Day 3】多样性监控
        logger.info(f"\n🧬 多样性监控 (v5.2 Day 3):")
        diversity_metrics = self.diversity_monitor.monitor(
            agents=self.moirai.agents,
            cycle=self.generation
        )
        
        logger.info(f"   基因熵: {diversity_metrics.gene_entropy:.3f}")
        logger.info(f"   策略熵: {diversity_metrics.strategy_entropy:.3f}")
        logger.info(f"   血统熵: {diversity_metrics.lineage_entropy:.3f}")
        logger.info(f"   活跃家族: {diversity_metrics.active_families}")
        logger.info(f"   多样性得分: {diversity_metrics.diversity_score:.3f}")
        logger.info(f"   健康状态: {'✅ 健康' if diversity_metrics.is_healthy else '⚠️ 需关注'}")
        
        # 3. 识别精英、存活者和淘汰者
        elite_count = max(1, int(total_agents * self.elite_ratio))
        eliminate_count = max(1, int(total_agents * self.elimination_ratio))
        
        elite_agents = rankings[:elite_count]
        survivors = rankings[:-eliminate_count] if eliminate_count < total_agents else []
        to_eliminate = rankings[-eliminate_count:]
        
        # 3.1 【v5.2 Day 3】多样性保护
        protected_ids = set()
        if not diversity_metrics.is_healthy:
            logger.warning(f"\n🛡️ 多样性保护触发 (得分: {diversity_metrics.diversity_score:.3f}):")
            
            # 提取排序后的agent列表
            ranked_agents_only = [agent for agent, _ in rankings]
            
            # 识别需要保护的Agent
            protected_ids, protection_details = self.diversity_protector.protect_diversity(
                agents=self.moirai.agents,
                ranked_agents=ranked_agents_only,
                diversity_metrics=diversity_metrics
            )
            
            logger.info(f"   保护Agent数: {len(protected_ids)}")
            logger.info(f"   - 生态位保护: {len(protection_details['niche_protection'])}")
            logger.info(f"   - 稀有策略保护: {len(protection_details['rare_strategy_protection'])}")
            logger.info(f"   - 稀有血统保护: {len(protection_details['rare_lineage_protection'])}")
            
            # 调整淘汰列表，排除受保护的Agent
            if protected_ids:
                original_eliminate = to_eliminate
                to_eliminate = self.diversity_protector.adjust_elimination(
                    ranked_agents=ranked_agents_only,
                    protected_ids=protected_ids,
                    elimination_count=eliminate_count
                )
                
                logger.info(f"   调整淘汰列表: {len(original_eliminate)} → {len(to_eliminate)}")
                
                # 更新为元组列表格式
                to_eliminate = [(agent, 0.0) for agent in to_eliminate]
        
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
            
            # 标记死亡
            self.moirai._atropos_eliminate_agent(agent, "进化淘汰")
            self.total_deaths += 1
        
        # 5. 🧵 Clotho纺织新生命
        logger.info(f"\n🧵 Clotho开始纺织新生命...")
        
        # 5.1 【v5.2 Day 3】如果多样性极低，触发强制多样化繁殖
        forced_diverse_breeding = []
        if diversity_metrics.diversity_score < 0.4:
            logger.warning(f"\n🧬 多样性极低({diversity_metrics.diversity_score:.3f})，启动强制多样化繁殖:")
            
            # 从存活者中强制多样化配对
            survivor_agents = [agent for agent, _ in survivors]
            forced_pairs = self.diversity_protector.force_diverse_breeding(
                agents=survivor_agents,
                num_offspring=min(3, eliminate_count // 2)  # 最多3对或淘汰数的一半
            )
            forced_diverse_breeding = forced_pairs
            logger.info(f"   强制配对数: {len(forced_pairs)}")
        
        new_agents = []
        attempts = 0
        max_total_attempts = eliminate_count * 20  # 增加到20倍（更多尝试机会）
        
        # v5.2：允许种群随机波动（±10%）
        # 随机决定本轮的繁殖目标：90%-110%之间
        breeding_ratio = random.uniform(0.90, 1.10)  # 随机比例
        target_breeding_count = max(1, round(eliminate_count * breeding_ratio))  # 使用round而非int
        emergency_threshold = int(eliminate_count * 0.90)    # 90%紧急阈值
        failed_attempts_threshold = eliminate_count * 5       # 失败阈值：淘汰数的5倍
        
        logger.info(f"📊 目标繁殖数: {target_breeding_count} (比例{breeding_ratio:.1%}，允许±5%波动)")
        logger.info(f"   紧急阈值: {emergency_threshold} (低于此值触发强制繁殖)")
        
        # v5.1.1：动态相似度阈值（多样性危机时更激进）
        if diversity_crisis:
            # 多样性危机：初始阈值降低，更快放宽
            similarity_threshold = 0.85  # 起始85%（而非90%）
            logger.warning(f"   🚨 多样性危机模式：相似度阈值{similarity_threshold:.0%}，每20次尝试-5%，最低50%")
            logger.warning(f"   🆘 如果{failed_attempts_threshold}次尝试后仍不足，将跳过相似度检查强制繁殖")
        else:
            similarity_threshold = 0.90  # 正常情况90%
            logger.info(f"   相似度阈值: {similarity_threshold:.0%}")
        
        # v5.2：修改终止条件，允许达到95%即可
        while len(new_agents) < target_breeding_count and attempts < max_total_attempts:
            attempts += 1
            try:
                # 【v5.2 Day 3】优先使用强制多样化配对
                if forced_diverse_breeding and len(new_agents) < len(forced_diverse_breeding):
                    parent1, parent2 = forced_diverse_breeding[len(new_agents)]
                    logger.info(f"   🧬 使用强制多样化配对: {parent1.agent_id[:8]} + {parent2.agent_id[:8]}")
                else:
                    # 动态放宽相似度阈值（多样性危机时每20次降低5%，正常每50次）
                    if diversity_crisis and attempts > 0:
                        # 多样性危机：快速放宽（每20次尝试-5%）
                        similarity_threshold = max(0.50, 0.85 - (attempts // 20) * 0.05)
                    elif attempts > 0:
                        # 正常情况：缓慢放宽（每50次尝试-5%）
                        similarity_threshold = max(0.70, 0.90 - (attempts // 50) * 0.05)
                    
                    # 选择父母（使用放宽版本）
                    parent1, parent2 = self._select_parents_relaxed(survivors)
                
                if not parent1 or not parent2:
                    logger.debug(f"   尝试{attempts}: 无法找到父母")
                    continue
                
                # v5.1.1：多样性危机时，禁止高相似度交配
                # 但如果尝试次数过多，跳过检查强制繁殖
                skip_similarity_check = (diversity_crisis and 
                                        attempts > failed_attempts_threshold and 
                                        len(new_agents) < eliminate_count)
                
                if diversity_crisis and not skip_similarity_check:
                    # 计算基因相似度（使用.vector属性，不是.genes）
                    gene_similarity = 1 - np.mean(np.abs(
                        parent1.genome.vector - parent2.genome.vector
                    ))
                    
                    if gene_similarity > similarity_threshold:
                        if attempts % 20 == 0:  # 每20次尝试记录一次
                            logger.warning(f"   尝试{attempts}: 父母相似度({gene_similarity:.1%})超过阈值({similarity_threshold:.1%})，继续尝试...")
                        continue
                
                # 如果跳过了相似度检查，记录日志
                if skip_similarity_check and attempts == failed_attempts_threshold + 1:
                    logger.error(f"   🆘 已尝试{failed_attempts_threshold}次，强制跳过相似度检查以保证种群稳定！")
                
                # 🧵 纺织新Agent（使用动态变异率）
                child = self._clotho_weave_child(parent1, parent2, mutation_rate=dynamic_mutation_rate)
                
                new_agents.append(child)
                self.total_births += 1
                
                # 日志
                lineage_type = child.lineage.classify_purity()
                logger.info(
                    f"   👶 {child.agent_id} | "
                    f"父母: {parent1.agent_id} × {parent2.agent_id} | "
                    f"第{child.generation}代 | "
                    f"{lineage_type}"
                )
                # v5.2：显示继承的本能
                logger.debug(
                    f"      本能: [{child.instinct.describe_instinct_values()}] | "
                    f"性格: {child.instinct.describe_personality()}"
                )
                
            except Exception as e:
                logger.error(f"   ❌ 繁殖失败（尝试{attempts}）: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        # v5.2：种群波动分析
        actual_breeding_ratio = len(new_agents) / eliminate_count
        population_change = len(new_agents) - eliminate_count  # 正数=增长，负数=萎缩
        
        if len(new_agents) >= target_breeding_count:
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
        
        # 6.5 v5.3：移民机制（每N轮注入新基因）
        if (self.immigration_enabled and 
            self.generation > 0 and 
            self.generation % self.immigration_interval == 0):
            logger.info(f"\n🛬 移民机制触发（第{self.generation}代，间隔{self.immigration_interval}）")
            immigrants = self._inject_immigrants()
            logger.info(f"   移民到达: {len(immigrants)}个全新基因的Agent")
        
        # 7. 记录统计
        self.generation += 1
        
        logger.info(f"\n🧬 进化周期完成:")
        logger.info(f"   新生: {len(new_agents)}个")
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
        
        # 6.4 持仓时间过少（总是空仓观望）
        if hasattr(agent, 'cycles_with_position') and cycles_survived > 0:
            position_time_ratio = agent.cycles_with_position / cycles_survived
            if position_time_ratio < 0.2:  # 80%时间空仓
                negativity_penalty *= 0.7
            elif position_time_ratio < 0.4:
                negativity_penalty *= 0.9
        
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
    
    def _rank_agents(self) -> List[Tuple[AgentV5, float]]:
        """
        评估并排序Agent（v5.2: 使用fitness v2）
        
        评估标准：综合fitness（包含生存、盈利、活跃度等）
        
        Returns:
            List[(agent, fitness)]: 按表现排序的Agent列表（从优到劣）
        """
        rankings = []
        
        # 计算total_cycles（用于归一化）
        total_cycles = max(
            getattr(agent, 'cycles_survived', 1) 
            for agent in self.moirai.agents
        ) if self.moirai.agents else 1
        
        for agent in self.moirai.agents:
            # 使用fitness v2计算
            fitness = self._calculate_fitness_v2(agent, total_cycles)
            rankings.append((agent, fitness))
        
        # 按fitness排序（从高到低）
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
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
        
        # 3. 🧬 继承本能（Instinct）
        child_instinct = Instinct.inherit_from_parents(
            parent1.instinct,
            parent2.instinct,
            child_generation
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
        
        # 5. 创建子代Agent
        child = AgentV5(
            agent_id=child_id,
            initial_capital=parent1.initial_capital,  # 继承父母的初始资金
            lineage=child_lineage,
            genome=child_genome,
            instinct=child_instinct,
            generation=child_generation,
            meta_genome=child_meta_genome  # v5.1新增
        )
        
        # 🔧 修复：为新Agent设置初始fitness（多样性保护器需要）
        # 新生儿还没有交易记录，使用基准fitness = 1.0
        child.fitness = 1.0
        
        return child
    
    def _inject_immigrants(self) -> List[AgentV5]:
        """
        v5.3：注入移民Agent
        
        移民机制：定期注入全新基因的Agent，防止基因池枯竭
        
        Returns:
            List[AgentV5]: 新创建的移民Agent列表
        """
        immigrants = []
        
        try:
            for i in range(self.immigrants_per_wave):
                # 使用Moirai创建全新的Agent（允许新家族）
                immigrant = self.moirai._clotho_create_single_agent(
                    allow_new_family=True  # 关键：允许创建新家族
                )
                
                # 初始化fitness
                immigrant.fitness = 1.0  # 给予基础适应度
                
                immigrants.append(immigrant)
                self.moirai.agents.append(immigrant)
                
                logger.info(f"   🛬 移民{i+1}: {immigrant.agent_id[:12]} "
                          f"(家族: {immigrant.lineage.family_id}, 新基因)")
            
            self.total_births += len(immigrants)
            
        except Exception as e:
            logger.error(f"❌ 移民注入失败: {e}")
        
        return immigrants
    
    def get_population_stats(self) -> Dict:
        """
        获取种群统计信息
        
        Returns:
            Dict: 种群统计
        """
        if not self.moirai.agents:
            return {}
        
        # 血统多样性
        lineages = [agent.lineage for agent in self.moirai.agents]
        lineage_entropy = self.blood_lab.calculate_lineage_entropy(lineages)
        
        # 基因多样性
        genomes = [agent.genome for agent in self.moirai.agents]
        gene_entropy = self.blood_lab.calculate_gene_entropy(genomes)
        
        # 代数分布
        generations = [agent.generation for agent in self.moirai.agents]
        
        return {
            'population_size': len(self.moirai.agents),
            'lineage_entropy': lineage_entropy,
            'gene_entropy': gene_entropy,
            'avg_generation': np.mean(generations),
            'max_generation': max(generations),
            'total_births': self.total_births,
            'total_deaths': self.total_deaths,
        }
