"""
价格冲击模型

模拟订单对价格的影响，包括：
- 临时冲击（订单完成后价格回归）
- 永久冲击（订单包含信息，价格不回归）
- 流动性依赖（流动性越低，冲击越大）

核心公式：
  impact = k * (net_order_flow / liquidity)^α

其中：
  - k: 冲击系数（市场特征）
  - net_order_flow: 净订单流（买-卖）
  - liquidity: 流动性
  - α: 冲击指数（通常0.5-0.7）
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class PriceImpactModel:
    """
    价格冲击模型
    
    功能：
      1. 计算订单对价格的冲击
      2. 区分临时冲击和永久冲击
      3. 考虑流动性影响
    
    参数：
      - impact_coefficient: 冲击系数（默认0.001）
      - impact_exponent: 冲击指数（默认0.5）
      - permanent_ratio: 永久冲击比例（默认0.5）
    """
    
    def __init__(
        self,
        impact_coefficient: float = 0.001,
        impact_exponent: float = 0.5,
        permanent_ratio: float = 0.5
    ):
        self.impact_coefficient = impact_coefficient
        self.impact_exponent = impact_exponent
        self.permanent_ratio = permanent_ratio
        
        logger.info(
            f"价格冲击模型初始化: k={impact_coefficient}, "
            f"α={impact_exponent}, permanent={permanent_ratio*100:.0f}%"
        )
    
    # ===== 核心方法 =====
    
    def calculate(
        self,
        net_order_flow: float,
        liquidity: float,
        current_price: float = 1.0
    ) -> float:
        """
        计算价格冲击
        
        参数：
          - net_order_flow: 净订单流（买-卖）
                           正值=买压，负值=卖压
          - liquidity: 流动性（订单簿深度）
          - current_price: 当前价格（用于计算百分比冲击）
        
        返回：
          - price_impact: 绝对价格冲击
        """
        if liquidity <= 0:
            logger.warning("流动性为0，使用默认值1000")
            liquidity = 1000.0
        
        # 归一化订单流
        normalized_flow = net_order_flow / liquidity
        
        # 计算冲击
        # impact = k * sign(flow) * |flow|^α
        if abs(normalized_flow) < 1e-10:
            return 0.0
        
        sign = np.sign(normalized_flow)
        magnitude = abs(normalized_flow) ** self.impact_exponent
        
        # 相对冲击（百分比）
        relative_impact = self.impact_coefficient * sign * magnitude
        
        # 转换为绝对冲击
        absolute_impact = relative_impact * current_price
        
        logger.debug(
            f"价格冲击计算: flow={net_order_flow:.2f}, "
            f"liquidity={liquidity:.2f}, impact={absolute_impact:+.4f}"
        )
        
        return absolute_impact
    
    def permanent_impact(self, temporary_impact: float) -> float:
        """
        计算永久冲击
        
        不是所有冲击都会消失：
          - 临时冲击：订单完成后价格回归（例如50%）
          - 永久冲击：订单包含信息，价格不回归（例如50%）
        
        参数：
          - temporary_impact: 总冲击
        
        返回：
          - permanent_impact: 永久冲击部分
        """
        return temporary_impact * self.permanent_ratio
    
    def temporary_impact(self, total_impact: float) -> float:
        """
        计算临时冲击
        
        参数：
          - total_impact: 总冲击
        
        返回：
          - temporary_impact: 临时冲击部分（会消失）
        """
        return total_impact * (1 - self.permanent_ratio)
    
    # ===== 高级功能 =====
    
    def calculate_multi_order(
        self,
        order_flows: list,
        liquidity: float,
        current_price: float = 1.0
    ) -> float:
        """
        计算多个订单的累积冲击
        
        参数：
          - order_flows: 订单流列表
          - liquidity: 流动性
          - current_price: 当前价格
        
        返回：
          - cumulative_impact: 累积冲击
        """
        cumulative_impact = 0.0
        current_liq = liquidity
        
        for flow in order_flows:
            # 计算单个订单的冲击
            impact = self.calculate(flow, current_liq, current_price)
            cumulative_impact += impact
            
            # 更新流动性（被消耗）
            current_liq = max(current_liq - abs(flow), liquidity * 0.1)
        
        return cumulative_impact
    
    def calculate_slippage(
        self,
        order_amount: float,
        order_side: str,
        liquidity: float,
        market_price: float
    ) -> float:
        """
        计算滑点
        
        滑点 = 实际成交价 - 预期价格
        
        参数：
          - order_amount: 订单数量
          - order_side: 订单方向（'buy' or 'sell'）
          - liquidity: 流动性
          - market_price: 市场价格
        
        返回：
          - actual_price: 实际成交价
        """
        # 买单为正流，卖单为负流
        net_flow = order_amount if order_side == 'buy' else -order_amount
        
        # 计算冲击
        impact = self.calculate(net_flow, liquidity, market_price)
        
        # 实际成交价 = 市场价 + 冲击
        actual_price = market_price + impact
        
        slippage_pct = (actual_price - market_price) / market_price * 100
        
        logger.debug(
            f"滑点计算: {order_side} {order_amount}, "
            f"market={market_price:.2f}, actual={actual_price:.2f}, "
            f"slippage={slippage_pct:+.3f}%"
        )
        
        return actual_price
    
    def estimate_execution_cost(
        self,
        order_amount: float,
        order_side: str,
        liquidity: float,
        market_price: float,
        fee_rate: float = 0.0005
    ) -> dict:
        """
        估算执行成本
        
        包括：
          - 滑点成本
          - 手续费
          - 总成本
        
        参数：
          - order_amount: 订单数量
          - order_side: 订单方向
          - liquidity: 流动性
          - market_price: 市场价格
          - fee_rate: 手续费率（默认0.05%）
        
        返回：
          - cost_breakdown: 成本明细
        """
        # 1. 计算滑点
        actual_price = self.calculate_slippage(
            order_amount, order_side, liquidity, market_price
        )
        slippage_cost = abs(actual_price - market_price) * order_amount
        
        # 2. 计算手续费
        fee_cost = actual_price * order_amount * fee_rate
        
        # 3. 总成本
        total_cost = slippage_cost + fee_cost
        
        # 4. 相对成本（百分比）
        relative_cost = total_cost / (market_price * order_amount) * 100
        
        return {
            'market_price': market_price,
            'actual_price': actual_price,
            'slippage_cost': slippage_cost,
            'fee_cost': fee_cost,
            'total_cost': total_cost,
            'relative_cost_pct': relative_cost
        }
    
    # ===== 校准方法 =====
    
    def calibrate(
        self,
        historical_trades: list,
        historical_liquidity: list
    ):
        """
        从历史数据校准模型参数
        
        参数：
          - historical_trades: 历史交易数据
                              [(order_flow, price_change), ...]
          - historical_liquidity: 历史流动性数据
        
        注意：此方法为占位符，实际实现需要统计回归
        """
        logger.warning("calibrate()方法尚未实现，使用默认参数")
        # TODO: 实现参数校准
        #   - 使用最小二乘法拟合impact_coefficient
        #   - 使用MLE估计impact_exponent
        #   - 使用时间序列分析确定permanent_ratio
        pass

