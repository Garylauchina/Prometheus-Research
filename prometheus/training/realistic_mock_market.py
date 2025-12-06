"""
RealisticMockMarket - 基于真实统计的市场模拟器

基于OKX历史数据的统计特征，生成逼真的市场价格。

核心特征：
- 厚尾分布（峰度6.5）
- 波动率聚集（自相关0.98）
- 极端事件（频率1.87%）
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class MarketState:
    """市场状态"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    
class RealisticMockMarket:
    """
    基于真实统计的市场模拟器
    
    特性：
    1. 厚尾分布（使用Student-t分布）
    2. 波动率聚集（GARCH效应）
    3. 极端事件模拟
    4. 趋势持续性
    """
    
    def __init__(
        self,
        initial_price: float = 50000.0,
        stats_file: str = "data/okx/market_statistics.json",
        seed: Optional[int] = None
    ):
        """
        初始化
        
        Args:
            initial_price: 初始价格
            stats_file: 统计文件路径
            seed: 随机种子
        """
        self.current_price = initial_price
        self.timestamp = 0
        
        if seed is not None:
            np.random.seed(seed)
        
        # 加载统计特征
        self._load_statistics(stats_file)
        
        # GARCH状态
        self.current_volatility = self.base_volatility
        
        # 历史记录
        self.price_history: List[MarketState] = []
        
    def _load_statistics(self, stats_file: str):
        """加载统计特征"""
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            # 收益率统计
            self.mean_return = stats['returns']['mean']
            self.base_volatility = stats['returns']['std']
            self.skewness = stats['returns']['skew']
            self.kurtosis = stats['returns']['kurtosis']
            
            # 波动率聚集参数
            self.vol_persistence = stats['volatility_clustering'][0]['correlation']
            
            # 极端事件
            self.extreme_freq = stats['extreme_events']['frequency']
            self.extreme_mean_size = stats['extreme_events']['mean_size']
            
            # 趋势持续
            self.mean_trend_length = stats['trend_persistence']['mean_run_length']
            
            print(f"✅ 加载统计特征成功")
            print(f"   波动率: {self.base_volatility*100:.2f}%")
            print(f"   峰度: {self.kurtosis:.2f}（厚尾）")
            print(f"   波动聚集: {self.vol_persistence:.4f}")
            
        except FileNotFoundError:
            print(f"⚠️  统计文件未找到，使用默认值")
            self.mean_return = 0.0002
            self.base_volatility = 0.01
            self.skewness = 0.0
            self.kurtosis = 6.0  # 厚尾
            self.vol_persistence = 0.9
            self.extreme_freq = 0.02
            self.extreme_mean_size = 0.05
            self.mean_trend_length = 3.0
    
    def _generate_return(self) -> float:
        """
        生成逼真的收益率
        
        使用Student-t分布模拟厚尾
        """
        # 1. 更新波动率（GARCH效应）
        # σ_t = α * σ_{t-1} + (1-α) * base_σ
        alpha = self.vol_persistence
        self.current_volatility = (
            alpha * self.current_volatility +
            (1 - alpha) * self.base_volatility
        )
        
        # 2. 生成收益率
        # 使用Student-t分布（自由度由峰度推算）
        df = 4 + 6 / (self.kurtosis - 3) if self.kurtosis > 3 else 5
        
        # Student-t分布
        t_sample = np.random.standard_t(df)
        
        # 标准化并缩放
        return_sample = t_sample * self.current_volatility + self.mean_return
        
        # 3. 偶尔插入极端事件
        if np.random.rand() < self.extreme_freq:
            # 极端事件：大幅波动
            extreme_sign = np.random.choice([-1, 1])
            extreme_size = np.random.exponential(self.extreme_mean_size)
            return_sample = extreme_sign * extreme_size
            
            # 极端事件后波动率飙升
            self.current_volatility *= 2.0
        
        return return_sample
    
    def step(self) -> MarketState:
        """
        模拟一个时间步
        
        Returns:
            MarketState: 当前市场状态
        """
        # 生成收益率
        ret = self._generate_return()
        
        # 更新价格
        open_price = self.current_price
        close_price = self.current_price * (1 + ret)
        
        # 生成高低价（简化版）
        volatility_factor = abs(ret) + self.current_volatility * 0.5
        high_price = max(open_price, close_price) * (1 + volatility_factor)
        low_price = min(open_price, close_price) * (1 - volatility_factor)
        
        # 生成成交量（简化版）
        volume = np.random.lognormal(10, 1) * (1 + abs(ret) * 10)
        
        # 创建市场状态
        state = MarketState(
            timestamp=self.timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume
        )
        
        # 更新状态
        self.current_price = close_price
        self.timestamp += 1
        self.price_history.append(state)
        
        return state
    
    def generate_sequence(self, length: int) -> List[MarketState]:
        """
        生成一段市场序列
        
        Args:
            length: 序列长度
            
        Returns:
            List[MarketState]: 市场状态序列
        """
        sequence = []
        for _ in range(length):
            state = self.step()
            sequence.append(state)
        return sequence
    
    def reset(self, initial_price: Optional[float] = None):
        """重置市场"""
        if initial_price is not None:
            self.current_price = initial_price
        self.timestamp = 0
        self.current_volatility = self.base_volatility
        self.price_history = []
    
    def get_statistics(self) -> Dict:
        """获取生成数据的统计信息"""
        if not self.price_history:
            return {}
        
        prices = [s.close for s in self.price_history]
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
        ]
        
        return {
            'count': len(self.price_history),
            'price_mean': np.mean(prices),
            'price_std': np.std(prices),
            'return_mean': np.mean(returns),
            'return_std': np.std(returns),
            'return_skew': float(np.mean([(r - np.mean(returns))**3 for r in returns]) / (np.std(returns)**3)),
            'return_kurtosis': float(np.mean([(r - np.mean(returns))**4 for r in returns]) / (np.std(returns)**4)),
        }


class RegimeBasedMockMarket(RealisticMockMarket):
    """
    基于Regime的市场模拟器
    
    可以模拟特定的市场regime：
    - bull: 牛市
    - bear: 熊市  
    - volatile: 高波动
    - sideways: 盘整
    """
    
    def __init__(
        self,
        regime: str = 'bull',
        initial_price: float = 50000.0,
        stats_file: str = "data/okx/market_statistics.json",
        seed: Optional[int] = None
    ):
        """
        初始化
        
        Args:
            regime: 市场regime类型
            initial_price: 初始价格
            stats_file: 统计文件路径
            seed: 随机种子
        """
        super().__init__(initial_price, stats_file, seed)
        self.regime = regime
        self._adjust_for_regime()
    
    def _adjust_for_regime(self):
        """根据regime调整参数"""
        if self.regime == 'bull':
            # 牛市：正向漂移
            self.mean_return = abs(self.mean_return) + 0.001
            self.current_volatility = self.base_volatility * 0.8
            
        elif self.regime == 'bear':
            # 熊市：负向漂移
            self.mean_return = -abs(self.mean_return) - 0.001
            self.current_volatility = self.base_volatility * 1.2
            
        elif self.regime == 'volatile':
            # 高波动：波动率翻倍
            self.mean_return = 0.0
            self.current_volatility = self.base_volatility * 2.0
            self.extreme_freq *= 2.0
            
        elif self.regime == 'sideways':
            # 盘整：低波动
            self.mean_return = 0.0
            self.current_volatility = self.base_volatility * 0.5
            self.extreme_freq *= 0.5
            
        print(f"✅ Regime: {self.regime}")
        print(f"   均值: {self.mean_return*100:.4f}%")
        print(f"   波动率: {self.current_volatility*100:.2f}%")


# 便捷函数
def create_bull_market(initial_price: float = 50000.0, seed: Optional[int] = None) -> RegimeBasedMockMarket:
    """创建牛市"""
    return RegimeBasedMockMarket('bull', initial_price, seed=seed)


def create_bear_market(initial_price: float = 50000.0, seed: Optional[int] = None) -> RegimeBasedMockMarket:
    """创建熊市"""
    return RegimeBasedMockMarket('bear', initial_price, seed=seed)


def create_volatile_market(initial_price: float = 50000.0, seed: Optional[int] = None) -> RegimeBasedMockMarket:
    """创建高波动市场"""
    return RegimeBasedMockMarket('volatile', initial_price, seed=seed)


def create_sideways_market(initial_price: float = 50000.0, seed: Optional[int] = None) -> RegimeBasedMockMarket:
    """创建盘整市场"""
    return RegimeBasedMockMarket('sideways', initial_price, seed=seed)

