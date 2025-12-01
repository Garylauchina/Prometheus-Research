"""
Gene - 基因模块

职责: 存储和计算市场特征偏好
"""

import random
from typing import Dict, List
import json


# 市场特征定义
MARKET_FEATURES = {
    'trend_direction': ['strong_bull', 'bull', 'weak_bull', 'sideways', 'weak_bear', 'bear', 'strong_bear'],
    'volatility': ['ultra_low_vol', 'low_vol', 'normal_vol', 'high_vol', 'extreme_high_vol'],
    'sentiment': ['extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed'],
    'volume': ['volume_drying_up', 'low_volume', 'normal_volume', 'volume_surge'],
    'price_pattern': ['breakout', 'breakdown', 'pullback', 'gap_up', 'gap_down', 'ranging', 'consolidation'],
    'trend_strength': ['very_strong_trend', 'strong_trend', 'weak_trend', 'no_trend', 'choppy'],
    'support_resistance': ['near_support', 'near_resistance', 'breaking_support', 'breaking_resistance', 'middle_range']
}


class Gene:
    """基因 - 纯数据类"""
    
    def __init__(self, preferences: Dict[str, float]):
        """
        Args:
            preferences: 市场特征偏好字典
            例如: {
                'extreme_fear': 0.8,
                'high_vol': 0.7,
                ...
            }
        """
        self.preferences = preferences
        self.species_name = None  # 物种名称（延迟生成）
    
    def calculate_signal(self, market_features: Dict[str, float]) -> float:
        """
        计算交易信号强度
        
        Args:
            market_features: 当前市场特征 {feature_name: value}
        
        Returns:
            信号强度 (-1.0 到 +1.0)
        """
        if not market_features:
            return 0.0
        
        # 计算加权得分
        total_score = 0.0
        total_weight = 0.0
        
        for feature, value in market_features.items():
            if feature in self.preferences:
                preference = self.preferences[feature]
                # 得分 = 特征值 × 偏好值
                score = value * preference
                total_score += score
                total_weight += abs(value)
        
        if total_weight == 0:
            return 0.0
        
        # 归一化到 [-1, 1]
        signal = total_score / total_weight
        signal = max(-1.0, min(1.0, signal))
        
        return signal
    
    def mutate(self, mutation_rate: float = 0.1) -> 'Gene':
        """
        基因变异
        
        Args:
            mutation_rate: 变异率 (0-1)
        
        Returns:
            新的变异基因
        """
        new_preferences = {}
        
        for feature, value in self.preferences.items():
            if random.random() < mutation_rate:
                # 变异: 在原值基础上加上随机扰动
                mutation = random.gauss(0, 0.2)
                new_value = value + mutation
                # 限制在 [0, 1] 范围内
                new_value = max(0.0, min(1.0, new_value))
                new_preferences[feature] = new_value
            else:
                new_preferences[feature] = value
        
        return Gene(new_preferences)
    
    def get_top_preferences(self, n: int = 3) -> List[tuple]:
        """
        获取偏好最高的N个特征
        
        Args:
            n: 返回数量
        
        Returns:
            [(feature, preference), ...] 按偏好值降序
        """
        sorted_prefs = sorted(self.preferences.items(), key=lambda x: x[1], reverse=True)
        return sorted_prefs[:n]
    
    def generate_species_name(self) -> str:
        """
        根据基因生成物种名称
        
        Returns:
            物种名称，例如: "volatility_hunter_extreme_fear_breakout"
        """
        if self.species_name:
            return self.species_name
        
        # 获取前3个最强偏好
        top_prefs = self.get_top_preferences(3)
        
        # 生成名称
        name_parts = []
        for feature, value in top_prefs:
            if value > 0.6:  # 只包含强偏好
                name_parts.append(feature)
        
        if not name_parts:
            name_parts = ['neutral']
        
        self.species_name = '_'.join(name_parts)
        return self.species_name
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'preferences': self.preferences.copy(),
            'species_name': self.species_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Gene':
        """从字典反序列化"""
        gene = cls(data['preferences'])
        gene.species_name = data.get('species_name')
        return gene
    
    @classmethod
    def random(cls) -> 'Gene':
        """生成随机基因"""
        preferences = {}
        
        # 为每个特征生成随机偏好值
        for category, features in MARKET_FEATURES.items():
            for feature in features:
                # 使用beta分布生成偏好值，集中在0.3-0.7之间
                preferences[feature] = random.betavariate(2, 2)
        
        return cls(preferences)
    
    def similarity(self, other: 'Gene') -> float:
        """
        计算与另一个基因的相似度
        
        Args:
            other: 另一个基因
        
        Returns:
            相似度 (0-1)
        """
        total_diff = 0.0
        total_count = 0
        
        for feature in self.preferences:
            if feature in other.preferences:
                diff = abs(self.preferences[feature] - other.preferences[feature])
                total_diff += diff
                total_count += 1
        
        if total_count == 0:
            return 0.0
        
        avg_diff = total_diff / total_count
        similarity = 1.0 - avg_diff
        
        return similarity
    
    def __repr__(self) -> str:
        species = self.generate_species_name()
        top_prefs = self.get_top_preferences(3)
        prefs_str = ', '.join([f"{f}={v:.2f}" for f, v in top_prefs])
        return f"Gene(species={species}, top_prefs=[{prefs_str}])"
