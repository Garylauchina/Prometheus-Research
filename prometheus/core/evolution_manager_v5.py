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

from .agent_v5 import AgentV5
from .lineage import LineageVector
from .genome import GenomeVector
from .instinct import Instinct
from .dual_entropy import PrometheusBloodLab

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
        
        # 进化统计
        self.generation = 0
        self.total_births = 0
        self.total_deaths = 0
        
        # 生殖隔离阈值（降低以减少限制）
        self.kinship_threshold = 0.8  # 提高阈值，减少限制
        
        logger.info(f"🧬 EvolutionManagerV5已初始化")
        logger.info(f"   精英比例: {elite_ratio:.0%}")
        logger.info(f"   淘汰比例: {elimination_ratio:.0%}")
        logger.info(f"   生殖隔离阈值: {self.kinship_threshold}")
    
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
        
        # 2. 评估Agent表现
        rankings = self._rank_agents()
        
        if not rankings:
            logger.warning("无Agent可进化")
            return
        
        total_agents = len(rankings)
        
        # 3. 识别精英、存活者和淘汰者
        elite_count = max(1, int(total_agents * self.elite_ratio))
        eliminate_count = max(1, int(total_agents * self.elimination_ratio))
        
        elite_agents = rankings[:elite_count]
        survivors = rankings[:-eliminate_count] if eliminate_count < total_agents else []
        to_eliminate = rankings[-eliminate_count:]
        
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
        
        new_agents = []
        attempts = 0
        max_total_attempts = eliminate_count * 10  # 增加到10倍
        
        while len(new_agents) < eliminate_count and attempts < max_total_attempts:
            attempts += 1
            try:
                # 选择父母（使用放宽版本）
                parent1, parent2 = self._select_parents_relaxed(survivors)
                
                if not parent1 or not parent2:
                    logger.debug(f"   尝试{attempts}: 无法找到父母")
                    continue
                
                # 🧵 纺织新Agent
                child = self._clotho_weave_child(parent1, parent2)
                
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
                
            except Exception as e:
                logger.error(f"   ❌ 繁殖失败（尝试{attempts}）: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        if len(new_agents) < eliminate_count:
            logger.warning(
                f"   ⚠️ 警告：只成功繁殖{len(new_agents)}个，"
                f"少于淘汰数{eliminate_count}"
            )
        
        # 6. 添加新Agent到Moirai
        self.moirai.agents.extend(new_agents)
        
        # 7. 记录统计
        self.generation += 1
        
        logger.info(f"\n🧬 进化周期完成:")
        logger.info(f"   新生: {len(new_agents)}个")
        logger.info(f"   当前种群: {len(self.moirai.agents)}个")
        logger.info(f"   累计出生: {self.total_births}")
        logger.info(f"   累计死亡: {self.total_deaths}")
        logger.info(f"{'='*70}")
    
    def _rank_agents(self) -> List[Tuple[AgentV5, float]]:
        """
        评估并排序Agent（v5.0专用）
        
        评估标准：
        1. 总盈亏（total_pnl）
        2. 胜率（win_rate）
        3. 资金比率（capital_ratio）
        
        Returns:
            List[(agent, pnl)]: 按表现排序的Agent列表（从优到劣）
        """
        rankings = []
        
        for agent in self.moirai.agents:
            # 计算综合评分
            capital_ratio = agent.current_capital / agent.initial_capital
            win_rate = agent.win_count / agent.trade_count if agent.trade_count > 0 else 0
            
            # 综合评分
            score = (
                agent.total_pnl * 0.5 +          # 总盈亏（权重50%）
                capital_ratio * 5000 * 0.3 +     # 资金比率（权重30%）
                win_rate * 1000 * 0.2            # 胜率（权重20%）
            )
            
            rankings.append((agent, agent.total_pnl))
        
        # 按总盈亏排序（从高到低）
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
        parent2: AgentV5
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
                mutation_rate=0.1
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
        
        return child
    
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
