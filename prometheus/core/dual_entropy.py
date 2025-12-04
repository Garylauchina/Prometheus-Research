"""
验血系统 (Blood Test System / Dual Entropy System) - Prometheus v5.0

这是一个给Agent"验血"的系统！🩸

就像医院的血液检测，我们可以：
1. 验血统（Lineage Test）：检测Agent的祖先血统纯度
2. 验基因（Genome Test）：检测Agent的基因多样性
3. 验健康（Health Assessment）：综合评估种群健康状态

核心功能：
1. 血统熵计算（Lineage Entropy）
2. 基因熵计算（Gene Entropy）
3. 种群健康评估（Dual Entropy Health System）
4. 多样性监控与预警
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy.stats import entropy as shannon_entropy
import logging

from .lineage import LineageVector
from .genome import GenomeVector, compute_genome_diversity

logger = logging.getLogger(__name__)


@dataclass
class DualEntropyMetrics:
    """双熵指标"""
    # 血统熵
    lineage_entropy: float  # 血统熵 (0-log2(num_families))
    lineage_entropy_normalized: float  # 归一化血统熵 (0-1)
    dominant_family_concentration: float  # 主导家族集中度 (0-1)
    effective_family_count: float  # 有效家族数量
    
    # 基因熵
    gene_entropy: float  # 基因熵（方差）(0-1)
    avg_unlocked_params: float  # 平均解锁参数数量
    param_diversity: Dict[str, float]  # 各参数的方差
    
    # 综合评估
    overall_health: str  # 'excellent', 'good', 'warning', 'critical'
    health_score: float  # 综合健康得分 (0-1)
    recommendations: List[str]  # 建议


# ==================== 血统熵计算 ====================

def calculate_lineage_entropy(lineages: List[LineageVector]) -> Dict[str, float]:
    """
    计算血统熵（Shannon Entropy）
    
    血统熵衡量创世家族在当前种群中的分布均匀程度：
    - 高熵：血统分布均匀，多样性高
    - 低熵：少数家族占主导，多样性低
    
    Args:
        lineages: LineageVector列表
    
    Returns:
        Dict: {
            'lineage_entropy': float,  # 原始熵值
            'normalized_entropy': float,  # 归一化熵 (0-1)
            'max_entropy': float,  # 最大可能熵
            'effective_families': float,  # 有效家族数量
            'concentration': float  # 主导家族集中度
        }
    
    Examples:
        >>> lineages = [LineageVector.create_genesis(i % 5, 50) for i in range(20)]
        >>> metrics = calculate_lineage_entropy(lineages)
        >>> print(f"血统熵: {metrics['normalized_entropy']:.2f}")
    """
    if not lineages:
        logger.warning("空的血统列表")
        return {
            'lineage_entropy': 0.0,
            'normalized_entropy': 0.0,
            'max_entropy': 0.0,
            'effective_families': 0,
            'concentration': 1.0
        }
    
    # 统计每个家族的血统总和
    num_families = len(lineages[0].vector)
    family_totals = np.zeros(num_families, dtype=np.float64)
    
    for lineage in lineages:
        family_totals += lineage.vector
    
    # 归一化为概率分布
    total = np.sum(family_totals)
    if total == 0:
        logger.error("血统总和为0，这不应该发生")
        return {
            'lineage_entropy': 0.0,
            'normalized_entropy': 0.0,
            'max_entropy': 0.0,
            'effective_families': 0,
            'concentration': 1.0
        }
    
    family_probs = family_totals / total
    
    # 过滤掉0概率（避免log(0)）
    nonzero_probs = family_probs[family_probs > 0]
    
    if len(nonzero_probs) == 0:
        logger.error("没有非零血统概率")
        return {
            'lineage_entropy': 0.0,
            'normalized_entropy': 0.0,
            'max_entropy': 0.0,
            'effective_families': 0,
            'concentration': 1.0
        }
    
    # 计算Shannon熵（使用log2）
    lineage_ent = shannon_entropy(nonzero_probs, base=2)
    
    # 最大可能熵（均匀分布）
    max_ent = np.log2(len(nonzero_probs))
    
    # 归一化熵 (0-1)
    normalized_ent = lineage_ent / max_ent if max_ent > 0 else 0.0
    
    # 有效家族数量（2的熵次方）
    effective_families = 2 ** lineage_ent
    
    # 主导家族集中度（前3家族的血统比例之和）
    top3_probs = np.sort(family_probs)[-3:]
    concentration = np.sum(top3_probs)
    
    return {
        'lineage_entropy': float(lineage_ent),
        'normalized_entropy': float(normalized_ent),
        'max_entropy': float(max_ent),
        'effective_families': float(effective_families),
        'concentration': float(concentration)
    }


# ==================== 基因熵计算 ====================

def calculate_gene_entropy_variance(genomes: List[GenomeVector]) -> Dict[str, float]:
    """
    计算基因熵（基于方差）
    
    基因熵衡量策略参数在种群中的多样性：
    - 高熵：参数值分布广，策略多样
    - 低熵：参数值趋同，策略单一
    
    Args:
        genomes: GenomeVector列表
    
    Returns:
        Dict: {
            'gene_entropy': float,  # 基因熵（方差）(0-1)
            'avg_unlocked': float,  # 平均解锁参数数量
            'param_variances': Dict[str, float],  # 各参数方差
            'low_diversity_params': List[str]  # 低多样性参数
        }
    
    Examples:
        >>> genomes = [GenomeVector.create_genesis() for _ in range(20)]
        >>> metrics = calculate_gene_entropy_variance(genomes)
        >>> print(f"基因熵: {metrics['gene_entropy']:.2f}")
    """
    if not genomes:
        logger.warning("空的基因组列表")
        return {
            'gene_entropy': 0.0,
            'avg_unlocked': 0.0,
            'param_variances': {},
            'low_diversity_params': []
        }
    
    from .genome import ALL_GENE_PARAMETERS
    
    # 收集所有已解锁参数的值
    param_values = {}
    for genome in genomes:
        for i in range(50):
            if genome.unlocked_mask[i]:
                param_name = ALL_GENE_PARAMETERS[i]
                if param_name not in param_values:
                    param_values[param_name] = []
                param_values[param_name].append(genome.vector[i])
    
    if not param_values:
        logger.warning("没有已解锁的参数")
        return {
            'gene_entropy': 0.0,
            'avg_unlocked': 0.0,
            'param_variances': {},
            'low_diversity_params': []
        }
    
    # 计算每个参数的方差
    param_variances = {}
    variances = []
    for param_name, values in param_values.items():
        if len(values) > 1:
            var = float(np.var(values))
            param_variances[param_name] = var
            variances.append(var)
        else:
            param_variances[param_name] = 0.0
    
    # 平均方差作为基因熵
    if variances:
        avg_variance = np.mean(variances)
        # 归一化到0-1（方差最大为0.25）
        gene_ent = min(1.0, avg_variance / 0.25 * 2)
    else:
        gene_ent = 0.0
    
    # 平均解锁参数数量
    avg_unlocked = np.mean([g.get_unlocked_count() for g in genomes])
    
    # 识别低多样性参数（方差 < 0.01）
    low_diversity_params = [
        param for param, var in param_variances.items()
        if var < 0.01
    ]
    
    return {
        'gene_entropy': float(gene_ent),
        'avg_unlocked': float(avg_unlocked),
        'param_variances': param_variances,
        'low_diversity_params': low_diversity_params
    }


def calculate_gene_entropy_discretized(genomes: List[GenomeVector], bins: int = 10) -> float:
    """
    计算基因熵（离散化Shannon Entropy）
    
    将参数值离散化为bins个区间，然后计算Shannon熵。
    适用于需要精确熵值的场景。
    
    Args:
        genomes: GenomeVector列表
        bins: 离散化区间数量
    
    Returns:
        float: 离散化Shannon熵 (0-log2(bins))
    
    Note:
        这个方法比方差更接近数学上的熵定义，但计算成本更高。
        对于大多数应用，基于方差的方法已经足够。
    """
    if not genomes or len(genomes) < 2:
        return 0.0
    
    from .genome import ALL_GENE_PARAMETERS
    
    # 收集所有参数值
    all_values = []
    for genome in genomes:
        for i in range(50):
            if genome.unlocked_mask[i]:
                all_values.append(genome.vector[i])
    
    if not all_values:
        return 0.0
    
    # 离散化到bins个区间
    hist, _ = np.histogram(all_values, bins=bins, range=(0, 1))
    
    # 归一化为概率分布
    probs = hist / np.sum(hist)
    
    # 过滤0概率
    nonzero_probs = probs[probs > 0]
    
    # Shannon熵
    ent = shannon_entropy(nonzero_probs, base=2)
    
    return float(ent)


# ==================== 双熵健康系统 ====================

class DualEntropyHealthSystem:
    """
    双熵健康系统
    
    监控血统熵和基因熵，评估种群健康状态，提供优化建议。
    
    Examples:
        >>> health_system = DualEntropyHealthSystem(num_families=50)
        >>> metrics = health_system.evaluate(lineages, genomes)
        >>> print(f"健康状态: {metrics.overall_health}")
        >>> print(f"健康得分: {metrics.health_score:.2f}")
        >>> for rec in metrics.recommendations:
        >>>     print(f"- {rec}")
    """
    
    def __init__(self, num_families: int = 50):
        """
        初始化双熵健康系统
        
        Args:
            num_families: 创世家族数量
        """
        self.num_families = num_families
        
        # 健康阈值配置
        self.thresholds = {
            'lineage_entropy': {
                'excellent': 0.85,  # 归一化熵 > 0.85
                'good': 0.70,
                'warning': 0.50,
                'critical': 0.30
            },
            'gene_entropy': {
                'excellent': 0.60,  # 方差熵 > 0.60
                'good': 0.40,
                'warning': 0.20,
                'critical': 0.10
            },
            'concentration': {
                'excellent': 0.30,  # 前3家族 < 30%
                'good': 0.50,
                'warning': 0.70,
                'critical': 0.85
            }
        }
    
    def evaluate(self, 
                 lineages: List[LineageVector],
                 genomes: List[GenomeVector]) -> DualEntropyMetrics:
        """
        评估种群健康
        
        Args:
            lineages: 血统向量列表
            genomes: 基因组向量列表
        
        Returns:
            DualEntropyMetrics: 双熵指标
        """
        # 计算血统熵
        lineage_metrics = calculate_lineage_entropy(lineages)
        
        # 计算基因熵
        gene_metrics = calculate_gene_entropy_variance(genomes)
        
        # 评估血统健康
        lineage_health, lineage_score = self._evaluate_lineage_health(lineage_metrics)
        
        # 评估基因健康
        gene_health, gene_score = self._evaluate_gene_health(gene_metrics)
        
        # 综合健康评估
        overall_health, health_score = self._综合评估(
            lineage_health, lineage_score,
            gene_health, gene_score
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(
            lineage_metrics, gene_metrics,
            lineage_health, gene_health
        )
        
        return DualEntropyMetrics(
            lineage_entropy=lineage_metrics['lineage_entropy'],
            lineage_entropy_normalized=lineage_metrics['normalized_entropy'],
            dominant_family_concentration=lineage_metrics['concentration'],
            effective_family_count=lineage_metrics['effective_families'],
            
            gene_entropy=gene_metrics['gene_entropy'],
            avg_unlocked_params=gene_metrics['avg_unlocked'],
            param_diversity=gene_metrics['param_variances'],
            
            overall_health=overall_health,
            health_score=health_score,
            recommendations=recommendations
        )
    
    def _evaluate_lineage_health(self, metrics: Dict) -> Tuple[str, float]:
        """评估血统健康"""
        norm_ent = metrics['normalized_entropy']
        concentration = metrics['concentration']
        
        # 基于归一化熵和集中度综合评分
        ent_score = norm_ent
        conc_score = 1.0 - concentration  # 集中度越低越好
        
        lineage_score = (ent_score * 0.7 + conc_score * 0.3)
        
        # 分级
        thresholds = self.thresholds['lineage_entropy']
        if lineage_score >= thresholds['excellent']:
            health = 'excellent'
        elif lineage_score >= thresholds['good']:
            health = 'good'
        elif lineage_score >= thresholds['warning']:
            health = 'warning'
        else:
            health = 'critical'
        
        return health, lineage_score
    
    def _evaluate_gene_health(self, metrics: Dict) -> Tuple[str, float]:
        """评估基因健康"""
        gene_ent = metrics['gene_entropy']
        
        # 基于基因熵评分
        gene_score = gene_ent
        
        # 分级
        thresholds = self.thresholds['gene_entropy']
        if gene_score >= thresholds['excellent']:
            health = 'excellent'
        elif gene_score >= thresholds['good']:
            health = 'good'
        elif gene_score >= thresholds['warning']:
            health = 'warning'
        else:
            health = 'critical'
        
        return health, gene_score
    
    def _综合评估(self, 
                  lineage_health: str, lineage_score: float,
                  gene_health: str, gene_score: float) -> Tuple[str, float]:
        """综合评估整体健康"""
        # 健康等级映射
        health_levels = {
            'excellent': 4,
            'good': 3,
            'warning': 2,
            'critical': 1
        }
        
        lineage_level = health_levels[lineage_health]
        gene_level = health_levels[gene_health]
        
        # 取较低的等级（木桶原理）
        min_level = min(lineage_level, gene_level)
        
        # 综合得分（加权平均）
        overall_score = lineage_score * 0.5 + gene_score * 0.5
        
        # 确定综合健康等级
        if min_level >= 4:
            overall_health = 'excellent'
        elif min_level >= 3:
            overall_health = 'good'
        elif min_level >= 2:
            overall_health = 'warning'
        else:
            overall_health = 'critical'
        
        return overall_health, overall_score
    
    def _generate_recommendations(self,
                                   lineage_metrics: Dict,
                                   gene_metrics: Dict,
                                   lineage_health: str,
                                   gene_health: str) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 血统相关建议
        if lineage_health in ['warning', 'critical']:
            eff_families = lineage_metrics['effective_families']
            concentration = lineage_metrics['concentration']
            
            if concentration > 0.7:
                recommendations.append(
                    f"⚠️ 血统集中度过高({concentration:.1%})，"
                    f"建议优先选择少数家族Agent交配"
                )
            
            if eff_families < 10:
                recommendations.append(
                    f"⚠️ 有效家族数过少({eff_families:.1f})，"
                    f"建议引入更多家族血统"
                )
        
        # 基因相关建议
        if gene_health in ['warning', 'critical']:
            gene_ent = gene_metrics['gene_entropy']
            low_div_params = gene_metrics['low_diversity_params']
            
            if gene_ent < 0.3:
                recommendations.append(
                    f"⚠️ 基因多样性过低({gene_ent:.2f})，"
                    f"建议提高变异率或变异幅度"
                )
            
            if len(low_div_params) > 5:
                recommendations.append(
                    f"⚠️ {len(low_div_params)}个参数多样性不足，"
                    f"建议加强这些参数的变异"
                )
        
        # 如果都健康，给予积极反馈
        if not recommendations:
            if lineage_health == 'excellent' and gene_health == 'excellent':
                recommendations.append("✅ 种群健康状态极佳，继续保持！")
            else:
                recommendations.append("✅ 种群健康状态良好")
        
        return recommendations


# ==================== 可视化辅助函数 ====================

def plot_dual_entropy_matrix(lineages: List[LineageVector],
                               genomes: List[GenomeVector],
                               save_path: Optional[str] = None):
    """
    绘制双熵矩阵图（验血报告可视化）🩸
    
    Args:
        lineages: 血统向量列表
        genomes: 基因组向量列表
        save_path: 保存路径（如果提供）
    
    Note:
        需要matplotlib库。这是一个可选功能。
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
    except ImportError:
        logger.warning("matplotlib未安装，无法绘图")
        return
    
    lineage_metrics = calculate_lineage_entropy(lineages)
    gene_metrics = calculate_gene_entropy_variance(genomes)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 左图：血统熵
    lineage_ent = lineage_metrics['normalized_entropy']
    ax1.bar(['血统熵'], [lineage_ent], color='skyblue')
    ax1.set_ylim(0, 1)
    ax1.set_ylabel('归一化熵')
    ax1.set_title(f'血统熵: {lineage_ent:.2f}')
    ax1.axhline(0.7, color='green', linestyle='--', label='良好')
    ax1.axhline(0.5, color='orange', linestyle='--', label='警告')
    ax1.axhline(0.3, color='red', linestyle='--', label='危险')
    ax1.legend()
    
    # 右图：基因熵
    gene_ent = gene_metrics['gene_entropy']
    ax2.bar(['基因熵'], [gene_ent], color='lightcoral')
    ax2.set_ylim(0, 1)
    ax2.set_ylabel('方差熵')
    ax2.set_title(f'基因熵: {gene_ent:.2f}')
    ax2.axhline(0.4, color='green', linestyle='--', label='良好')
    ax2.axhline(0.2, color='orange', linestyle='--', label='警告')
    ax2.axhline(0.1, color='red', linestyle='--', label='危险')
    ax2.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"双熵矩阵图已保存: {save_path}")
    else:
        plt.show()
    
    plt.close()


# ==================== 验血系统（高层API）====================

@dataclass
class BloodTestReport:
    """
    验血报告 🩸
    
    就像医院的血液检查报告单！
    """
    agent_id: str
    test_time: str
    
    # 血统检测
    lineage_purity: str  # 'pure', 'mixed', 'hybrid'
    lineage_purity_score: float  # 纯度得分 (0-1)
    dominant_families: List[Tuple[int, float]]  # [(family_id, proportion), ...]
    
    # 基因检测
    unlocked_params_count: int  # 已解锁参数数量
    gene_complexity: str  # 'basic', 'intermediate', 'advanced', 'master'
    
    # 配对建议
    mating_compatibility: Dict[str, bool]  # {other_agent_id: can_mate}
    
    def __repr__(self) -> str:
        """格式化输出验血报告"""
        report = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🩸 验血报告 - {self.agent_id}",
            f"   检测时间: {self.test_time}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "【血统检测】",
            f"  纯度等级: {self.lineage_purity} ({self.lineage_purity_score:.1%})",
            f"  主要血统:",
        ]
        
        for fam, prop in self.dominant_families[:3]:
            report.append(f"    - 家族{fam}: {prop:.1%}")
        
        report.extend([
            "",
            "【基因检测】",
            f"  复杂度: {self.gene_complexity}",
            f"  已解锁参数: {self.unlocked_params_count}/50",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ])
        
        return "\n".join(report)


class PrometheusBloodLab:
    """
    普罗米修斯验血实验室 🏥🩸
    
    这是一个给Agent做"血液检查"的实验室！
    
    提供的服务：
    1. 验血统（Lineage Test）：检测祖先血统
    2. 验基因（Genome Test）：检测基因复杂度
    3. 配对测试（Compatibility Test）：检测两个Agent是否可以交配
    4. 种群体检（Population Health Check）：整体健康评估
    
    Examples:
        >>> lab = PrometheusBloodLab()
        
        >>> # 给单个Agent验血
        >>> report = lab.test_agent(agent)
        >>> print(report)
        
        >>> # 检测两个Agent的配对兼容性
        >>> compatible = lab.test_compatibility(agent1, agent2)
        >>> print(f"可以交配: {compatible}")
        
        >>> # 种群体检
        >>> health = lab.population_checkup(all_agents)
        >>> print(f"种群健康: {health.overall_health}")
    """
    
    def __init__(self, num_families: int = 50):
        """
        初始化验血实验室
        
        Args:
            num_families: 创世家族数量
        """
        self.num_families = num_families
        self.health_system = DualEntropyHealthSystem(num_families)
        logger.info("🏥 普罗米修斯验血实验室已开业！")
    
    def test_agent(self, agent, other_agents: Optional[List] = None) -> BloodTestReport:
        """
        给单个Agent验血 🩸
        
        Args:
            agent: 要检测的Agent（需要有lineage和genome属性）
            other_agents: 其他Agent列表（用于配对兼容性测试）
        
        Returns:
            BloodTestReport: 验血报告
        
        Examples:
            >>> lab = PrometheusBloodLab()
            >>> report = lab.test_agent(agent, other_agents)
            >>> print(report)
        """
        from datetime import datetime
        
        # 血统检测
        lineage = agent.lineage
        purity = lineage.classify_purity()
        dominant_families = lineage.get_dominant_families(top_k=5)
        
        # 基因检测
        genome = agent.genome
        unlocked_count = genome.get_unlocked_count()
        
        # 基因复杂度分类
        if unlocked_count <= 3:
            complexity = 'basic'
        elif unlocked_count <= 10:
            complexity = 'intermediate'
        elif unlocked_count <= 20:
            complexity = 'advanced'
        else:
            complexity = 'master'
        
        # 配对兼容性测试
        mating_compatibility = {}
        if other_agents:
            for other in other_agents:
                if hasattr(other, 'agent_id') and hasattr(other, 'lineage'):
                    if other.agent_id != agent.agent_id:
                        compatible = lineage.can_mate_with(other.lineage)
                        mating_compatibility[other.agent_id] = compatible
        
        return BloodTestReport(
            agent_id=agent.agent_id,
            test_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            lineage_purity=purity.category,
            lineage_purity_score=purity.purity_score,
            dominant_families=dominant_families,
            unlocked_params_count=unlocked_count,
            gene_complexity=complexity,
            mating_compatibility=mating_compatibility
        )
    
    def test_compatibility(self, agent1, agent2, threshold: float = 0.85) -> bool:
        """
        配对兼容性测试（检测是否可以交配）🩸❤️
        
        Args:
            agent1: Agent 1
            agent2: Agent 2
            threshold: 亲缘系数阈值
        
        Returns:
            bool: True=可以交配，False=近亲禁止
        
        Examples:
            >>> lab = PrometheusBloodLab()
            >>> if lab.test_compatibility(agent1, agent2):
            >>>     print("✅ 可以交配")
            >>> else:
            >>>     print("❌ 近亲禁止")
        """
        return agent1.lineage.can_mate_with(agent2.lineage, threshold)
    
    def population_checkup(self, agents: List) -> DualEntropyMetrics:
        """
        种群体检（整体健康评估）🏥
        
        Args:
            agents: Agent列表（需要有lineage和genome属性）
        
        Returns:
            DualEntropyMetrics: 双熵健康指标
        
        Examples:
            >>> lab = PrometheusBloodLab()
            >>> health = lab.population_checkup(all_agents)
            >>> print(f"种群健康: {health.overall_health}")
            >>> print(f"血统熵: {health.lineage_entropy_normalized:.2f}")
            >>> print(f"基因熵: {health.gene_entropy:.2f}")
            >>> for rec in health.recommendations:
            >>>     print(f"  - {rec}")
        """
        # 提取血统和基因组
        lineages = [agent.lineage for agent in agents if hasattr(agent, 'lineage')]
        genomes = [agent.genome for agent in agents if hasattr(agent, 'genome')]
        
        if not lineages or not genomes:
            logger.warning("没有有效的血统或基因组数据")
            return DualEntropyMetrics(
                lineage_entropy=0.0,
                lineage_entropy_normalized=0.0,
                dominant_family_concentration=1.0,
                effective_family_count=0,
                gene_entropy=0.0,
                avg_unlocked_params=0.0,
                param_diversity={},
                overall_health='critical',
                health_score=0.0,
                recommendations=["⚠️ 无有效数据"]
            )
        
        # 使用双熵健康系统评估
        return self.health_system.evaluate(lineages, genomes)
    
    def generate_report_summary(self, metrics: DualEntropyMetrics) -> str:
        """
        生成体检报告摘要 📋
        
        Args:
            metrics: 双熵指标
        
        Returns:
            str: 格式化的体检报告
        """
        report = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🏥 种群体检报告",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "【血统检测】",
            f"  血统熵: {metrics.lineage_entropy_normalized:.2f} (归一化)",
            f"  有效家族: {metrics.effective_family_count:.1f}个",
            f"  主导集中度: {metrics.dominant_family_concentration:.1%}",
            "",
            "【基因检测】",
            f"  基因熵: {metrics.gene_entropy:.2f}",
            f"  平均参数: {metrics.avg_unlocked_params:.1f}/50",
            "",
            "【综合评估】",
            f"  健康状态: {metrics.overall_health.upper()}",
            f"  健康得分: {metrics.health_score:.1%}",
            "",
            "【建议】",
        ]
        
        for rec in metrics.recommendations:
            report.append(f"  {rec}")
        
        report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(report)
    
    def __repr__(self) -> str:
        """实验室信息"""
        return f"PrometheusBloodLab(families={self.num_families}, status='营业中🏥')"

