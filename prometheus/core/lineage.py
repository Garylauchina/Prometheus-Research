"""
血统系统 (Lineage System) - Prometheus v5.0

核心功能：
1. 血统向量表示（LineageVector）
2. 亲缘系数计算（Bhattacharyya）
3. 生殖隔离判断
4. 血统纯度分类
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LineagePurityClass:
    """血统纯度分类"""
    category: str  # 'pure', 'mixed', 'hybrid'
    dominant_family: int  # 主导家族ID
    purity_score: float  # 纯度得分 (0-1)
    family_distribution: Dict[int, float]  # 家族血统分布


class LineageVector:
    """
    血统向量 (Lineage Vector)
    
    用固定维度向量表示Agent的血统，支持快速亲缘计算和生殖隔离判断。
    
    向量维度 = 创世家族数量 (默认50)
    向量元素 = 每个家族的血统比例 (和为1)
    
    Examples:
        >>> # 创世Agent（纯血）
        >>> lineage = LineageVector.create_genesis(family_id=0, num_families=50)
        >>> print(lineage.vector)  # [1.0, 0.0, 0.0, ..., 0.0]
        
        >>> # 交叉繁殖（混血）
        >>> child = LineageVector.create_child(parent1, parent2)
        >>> kinship = parent1.compute_kinship(child)
        >>> print(f"亲缘系数: {kinship:.3f}")  # 0.707
    """
    
    def __init__(self, vector: np.ndarray):
        """
        初始化血统向量
        
        Args:
            vector: 血统向量 (已归一化)
        """
        self.vector = vector
        self._normalize()  # 确保归一化
    
    @classmethod
    def create_genesis(cls, family_id: int, num_families: int = 50) -> 'LineageVector':
        """
        创建创世Agent的血统（纯血）
        
        Args:
            family_id: 家族ID (0 到 num_families-1)
            num_families: 总家族数量
        
        Returns:
            LineageVector: 纯血血统向量
        
        Examples:
            >>> lineage = LineageVector.create_genesis(family_id=0, num_families=50)
            >>> lineage.vector[0]  # 1.0 (纯家族0血统)
        """
        if family_id < 0 or family_id >= num_families:
            raise ValueError(f"family_id必须在[0, {num_families-1}]范围内")
        
        vector = np.zeros(num_families, dtype=np.float64)
        vector[family_id] = 1.0
        
        logger.debug(f"创建创世血统: family_{family_id} (纯度: 100%)")
        
        lineage = cls(vector)
        # 存储家族ID，供多样性/移民等功能使用
        lineage.family_id = family_id
        return lineage
    
    @classmethod
    def create_child(cls, parent1: 'LineageVector', parent2: 'LineageVector') -> 'LineageVector':
        """
        创建子代血统（父母血统混合）
        
        使用简单平均混合（孟德尔遗传）
        
        Args:
            parent1: 父母1的血统
            parent2: 父母2的血统
        
        Returns:
            LineageVector: 子代血统向量
        
        Examples:
            >>> # 家族0和家族1的纯血交配
            >>> p1 = LineageVector.create_genesis(0, 50)
            >>> p2 = LineageVector.create_genesis(1, 50)
            >>> child = LineageVector.create_child(p1, p2)
            >>> child.vector[0]  # 0.5
            >>> child.vector[1]  # 0.5
        """
        if parent1.vector.shape != parent2.vector.shape:
            raise ValueError("父母血统向量维度不匹配")
        
        # 简单平均混合
        child_vector = (parent1.vector + parent2.vector) / 2.0
        
        logger.debug(f"创建子代血统: 混合度 {cls._compute_mixing_degree(parent1, parent2):.2f}")
        
        child = cls(child_vector)
        # 为子代设置family_id（取血统占比最高的家族）
        dominant_idx = int(np.argmax(child.vector))
        child.family_id = dominant_idx
        return child
    
    @staticmethod
    def _compute_mixing_degree(parent1: 'LineageVector', parent2: 'LineageVector') -> float:
        """计算父母间的混合度（0=完全相同，1=完全不同）"""
        # 使用欧几里得距离
        return float(np.linalg.norm(parent1.vector - parent2.vector))
    
    def compute_kinship(self, other: 'LineageVector') -> float:
        """
        计算与另一个Agent的亲缘系数
        
        使用Bhattacharyya系数：
            BC = Σ sqrt(p_i * q_i)
        
        返回值：
            0.0 = 完全无关（不同家族）
            1.0 = 完全相同（克隆或自己）
            0.5 = 兄弟姐妹（同父母）
            0.707 = 父子/母子关系
        
        Args:
            other: 另一个Agent的血统
        
        Returns:
            float: 亲缘系数 (0-1)
        
        Examples:
            >>> p1 = LineageVector.create_genesis(0, 50)
            >>> p2 = LineageVector.create_genesis(1, 50)
            >>> p1.compute_kinship(p2)  # 0.0 (无关)
            >>> p1.compute_kinship(p1)  # 1.0 (自己)
            
            >>> child = LineageVector.create_child(p1, p2)
            >>> p1.compute_kinship(child)  # ~0.707 (父子)
        """
        if self.vector.shape != other.vector.shape:
            raise ValueError("血统向量维度不匹配")
        
        # Bhattacharyya系数
        bc = np.sum(np.sqrt(self.vector * other.vector))
        
        # 限制在[0, 1]范围
        bc = np.clip(bc, 0.0, 1.0)
        
        return float(bc)
    
    def can_mate_with(self, other: 'LineageVector', threshold: float = 0.85) -> bool:
        """
        判断是否可以与另一个Agent交配（生殖隔离检查）
        
        Args:
            other: 另一个Agent的血统
            threshold: 亲缘系数阈值（默认0.85，即只允许一级亲属以下）
        
        Returns:
            bool: True=可以交配，False=近亲禁止
        
        Examples:
            >>> p1 = LineageVector.create_genesis(0, 50)
            >>> p2 = LineageVector.create_genesis(1, 50)
            >>> p1.can_mate_with(p2)  # True (无关)
            
            >>> child = LineageVector.create_child(p1, p2)
            >>> p1.can_mate_with(child)  # False (父子禁止)
        """
        kinship = self.compute_kinship(other)
        return kinship < threshold
    
    def get_dominant_families(self, top_k: int = 3) -> List[Tuple[int, float]]:
        """
        获取主导家族（血统比例最高的前K个）
        
        Args:
            top_k: 返回前K个家族
        
        Returns:
            List[Tuple[int, float]]: [(family_id, proportion), ...]
        
        Examples:
            >>> lineage = LineageVector.create_genesis(0, 50)
            >>> lineage.get_dominant_families(top_k=3)
            [(0, 1.0), (1, 0.0), (2, 0.0)]
        """
        # 获取非零血统的家族
        nonzero_indices = np.nonzero(self.vector)[0]
        if len(nonzero_indices) == 0:
            logger.warning("血统向量全为0，这不应该发生")
            return []
        
        # 按血统比例排序
        sorted_indices = np.argsort(self.vector)[::-1][:top_k]
        
        result = [
            (int(idx), float(self.vector[idx]))
            for idx in sorted_indices
            if self.vector[idx] > 0
        ]
        
        return result
    
    def get_dominant_family(self) -> int:
        """
        获取主导家族ID（用于多样性监控）
        
        Returns:
            int: 主导家族ID（血统比例最高的家族）
        
        Examples:
            >>> lineage = LineageVector.create_genesis(5, 50)
            >>> lineage.get_dominant_family()  # 5
        """
        # 优先使用显式标记的family_id（创建时写入）
        explicit_family = getattr(self, 'family_id', None)
        if explicit_family is not None:
            return int(explicit_family)
        dominant_idx = np.argmax(self.vector)
        return int(dominant_idx)
    
    def classify_purity(self, pure_threshold: float = 0.95) -> LineagePurityClass:
        """
        分类血统纯度
        
        Args:
            pure_threshold: 纯血阈值（单一家族比例 > 此值即为纯血）
        
        Returns:
            LineagePurityClass: 血统分类
        
        Classifications:
            - pure: 单一家族 > 95%
            - mixed: 2-3个家族
            - hybrid: 4+个家族
        
        Examples:
            >>> p1 = LineageVector.create_genesis(0, 50)
            >>> p1.classify_purity().category  # 'pure'
            >>> p1.classify_purity().purity_score  # 1.0
        """
        # 找到主导家族
        dominant_families = self.get_dominant_families(top_k=10)
        max_proportion = dominant_families[0][1] if dominant_families else 0.0
        dominant_family = dominant_families[0][0] if dominant_families else -1
        
        # 计算有效家族数（血统比例 > 0.01）
        effective_families = np.sum(self.vector > 0.01)
        
        # 分类
        if max_proportion >= pure_threshold:
            category = 'pure'
            purity_score = max_proportion
        elif effective_families <= 3:
            category = 'mixed'
            purity_score = max_proportion
        else:
            category = 'hybrid'
            # 使用香农熵的倒数作为纯度得分
            from scipy.stats import entropy
            # 避免log(0)
            nonzero_vector = self.vector[self.vector > 0]
            ent = entropy(nonzero_vector, base=2)
            max_entropy = np.log2(len(nonzero_vector))
            purity_score = 1.0 - (ent / max_entropy) if max_entropy > 0 else 0.5
        
        # 构建家族分布
        family_distribution = {
            int(fam): float(prop)
            for fam, prop in dominant_families
            if prop > 0.01  # 过滤掉微量血统
        }
        
        return LineagePurityClass(
            category=category,
            dominant_family=dominant_family,
            purity_score=float(purity_score),
            family_distribution=family_distribution
        )
    
    def _normalize(self):
        """归一化血统向量（和为1）"""
        total = np.sum(self.vector)
        if total > 0:
            self.vector = self.vector / total
        else:
            logger.error("血统向量总和为0，无法归一化")
            # 设置为均匀分布作为后备
            self.vector[:] = 1.0 / len(self.vector)
    
    def to_dict(self) -> Dict:
        """
        转换为字典（用于序列化）
        
        Returns:
            Dict: 血统数据
        """
        dominant = self.get_dominant_families(top_k=5)
        purity = self.classify_purity()
        
        return {
            'vector': self.vector.tolist(),
            'dimension': len(self.vector),
            'dominant_families': dominant,
            'purity_class': purity.category,
            'purity_score': purity.purity_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LineageVector':
        """
        从字典恢复（用于反序列化）
        
        Args:
            data: 血统数据字典
        
        Returns:
            LineageVector: 恢复的血统对象
        """
        vector = np.array(data['vector'], dtype=np.float64)
        return cls(vector)
    
    def __repr__(self) -> str:
        """字符串表示"""
        dominant = self.get_dominant_families(top_k=3)
        dominant_str = ", ".join([f"F{fam}:{prop:.2%}" for fam, prop in dominant])
        purity = self.classify_purity()
        
        return (f"LineageVector(dim={len(self.vector)}, "
                f"purity={purity.category}({purity.purity_score:.2f}), "
                f"dominant=[{dominant_str}])")


# ==================== 辅助函数 ====================

def batch_compute_kinship_matrix(lineages: List[LineageVector]) -> np.ndarray:
    """
    批量计算亲缘矩阵
    
    Args:
        lineages: LineageVector列表
    
    Returns:
        np.ndarray: 亲缘矩阵 (N×N)
    
    Examples:
        >>> lineages = [LineageVector.create_genesis(i, 50) for i in range(5)]
        >>> matrix = batch_compute_kinship_matrix(lineages)
        >>> matrix.shape  # (5, 5)
        >>> matrix[0, 0]  # 1.0 (自己)
        >>> matrix[0, 1]  # 0.0 (不同家族)
    """
    n = len(lineages)
    matrix = np.zeros((n, n), dtype=np.float64)
    
    for i in range(n):
        for j in range(i, n):  # 只计算上三角（对称矩阵）
            kinship = lineages[i].compute_kinship(lineages[j])
            matrix[i, j] = kinship
            matrix[j, i] = kinship  # 对称
    
    return matrix


def find_compatible_mates(
    agent_lineage: LineageVector, 
    candidate_lineages: List[LineageVector],
    threshold: float = 0.85
) -> List[int]:
    """
    从候选者中找出所有可交配的个体
    
    Args:
        agent_lineage: 目标Agent的血统
        candidate_lineages: 候选者血统列表
        threshold: 亲缘系数阈值
    
    Returns:
        List[int]: 可交配的候选者索引列表
    
    Examples:
        >>> agent = LineageVector.create_genesis(0, 50)
        >>> candidates = [LineageVector.create_genesis(i, 50) for i in range(10)]
        >>> compatible_indices = find_compatible_mates(agent, candidates)
        >>> len(compatible_indices)  # 9 (除了自己)
    """
    compatible = []
    
    for i, candidate in enumerate(candidate_lineages):
        if agent_lineage.can_mate_with(candidate, threshold):
            compatible.append(i)
    
    return compatible

