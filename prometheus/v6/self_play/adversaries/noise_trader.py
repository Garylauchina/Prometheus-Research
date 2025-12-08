"""
噪音交易者对手盘

策略特点：
  - 随机交易
  - 情绪化
  - 制造市场噪音
  - 无明确策略

行为模式：
  - 随机买卖
  - 随机持仓时间
  - 模拟散户行为
  - 增加市场不确定性
"""

from typing import Dict, Optional
from dataclasses import dataclass
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class NoiseTraderConfig:
    """噪音交易者配置"""
    trade_frequency: float = 0.10       # 交易频率（10%概率）
    position_size_range: tuple = (0.1, 0.5)  # 仓位大小范围
    hold_time_range: tuple = (5, 20)    # 持仓时间范围
    panic_threshold: float = 0.05       # 恐慌阈值（5%跌幅）


class NoiseTraderAdversary:
    """
    噪音交易者对手盘
    
    核心功能：
      1. 随机交易
      2. 恐慌性抛售
      3. FOMO买入
    """
    
    def __init__(self, config: Optional[NoiseTraderConfig] = None):
        self.config = config or NoiseTraderConfig()
        self.position = 0.0
        self.entry_price = 0.0
        self.entry_cycle = 0
        self.target_hold_time = 0
        self.last_price = 0.0
        
        logger.info(f"噪音交易者初始化: trade_freq={self.config.trade_frequency*100:.0f}%")
    
    def should_panic_sell(self, current_price: float) -> bool:
        """
        是否应该恐慌性抛售
        
        规则：
          - 持多仓
          - 价格快速下跌超过阈值
        """
        if self.position <= 0 or self.last_price == 0:
            return False
        
        price_drop_pct = (current_price - self.last_price) / self.last_price
        
        return price_drop_pct < -self.config.panic_threshold
    
    def should_fomo_buy(self, current_price: float) -> bool:
        """
        是否应该FOMO买入
        
        规则：
          - 无仓位或持空仓
          - 价格快速上涨超过阈值
        """
        if self.position >= 0.5 or self.last_price == 0:
            return False
        
        price_rise_pct = (current_price - self.last_price) / self.last_price
        
        return price_rise_pct > self.config.panic_threshold
    
    def should_random_trade(self) -> bool:
        """
        是否应该随机交易
        
        规则：基于trade_frequency随机
        """
        return random.random() < self.config.trade_frequency
    
    def should_exit_position(self, cycle: int) -> bool:
        """
        是否应该退出仓位
        
        规则：达到目标持仓时间
        """
        if self.position == 0:
            return False
        
        hold_time = cycle - self.entry_cycle
        return hold_time >= self.target_hold_time
    
    def generate_signal(
        self,
        current_price: float,
        cycle: int
    ) -> Optional[Dict]:
        """
        生成交易信号
        
        参数：
          - current_price: 当前价格
          - cycle: 当前周期
        
        返回：
          - signal: 交易信号
        """
        # 1. 恐慌性抛售
        if self.should_panic_sell(current_price):
            signal = {
                'action': 'close',
                'side': 'sell',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'panic'
            }
            
            logger.info(
                f"噪音交易者恐慌抛售: {signal['amount']:.2f} "
                f"(price_drop={(current_price - self.last_price)/self.last_price*100:+.2f}%)"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 2. FOMO买入
        if self.should_fomo_buy(current_price):
            amount = random.uniform(*self.config.position_size_range)
            
            signal = {
                'action': 'open',
                'side': 'buy',
                'amount': amount,
                'type': 'market',
                'reason': 'fomo'
            }
            
            logger.info(
                f"噪音交易者FOMO买入: {amount:.2f} "
                f"(price_rise={(current_price - self.last_price)/self.last_price*100:+.2f}%)"
            )
            
            # 更新仓位
            self.position = amount
            self.entry_price = current_price
            self.entry_cycle = cycle
            self.target_hold_time = random.randint(*self.config.hold_time_range)
            
            return signal
        
        # 3. 达到目标持仓时间 → 平仓
        if self.should_exit_position(cycle):
            signal = {
                'action': 'close',
                'side': 'sell' if self.position > 0 else 'buy',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'target_hold_time'
            }
            
            logger.info(
                f"噪音交易者平仓: {signal['side']} {signal['amount']:.2f} "
                f"(hold_time={cycle - self.entry_cycle})"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 4. 随机交易
        if self.position == 0 and self.should_random_trade():
            side = random.choice(['buy', 'sell'])
            amount = random.uniform(*self.config.position_size_range)
            
            signal = {
                'action': 'open',
                'side': side,
                'amount': amount,
                'type': 'market',
                'reason': 'random'
            }
            
            logger.info(f"噪音交易者随机交易: {side} {amount:.2f}")
            
            # 更新仓位
            self.position = amount if side == 'buy' else -amount
            self.entry_price = current_price
            self.entry_cycle = cycle
            self.target_hold_time = random.randint(*self.config.hold_time_range)
            
            return signal
        
        # 更新last_price
        self.last_price = current_price
        
        return None
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        return {
            'type': 'noise_trader',
            'position': self.position,
            'entry_price': self.entry_price,
            'target_hold_time': self.target_hold_time,
            'last_price': self.last_price
        }

