"""
资金费率模型 (Funding Rate Model) - Prometheus v5.1
====================================================

模拟永续合约的资金费率机制

核心概念：
- 资金费率 = 让合约价格锚定现货价格的经济激励
- 市场偏多 → 多头支付空头 → 鼓励做空
- 市场偏空 → 空头支付多头 → 鼓励做多

Author: Prometheus Team
Version: 5.1
Date: 2025-12-04
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketSentiment(Enum):
    """市场情绪"""
    EXTREME_BULLISH = "extreme_bullish"    # 极度看多
    BULLISH = "bullish"                    # 看多
    NEUTRAL = "neutral"                    # 中性
    BEARISH = "bearish"                    # 看空
    EXTREME_BEARISH = "extreme_bearish"    # 极度看空


@dataclass
class FundingRateResult:
    """资金费率计算结果"""
    funding_rate: float              # 资金费率（8小时，百分比）
    annualized_rate: float           # 年化费率（参考）
    market_sentiment: MarketSentiment  # 市场情绪
    premium_index: float             # 溢价指数
    long_cost_8h: float             # 多头持仓成本（8小时，$10000仓位）
    short_cost_8h: float            # 空头持仓成本（8小时，$10000仓位）


class FundingRateModel:
    """
    资金费率模型
    
    模拟永续合约资金费率：
    1. 基于溢价指数计算费率
    2. 考虑市场情绪和持仓偏向
    3. 包含动态调整机制
    
    典型费率范围：
    - 正常市场：-0.01% ~ +0.01%（每8小时）
    - 偏多市场：+0.01% ~ +0.10%
    - 偏空市场：-0.01% ~ -0.10%
    - 极端市场：±0.10% ~ ±0.50%
    """
    
    # 常量配置
    BASE_RATE = 0.0001              # 基础费率 0.01%
    INTEREST_RATE = 0.0003          # 利息成分 0.03%（模拟无风险利率）
    PREMIUM_IMPACT_FACTOR = 0.5     # 溢价影响系数
    MAX_FUNDING_RATE = 0.005        # 最大费率 0.5%（8小时）
    MIN_FUNDING_RATE = -0.005       # 最小费率 -0.5%
    
    def __init__(
        self,
        base_rate: float = BASE_RATE,
        interest_rate: float = INTEREST_RATE,
        max_rate: float = MAX_FUNDING_RATE,
    ):
        """
        初始化资金费率模型
        
        Args:
            base_rate: 基础费率
            interest_rate: 利息成分
            max_rate: 最大费率（绝对值）
        """
        self.base_rate = base_rate
        self.interest_rate = interest_rate
        self.max_rate = max_rate
        self.min_rate = -max_rate
        
        logger.info(f"资金费率模型已初始化 | 基础费率={base_rate:.4%} | 最大费率=±{max_rate:.4%}")
    
    def calculate_funding_rate(
        self,
        mark_price: float,
        index_price: float,
        long_short_ratio: Optional[float] = None,
        open_interest: Optional[float] = None,
    ) -> FundingRateResult:
        """
        计算资金费率
        
        Args:
            mark_price: 标记价格（合约价格）
            index_price: 指数价格（现货价格）
            long_short_ratio: 多空比（可选，多头/空头持仓比例）
            open_interest: 持仓量（可选，美元计）
        
        Returns:
            FundingRateResult: 资金费率计算结果
        """
        # 1. 计算溢价指数（Premium Index）
        premium_index = (mark_price - index_price) / index_price
        
        # 2. 基础资金费率 = 利息成分 + 溢价成分
        premium_component = premium_index * self.PREMIUM_IMPACT_FACTOR
        funding_rate = self.interest_rate + premium_component
        
        # 3. 多空比调整（如果提供）
        if long_short_ratio is not None:
            # 多空比 > 1 → 市场偏多 → 增加资金费率（多头支付更多）
            # 多空比 < 1 → 市场偏空 → 减少资金费率（空头支付更多）
            ratio_adjustment = (long_short_ratio - 1.0) * 0.0001
            funding_rate += ratio_adjustment
        
        # 4. 持仓量调整（如果提供）- 高持仓量 = 高市场压力
        if open_interest is not None:
            # 归一化到10M，持仓量越高费率波动越大
            oi_multiplier = 1.0 + (open_interest / 10000000.0) * 0.2
            funding_rate *= oi_multiplier
        
        # 5. 限制在合理范围内
        funding_rate = np.clip(funding_rate, self.min_rate, self.max_rate)
        
        # 6. 年化费率（参考）
        annualized_rate = funding_rate * 3 * 365  # 每天3次，一年365天
        
        # 7. 判断市场情绪
        market_sentiment = self._determine_sentiment(funding_rate, premium_index)
        
        # 8. 计算持仓成本（假设$10000仓位）
        position_size = 10000.0
        long_cost_8h = position_size * funding_rate  # 多头支付
        short_cost_8h = -position_size * funding_rate  # 空头收取（或支付）
        
        result = FundingRateResult(
            funding_rate=funding_rate,
            annualized_rate=annualized_rate,
            market_sentiment=market_sentiment,
            premium_index=premium_index,
            long_cost_8h=long_cost_8h,
            short_cost_8h=short_cost_8h,
        )
        
        logger.debug(
            f"资金费率: {funding_rate:.4%} | "
            f"溢价: {premium_index:.4%} | "
            f"情绪: {market_sentiment.value} | "
            f"多头成本: ${long_cost_8h:.2f}/8h"
        )
        
        return result
    
    def _determine_sentiment(
        self,
        funding_rate: float,
        premium_index: float
    ) -> MarketSentiment:
        """
        判断市场情绪
        
        Args:
            funding_rate: 资金费率
            premium_index: 溢价指数
        
        Returns:
            MarketSentiment: 市场情绪
        """
        if funding_rate > 0.002:  # > 0.2%
            return MarketSentiment.EXTREME_BULLISH
        elif funding_rate > 0.0005:  # > 0.05%
            return MarketSentiment.BULLISH
        elif funding_rate < -0.002:  # < -0.2%
            return MarketSentiment.EXTREME_BEARISH
        elif funding_rate < -0.0005:  # < -0.05%
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.NEUTRAL
    
    def estimate_daily_cost(
        self,
        position_size_usd: float,
        side: str,
        funding_rate: float
    ) -> float:
        """
        估算每日持仓成本
        
        Args:
            position_size_usd: 仓位大小（美元）
            side: 仓位方向（"long" 或 "short"）
            funding_rate: 当前资金费率（8小时）
        
        Returns:
            float: 每日成本（美元，正数=支付，负数=收取）
        """
        # 每天3次结算
        if side.lower() == "long":
            # 多头支付资金费率
            daily_cost = position_size_usd * funding_rate * 3
        else:
            # 空头收取资金费率（或支付，如果费率为负）
            daily_cost = -position_size_usd * funding_rate * 3
        
        return daily_cost
    
    def get_funding_pressure(self, funding_rate: float) -> float:
        """
        将资金费率转换为市场压力指标
        
        极端资金费率 = 市场失衡 = 高压力
        
        Args:
            funding_rate: 资金费率
        
        Returns:
            float: 压力指标（0-1）
        """
        # 资金费率的绝对值越大，压力越大
        abs_rate = abs(funding_rate)
        
        # 归一化到0.5%（极端费率）
        pressure = min(1.0, abs_rate / 0.005)
        
        return pressure


def simulate_market_funding_rate(
    market_conditions: Dict,
    historical_bias: float = 0.0
) -> FundingRateResult:
    """
    模拟市场资金费率（便捷函数）
    
    Args:
        market_conditions: 市场条件字典
            - mark_price: 标记价格
            - index_price: 指数价格
            - long_short_ratio: 多空比（可选）
            - open_interest: 持仓量（可选）
        historical_bias: 历史偏向（正=偏多，负=偏空）
    
    Returns:
        FundingRateResult: 资金费率结果
    """
    model = FundingRateModel()
    
    # 如果没有提供价格，生成模拟数据
    if 'mark_price' not in market_conditions or 'index_price' not in market_conditions:
        base_price = 50000.0
        # 根据历史偏向生成溢价
        premium = historical_bias * 0.001  # 历史偏向转换为溢价
        # 添加随机噪声
        premium += np.random.normal(0, 0.0005)
        
        market_conditions['index_price'] = base_price
        market_conditions['mark_price'] = base_price * (1 + premium)
    
    return model.calculate_funding_rate(
        mark_price=market_conditions['mark_price'],
        index_price=market_conditions['index_price'],
        long_short_ratio=market_conditions.get('long_short_ratio'),
        open_interest=market_conditions.get('open_interest'),
    )

