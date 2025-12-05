"""
多样性保护机制 (Diversity Protection) - Prometheus v5.2 Day 3

核心功能：
1. 当多样性过低时自动触发保护机制
2. 保护少数策略（Niche保护）
3. 强制多样化繁殖
4. 引入新基因

设计哲学：
- "防止单一策略统治"
- "保护稀有但有价值的策略"
- "维持生态平衡"
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
import logging
import random

logger = logging.getLogger(__name__)


class DiversityProtector:
    """
    多样性保护器
    
    职责：
    1. 识别需要保护的少数群体
    2. 调整淘汰/繁殖策略
    3. 强制引入多样性
    """
    
    def __init__(self, 
                 protection_ratio: float = 0.1,
                 min_niche_size: int = 3,
                 max_protection_count: int = 5):
        """
        初始化多样性保护器
        
        Args:
            protection_ratio: 保护比例（种群的百分比）
            min_niche_size: 生态位最小规模
            max_protection_count: 最多保护的Agent数量
        """
        self.protection_ratio = protection_ratio
        self.min_niche_size = min_niche_size
        self.max_protection_count = max_protection_count
        
        # 统计
        self.total_protections = 0
        self.protection_history: List[Dict] = []
        
        logger.info(f"多样性保护器已初始化 | 保护比例: {protection_ratio:.1%}")
    
    # ==================== 核心保护方法 ====================
    
    def protect_diversity(self, 
                         agents: List,
                         ranked_agents: List,
                         diversity_metrics) -> Tuple[Set[str], Dict]:
        """
        识别需要保护的Agent
        
        Args:
            agents: 所有Agent列表
            ranked_agents: 按fitness排序的Agent列表（从高到低）
            diversity_metrics: 当前多样性指标
        
        Returns:
            Tuple[Set[str], Dict]:
                - 需要保护的Agent ID集合
                - 保护详情字典
        """
        protected_ids = set()
        protection_details = {
            'niche_protection': [],
            'rare_strategy_protection': [],
            'rare_lineage_protection': [],
            'total_protected': 0
        }
        
        if not agents or not ranked_agents:
            return protected_ids, protection_details
        
        # 1. 识别生态位（策略聚类）
        niches = self._identify_niches(agents)
        
        # 2. 保护小型生态位
        niche_protected = self._protect_small_niches(niches, ranked_agents)
        protected_ids.update(niche_protected)
        protection_details['niche_protection'] = list(niche_protected)
        
        # 3. 保护稀有策略
        rare_strategy_protected = self._protect_rare_strategies(agents, ranked_agents)
        protected_ids.update(rare_strategy_protected)
        protection_details['rare_strategy_protection'] = list(rare_strategy_protected)
        
        # 4. 保护稀有血统
        rare_lineage_protected = self._protect_rare_lineages(agents, ranked_agents)
        protected_ids.update(rare_lineage_protected)
        protection_details['rare_lineage_protection'] = list(rare_lineage_protected)
        
        # 5. 限制保护数量
        if len(protected_ids) > self.max_protection_count:
            # 优先保护fitness较高的
            protected_list = list(protected_ids)
            fitness_scores = {
                aid: next((a.fitness for a in ranked_agents if a.agent_id == aid), 0)
                for aid in protected_list
            }
            sorted_protected = sorted(protected_list, key=lambda x: fitness_scores[x], reverse=True)
            protected_ids = set(sorted_protected[:self.max_protection_count])
        
        protection_details['total_protected'] = len(protected_ids)
        
        if protected_ids:
            self.total_protections += len(protected_ids)
            self.protection_history.append(protection_details)
            logger.info(f"🛡️ 保护了 {len(protected_ids)} 个Agent | "
                       f"生态位: {len(protection_details['niche_protection'])}, "
                       f"稀有策略: {len(protection_details['rare_strategy_protection'])}, "
                       f"稀有血统: {len(protection_details['rare_lineage_protection'])}")
        
        return protected_ids, protection_details
    
    # ==================== 生态位识别 ====================
    
    def _identify_niches(self, agents: List) -> List[List]:
        """
        识别策略生态位（简单聚类）
        
        基于fear_of_death和risk_appetite进行聚类
        
        Returns:
            List[List]: 每个生态位包含的Agent列表
        """
        if not agents:
            return []
        
        try:
            # 提取策略特征
            features = np.array([
                [agent.instinct.fear_of_death, agent.instinct.risk_appetite]
                for agent in agents
            ])
            
            # 简单的网格聚类（5x5网格）
            fear_bins = np.linspace(0, 2, 6)  # [0, 0.4, 0.8, 1.2, 1.6, 2.0]
            risk_bins = np.linspace(0, 1, 6)  # [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            
            niches = {}
            for i, agent in enumerate(agents):
                fear_idx = np.digitize(features[i, 0], fear_bins) - 1
                risk_idx = np.digitize(features[i, 1], risk_bins) - 1
                niche_key = (fear_idx, risk_idx)
                
                if niche_key not in niches:
                    niches[niche_key] = []
                niches[niche_key].append(agent)
            
            return list(niches.values())
        
        except Exception as e:
            logger.error(f"识别生态位失败: {e}")
            return []
    
    def _protect_small_niches(self, niches: List[List], ranked_agents: List) -> Set[str]:
        """
        保护小型生态位
        
        Args:
            niches: 生态位列表
            ranked_agents: 排序后的Agent
        
        Returns:
            Set[str]: 需要保护的Agent ID
        """
        protected = set()
        
        for niche in niches:
            if len(niche) == 0:
                continue
            
            # 小型生态位：数量 <= min_niche_size
            if len(niche) <= self.min_niche_size:
                # 保护该生态位中fitness最高的Agent
                niche_sorted = sorted(niche, key=lambda a: a.fitness, reverse=True)
                protected.add(niche_sorted[0].agent_id)
                
                logger.debug(f"保护小型生态位 | 规模: {len(niche)} | Agent: {niche_sorted[0].agent_id}")
        
        return protected
    
    # ==================== 稀有策略保护 ====================
    
    def _protect_rare_strategies(self, agents: List, ranked_agents: List) -> Set[str]:
        """
        保护稀有策略
        
        稀有策略定义：
        - fear_of_death极端值（<0.3 or >1.7）
        - risk_appetite极端值（<0.2 or >0.8）
        """
        protected = set()
        
        if not agents:
            return protected
        
        try:
            # 提取策略特征
            fears = [a.instinct.fear_of_death for a in agents]
            risks = [a.instinct.risk_appetite for a in agents]
            
            # 计算分位数
            fear_low = np.percentile(fears, 10)
            fear_high = np.percentile(fears, 90)
            risk_low = np.percentile(risks, 10)
            risk_high = np.percentile(risks, 90)
            
            # 识别稀有策略Agent
            rare_agents = []
            for agent in agents:
                is_rare = (
                    agent.instinct.fear_of_death < fear_low or
                    agent.instinct.fear_of_death > fear_high or
                    agent.instinct.risk_appetite < risk_low or
                    agent.instinct.risk_appetite > risk_high
                )
                
                if is_rare:
                    rare_agents.append(agent)
            
            # 保护fitness较高的稀有策略Agent
            if rare_agents:
                rare_sorted = sorted(rare_agents, key=lambda a: a.fitness, reverse=True)
                # 保护前20%或至少1个
                protect_count = max(1, int(len(rare_agents) * 0.2))
                for agent in rare_sorted[:protect_count]:
                    protected.add(agent.agent_id)
                    logger.debug(f"保护稀有策略 | Agent: {agent.agent_id} | "
                               f"fear={agent.instinct.fear_of_death:.2f}, "
                               f"risk={agent.instinct.risk_appetite:.2f}")
        
        except Exception as e:
            logger.error(f"保护稀有策略失败: {e}")
        
        return protected
    
    # ==================== 稀有血统保护 ====================
    
    def _protect_rare_lineages(self, agents: List, ranked_agents: List) -> Set[str]:
        """
        保护稀有血统（v5.3增强版）
        
        v5.3改进：
        - 稀有家族阈值：5% → 10%（更多家族被保护）
        - 保护数量：TOP 1 → TOP 2（每个小家族保护2个）
        """
        protected = set()
        
        if not agents:
            return protected
        
        try:
            # 统计每个家族的Agent数量
            family_counts = {}
            family_agents = {}
            
            for agent in agents:
                dominant_family = agent.lineage.get_dominant_family()
                family_counts[dominant_family] = family_counts.get(dominant_family, 0) + 1
                
                if dominant_family not in family_agents:
                    family_agents[dominant_family] = []
                family_agents[dominant_family].append(agent)
            
            # v5.3：识别稀有家族（数量 < 10%，提高保护范围）
            threshold = len(agents) * 0.10  # v5.3: 从5%提高到10%
            rare_families = [fid for fid, count in family_counts.items() if count < threshold]
            
            # v5.3：保护稀有家族中fitness最高的2个Agent（而不是1个）
            for family_id in rare_families:
                agents_in_family = family_agents[family_id]
                # 按fitness排序
                agents_in_family_sorted = sorted(agents_in_family, 
                                                key=lambda a: a.fitness, 
                                                reverse=True)
                
                # v5.3：保护TOP 2
                for i, agent in enumerate(agents_in_family_sorted[:2]):  # v5.3: 保护2个
                    protected.add(agent.agent_id)
                    
                    logger.debug(f"保护稀有血统#{i+1} | 家族: {family_id} | "
                               f"数量: {family_counts[family_id]} | "
                               f"Agent: {agent.agent_id[:8]}")
        
        except Exception as e:
            logger.error(f"保护稀有血统失败: {e}")
        
        return protected
    
    # ==================== 强制多样化繁殖 ====================
    
    def force_diverse_breeding(self, 
                              agents: List,
                              num_offspring: int = 5,
                              force_cross_family: bool = True) -> List[Tuple]:  # v5.3: 新增参数
        """
        强制多样化繁殖（v5.3增强版）
        
        v5.3新增：
        - 优先跨家族交配
        - 保护小家族
        
        Args:
            agents: Agent列表
            num_offspring: 需要产生的后代数量
            force_cross_family: v5.3: 是否强制跨家族交配
        
        Returns:
            List[Tuple]: 配对列表 [(parent1, parent2), ...]
        """
        if len(agents) < 2:
            return []
        
        try:
            # v5.3：按家族分组
            families = {}
            for agent in agents:
                family_id = agent.lineage.family_id
                if family_id not in families:
                    families[family_id] = []
                families[family_id].append(agent)
            
            logger.info(f"🧬 v5.3强制多样化繁殖 | {len(families)}个家族参与")
            
            # 提取基因向量
            gene_vectors = np.array([agent.genome.vector for agent in agents])
            
            # 计算所有配对的基因距离和家族关系
            pairs = []
            for i in range(len(agents)):
                for j in range(i+1, len(agents)):
                    distance = np.linalg.norm(gene_vectors[i] - gene_vectors[j])
                    same_family = (agents[i].lineage.family_id == agents[j].lineage.family_id)
                    
                    # v5.3：跨家族配对获得额外权重
                    if force_cross_family and not same_family:
                        distance *= 1.5  # 跨家族配对距离×1.5
                    elif force_cross_family and same_family:
                        distance *= 0.5  # 同家族配对距离×0.5（降低优先级）
                    
                    pairs.append((distance, agents[i], agents[j], same_family))
            
            # 按距离排序（从大到小）
            pairs.sort(key=lambda x: x[0], reverse=True)
            
            # 选择距离最远的配对
            selected_pairs = []
            used_agents = set()
            cross_family_count = 0
            
            for distance, p1, p2, same_family in pairs:
                if len(selected_pairs) >= num_offspring:
                    break
                
                # 避免重复使用Agent
                if p1.agent_id not in used_agents and p2.agent_id not in used_agents:
                    selected_pairs.append((p1, p2))
                    used_agents.add(p1.agent_id)
                    used_agents.add(p2.agent_id)
                    
                    if not same_family:
                        cross_family_count += 1
                    
                    family_info = "跨家族" if not same_family else "同家族"
                    logger.debug(f"多样化繁殖配对 | {p1.agent_id[:8]} + {p2.agent_id[:8]} "
                               f"| {family_info} | 距离: {distance:.3f}")
            
            logger.info(f"🧬 强制多样化繁殖 | 配对数: {len(selected_pairs)} | "
                       f"跨家族: {cross_family_count}/{len(selected_pairs)}")
            
            return selected_pairs
        
        except Exception as e:
            logger.error(f"强制多样化繁殖失败: {e}")
            return []
    
    # ==================== 引入新基因 ====================
    
    def inject_new_genes(self,
                        agents: List,
                        mutation_rate: float = 0.3) -> List:
        """
        向低多样性Agent注入新基因
        
        选择基因相似度高的Agent，增加其变异率
        
        Args:
            agents: Agent列表
            mutation_rate: 额外变异率
        
        Returns:
            List: 需要注入新基因的Agent ID列表
        """
        if len(agents) < 2:
            return []
        
        try:
            # 提取基因向量
            gene_vectors = np.array([agent.genome.vector for agent in agents])
            
            # 计算每个Agent到所有其他Agent的平均距离
            avg_distances = []
            for i in range(len(agents)):
                distances = []
                for j in range(len(agents)):
                    if i != j:
                        dist = np.linalg.norm(gene_vectors[i] - gene_vectors[j])
                        distances.append(dist)
                avg_dist = np.mean(distances)
                avg_distances.append((avg_dist, agents[i]))
            
            # 选择平均距离较小的Agent（基因相似度高）
            avg_distances.sort(key=lambda x: x[0])
            
            # 选择前20%注入新基因
            inject_count = max(1, int(len(agents) * 0.2))
            selected_agents = [agent.agent_id for _, agent in avg_distances[:inject_count]]
            
            logger.info(f"💉 注入新基因 | 目标Agent数: {len(selected_agents)}")
            
            return selected_agents
        
        except Exception as e:
            logger.error(f"注入新基因失败: {e}")
            return []
    
    # ==================== 调整淘汰策略 ====================
    
    def adjust_elimination(self,
                          ranked_agents: List,
                          protected_ids: Set[str],
                          elimination_count: int) -> List:
        """
        调整淘汰列表，排除受保护的Agent
        
        Args:
            ranked_agents: 按fitness排序的Agent（从高到低）
            protected_ids: 受保护的Agent ID集合
            elimination_count: 原计划淘汰数量
        
        Returns:
            List: 实际应该淘汰的Agent列表
        """
        # 从fitness最低的开始，跳过受保护的
        to_eliminate = []
        
        for agent in reversed(ranked_agents):
            if len(to_eliminate) >= elimination_count:
                break
            
            if agent.agent_id not in protected_ids:
                to_eliminate.append(agent)
        
        # 如果因为保护而淘汰数量不足，从更高fitness的Agent中选择
        if len(to_eliminate) < elimination_count:
            logger.warning(f"⚠️ 保护导致淘汰数量不足 | "
                          f"计划: {elimination_count}, 实际: {len(to_eliminate)}")
            
            # 从未保护的Agent中补充
            for agent in reversed(ranked_agents):
                if len(to_eliminate) >= elimination_count:
                    break
                if agent not in to_eliminate and agent.agent_id not in protected_ids:
                    to_eliminate.append(agent)
        
        return to_eliminate
    
    # ==================== 统计报告 ====================
    
    def get_protection_stats(self) -> Dict:
        """获取保护统计"""
        return {
            'total_protections': self.total_protections,
            'protection_events': len(self.protection_history),
            'recent_protections': self.protection_history[-5:] if self.protection_history else []
        }
    
    def generate_report(self) -> str:
        """生成保护报告"""
        stats = self.get_protection_stats()
        
        report = f"""
{'='*80}
🛡️ 多样性保护报告
{'='*80}

📊 总体统计
{'─'*80}
  • 累计保护次数: {stats['total_protections']}
  • 保护事件数: {stats['protection_events']}

📋 最近保护事件
{'─'*80}
"""
        
        for i, event in enumerate(stats['recent_protections'][-3:], 1):
            report += f"  事件 {i}:\n"
            report += f"    • 生态位保护: {len(event.get('niche_protection', []))}\n"
            report += f"    • 稀有策略保护: {len(event.get('rare_strategy_protection', []))}\n"
            report += f"    • 稀有血统保护: {len(event.get('rare_lineage_protection', []))}\n"
            report += f"    • 总计: {event.get('total_protected', 0)}\n\n"
        
        report += "="*80 + "\n"
        
        return report

