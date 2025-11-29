"""
Strategy - 策略模块

职责: 根据基因和市场特征计算交易决策
"""

from typing import Dict, Tuple
from .gene import Gene


class Strategy:
    """策略 - 纯计算类"""
    
    def __init__(self, gene: Gene, config: Dict):
        """
        Args:
            gene: 基因
            config: 策略配置
        """
        self.gene = gene
        self.config = config
    
    def calculate_position(self, market_features: Dict[str, float]) -> Tuple[float, float]:
        """
        计算目标仓位
        
        Args:
            market_features: 市场特征
        
        Returns:
            (long_ratio, short_ratio) 多头比例和空头比例
        """
        # 1. 计算交易信号
        signal = self.gene.calculate_signal(market_features)
        
        # 2. 根据信号计算仓位
        long_ratio = 0.0
        short_ratio = 0.0
        
        if signal > self.config['long_threshold']:
            # 做多信号
            # 信号越强，仓位越大
            strength = (signal - self.config['long_threshold']) / (1.0 - self.config['long_threshold'])
            long_ratio = strength * self.config['max_position']
        
        elif signal < self.config['short_threshold']:
            # 做空信号
            strength = (self.config['short_threshold'] - signal) / (1.0 + self.config['short_threshold'])
            short_ratio = strength * self.config['max_position']
        
        # 3. 限制总杠杆
        total_leverage = long_ratio + short_ratio
        if total_leverage > self.config['max_leverage']:
            scale = self.config['max_leverage'] / total_leverage
            long_ratio *= scale
            short_ratio *= scale
        
        return long_ratio, short_ratio
    
    def calculate_trade_value(self, 
                             current_long: float, 
                             current_short: float,
                             target_long: float,
                             target_short: float,
                             capital: float) -> float:
        """
        计算交易金额（用于手续费计算）
        
        Args:
            current_long: 当前多头比例
            current_short: 当前空头比例
            target_long: 目标多头比例
            target_short: 目标空头比例
            capital: 资金
        
        Returns:
            交易金额（绝对值）
        """
        long_change = abs(target_long - current_long)
        short_change = abs(target_short - current_short)
        total_change = long_change + short_change
        
        return total_change * capital
    
    def __repr__(self) -> str:
        return f"Strategy(gene={self.gene.generate_species_name()})"
