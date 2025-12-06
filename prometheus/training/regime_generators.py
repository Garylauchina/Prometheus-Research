"""
Market Regime生成器

模拟不同的市场环境，用于训练Agent
"""

import numpy as np
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class RegimeGenerator(ABC):
    """
    Market Regime生成器基类
    """
    
    def __init__(self, name: str, start_price: float = 50000):
        """
        初始化
        
        Args:
            name: Regime名称
            start_price: 起始价格
        """
        self.name = name
        self.start_price = start_price
        self.current_price = start_price
        self.prices = [start_price]
        self.day = 0
    
    @abstractmethod
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        pass
    
    def reset(self, start_price: float = None):
        """重置生成器"""
        if start_price is not None:
            self.start_price = start_price
        self.current_price = self.start_price
        self.prices = [self.start_price]
        self.day = 0
    
    def generate_series(self, days: int) -> np.ndarray:
        """
        生成价格序列
        
        Args:
            days: 天数
            
        Returns:
            价格序列
        """
        self.reset()
        
        for _ in range(days - 1):
            next_price = self.generate_next_price()
            self.prices.append(next_price)
            self.current_price = next_price
            self.day += 1
        
        return np.array(self.prices)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if len(self.prices) < 2:
            return {}
        
        prices = np.array(self.prices)
        returns = np.diff(prices) / prices[:-1]
        
        return {
            'regime': self.name,
            'start_price': self.start_price,
            'end_price': self.current_price,
            'total_return': (self.current_price / self.start_price - 1) * 100,
            'avg_daily_return': np.mean(returns) * 100,
            'volatility': np.std(returns) * 100,
            'max_price': np.max(prices),
            'min_price': np.min(prices),
            'days': len(self.prices)
        }


class BullMarketGenerator(RegimeGenerator):
    """
    牛市生成器
    
    特征：
    - 持续上涨趋势
    - 低到中等波动
    - 偶尔回调
    """
    
    def __init__(
        self,
        start_price: float = 50000,
        drift: float = 0.002,  # 每天+0.2%
        volatility: float = 0.02,  # 2%波动
        pullback_prob: float = 0.1  # 10%概率回调
    ):
        super().__init__("牛市", start_price)
        self.drift = drift
        self.volatility = volatility
        self.pullback_prob = pullback_prob
    
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        # 偶尔回调
        if np.random.rand() < self.pullback_prob:
            current_drift = -self.drift * 2  # 回调幅度是上涨的2倍
        else:
            current_drift = self.drift
        
        # 几何布朗运动
        random_return = np.random.normal(current_drift, self.volatility)
        new_price = self.current_price * (1 + random_return)
        
        # 限制价格范围
        new_price = max(new_price, self.start_price * 0.5)
        new_price = min(new_price, self.start_price * 5)
        
        return new_price


class BearMarketGenerator(RegimeGenerator):
    """
    熊市生成器
    
    特征：
    - 持续下跌趋势
    - 高波动
    - 偶尔反弹
    """
    
    def __init__(
        self,
        start_price: float = 50000,
        drift: float = -0.003,  # 每天-0.3%
        volatility: float = 0.04,  # 4%波动
        bounce_prob: float = 0.15  # 15%概率反弹
    ):
        super().__init__("熊市", start_price)
        self.drift = drift
        self.volatility = volatility
        self.bounce_prob = bounce_prob
    
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        # 偶尔反弹
        if np.random.rand() < self.bounce_prob:
            current_drift = -self.drift * 1.5  # 反弹
        else:
            current_drift = self.drift
        
        random_return = np.random.normal(current_drift, self.volatility)
        new_price = self.current_price * (1 + random_return)
        
        # 限制价格范围
        new_price = max(new_price, self.start_price * 0.2)
        new_price = min(new_price, self.start_price * 2)
        
        return new_price


class VolatilityGenerator(RegimeGenerator):
    """
    高波震荡生成器
    
    特征：
    - 无明确趋势
    - 高波动
    - 快速波动
    """
    
    def __init__(
        self,
        start_price: float = 50000,
        volatility: float = 0.06,  # 6%波动
        momentum: float = 0.3  # 30%动量延续
    ):
        super().__init__("高波震荡", start_price)
        self.volatility = volatility
        self.momentum = momentum
        self.last_direction = 0  # -1下跌, 0中性, 1上涨
    
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        # 动量延续
        if np.random.rand() < self.momentum and self.last_direction != 0:
            drift = self.last_direction * 0.01
        else:
            drift = 0
        
        random_return = np.random.normal(drift, self.volatility)
        new_price = self.current_price * (1 + random_return)
        
        # 记录方向
        if random_return > 0.02:
            self.last_direction = 1
        elif random_return < -0.02:
            self.last_direction = -1
        else:
            self.last_direction = 0
        
        # 限制价格范围
        new_price = max(new_price, self.start_price * 0.5)
        new_price = min(new_price, self.start_price * 2)
        
        return new_price


class SidewaysGenerator(RegimeGenerator):
    """
    低波盘整生成器
    
    特征：
    - 无明确趋势
    - 低波动
    - 围绕均值震荡
    """
    
    def __init__(
        self,
        start_price: float = 50000,
        volatility: float = 0.01,  # 1%波动
        mean_reversion: float = 0.05  # 5%均值回归力度
    ):
        super().__init__("低波盘整", start_price)
        self.volatility = volatility
        self.mean_reversion = mean_reversion
        self.mean_price = start_price
    
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        # 均值回归
        deviation = (self.current_price - self.mean_price) / self.mean_price
        drift = -deviation * self.mean_reversion
        
        random_return = np.random.normal(drift, self.volatility)
        new_price = self.current_price * (1 + random_return)
        
        # 限制价格范围
        new_price = max(new_price, self.mean_price * 0.8)
        new_price = min(new_price, self.mean_price * 1.2)
        
        return new_price


class MultiRegimeGenerator:
    """
    多Regime生成器
    
    可以在不同regime之间切换
    """
    
    def __init__(
        self,
        regimes: List[RegimeGenerator],
        switch_probability: float = 0.1  # 每天10%概率切换regime
    ):
        """
        初始化
        
        Args:
            regimes: Regime生成器列表
            switch_probability: 切换概率
        """
        self.regimes = regimes
        self.switch_probability = switch_probability
        self.current_regime_idx = 0
        self.current_regime = regimes[0]
        self.regime_history = []
        self.prices = []
        self.day = 0
    
    def generate_next_price(self) -> float:
        """生成下一个价格"""
        # 随机切换regime
        if np.random.rand() < self.switch_probability and self.day > 0:
            old_idx = self.current_regime_idx
            # 随机选择新regime（不能是当前regime）
            available_indices = [i for i in range(len(self.regimes)) if i != old_idx]
            self.current_regime_idx = np.random.choice(available_indices)
            
            # 切换到新regime
            self.current_regime = self.regimes[self.current_regime_idx]
            self.current_regime.current_price = self.prices[-1] if self.prices else self.current_regime.start_price
            
            logger.debug(f"Day {self.day}: Regime切换 {self.regimes[old_idx].name} → {self.current_regime.name}")
        
        # 生成价格
        next_price = self.current_regime.generate_next_price()
        self.prices.append(next_price)
        self.regime_history.append(self.current_regime_idx)
        self.day += 1
        
        return next_price
    
    def generate_series(self, days: int, start_price: float = 50000) -> Tuple[np.ndarray, List[int]]:
        """
        生成多regime价格序列
        
        Args:
            days: 天数
            start_price: 起始价格
            
        Returns:
            (价格序列, regime历史)
        """
        # 重置
        self.prices = [start_price]
        self.regime_history = [0]
        self.day = 0
        self.current_regime_idx = 0
        self.current_regime = self.regimes[0]
        self.current_regime.current_price = start_price
        
        # 生成
        for _ in range(days - 1):
            self.generate_next_price()
        
        return np.array(self.prices), self.regime_history
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if len(self.prices) < 2:
            return {}
        
        # 计算每个regime的占比
        regime_counts = {}
        for idx in self.regime_history:
            name = self.regimes[idx].name
            regime_counts[name] = regime_counts.get(name, 0) + 1
        
        regime_distribution = {
            name: count / len(self.regime_history) * 100
            for name, count in regime_counts.items()
        }
        
        # 计算切换次数
        switches = sum(1 for i in range(1, len(self.regime_history))
                      if self.regime_history[i] != self.regime_history[i-1])
        
        prices = np.array(self.prices)
        returns = np.diff(prices) / prices[:-1]
        
        return {
            'total_days': len(self.prices),
            'total_return': (prices[-1] / prices[0] - 1) * 100,
            'avg_daily_return': np.mean(returns) * 100,
            'volatility': np.std(returns) * 100,
            'max_price': np.max(prices),
            'min_price': np.min(prices),
            'regime_switches': switches,
            'regime_distribution': regime_distribution
        }


def create_regime_generator(regime_type: str, **kwargs) -> RegimeGenerator:
    """
    工厂函数：创建regime生成器
    
    Args:
        regime_type: 'bull', 'bear', 'volatile', 'sideways'
        **kwargs: 传递给生成器的参数
        
    Returns:
        RegimeGenerator实例
    """
    generators = {
        'bull': BullMarketGenerator,
        'bear': BearMarketGenerator,
        'volatile': VolatilityGenerator,
        'sideways': SidewaysGenerator
    }
    
    if regime_type not in generators:
        raise ValueError(f"Unknown regime type: {regime_type}")
    
    return generators[regime_type](**kwargs)


def create_standard_multi_regime() -> MultiRegimeGenerator:
    """
    创建标准的多regime生成器
    
    包含4种基本regime
    """
    regimes = [
        BullMarketGenerator(drift=0.002, volatility=0.02),
        BearMarketGenerator(drift=-0.003, volatility=0.04),
        VolatilityGenerator(volatility=0.06),
        SidewaysGenerator(volatility=0.01)
    ]
    
    return MultiRegimeGenerator(regimes, switch_probability=0.05)  # 5%切换概率

