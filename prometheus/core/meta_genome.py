"""
元基因组系统 (Meta-Genome System) - Prometheus v5.1
====================================================

元参数：控制Agent行为模式的高层参数，可遗传和进化

核心概念：
- 策略参数（Genome）：控制"如何分析市场"
- 元参数（MetaGenome）：控制"如何做决策"

Author: Prometheus Team
Version: 5.1
Date: 2025-12-04
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetaGenome:
    """
    元基因组 - 控制Agent的决策风格
    
    元参数类别：
    1. Daimon权重（6个）- 决定各个声音的影响力
    2. 行为特征（4个）- 学习速度、探索欲等
    3. 策略偏好（3个）- 对不同策略的偏好
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. Daimon权重（6个声音）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    daimon_instinct_weight: float = 1.0      # 本能声音（固定为1.0）
    daimon_experience_weight: float = 0.7    # 经验声音
    daimon_prophecy_weight: float = 0.6      # 预言声音
    daimon_strategy_weight: float = 0.5      # 策略声音
    daimon_genome_weight: float = 0.5        # 基因声音
    daimon_emotion_weight: float = 0.3       # 情绪声音
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. 行为特征（4个）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    learning_rate: float = 0.1               # 学习速度（0-1）
    exploration_rate: float = 0.2            # 探索欲（0-1）
    patience_multiplier: float = 1.0         # 耐心倍数（0.5-2.0）
    aggression: float = 0.5                  # 进攻性（0-1）
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. 策略偏好（3个主要策略）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    prefer_trend_following: float = 0.5      # 趋势跟随偏好
    prefer_mean_reversion: float = 0.3       # 均值回归偏好
    prefer_grid_trading: float = 0.2         # 网格交易偏好
    
    @classmethod
    def create_genesis(cls) -> 'MetaGenome':
        """
        创建创世元基因组（随机初始化）
        
        Returns:
            MetaGenome: 随机初始化的元基因组
        """
        return cls(
            # Daimon权重（instinct固定为1.0，其他随机）
            daimon_instinct_weight=1.0,  # 固定
            daimon_experience_weight=np.random.uniform(0.3, 1.0),
            daimon_prophecy_weight=np.random.uniform(0.3, 1.0),
            daimon_strategy_weight=np.random.uniform(0.3, 1.0),
            daimon_genome_weight=np.random.uniform(0.3, 1.0),
            daimon_emotion_weight=np.random.uniform(0.1, 0.5),
            
            # 行为特征
            learning_rate=np.random.uniform(0.05, 0.3),
            exploration_rate=np.random.uniform(0.1, 0.4),
            patience_multiplier=np.random.uniform(0.5, 2.0),
            aggression=np.random.uniform(0.2, 0.8),
            
            # 策略偏好（归一化到总和=1）
            prefer_trend_following=np.random.random(),
            prefer_mean_reversion=np.random.random(),
            prefer_grid_trading=np.random.random(),
        )
    
    def normalize_strategy_preferences(self):
        """归一化策略偏好，使总和=1"""
        total = (
            self.prefer_trend_following + 
            self.prefer_mean_reversion + 
            self.prefer_grid_trading
        )
        
        if total > 0:
            self.prefer_trend_following /= total
            self.prefer_mean_reversion /= total
            self.prefer_grid_trading /= total
    
    @classmethod
    def crossover(
        cls,
        parent1: 'MetaGenome',
        parent2: 'MetaGenome',
        crossover_rate: float = 0.5
    ) -> 'MetaGenome':
        """
        交叉繁殖（均匀交叉）
        
        每个参数有50%概率来自父母1，50%来自父母2
        
        Args:
            parent1: 父母1的元基因组
            parent2: 父母2的元基因组
            crossover_rate: 交叉率（默认0.5）
        
        Returns:
            MetaGenome: 子代元基因组
        """
        # 获取所有可遗传的字段（排除instinct权重，它固定为1.0）
        child_params = {}
        
        for key in parent1.__dataclass_fields__.keys():
            # instinct权重固定，不遗传
            if key == 'daimon_instinct_weight':
                child_params[key] = 1.0
                continue
            
            # 其他参数：随机选择父母之一
            if np.random.random() < crossover_rate:
                child_params[key] = getattr(parent1, key)
            else:
                child_params[key] = getattr(parent2, key)
        
        child = cls(**child_params)
        child.normalize_strategy_preferences()
        
        logger.debug("元基因组交叉繁殖完成")
        return child
    
    def mutate(self, mutation_rate: float = 0.1):
        """
        变异（随机调整参数）
        
        Args:
            mutation_rate: 变异概率（默认10%）
        """
        mutated_count = 0
        
        # Daimon权重变异
        for weight_name in [
            'daimon_experience_weight',
            'daimon_prophecy_weight',
            'daimon_strategy_weight',
            'daimon_genome_weight',
            'daimon_emotion_weight',
        ]:
            if np.random.random() < mutation_rate:
                current = getattr(self, weight_name)
                # 高斯变异 ± 0.1
                delta = np.random.normal(0, 0.1)
                new_value = np.clip(current + delta, 0.1, 1.0)
                setattr(self, weight_name, new_value)
                mutated_count += 1
        
        # 行为特征变异
        if np.random.random() < mutation_rate:
            self.learning_rate = np.clip(
                self.learning_rate + np.random.normal(0, 0.05),
                0.01, 0.5
            )
            mutated_count += 1
        
        if np.random.random() < mutation_rate:
            self.exploration_rate = np.clip(
                self.exploration_rate + np.random.normal(0, 0.1),
                0.0, 1.0
            )
            mutated_count += 1
        
        if np.random.random() < mutation_rate:
            self.patience_multiplier = np.clip(
                self.patience_multiplier + np.random.normal(0, 0.2),
                0.3, 3.0
            )
            mutated_count += 1
        
        if np.random.random() < mutation_rate:
            self.aggression = np.clip(
                self.aggression + np.random.normal(0, 0.1),
                0.0, 1.0
            )
            mutated_count += 1
        
        # 策略偏好变异
        if np.random.random() < mutation_rate:
            self.prefer_trend_following += np.random.normal(0, 0.1)
            self.prefer_mean_reversion += np.random.normal(0, 0.1)
            self.prefer_grid_trading += np.random.normal(0, 0.1)
            
            # 确保非负
            self.prefer_trend_following = max(0.01, self.prefer_trend_following)
            self.prefer_mean_reversion = max(0.01, self.prefer_mean_reversion)
            self.prefer_grid_trading = max(0.01, self.prefer_grid_trading)
            
            # 归一化
            self.normalize_strategy_preferences()
            mutated_count += 1
        
        if mutated_count > 0:
            logger.debug(f"元基因组变异: {mutated_count}个参数改变")
    
    def get_daimon_weights(self) -> Dict[str, float]:
        """
        获取Daimon权重配置
        
        Returns:
            Dict: 权重字典，可直接传给Daimon
        """
        return {
            'instinct': self.daimon_instinct_weight,
            'experience': self.daimon_experience_weight,
            'prophecy': self.daimon_prophecy_weight,
            'strategy': self.daimon_strategy_weight,
            'genome': self.daimon_genome_weight,
            'emotion': self.daimon_emotion_weight,
        }
    
    def get_strategy_preferences(self) -> Dict[str, float]:
        """
        获取策略偏好
        
        Returns:
            Dict: 策略偏好字典
        """
        return {
            'TrendFollowing': self.prefer_trend_following,
            'MeanReversion': self.prefer_mean_reversion,
            'GridTrading': self.prefer_grid_trading,
        }
    
    def describe_decision_style(self) -> str:
        """
        描述决策风格
        
        Returns:
            str: 风格描述
        """
        # 找出权重最高的2个声音（除了instinct）
        weights = {
            '经验': self.daimon_experience_weight,
            '预言': self.daimon_prophecy_weight,
            '策略': self.daimon_strategy_weight,
            '基因': self.daimon_genome_weight,
            '情绪': self.daimon_emotion_weight,
        }
        
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        top2 = [name for name, _ in sorted_weights[:2]]
        
        # 行为特征描述
        traits = []
        if self.learning_rate > 0.2:
            traits.append("善学")
        if self.exploration_rate > 0.3:
            traits.append("爱冒险")
        if self.patience_multiplier > 1.5:
            traits.append("极有耐心")
        elif self.patience_multiplier < 0.7:
            traits.append("急性子")
        if self.aggression > 0.7:
            traits.append("激进")
        elif self.aggression < 0.3:
            traits.append("保守")
        
        # 策略偏好描述
        strategy_pref = max(
            ('趋势型', self.prefer_trend_following),
            ('回归型', self.prefer_mean_reversion),
            ('网格型', self.prefer_grid_trading),
            key=lambda x: x[1]
        )[0]
        
        # 组合描述
        style = f"{strategy_pref}、重{'+'.join(top2)}"
        if traits:
            style += f"、{'+'.join(traits)}"
        
        return style
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'daimon_weights': self.get_daimon_weights(),
            'behavior_traits': {
                'learning_rate': self.learning_rate,
                'exploration_rate': self.exploration_rate,
                'patience_multiplier': self.patience_multiplier,
                'aggression': self.aggression,
            },
            'strategy_preferences': self.get_strategy_preferences(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MetaGenome':
        """从字典创建"""
        daimon = data.get('daimon_weights', {})
        behavior = data.get('behavior_traits', {})
        strategy = data.get('strategy_preferences', {})
        
        return cls(
            daimon_instinct_weight=daimon.get('instinct', 1.0),
            daimon_experience_weight=daimon.get('experience', 0.7),
            daimon_prophecy_weight=daimon.get('prophecy', 0.6),
            daimon_strategy_weight=daimon.get('strategy', 0.5),
            daimon_genome_weight=daimon.get('genome', 0.5),
            daimon_emotion_weight=daimon.get('emotion', 0.3),
            
            learning_rate=behavior.get('learning_rate', 0.1),
            exploration_rate=behavior.get('exploration_rate', 0.2),
            patience_multiplier=behavior.get('patience_multiplier', 1.0),
            aggression=behavior.get('aggression', 0.5),
            
            prefer_trend_following=strategy.get('TrendFollowing', 0.5),
            prefer_mean_reversion=strategy.get('MeanReversion', 0.3),
            prefer_grid_trading=strategy.get('GridTrading', 0.2),
        )


class MetaGenomeEvolution:
    """元基因组进化系统"""
    
    @staticmethod
    def crossover_and_mutate(
        parent1: MetaGenome,
        parent2: MetaGenome,
        crossover_rate: float = 0.5,
        mutation_rate: float = 0.1
    ) -> MetaGenome:
        """
        交叉 + 变异（一步完成）
        
        Args:
            parent1: 父母1
            parent2: 父母2
            crossover_rate: 交叉率
            mutation_rate: 变异率
        
        Returns:
            MetaGenome: 子代元基因组
        """
        # 1. 交叉
        child = MetaGenome.crossover(parent1, parent2, crossover_rate)
        
        # 2. 变异
        child.mutate(mutation_rate)
        
        return child
    
    @staticmethod
    def calculate_diversity(meta_genomes: list) -> float:
        """
        计算元基因组多样性
        
        Args:
            meta_genomes: MetaGenome列表
        
        Returns:
            float: 多样性分数（0-1）
        """
        if not meta_genomes:
            return 0.0
        
        # 提取所有Daimon权重为向量
        vectors = []
        for mg in meta_genomes:
            vec = [
                mg.daimon_experience_weight,
                mg.daimon_prophecy_weight,
                mg.daimon_strategy_weight,
                mg.daimon_genome_weight,
                mg.daimon_emotion_weight,
                mg.learning_rate,
                mg.exploration_rate,
                mg.patience_multiplier,
                mg.aggression,
            ]
            vectors.append(vec)
        
        # 计算方差（作为多样性指标）
        vectors = np.array(vectors)
        diversity = np.mean(np.var(vectors, axis=0))
        
        return diversity

