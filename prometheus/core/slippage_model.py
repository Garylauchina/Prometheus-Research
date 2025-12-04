"""
滑点模拟模型 - Prometheus v5.1
=================================

模拟真实市场中的滑点效应，让Agent在更真实的环境中进化。

滑点来源：
1. 市场流动性不足
2. 订单规模过大
3. 市场波动剧烈
4. 网络延迟

Author: Prometheus Team
Version: 5.1
Date: 2025-12-04
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"   # 市价单（滑点更大）
    LIMIT = "limit"     # 限价单（滑点更小）


@dataclass
class MarketCondition:
    """市场状况"""
    price: float                    # 当前价格
    volume: float                   # 当前成交量
    volatility: float = 0.02        # 波动率（默认2%）
    liquidity_depth: float = 1000000  # 流动性深度（USD）
    spread: float = 0.0001          # 买卖价差（默认0.01%）


@dataclass
class SlippageResult:
    """滑点计算结果"""
    expected_price: float      # 预期价格
    actual_price: float        # 实际成交价格
    slippage_rate: float       # 滑点率
    slippage_amount: float     # 滑点金额
    breakdown: Dict[str, float]  # 滑点来源分解


class SlippageModel:
    """
    滑点模型
    
    基于真实市场特征计算滑点：
    1. 流动性影响：订单越大相对于流动性，滑点越大
    2. 波动率影响：市场波动越大，滑点越大
    3. 价差影响：买卖价差越大，滑点越大
    4. 订单类型：市价单滑点大于限价单
    """
    
    def __init__(
        self,
        base_slippage: float = 0.0005,     # 基础滑点 0.05%
        liquidity_factor: float = 0.01,    # 流动性因子
        volatility_factor: float = 0.5,    # 波动率因子
        size_impact_exponent: float = 1.5, # 规模影响指数
        random_noise: float = 0.0002,      # 随机噪声 0.02%
    ):
        """
        初始化滑点模型
        
        Args:
            base_slippage: 基础滑点率
            liquidity_factor: 流动性影响系数
            volatility_factor: 波动率影响系数
            size_impact_exponent: 订单规模影响指数（>1表示非线性）
            random_noise: 随机噪声标准差
        """
        self.base_slippage = base_slippage
        self.liquidity_factor = liquidity_factor
        self.volatility_factor = volatility_factor
        self.size_impact_exponent = size_impact_exponent
        self.random_noise = random_noise
        
        logger.info(f"滑点模型已初始化 | 基础滑点={base_slippage:.4%}")
    
    def calculate_slippage(
        self,
        order_side: OrderSide,
        order_size_usd: float,
        order_type: OrderType,
        market_condition: MarketCondition
    ) -> SlippageResult:
        """
        计算滑点
        
        Args:
            order_side: 订单方向（买/卖）
            order_size_usd: 订单金额（USD）
            order_type: 订单类型（市价/限价）
            market_condition: 市场状况
        
        Returns:
            SlippageResult: 滑点计算结果
        """
        # 1. 基础滑点
        base = self.base_slippage
        
        # 2. 买卖价差影响（立即成交的成本）
        spread_impact = market_condition.spread / 2
        
        # 3. 流动性影响（订单规模 vs 市场深度）
        liquidity_ratio = order_size_usd / market_condition.liquidity_depth
        liquidity_impact = self.liquidity_factor * (
            liquidity_ratio ** self.size_impact_exponent
        )
        
        # 4. 波动率放大因子（波动率越高，基础滑点放大越多）
        volatility_multiplier = 1 + (
            self.volatility_factor * market_condition.volatility
        )
        
        # 5. 订单类型放大因子
        if order_type == OrderType.MARKET:
            order_type_multiplier = 1.5  # 市价单滑点更大
        else:
            order_type_multiplier = 0.3  # 限价单滑点较小（但不为0）
        
        # 6. 随机噪声（模拟不可预测因素）
        noise = np.random.normal(0, self.random_noise)
        
        # 7. 综合滑点率（基础+价差+流动性）× 波动率放大 × 订单类型放大 + 噪声
        base_slippage_component = base + spread_impact + liquidity_impact
        total_slippage_rate = (
            base_slippage_component * volatility_multiplier * order_type_multiplier
            + noise
        )
        
        # 确保滑点非负
        total_slippage_rate = max(total_slippage_rate, 0)
        
        # 8. 应用方向（买入价格上升，卖出价格下降）
        if order_side == OrderSide.BUY:
            actual_price = market_condition.price * (1 + total_slippage_rate)
        else:  # SELL
            actual_price = market_condition.price * (1 - total_slippage_rate)
        
        # 9. 计算滑点金额
        slippage_amount = abs(actual_price - market_condition.price) * (
            order_size_usd / market_condition.price
        )
        
        # 10. 分解滑点来源（用于分析）
        breakdown = {
            'base': base,
            'spread': spread_impact,
            'liquidity': liquidity_impact,
            'volatility_multiplier': volatility_multiplier,
            'order_type_multiplier': order_type_multiplier,
            'noise': noise,
            'base_component': base_slippage_component,
        }
        
        logger.debug(
            f"滑点计算: {order_side.value} ${order_size_usd:.0f} | "
            f"滑点率={total_slippage_rate:.4%} | "
            f"价格: ${market_condition.price:.2f} -> ${actual_price:.2f}"
        )
        
        return SlippageResult(
            expected_price=market_condition.price,
            actual_price=actual_price,
            slippage_rate=total_slippage_rate,
            slippage_amount=slippage_amount,
            breakdown=breakdown
        )
    
    def estimate_execution_cost(
        self,
        order_size_usd: float,
        market_condition: MarketCondition,
        order_type: OrderType = OrderType.MARKET
    ) -> Dict[str, float]:
        """
        预估执行成本（买卖往返）
        
        用于Agent在决策时评估交易成本
        
        Args:
            order_size_usd: 订单金额
            market_condition: 市场状况
            order_type: 订单类型
        
        Returns:
            Dict: {'buy_cost': 买入成本, 'sell_cost': 卖出成本, 'round_trip': 往返成本}
        """
        # 买入滑点
        buy_result = self.calculate_slippage(
            OrderSide.BUY, order_size_usd, order_type, market_condition
        )
        
        # 卖出滑点
        sell_result = self.calculate_slippage(
            OrderSide.SELL, order_size_usd, order_type, market_condition
        )
        
        # 往返成本
        round_trip_cost = buy_result.slippage_amount + sell_result.slippage_amount
        
        return {
            'buy_cost': buy_result.slippage_amount,
            'sell_cost': sell_result.slippage_amount,
            'round_trip': round_trip_cost,
            'round_trip_rate': (buy_result.slippage_rate + sell_result.slippage_rate)
        }


class RealisticSlippageModel(SlippageModel):
    """
    真实市场滑点模型（参数基于实际BTC永续合约市场）
    
    特点：
    - 更高的基础滑点（真实市场条件）
    - 更强的流动性影响（大单冲击）
    - 考虑极端行情（黑天鹅）
    """
    
    def __init__(self):
        super().__init__(
            base_slippage=0.001,        # 0.1% 基础滑点
            liquidity_factor=0.02,      # 更强的流动性影响
            volatility_factor=1.0,      # 更强的波动率影响
            size_impact_exponent=2.0,   # 更强的非线性影响
            random_noise=0.0005,        # 更大的随机性
        )
        logger.info("真实市场滑点模型已初始化（高滑点模式）")


class LowSlippageModel(SlippageModel):
    """
    低滑点模型（用于高流动性市场或小仓位测试）
    """
    
    def __init__(self):
        super().__init__(
            base_slippage=0.0002,       # 0.02% 基础滑点
            liquidity_factor=0.005,     # 较弱的流动性影响
            volatility_factor=0.3,      # 较弱的波动率影响
            size_impact_exponent=1.2,   # 较弱的非线性影响
            random_noise=0.0001,        # 较小的随机性
        )
        logger.info("低滑点模型已初始化（理想市场模式）")


# 工厂函数
def create_slippage_model(model_type: str = "realistic") -> SlippageModel:
    """
    创建滑点模型
    
    Args:
        model_type: 模型类型
            - "realistic": 真实市场（默认）
            - "low": 低滑点（理想市场）
            - "base": 基础模型（可自定义）
    
    Returns:
        SlippageModel: 滑点模型实例
    """
    if model_type == "realistic":
        return RealisticSlippageModel()
    elif model_type == "low":
        return LowSlippageModel()
    else:
        return SlippageModel()

