"""
基因库系统 - Prometheus v4.0
保存和管理优秀Agent的基因和性格
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import numpy as np
import json

logger = logging.getLogger(__name__)


@dataclass
class GeneRecord:
    """基因记录"""
    gene_id: str
    agent_id: str
    gene: Dict
    personality: Dict
    
    # 表现指标
    total_trades: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    survival_days: int
    
    # 适应场景
    best_market_regime: str  # bull/bear/ranging/volatile
    avg_market_volatility: float
    适应度评分: float
    
    # 元数据
    birth_time: datetime
    death_time: datetime
    death_reason: str
    generation: int  # 第几代
    parent_genes: List[str]  # 父代基因ID
    
    # 使用统计
    times_used: int = 0  # 被繁殖使用次数
    last_used: Optional[datetime] = None


class GenePool:
    """
    基因库 - 保存和管理优秀基因
    
    职责：
    1. 保存表现优秀的Agent基因
    2. 根据市场环境推荐合适的基因
    3. 管理基因多样性
    4. 支持基因繁殖和变异
    """
    
    def __init__(self, max_genes: int = 1000):
        """
        初始化基因库
        
        Args:
            max_genes: 最大基因数量
        """
        self.max_genes = max_genes
        self.genes: Dict[str, GeneRecord] = {}
        self.generation_counter = 0
        
        logger.info(f"基因库已初始化，最大容量: {max_genes}")
    
    def add_gene(self,
                 agent_id: str,
                 gene: Dict,
                 personality: Dict,
                 performance_metrics: Dict,
                 market_context: Dict) -> str:
        """
        添加基因到基因库
        
        Args:
            agent_id: Agent ID
            gene: 基因数据
            personality: 性格数据
            performance_metrics: 表现指标
            market_context: 市场环境
            
        Returns:
            str: 基因ID
        """
        # 检查是否值得保存（过滤标准）
        if not self._is_worth_saving(performance_metrics):
            logger.debug(f"Agent {agent_id} 表现不足以进入基因库")
            return None
        
        # 生成基因ID
        gene_id = f"GENE-{len(self.genes)+1:06d}"
        
        # 创建基因记录
        record = GeneRecord(
            gene_id=gene_id,
            agent_id=agent_id,
            gene=gene.copy(),
            personality=personality.copy(),
            total_trades=performance_metrics.get('total_trades', 0),
            win_rate=performance_metrics.get('win_rate', 0),
            total_return=performance_metrics.get('total_return', 0),
            sharpe_ratio=performance_metrics.get('sharpe_ratio', 0),
            max_drawdown=performance_metrics.get('max_drawdown', 0),
            survival_days=performance_metrics.get('survival_days', 0),
            best_market_regime=market_context.get('regime', 'unknown'),
            avg_market_volatility=market_context.get('volatility', 0),
            适应度评分=self._calculate_fitness(performance_metrics),
            birth_time=performance_metrics.get('birth_time'),
            death_time=performance_metrics.get('death_time'),
            death_reason=performance_metrics.get('death_reason', 'unknown'),
            generation=performance_metrics.get('generation', 0),
            parent_genes=performance_metrics.get('parent_genes', [])
        )
        
        # 添加到基因库
        self.genes[gene_id] = record
        
        # 检查容量，必要时清理
        if len(self.genes) > self.max_genes:
            self._cleanup_genes()
        
        logger.info(f"基因 {gene_id} 已保存，适应度: {record.适应度评分:.2f}, 适应场景: {record.best_market_regime}")
        return gene_id
    
    def _is_worth_saving(self, metrics: Dict) -> bool:
        """
        判断基因是否值得保存
        
        Args:
            metrics: 表现指标
            
        Returns:
            bool: 是否值得保存
        """
        # 保存标准：
        # 1. 胜率 > 55%
        # 2. 总收益 > 10%
        # 3. 存活时间 > 7天
        # 4. 至少交易过10次
        
        return (
            metrics.get('win_rate', 0) > 0.55 and
            metrics.get('total_return', 0) > 0.10 and
            metrics.get('survival_days', 0) > 7 and
            metrics.get('total_trades', 0) > 10
        )
    
    def _calculate_fitness(self, metrics: Dict) -> float:
        """
        计算适应度评分
        
        Args:
            metrics: 表现指标
            
        Returns:
            float: 适应度评分 (0-1)
        """
        # 综合评分
        win_rate_score = metrics.get('win_rate', 0)
        return_score = min(metrics.get('total_return', 0) / 0.5, 1.0)  # 50%收益=满分
        sharpe_score = min(metrics.get('sharpe_ratio', 0) / 2.0, 1.0)  # Sharpe 2.0=满分
        survival_score = min(metrics.get('survival_days', 0) / 90.0, 1.0)  # 90天=满分
        
        # 加权平均
        fitness = (
            win_rate_score * 0.3 +
            return_score * 0.3 +
            sharpe_score * 0.2 +
            survival_score * 0.2
        )
        
        return fitness
    
    def get_best_genes(self,
                       market_regime: str,
                       count: int = 10) -> List[GeneRecord]:
        """
        获取最适合当前市场的基因
        
        Args:
            market_regime: 当前市场状态
            count: 返回数量
            
        Returns:
            List[GeneRecord]: 基因记录列表
        """
        # 筛选适合当前市场的基因
        suitable_genes = [
            record for record in self.genes.values()
            if record.best_market_regime == market_regime or record.best_market_regime == 'all'
        ]
        
        if not suitable_genes:
            # 如果没有匹配的，返回全局最优
            suitable_genes = list(self.genes.values())
        
        # 按适应度排序
        suitable_genes.sort(key=lambda x: x.适应度评分, reverse=True)
        
        return suitable_genes[:count]
    
    def breed_new_gene(self,
                       parent1_id: Optional[str] = None,
                       parent2_id: Optional[str] = None,
                       market_regime: str = 'unknown',
                       mutation_rate: float = 0.1) -> Tuple[Dict, Dict]:
        """
        繁殖新基因
        
        Args:
            parent1_id: 父代1基因ID（None则随机选择）
            parent2_id: 父代2基因ID（None则随机选择）
            market_regime: 当前市场状态
            mutation_rate: 突变率
            
        Returns:
            Tuple[Dict, Dict]: (新基因, 新性格)
        """
        # 选择父代
        if not parent1_id or parent1_id not in self.genes:
            best_genes = self.get_best_genes(market_regime, 10)
            parent1 = np.random.choice(best_genes) if best_genes else None
        else:
            parent1 = self.genes[parent1_id]
        
        if not parent2_id or parent2_id not in self.genes:
            best_genes = self.get_best_genes(market_regime, 10)
            parent2 = np.random.choice(best_genes) if best_genes else None
        else:
            parent2 = self.genes[parent2_id]
        
        # 如果基因库为空，返回随机基因
        if not parent1 or not parent2:
            logger.warning("基因库为空，生成随机基因")
            return None, None
        
        # 基因交叉
        new_gene = self._crossover_genes(parent1.gene, parent2.gene, mutation_rate)
        new_personality = self._crossover_personality(parent1.personality, parent2.personality, mutation_rate)
        
        # 更新使用统计
        parent1.times_used += 1
        parent1.last_used = datetime.now()
        parent2.times_used += 1
        parent2.last_used = datetime.now()
        
        self.generation_counter += 1
        
        logger.info(f"繁殖新基因 (第{self.generation_counter}代)，父代: {parent1.gene_id}, {parent2.gene_id}")
        
        return new_gene, new_personality
    
    def _crossover_genes(self, gene1: Dict, gene2: Dict, mutation_rate: float) -> Dict:
        """
        基因交叉（遗传+变异）
        
        Args:
            gene1: 父代基因1
            gene2: 父代基因2
            mutation_rate: 突变率
            
        Returns:
            Dict: 新基因
        """
        new_gene = {}
        
        for key in gene1.keys():
            # 50%概率继承父代1，50%继承父代2
            if np.random.random() < 0.5:
                value = gene1[key]
            else:
                value = gene2[key]
            
            # 突变
            if np.random.random() < mutation_rate:
                if isinstance(value, (int, float)):
                    # 数值变异：±20%
                    value *= np.random.uniform(0.8, 1.2)
                elif isinstance(value, dict):
                    # 字典递归变异
                    value = self._mutate_dict(value, mutation_rate)
            
            new_gene[key] = value
        
        return new_gene
    
    def _crossover_personality(self, p1: Dict, p2: Dict, mutation_rate: float) -> Dict:
        """
        性格交叉（遗传+变异）
        
        Args:
            p1: 父代性格1
            p2: 父代性格2
            mutation_rate: 突变率
            
        Returns:
            Dict: 新性格
        """
        new_personality = {}
        
        for key in p1.keys():
            # 混合继承（平均值+随机偏移）
            value = (p1[key] + p2[key]) / 2
            
            # 突变
            if np.random.random() < mutation_rate:
                value += np.random.uniform(-0.2, 0.2)
                value = np.clip(value, 0, 1)
            
            new_personality[key] = value
        
        return new_personality
    
    def _mutate_dict(self, d: Dict, mutation_rate: float) -> Dict:
        """递归变异字典"""
        result = {}
        for k, v in d.items():
            if isinstance(v, (int, float)):
                if np.random.random() < mutation_rate:
                    v *= np.random.uniform(0.8, 1.2)
            elif isinstance(v, dict):
                v = self._mutate_dict(v, mutation_rate)
            result[k] = v
        return result
    
    def _cleanup_genes(self):
        """清理基因库，移除最差的基因"""
        # 按适应度排序
        sorted_genes = sorted(self.genes.values(), key=lambda x: x.适应度评分)
        
        # 移除最差的10%
        remove_count = max(1, len(self.genes) // 10)
        for i in range(remove_count):
            gene_id = sorted_genes[i].gene_id
            del self.genes[gene_id]
            logger.debug(f"清理基因 {gene_id}")
    
    def calculate_diversity(self) -> float:
        """
        计算基因库的多样性
        
        Returns:
            float: 多样性分数 (0-1)
        """
        if len(self.genes) < 2:
            return 0.0
        
        # 计算所有基因对之间的平均差异
        from itertools import combinations
        
        gene_records = list(self.genes.values())
        differences = []
        
        for r1, r2 in combinations(gene_records, 2):
            # 简化：只比较适应度和市场适应性
            diff = abs(r1.适应度评分 - r2.适应度评分)
            regime_diff = 0.2 if r1.best_market_regime != r2.best_market_regime else 0
            differences.append(diff + regime_diff)
        
        diversity = np.mean(differences) if differences else 0
        return min(diversity, 1.0)
    
    def export_to_file(self, filepath: str):
        """导出基因库到文件"""
        data = {
            gene_id: asdict(record)
            for gene_id, record in self.genes.items()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"基因库已导出到 {filepath}")
    
    def import_from_file(self, filepath: str):
        """从文件导入基因库"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for gene_id, record_dict in data.items():
            # 重建GeneRecord对象
            record = GeneRecord(**record_dict)
            self.genes[gene_id] = record
        
        logger.info(f"从 {filepath} 导入了 {len(data)} 个基因")
    
    def get_statistics(self) -> Dict:
        """
        获取基因库统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.genes:
            return {
                'total_genes': 0,
                'avg_fitness': 0,
                'diversity': 0
            }
        
        fitness_scores = [r.适应度评分 for r in self.genes.values()]
        
        # 按市场状态分组
        regime_counts = {}
        for record in self.genes.values():
            regime = record.best_market_regime
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        return {
            'total_genes': len(self.genes),
            'avg_fitness': np.mean(fitness_scores),
            'max_fitness': np.max(fitness_scores),
            'min_fitness': np.min(fitness_scores),
            'diversity': self.calculate_diversity(),
            'generation': self.generation_counter,
            'regime_distribution': regime_counts
        }

