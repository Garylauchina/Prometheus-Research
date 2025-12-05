"""
简化的Agent交易模块

快速实现版本，用于v5.3阶段2.1验证
使用固定成本假设，避免复杂的microstructure接口

Author: Prometheus Team
Version: v5.3
Date: 2025-12-06
"""

import random
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class SimpleTradeCost:
    """简化的交易成本"""
    exchange_fee_pct: float     # 交易所手续费（百分比）
    spread_cost_pct: float      # 价差成本（百分比）
    slippage_cost_pct: float    # 滑点成本（百分比）
    impact_cost_pct: float      # 冲击成本（百分比）
    total_cost_pct: float       # 总成本（百分比）
    estimated_price: float      # 预估成交价


@dataclass
class TradeResult:
    """交易结果"""
    success: bool
    executed_price: float
    quantity: float
    cost: SimpleTradeCost
    pnl: float = 0.0


class SimpleAgentTrader:
    """
    简化的Agent交易器
    
    特点：
    - 固定成本假设（简单但真实）
    - 考虑市场状态（价格、波动）
    - 理性决策（成本-收益分析）
    - 快速集成
    """
    
    def __init__(self, 
                 market,
                 network_simulator=None,
                 exchange_fee_pct: float = 0.001,     # 0.10% OKX Taker费率
                 base_spread_pct: float = 0.0001,     # 0.01% 真实价差
                 base_slippage_pct: float = 0.0001,   # 0.01% 真实滑点
                 base_impact_pct: float = 0.0):       # 0% 小额无冲击
        """
        初始化简化交易器（使用真实OKX费率）
        
        Args:
            market: 市场对象
            network_simulator: 网络模拟器（可选）
            exchange_fee_pct: 交易所手续费（OKX Taker: 0.10%）
            base_spread_pct: 基础价差百分比（BTC/USDT真实价差）
            base_slippage_pct: 基础滑点百分比
            base_impact_pct: 基础冲击百分比
        """
        self.market = market
        self.network = network_simulator
        
        self.exchange_fee_pct = exchange_fee_pct
        self.base_spread_pct = base_spread_pct
        self.base_slippage_pct = base_slippage_pct
        self.base_impact_pct = base_impact_pct
        
        self.total_trades = 0
        self.total_cost = 0.0
        
        total_base_cost = exchange_fee_pct + base_spread_pct + base_slippage_pct + base_impact_pct
        logger.debug(f"🔧 简化交易器已初始化 (真实OKX费率)")
        logger.debug(f"   交易所手续费: {exchange_fee_pct*100:.3f}%")
        logger.debug(f"   总基础成本: {total_base_cost*100:.3f}%")
    
    def get_market_state(self) -> Dict:
        """
        获取市场状态（简化版）
        
        Returns:
            市场状态字典
        """
        # 模拟市场数据延迟
        if self.network:
            self.network.simulate_market_data_delay(execute=True)
        
        # 获取基础市场信息
        state = {
            'price': self.market.current_price,
            'liquidity': getattr(self.market, 'liquidity_mgr', None),
            'volatility': 0.01  # 简化：固定1%波动率
        }
        
        return state
    
    def estimate_trade_cost(self, 
                           side: OrderSide,
                           quantity: float,
                           current_price: float) -> SimpleTradeCost:
        """
        估算交易成本（简化但真实）
        
        成本模型：
        - 价差成本：固定0.1%
        - 滑点成本：固定0.05% + 随机0-0.05%
        - 冲击成本：固定0.03% + 交易量调整
        
        Args:
            side: 买/卖
            quantity: 数量
            current_price: 当前价格
            
        Returns:
            SimpleTradeCost对象
        """
        trade_value = quantity * current_price
        
        # 1. 交易所手续费（OKX Taker: 0.10%）
        exchange_fee = self.exchange_fee_pct
        
        # 2. 价差成本（真实BTC/USDT价差约0.01%）
        spread_cost_pct = self.base_spread_pct
        
        # 3. 滑点成本（小额交易约0.01%）
        random_slippage = random.uniform(0, self.base_slippage_pct)
        slippage_cost_pct = self.base_slippage_pct + random_slippage
        
        # 4. 冲击成本（小额交易几乎为0）
        volume_impact = (trade_value / 10000) * 0.0001 if trade_value > 10000 else 0
        impact_cost_pct = self.base_impact_pct + volume_impact
        
        # 5. 总成本 = 手续费 + 价差 + 滑点 + 冲击
        total_cost_pct = exchange_fee + spread_cost_pct + slippage_cost_pct + impact_cost_pct
        
        # 限制最大成本（0.3%）
        total_cost_pct = min(total_cost_pct, 0.003)
        
        # 6. 预估成交价
        if side == OrderSide.BUY:
            estimated_price = current_price * (1 + total_cost_pct)
        else:
            estimated_price = current_price * (1 - total_cost_pct)
        
        return SimpleTradeCost(
            exchange_fee_pct=exchange_fee,
            spread_cost_pct=spread_cost_pct,
            slippage_cost_pct=slippage_cost_pct,
            impact_cost_pct=impact_cost_pct,
            total_cost_pct=total_cost_pct,
            estimated_price=estimated_price
        )
    
    def execute_trade(self,
                     agent_id: str,
                     side: OrderSide,
                     quantity: float,
                     agent_capital: float,
                     expected_profit_pct: float = 0.0) -> TradeResult:
        """
        执行交易（带理性决策）
        
        决策逻辑：
        1. 评估成本
        2. 检查资金
        3. 如果预期收益 > 成本，则交易
        4. 否则放弃
        
        Args:
            agent_id: Agent ID
            side: 买/卖
            quantity: 数量
            agent_capital: Agent资金
            expected_profit_pct: 预期收益百分比
            
        Returns:
            TradeResult对象
        """
        # 模拟订单延迟
        if self.network:
            self.network.simulate_order_delay(execute=True)
        
        # 获取当前价格
        current_price = self.market.current_price
        
        # 评估成本
        cost = self.estimate_trade_cost(side, quantity, current_price)
        
        # 理性决策：预期收益必须大于成本
        trade_value = quantity * current_price
        required_capital = quantity * cost.estimated_price if side == OrderSide.BUY else 0
        
        # 检查1：资金是否足够
        if side == OrderSide.BUY and required_capital > agent_capital:
            logger.debug(f"❌ 资金不足 | {agent_id} | 需要${required_capital:.2f}, 拥有${agent_capital:.2f}")
            return TradeResult(
                success=False,
                executed_price=current_price,
                quantity=0,
                cost=cost,
                pnl=0
            )
        
        # 检查2：预期收益是否大于成本
        if expected_profit_pct < cost.total_cost_pct:
            logger.debug(f"⏸️ 放弃交易 | {agent_id} | 成本{cost.total_cost_pct*100:.3f}% > 预期{expected_profit_pct*100:.3f}%")
            return TradeResult(
                success=False,
                executed_price=current_price,
                quantity=0,
                cost=cost,
                pnl=0
            )
        
        # 执行交易
        executed_price = cost.estimated_price
        
        # 计算盈亏（简化：假设立即平仓）
        if side == OrderSide.BUY:
            # 买入：成本是负的
            pnl = -trade_value * cost.total_cost_pct
        else:
            # 卖出：收益是正的（假设之前持有）
            pnl = trade_value * (expected_profit_pct - cost.total_cost_pct)
        
        # 更新统计
        self.total_trades += 1
        self.total_cost += trade_value * cost.total_cost_pct
        
        # 模拟确认延迟
        if self.network:
            self.network.simulate_confirmation_delay(execute=True)
        
        logger.debug(f"✅ 交易完成 | {agent_id} | {side.value} {quantity:.4f} @ ${executed_price:.2f} | PnL: ${pnl:.2f}")
        
        return TradeResult(
            success=True,
            executed_price=executed_price,
            quantity=quantity,
            cost=cost,
            pnl=pnl
        )
    
    def get_stats(self) -> Dict:
        """获取交易统计"""
        avg_cost = self.total_cost / self.total_trades if self.total_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'total_cost': self.total_cost,
            'avg_cost_per_trade': avg_cost,
            'network_stats': self.network.get_stats() if self.network else None
        }


def agent_make_trading_decision(agent, market_price: float) -> Tuple[bool, OrderSide, float, float]:
    """
    Agent做出交易决策（简化版）
    
    决策逻辑：
    - 随机决定是否交易（50%概率）
    - 随机选择买/卖
    - 交易量为资金的1-5%
    - 预期收益为0.5-3%
    
    Args:
        agent: Agent对象
        market_price: 当前市场价格
        
    Returns:
        (是否交易, 方向, 数量, 预期收益百分比)
    """
    # 50%概率交易
    if random.random() > 0.5:
        return False, OrderSide.BUY, 0, 0
    
    # 随机方向
    side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
    
    # 交易量：资金的1-5%
    trade_pct = random.uniform(0.01, 0.05)
    trade_value = agent.current_capital * trade_pct
    quantity = trade_value / market_price
    
    # 预期收益：0.5-3%
    expected_profit_pct = random.uniform(0.005, 0.03)
    
    return True, side, quantity, expected_profit_pct


# ============================================
# 测试代码
# ============================================

def test_simple_trading():
    """测试简化交易模块"""
    print("="*70)
    print("🧪 简化交易模块测试")
    print("="*70)
    
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from prometheus.market.advanced_market import AdvancedOpponentMarket
        from prometheus.market.network_simulator import NetworkSimulator
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建市场和网络
    print("\n1️⃣ 初始化市场和网络...")
    market = AdvancedOpponentMarket(initial_price=50000.0)
    network = NetworkSimulator(enabled=True, base_latency_ms=30)
    trader = SimpleAgentTrader(market=market, network_simulator=network)
    print("   ✅ 初始化完成")
    
    # 测试成本估算
    print("\n2️⃣ 测试成本估算（真实OKX费率）...")
    cost = trader.estimate_trade_cost(
        side=OrderSide.BUY,
        quantity=0.1,
        current_price=50000
    )
    print(f"   交易所手续费: {cost.exchange_fee_pct*100:.3f}%")
    print(f"   价差成本: {cost.spread_cost_pct*100:.3f}%")
    print(f"   滑点成本: {cost.slippage_cost_pct*100:.3f}%")
    print(f"   冲击成本: {cost.impact_cost_pct*100:.3f}%")
    print(f"   总成本: {cost.total_cost_pct*100:.3f}% (vs 旧版0.204%)")
    print(f"   预估价格: ${cost.estimated_price:,.2f}")
    
    # 测试交易执行（成功）
    print("\n3️⃣ 测试交易执行（预期收益2%，应该成功）...")
    result = trader.execute_trade(
        agent_id="TEST_AGENT_001",
        side=OrderSide.BUY,
        quantity=0.1,
        agent_capital=10000,
        expected_profit_pct=0.02
    )
    print(f"   交易成功: {result.success}")
    if result.success:
        print(f"   成交价格: ${result.executed_price:,.2f}")
        print(f"   交易数量: {result.quantity:.4f}")
        print(f"   盈亏: ${result.pnl:.2f}")
    
    # 测试交易执行（失败 - 预期收益太低）
    print("\n4️⃣ 测试交易执行（预期收益0.05%，应该放弃）...")
    result = trader.execute_trade(
        agent_id="TEST_AGENT_002",
        side=OrderSide.BUY,
        quantity=0.1,
        agent_capital=10000,
        expected_profit_pct=0.0005
    )
    print(f"   交易成功: {result.success} (预期: False)")
    
    # 统计
    print("\n5️⃣ 交易统计...")
    stats = trader.get_stats()
    print(f"   总交易数: {stats['total_trades']}")
    print(f"   总成本: ${stats['total_cost']:.2f}")
    print(f"   平均成本: ${stats['avg_cost_per_trade']:.2f}")
    
    print("\n✅ 测试完成！")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    test_simple_trading()

