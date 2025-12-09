"""
StrategyParams - AlphaZero式纯理性策略参数
================================================

设计理念：
1. 移除所有情绪化本能（fear_of_death, despair, greed等）
2. 改为客观的"策略参数"
3. 所有决策基于理性评估
4. 完全可进化

核心原则：
- 只保留"与盈利直接相关"的参数
- 所有参数都是"可观测、可量化"的
- 没有情绪，只有策略选择
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyParams:
    """
    策略参数 - AlphaZero式极简设计
    
    7个核心策略参数，全部可进化：
    1. position_size_base: 基础仓位比例（0-1）
    2. holding_preference: 持仓时长偏好（0-1）
    3. directional_bias: 方向偏好（0-1）
    4. stop_loss_threshold: 止损阈值（0-1）
    5. take_profit_threshold: 止盈阈值（0-1）
    6. trend_following_strength: 趋势跟踪强度（0-1）
    7. leverage_preference: 杠杆偏好（0-1，映射到1-100x）
    """
    
    # ========== 核心策略参数（6个） ==========
    
    position_size_base: float = 0.5
    # 基础仓位比例（0-1）
    # 0.1: 保守型（10%资金）
    # 0.5: 平衡型（50%资金）
    # 0.9: 激进型（90%资金）
    
    holding_preference: float = 0.5
    # 持仓时长偏好（0-1）
    # 0: 短线（1-5个周期）
    # 0.5: 中线（5-20个周期）
    # 1: 长线（20+个周期）
    
    directional_bias: float = 0.5
    # 方向偏好（0-1）
    # 0: 偏好做多
    # 0.5: 双向（buy + short）
    # 1: 偏好做空
    
    stop_loss_threshold: float = 0.15
    # 止损阈值（0-1）
    # 0.05: 紧止损（亏损5%止损）
    # 0.2: 松止损（亏损20%止损）
    # 1.0: 不止损（死扛）
    
    take_profit_threshold: float = 0.25
    # 止盈阈值（0-1）
    # 0.05: 快止盈（盈利5%就跑）
    # 0.3: 慢止盈（盈利30%再跑）
    # 1.0: 永不止盈（持有到底）
    
    trend_following_strength: float = 0.5
    # 趋势跟踪强度（0-1）
    # 0: 逆势（均值回归）
    # 0.5: 混合
    # 1: 顺势（趋势追踪）
    
    leverage_preference: float = 0.03  # ✨ 新增：杠杆偏好（默认3x）
    # 杠杆偏好（0-1，映射到1-100x）
    # 0.00: 极保守（1x，无杠杆）
    # 0.03: 保守（3x）
    # 0.10: 平衡（10x）
    # 0.50: 激进（50x）
    # 1.00: 极限（100x，高风险！）
    # 映射公式：leverage = 1 + leverage_preference * 99
    
    # ========== 元数据 ==========
    generation: int = 0
    parent_params: Optional[Tuple] = None
    
    def __post_init__(self):
        """确保所有参数在[0, 1]范围内"""
        self.position_size_base = np.clip(self.position_size_base, 0, 1)
        self.holding_preference = np.clip(self.holding_preference, 0, 1)
        self.directional_bias = np.clip(self.directional_bias, 0, 1)
        self.stop_loss_threshold = np.clip(self.stop_loss_threshold, 0, 1)
        self.take_profit_threshold = np.clip(self.take_profit_threshold, 0, 1)
        self.trend_following_strength = np.clip(self.trend_following_strength, 0, 1)
        self.leverage_preference = np.clip(self.leverage_preference, 0, 1)
    
    # ========== 创世方法 ==========
    @classmethod
    def create_genesis(cls) -> 'StrategyParams':
        """
        创建创世策略参数
        
        使用Beta(2, 2)分布，集中在0.5附近但有足够多样性
        """
        return cls(
            position_size_base=np.random.beta(2, 2),
            holding_preference=np.random.beta(2, 2),
            directional_bias=np.random.beta(2, 2),
            stop_loss_threshold=np.random.beta(2, 2),
            take_profit_threshold=np.random.beta(2, 2),
            trend_following_strength=np.random.beta(2, 2),
            leverage_preference=np.random.beta(2, 5) * 0.2,  # ✨ 偏向低杠杆（1-20x）
            generation=0
        )
    
    # ========== 遗传方法 ==========
    @classmethod
    def crossover(cls, parent1: 'StrategyParams', parent2: 'StrategyParams') -> 'StrategyParams':
        """
        交叉遗传（简单平均）
        """
        return cls(
            position_size_base=(parent1.position_size_base + parent2.position_size_base) / 2,
            holding_preference=(parent1.holding_preference + parent2.holding_preference) / 2,
            directional_bias=(parent1.directional_bias + parent2.directional_bias) / 2,
            stop_loss_threshold=(parent1.stop_loss_threshold + parent2.stop_loss_threshold) / 2,
            take_profit_threshold=(parent1.take_profit_threshold + parent2.take_profit_threshold) / 2,
            trend_following_strength=(parent1.trend_following_strength + parent2.trend_following_strength) / 2,
            leverage_preference=(parent1.leverage_preference + parent2.leverage_preference) / 2,  # ✨ 杠杆遗传
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_params=(parent1, parent2)
        )
    
    def mutate(self, mutation_rate: float = 0.1, diversity_boost: float = 1.0) -> 'StrategyParams':
        """
        ✅ Stage 1.1: 增强突变机制（可控多样性）
        
        突变策略：
        1. 基础突变：高斯噪声（mutation_rate）
        2. 多样性增强：diversity_boost（1.0=正常，2.0=2倍幅度）
        3. 关键参数（directional_bias）获得更大突变幅度
        
        Args:
            mutation_rate: 基础突变率（默认0.1）
            diversity_boost: 多样性增强系数（1.0=正常，2.0=双倍）
        
        Returns:
            新的突变StrategyParams
        """
        # ✅ Stage 1.1: 关键参数（directional_bias）获得1.5倍突变幅度
        # 原因：directional_bias决定多空方向，是多样性的核心
        directional_mutation_rate = mutation_rate * 1.5 * diversity_boost
        standard_mutation_rate = mutation_rate * diversity_boost
        
        mutated = StrategyParams(
            position_size_base=self.position_size_base + np.random.normal(0, standard_mutation_rate),
            holding_preference=self.holding_preference + np.random.normal(0, standard_mutation_rate),
            directional_bias=self.directional_bias + np.random.normal(0, directional_mutation_rate),  # ✅ 增强
            stop_loss_threshold=self.stop_loss_threshold + np.random.normal(0, standard_mutation_rate),
            take_profit_threshold=self.take_profit_threshold + np.random.normal(0, standard_mutation_rate),
            trend_following_strength=self.trend_following_strength + np.random.normal(0, standard_mutation_rate),
            leverage_preference=self.leverage_preference + np.random.normal(0, standard_mutation_rate),
            generation=self.generation,
            parent_params=self.parent_params
        )
        return mutated
    
    # ========== 工具方法 ==========
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'position_size_base': self.position_size_base,
            'holding_preference': self.holding_preference,
            'directional_bias': self.directional_bias,
            'stop_loss_threshold': self.stop_loss_threshold,
            'take_profit_threshold': self.take_profit_threshold,
            'trend_following_strength': self.trend_following_strength,
            'generation': self.generation,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StrategyParams':
        """
        从字典创建StrategyParams
        
        ✨ v6.0: 用于智能创世，从ExperienceDB加载历史优秀策略参数
        """
        return cls(
            position_size_base=data.get('position_size_base', 0.3),
            holding_preference=data.get('holding_preference', 0.5),
            directional_bias=data.get('directional_bias', 0.5),
            stop_loss_threshold=data.get('stop_loss_threshold', 0.05),
            take_profit_threshold=data.get('take_profit_threshold', 0.1),
            trend_following_strength=data.get('trend_following_strength', 0.5),
            generation=data.get('generation', 0)
        )
    
    def get_display_string(self) -> str:
        """获取显示字符串"""
        strategy_type = self._get_strategy_type()
        position_type = self._get_position_type()
        
        return f"{strategy_type}|{position_type}"
    
    def _get_strategy_type(self) -> str:
        """获取策略类型"""
        if self.trend_following_strength > 0.7:
            return "趋势追踪"
        elif self.trend_following_strength < 0.3:
            return "均值回归"
        else:
            return "混合策略"
    
    def _get_position_type(self) -> str:
        """获取仓位类型"""
        if self.position_size_base > 0.7:
            return "激进型"
        elif self.position_size_base < 0.3:
            return "保守型"
        else:
            return "平衡型"
    
    def __repr__(self) -> str:
        return f"StrategyParams({self.get_display_string()})"

