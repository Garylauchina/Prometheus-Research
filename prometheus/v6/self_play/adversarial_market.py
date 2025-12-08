"""
对手盘市场模拟器

统一入口，整合：
  1. OrderBook（订单簿）
  2. PriceImpactModel（价格冲击模型）
  3. 5种对手盘Agent（MarketMaker, TrendFollower, Contrarian, Arbitrageur, NoiseTrader）

核心功能：
  - 创建对手盘种群
  - 模拟订单撮合
  - 计算价格冲击
  - 管理市场状态

遵循三大铁律：
  - 铁律1: 通过SelfPlaySystem统一调用
  - 铁律2: 本模块为Self-Play核心实现
  - 铁律3: 所有交易原子化
"""

from typing import List, Dict, Tuple, Optional
import random
import logging
from dataclasses import dataclass

from .order_book import OrderBook, Order, Trade, OrderType, OrderSide, OrderStatus
from .price_impact_model import PriceImpactModel
from .adversaries import (
    MarketMakerAdversary,
    TrendFollowerAdversary,
    ContrarianAdversary,
    ArbitrageurAdversary,
    NoiseTraderAdversary
)

logger = logging.getLogger(__name__)


@dataclass
class AdversarialAgent:
    """
    对手盘Agent封装
    
    属性：
      - agent_id: Agent ID
      - agent_type: Agent类型
      - strategy: 策略对象
      - role: 角色（'adversary' or 'shadow'）
    """
    agent_id: str
    agent_type: str
    strategy: object
    role: str = 'adversary'


class AdversarialMarket:
    """
    对手盘市场模拟器
    
    核心功能：
      1. 生成各种类型的"对手盘Agent"
      2. 模拟订单簿撮合
      3. 计算价格冲击
      4. 让主Agent与对手盘竞争
    """
    
    def __init__(self):
        self.order_book = OrderBook()
        self.price_impact_model = PriceImpactModel()
        
        # 对手盘策略工厂
        self.adversary_factory = {
            'market_maker': MarketMakerAdversary,
            'trend_follower': TrendFollowerAdversary,
            'contrarian': ContrarianAdversary,
            'arbitrageur': ArbitrageurAdversary,
            'noise_trader': NoiseTraderAdversary
        }
        
        self.adversarial_agents: List[AdversarialAgent] = []
        self.next_agent_id = 0
        
        logger.info("对手盘市场初始化完成")
    
    # ===== 对手盘生成 =====
    
    def create_adversarial_population(
        self,
        num_adversaries: int = 10,
        type_distribution: Optional[Dict[str, float]] = None
    ) -> List[AdversarialAgent]:
        """
        创建对手盘种群
        
        参数：
          - num_adversaries: 对手盘数量
          - type_distribution: 类型分布（例如 {'market_maker': 0.2, ...}）
                              如果为None，则均匀分布
        
        返回：
          - adversaries: 对手盘Agent列表
        """
        if type_distribution is None:
            # 默认分布
            type_distribution = {
                'market_maker': 0.20,      # 20% 做市商
                'trend_follower': 0.30,    # 30% 趋势跟随
                'contrarian': 0.20,        # 20% 逆向交易
                'arbitrageur': 0.15,       # 15% 套利者
                'noise_trader': 0.15       # 15% 噪音交易者
            }
        
        adversaries = []
        
        for i in range(num_adversaries):
            # 根据分布随机选择类型
            adv_type = random.choices(
                list(type_distribution.keys()),
                weights=list(type_distribution.values())
            )[0]
            
            # 创建策略对象
            strategy_class = self.adversary_factory[adv_type]
            strategy = strategy_class()
            
            # 创建对手盘Agent
            agent = AdversarialAgent(
                agent_id=f"ADV{self.next_agent_id:04d}",
                agent_type=adv_type,
                strategy=strategy,
                role='adversary'
            )
            
            adversaries.append(agent)
            self.next_agent_id += 1
        
        self.adversarial_agents = adversaries
        
        logger.info(
            f"创建对手盘种群: {num_adversaries}个 "
            f"(MM:{type_distribution.get('market_maker', 0)*100:.0f}%, "
            f"TF:{type_distribution.get('trend_follower', 0)*100:.0f}%, "
            f"CT:{type_distribution.get('contrarian', 0)*100:.0f}%, "
            f"ARB:{type_distribution.get('arbitrageur', 0)*100:.0f}%, "
            f"NT:{type_distribution.get('noise_trader', 0)*100:.0f}%)"
        )
        
        return adversaries
    
    def create_shadow_adversaries(
        self,
        main_agents: List,
        shadow_ratio: float = 0.10
    ) -> List[AdversarialAgent]:
        """
        创建影子对手盘
        
        影子对手盘 = 克隆主Agent的策略 + 变异
        
        参数：
          - main_agents: 主Agent列表
          - shadow_ratio: 影子对手盘比例
        
        返回：
          - shadows: 影子对手盘列表
        """
        num_shadows = int(len(main_agents) * shadow_ratio)
        shadows = []
        
        for i in range(num_shadows):
            # 随机选择一个主Agent作为模板
            template = random.choice(main_agents)
            
            # TODO: 实际实现需要克隆Agent的genome并变异
            # 这里先创建占位符
            shadow = AdversarialAgent(
                agent_id=f"SHADOW{self.next_agent_id:04d}",
                agent_type='shadow',
                strategy=None,  # TODO: 克隆+变异策略
                role='shadow_adversary'
            )
            
            shadows.append(shadow)
            self.next_agent_id += 1
        
        logger.info(f"创建影子对手盘: {num_shadows}个")
        
        return shadows
    
    # ===== 订单撮合 =====
    
    def simulate_order_matching(
        self,
        orders: List[Dict],
        current_price: float,
        cycle: int
    ) -> Tuple[List[Trade], float]:
        """
        模拟订单撮合
        
        与简化的"即时成交"不同，这里模拟真实的订单簿：
          1. 订单进入订单簿
          2. 按价格-时间优先匹配
          3. 大单会产生价格冲击
          4. 流动性不足会导致部分成交
        
        参数：
          - orders: 订单列表 [{'agent_id': ..., 'side': ..., 'amount': ..., 'type': ...}, ...]
          - current_price: 当前市场价格
          - cycle: 当前周期
        
        返回：
          - trades: 成交记录列表
          - new_price: 新的市场价格
        """
        trades = []
        new_price = current_price
        
        # 1. 生成对手盘订单
        adversary_orders = self._generate_adversary_orders(current_price, cycle)
        all_orders = orders + adversary_orders
        
        logger.debug(
            f"订单撮合开始: {len(orders)}个主订单 + {len(adversary_orders)}个对手盘订单"
        )
        
        # 2. 将订单转换为Order对象
        order_objects = []
        for order_dict in all_orders:
            order_obj = Order(
                order_id=f"O{cycle:06d}_{len(order_objects):04d}",
                agent_id=order_dict.get('agent_id', 'UNKNOWN'),
                order_type=OrderType.MARKET if order_dict.get('type') == 'market' else OrderType.LIMIT,
                side=OrderSide.BUY if order_dict['side'] == 'buy' else OrderSide.SELL,
                amount=order_dict['amount'],
                price=order_dict.get('price')
            )
            order_objects.append(order_obj)
        
        # 3. 按订单类型处理
        market_orders = [o for o in order_objects if o.order_type == OrderType.MARKET]
        limit_orders = [o for o in order_objects if o.order_type == OrderType.LIMIT]
        
        # 4. 先处理市价单
        for order in market_orders:
            trade, price_impact = self.order_book.match_market_order(order, new_price)
            if trade:
                trades.append(trade)
                new_price += price_impact
        
        # 5. 再处理限价单
        for order in limit_orders:
            self.order_book.add_order(order)
        
        # 尝试匹配限价单
        for order in limit_orders:
            if order.status == OrderStatus.PENDING:
                trade = self.order_book.match_limit_order(order)
                if trade:
                    trades.append(trade)
        
        # 6. 计算总体价格冲击
        net_order_flow = sum([
            o.amount if o.side == OrderSide.BUY else -o.amount
            for o in market_orders
        ])
        
        liquidity = self.order_book.liquidity()
        if liquidity == 0:
            liquidity = 1000.0
        
        total_impact = self.price_impact_model.calculate(
            net_order_flow,
            liquidity,
            current_price
        )
        
        new_price = current_price + total_impact
        
        logger.debug(
            f"订单撮合完成: {len(trades)}笔成交, "
            f"价格 {current_price:.2f} → {new_price:.2f} ({total_impact:+.4f})"
        )
        
        return trades, new_price
    
    def _generate_adversary_orders(
        self,
        current_price: float,
        cycle: int
    ) -> List[Dict]:
        """
        生成对手盘订单
        
        参数：
          - current_price: 当前价格
          - cycle: 当前周期
        
        返回：
          - orders: 订单列表
        """
        orders = []
        
        for adv_agent in self.adversarial_agents:
            # 根据类型调用策略
            if adv_agent.agent_type == 'market_maker':
                # 做市商：生成双边报价
                quotes = adv_agent.strategy.generate_quotes(current_price, cycle)
                for quote in quotes:
                    orders.append({
                        'agent_id': adv_agent.agent_id,
                        'side': quote['side'],
                        'price': quote['price'],
                        'amount': quote['amount'],
                        'type': quote['type']
                    })
            
            elif adv_agent.agent_type in ['trend_follower', 'contrarian', 'arbitrageur', 'noise_trader']:
                # 其他类型：生成信号
                signal = adv_agent.strategy.generate_signal(current_price, cycle)
                if signal:
                    orders.append({
                        'agent_id': adv_agent.agent_id,
                        'side': signal['side'],
                        'price': signal.get('price'),
                        'amount': signal['amount'],
                        'type': signal['type']
                    })
        
        return orders
    
    # ===== 辅助方法 =====
    
    def calculate_slippage(
        self,
        order_amount: float,
        order_side: str,
        market_price: float
    ) -> float:
        """
        计算滑点
        
        参数：
          - order_amount: 订单数量
          - order_side: 订单方向（'buy' or 'sell'）
          - market_price: 市场价格
        
        返回：
          - actual_price: 实际成交价
        """
        liquidity = self.order_book.liquidity()
        if liquidity == 0:
            liquidity = 1000.0
        
        actual_price = self.price_impact_model.calculate_slippage(
            order_amount,
            order_side,
            liquidity,
            market_price
        )
        
        return actual_price
    
    def get_market_statistics(self) -> Dict:
        """
        获取市场统计信息
        
        返回：
          - stats: 统计信息字典
        """
        order_book_stats = self.order_book.get_statistics()
        
        adversary_stats = {}
        for adv_type in self.adversary_factory.keys():
            count = sum(1 for a in self.adversarial_agents if a.agent_type == adv_type)
            adversary_stats[adv_type] = count
        
        return {
            'order_book': order_book_stats,
            'adversaries': adversary_stats,
            'total_adversaries': len(self.adversarial_agents)
        }
    
    def reset(self):
        """重置市场状态"""
        self.order_book.clear()
        self.adversarial_agents.clear()
        logger.info("对手盘市场已重置")

