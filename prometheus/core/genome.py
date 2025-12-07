"""
基因组系统 (Genome System) - Prometheus v5.0

核心功能：
1. 基因组向量表示（GenomeVector）
2. 参数解锁与管理
3. 交叉与变异
4. 基因多样性计算
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import random
import logging

logger = logging.getLogger(__name__)


# ==================== 参数定义 ====================

# 所有可用的基因参数（50维）
ALL_GENE_PARAMETERS = [
    # === Tier 1: 基础参数（初始3个）===
    'risk_appetite',      # 风险偏好 (0-1)
    'trend_pref',         # 趋势偏好 (0-1, 0=逆势, 1=顺势)
    'patience',           # 耐心值 (0-1)
    
    # === Tier 2: 中级参数（3-10代解锁）===
    'volatility_sens',    # 波动敏感度
    'max_position_pct',   # 最大仓位比例
    'stop_loss_pct',      # 止损百分比
    'take_profit_pct',    # 止盈百分比
    'position_sizing',    # 仓位管理策略
    
    # === Tier 3: 高级参数（10-20代解锁）===
    'momentum_weight',    # 动量权重
    'mean_reversion',     # 均值回归倾向
    'breakout_sens',      # 突破敏感度
    'volume_importance',  # 量能重要性
    'ma_period_pref',     # 均线周期偏好
    
    # === Tier 4: 稀有参数（20+代低概率解锁）===
    'market_timing',      # 市场择时能力
    'fear_control',       # 恐惧控制
    'profit_locking',     # 利润锁定策略
    'drawdown_tolerance', # 回撤容忍度
    'correlation_awareness',  # 关联性意识
    
    # === 更多参数（预留用于扩展）===
    'liquidity_pref',     # 流动性偏好
    'spread_sensitivity', # 点差敏感度
    'slippage_tolerance', # 滑点容忍度
    'news_reactivity',    # 新闻反应速度
    'technical_vs_fundamental',  # 技术vs基本面权重
    
    # 情绪相关
    'optimism',           # 乐观度
    'panic_threshold',    # 恐慌阈值
    'greed_control',      # 贪婪控制
    'confidence_boost',   # 信心加成
    'stress_resistance',  # 抗压能力
    
    # 时间相关
    'holding_period_pref',  # 持仓周期偏好
    'entry_timing',         # 入场时机选择
    'exit_timing',          # 出场时机选择
    'reentry_patience',     # 再入场耐心
    'cut_loss_speed',       # 止损速度
    
    # 市场环境适应
    'bull_market_aggression',   # 牛市进攻性
    'bear_market_defense',      # 熊市防守性
    'sideways_patience',        # 震荡市耐心
    'volatility_exploitation',  # 波动性利用
    'low_vol_patience',         # 低波环境耐心
    
    # 高级策略
    'trend_following',     # 趋势跟随
    'counter_trend',       # 逆势交易
    'range_trading',       # 区间交易
    'scalping_tendency',   # 刷单倾向
    'swing_trading',       # 波段交易
    
    # 风险管理
    'kelly_criterion',     # 凯利公式系数
    'var_limit',           # VaR限制
    'sharpe_target',       # 夏普目标
    'max_drawdown_limit',  # 最大回撤限制
    'risk_parity',         # 风险平价
    
    # 网格交易相关（补充到50个）
    'grid_size',           # 网格大小
    'grid_density',        # 网格密度
]

# 确保50个参数
assert len(ALL_GENE_PARAMETERS) == 50, f"参数数量必须为50，当前{len(ALL_GENE_PARAMETERS)}"


@dataclass
class ParameterTier:
    """参数解锁层级"""
    tier: int
    unlock_generation: int  # 解锁世代
    unlock_probability: float  # 解锁概率


# 参数分层配置
PARAMETER_TIERS = {
    'tier_1': ParameterTier(1, unlock_generation=1, unlock_probability=1.0),   # 初始必有
    'tier_2': ParameterTier(2, unlock_generation=3, unlock_probability=0.6),   # 3代后60%概率
    'tier_3': ParameterTier(3, unlock_generation=10, unlock_probability=0.3),  # 10代后30%概率
    'tier_4': ParameterTier(4, unlock_generation=20, unlock_probability=0.1),  # 20代后10%概率
}


class GenomeVector:
    """
    基因组向量 (Genome Vector)
    
    用50维向量表示Agent的策略参数（基因组）。
    
    向量维度 = 50 (固定)
    向量元素 = 参数值 (0-1)
    解锁掩码 = unlocked_mask (True=已解锁，False=未解锁)
    
    Examples:
        >>> # 创建初始基因组（3个基础参数）
        >>> genome = GenomeVector.create_genesis()
        >>> genome.get_unlocked_count()  # 3
        
        >>> # 交叉繁殖
        >>> child = GenomeVector.crossover(parent1.genome, parent2.genome)
        
        >>> # 变异（可能解锁新参数）
        >>> child.mutate(generation=5)
    """
    
    def __init__(self, 
                 vector: Optional[np.ndarray] = None,
                 unlocked_mask: Optional[np.ndarray] = None):
        """
        初始化基因组向量
        
        Args:
            vector: 参数向量 (50维, 0-1范围)
            unlocked_mask: 解锁掩码 (50维布尔数组)
        """
        if vector is None:
            self.vector = np.zeros(50, dtype=np.float64)
        else:
            if len(vector) != 50:
                raise ValueError(f"基因组向量必须是50维，当前{len(vector)}维")
            self.vector = np.array(vector, dtype=np.float64)
        
        if unlocked_mask is None:
            self.unlocked_mask = np.zeros(50, dtype=bool)
        else:
            if len(unlocked_mask) != 50:
                raise ValueError(f"解锁掩码必须是50维，当前{len(unlocked_mask)}维")
            self.unlocked_mask = np.array(unlocked_mask, dtype=bool)
        
        # 确保未解锁的参数值为0
        self.vector[~self.unlocked_mask] = 0.0
    
    @property
    def active_params(self) -> Dict[str, float]:
        """获取已激活(解锁)的参数字典（兼容性属性）"""
        return self.to_dict()
    
    @classmethod
    def create_genesis(cls, full_unlock: bool = False) -> 'GenomeVector':
        """
        创建创世基因组
        
        Args:
            full_unlock: 是否解锁所有50个参数（激进模式）
                        - False: 只解锁Tier 1的3个基础参数（渐进式）
                        - True: 解锁所有50个参数（完全自由）
        
        Returns:
            GenomeVector: 初始基因组
        
        Examples:
            >>> # 渐进式（默认）
            >>> genome = GenomeVector.create_genesis()
            >>> genome.get_unlocked_count()  # 3
            
            >>> # 激进模式
            >>> genome = GenomeVector.create_genesis(full_unlock=True)
            >>> genome.get_unlocked_count()  # 50
        """
        genome = cls()
        
        if full_unlock:
            # ⚡ 激进模式：解锁所有50个参数！
            for i in range(50):
                genome.unlocked_mask[i] = True
                # 使用Beta分布生成初始值（避免极端值）
                genome.vector[i] = np.random.beta(2, 2)
            logger.info(f"🔥 激进模式创世：解锁所有{genome.get_unlocked_count()}个参数")
        else:
            # 渐进式：解锁Tier 1参数（前3个）
            for i in range(3):
                genome.unlocked_mask[i] = True
                # 使用Beta分布生成初始值（避免极端值）
                genome.vector[i] = np.random.beta(2, 2)
            logger.debug(f"创建创世基因组: 解锁{genome.get_unlocked_count()}个参数")
        
        return genome
    
    @classmethod
    def crossover(cls, parent1: 'GenomeVector', parent2: 'GenomeVector') -> 'GenomeVector':
        """
        交叉繁殖（混合父母基因组）
        
        策略：
        - 70%概率使用父母平均值（融合）
        - 30%概率随机选择一个父母的值（选择）
        - 子代继承父母已解锁的所有参数
        
        Args:
            parent1: 父母1的基因组
            parent2: 父母2的基因组
        
        Returns:
            GenomeVector: 子代基因组
        
        Examples:
            >>> p1 = GenomeVector.create_genesis()
            >>> p2 = GenomeVector.create_genesis()
            >>> child = GenomeVector.crossover(p1, p2)
        """
        child = cls()
        
        # 子代继承父母已解锁的所有参数
        child.unlocked_mask = parent1.unlocked_mask | parent2.unlocked_mask
        
        # 对每个已解锁的参数进行交叉
        for i in range(50):
            if child.unlocked_mask[i]:
                # 70%概率平均，30%概率随机选择
                if random.random() < 0.7:
                    # 平均混合
                    v1 = parent1.vector[i] if parent1.unlocked_mask[i] else 0.5
                    v2 = parent2.vector[i] if parent2.unlocked_mask[i] else 0.5
                    child.vector[i] = (v1 + v2) / 2.0
                else:
                    # 随机选择一个父母
                    if parent1.unlocked_mask[i] and parent2.unlocked_mask[i]:
                        child.vector[i] = random.choice([parent1.vector[i], parent2.vector[i]])
                    elif parent1.unlocked_mask[i]:
                        child.vector[i] = parent1.vector[i]
                    else:
                        child.vector[i] = parent2.vector[i]
            else:
                child.vector[i] = 0.0
        
        logger.debug(f"交叉繁殖: 子代继承{child.get_unlocked_count()}个参数")
        
        return child
    
    def mutate(self, 
               generation: int,
               mutation_rate: float = 0.5,
               mutation_strength: float = 0.15,
               environmental_hints: Optional[List[str]] = None) -> 'GenomeVector':
        """
        变异（修改现有参数或解锁新参数）
        
        变异类型：
        1. 参数值变异：已解锁参数值±mutation_strength
        2. 参数解锁：根据世代和层级概率解锁新参数
        3. 适应性解锁：根据环境提示优先解锁相关参数
        
        Args:
            generation: 当前世代
            mutation_rate: 变异概率（0-1）
            mutation_strength: 变异幅度（0-1）
            environmental_hints: 环境提示（建议解锁的参数）
        
        Returns:
            GenomeVector: 变异后的自己（in-place修改）
        
        Examples:
            >>> genome = GenomeVector.create_genesis()
            >>> genome.mutate(generation=1)
            >>> genome.mutate(generation=10, environmental_hints=['momentum_weight'])
        """
        # 1. 参数值变异
        for i in range(50):
            if self.unlocked_mask[i] and random.random() < mutation_rate:
                # 添加高斯噪声
                noise = np.random.normal(0, mutation_strength)
                self.vector[i] = np.clip(self.vector[i] + noise, 0.0, 1.0)
                logger.debug(f"参数{ALL_GENE_PARAMETERS[i]}变异: {self.vector[i]:.3f}")
        
        # 2. 参数解锁（尝试解锁1-2个新参数）
        unlock_attempts = random.randint(1, 2)
        for _ in range(unlock_attempts):
            self._try_unlock_parameter(generation, environmental_hints)
        
        return self
    
    def _try_unlock_parameter(self, 
                               generation: int,
                               environmental_hints: Optional[List[str]] = None):
        """
        尝试解锁一个新参数
        
        策略：
        1. 如果有环境提示，优先尝试解锁提示的参数
        2. 否则，根据层级和世代概率随机解锁
        
        Args:
            generation: 当前世代
            environmental_hints: 环境提示参数列表
        """
        # 找出未解锁的参数
        unlocked_indices = set(np.where(self.unlocked_mask)[0])
        all_indices = set(range(50))
        locked_indices = list(all_indices - unlocked_indices)
        
        if not locked_indices:
            logger.debug("所有参数已解锁")
            return
        
        # 策略1：环境提示优先
        if environmental_hints:
            hint_indices = [
                i for i, param in enumerate(ALL_GENE_PARAMETERS)
                if param in environmental_hints and i in locked_indices
            ]
            if hint_indices:
                # 30%概率使用提示
                if random.random() < 0.3:
                    idx = random.choice(hint_indices)
                    self._unlock_parameter(idx)
                    logger.info(f"🌟 适应性解锁: {ALL_GENE_PARAMETERS[idx]} (先知提示)")
                    return
        
        # 策略2：基于层级的概率解锁
        # 根据世代确定可解锁的参数范围
        eligible_indices = []
        for idx in locked_indices:
            tier = self._get_parameter_tier(idx)
            tier_config = PARAMETER_TIERS.get(f'tier_{tier}')
            
            if tier_config and generation >= tier_config.unlock_generation:
                # 满足世代要求，按概率加入候选
                if random.random() < tier_config.unlock_probability:
                    eligible_indices.append(idx)
        
        if eligible_indices:
            idx = random.choice(eligible_indices)
            self._unlock_parameter(idx)
            tier = self._get_parameter_tier(idx)
            logger.info(f"🔓 解锁新参数: {ALL_GENE_PARAMETERS[idx]} (Tier {tier})")
    
    def _get_parameter_tier(self, param_index: int) -> int:
        """获取参数所属层级"""
        if param_index < 3:
            return 1
        elif param_index < 8:
            return 2
        elif param_index < 13:
            return 3
        else:
            return 4
    
    def _unlock_parameter(self, param_index: int):
        """解锁指定参数"""
        if not self.unlocked_mask[param_index]:
            self.unlocked_mask[param_index] = True
            # 使用Beta分布初始化参数值
            self.vector[param_index] = np.random.beta(2, 2)
            logger.debug(f"参数{ALL_GENE_PARAMETERS[param_index]}已解锁，初始值: {self.vector[param_index]:.3f}")
    
    def get_unlocked_count(self) -> int:
        """获取已解锁参数数量"""
        return int(np.sum(self.unlocked_mask))
    
    def get_unlocked_params(self) -> List[str]:
        """获取已解锁参数名称列表"""
        return [
            ALL_GENE_PARAMETERS[i]
            for i in range(50)
            if self.unlocked_mask[i]
        ]
    
    def get_param_value(self, param_name: str) -> Optional[float]:
        """
        获取指定参数的值
        
        Args:
            param_name: 参数名称
        
        Returns:
            float or None: 参数值（如果已解锁），否则None
        """
        try:
            idx = ALL_GENE_PARAMETERS.index(param_name)
            if self.unlocked_mask[idx]:
                return float(self.vector[idx])
            else:
                return None
        except ValueError:
            logger.warning(f"未知参数: {param_name}")
            return None
    
    def to_dict(self) -> Dict[str, float]:
        """
        转换为字典（只包含已解锁的参数）
        
        Returns:
            Dict[str, float]: {param_name: value, ...}
        """
        return {
            ALL_GENE_PARAMETERS[i]: float(self.vector[i])
            for i in range(50)
            if self.unlocked_mask[i]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'GenomeVector':
        """
        从字典恢复基因组
        
        Args:
            data: {param_name: value, ...}
        
        Returns:
            GenomeVector: 恢复的基因组
        """
        genome = cls()
        
        for param_name, value in data.items():
            try:
                idx = ALL_GENE_PARAMETERS.index(param_name)
                genome.unlocked_mask[idx] = True
                genome.vector[idx] = value
            except ValueError:
                logger.warning(f"跳过未知参数: {param_name}")
        
        return genome
    
    def __repr__(self) -> str:
        """字符串表示"""
        unlocked_count = self.get_unlocked_count()
        unlocked_params = self.get_unlocked_params()
        param_preview = ", ".join(unlocked_params[:5])
        if len(unlocked_params) > 5:
            param_preview += ", ..."
        
        return (f"GenomeVector(unlocked={unlocked_count}/50, "
                f"params=[{param_preview}])")


# ==================== 基因多样性计算 ====================

def compute_genome_diversity(genomes: List[GenomeVector]) -> float:
    """
    计算基因组多样性（使用方差）
    
    Args:
        genomes: GenomeVector列表
    
    Returns:
        float: 多样性得分 (0-1)
    
    Examples:
        >>> genomes = [GenomeVector.create_genesis() for _ in range(10)]
        >>> diversity = compute_genome_diversity(genomes)
        >>> print(f"基因多样性: {diversity:.2f}")
    """
    if len(genomes) < 2:
        return 0.0
    
    # 收集所有已解锁参数的值
    param_values = {}
    for genome in genomes:
        for i in range(50):
            if genome.unlocked_mask[i]:
                if i not in param_values:
                    param_values[i] = []
                param_values[i].append(genome.vector[i])
    
    if not param_values:
        return 0.0
    
    # 计算每个参数的方差
    variances = []
    for values in param_values.values():
        if len(values) > 1:
            var = np.var(values)
            variances.append(var)
    
    if not variances:
        return 0.0
    
    # 平均方差作为多样性指标（归一化到0-1）
    avg_variance = np.mean(variances)
    diversity = min(1.0, avg_variance / 0.25 * 2)  # 0.25是均匀分布的最大方差
    
    return float(diversity)

