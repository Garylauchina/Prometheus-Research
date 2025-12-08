"""
趋势跟随者对手盘

策略特点：
  - 追涨杀跌
  - 动量交易
  - 制造"羊群效应"
  - 长持仓时间
  - 高风险高收益

行为模式：
  - 价格上涨 → 买入（追涨）
  - 价格下跌 → 卖出（杀跌）
  - 使用动量指标（例如MA, MACD）
  - 趋势确认后大举进场
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrendFollowerConfig:
    """趋势跟随者配置"""
    momentum_threshold: float = 0.02    # 动量阈值（2%）
    position_size_pct: float = 0.80     # 仓位大小（80%）
    hold_time_min: int = 20             # 最小持仓时间（20周期）
    stop_loss_pct: float = 0.05         # 止损（5%）


class TrendFollowerAdversary:
    """
    趋势跟随者对手盘
    
    核心功能：
      1. 动量识别
      2. 趋势跟随
      3. 止损管理
    """
    
    def __init__(self, config: Optional[TrendFollowerConfig] = None):
        self.config = config or TrendFollowerConfig()
        self.position = 0.0  # 当前仓位（正=多头，负=空头）
        self.entry_price = 0.0
        self.entry_cycle = 0
        self.price_history = []  # 价格历史（用于计算动量）
        
        logger.info(
            f"趋势跟随者初始化: momentum_threshold={self.config.momentum_threshold*100:.1f}%"
        )
    
    def update_price_history(self, price: float):
        """
        更新价格历史
        
        参数：
          - price: 当前价格
        """
        self.price_history.append(price)
        
        # 只保留最近50个价格
        if len(self.price_history) > 50:
            self.price_history.pop(0)
    
    def calculate_momentum(self) -> float:
        """
        计算动量
        
        动量 = (当前价格 - 10周期前价格) / 10周期前价格
        
        返回：
          - momentum: 动量值
        """
        if len(self.price_history) < 10:
            return 0.0
        
        current_price = self.price_history[-1]
        past_price = self.price_history[-10]
        
        momentum = (current_price - past_price) / past_price
        
        return momentum
    
    def should_enter_long(self, momentum: float) -> bool:
        """
        是否应该做多
        
        规则：
          - 动量 > 阈值
          - 当前无仓位或持空仓
        """
        return momentum > self.config.momentum_threshold and self.position <= 0
    
    def should_enter_short(self, momentum: float) -> bool:
        """
        是否应该做空
        
        规则：
          - 动量 < -阈值
          - 当前无仓位或持多仓
        """
        return momentum < -self.config.momentum_threshold and self.position >= 0
    
    def should_stop_loss(self, current_price: float) -> bool:
        """
        是否应该止损
        
        规则：
          - 多头：价格跌破entry_price * (1 - stop_loss_pct)
          - 空头：价格突破entry_price * (1 + stop_loss_pct)
        """
        if self.position == 0 or self.entry_price == 0:
            return False
        
        if self.position > 0:
            # 多头止损
            stop_price = self.entry_price * (1 - self.config.stop_loss_pct)
            return current_price < stop_price
        else:
            # 空头止损
            stop_price = self.entry_price * (1 + self.config.stop_loss_pct)
            return current_price > stop_price
    
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
        # 更新价格历史
        self.update_price_history(current_price)
        
        # 计算动量
        momentum = self.calculate_momentum()
        
        # 1. 止损检查
        if self.should_stop_loss(current_price):
            signal = {
                'action': 'close',
                'side': 'sell' if self.position > 0 else 'buy',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'stop_loss'
            }
            
            logger.info(
                f"趋势跟随者止损: {signal['side']} {signal['amount']:.2f} "
                f"(entry={self.entry_price:.2f}, current={current_price:.2f})"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 2. 开仓信号
        if self.should_enter_long(momentum):
            signal = {
                'action': 'open',
                'side': 'buy',
                'amount': self.config.position_size_pct,
                'type': 'market',
                'reason': 'momentum_long'
            }
            
            logger.info(
                f"趋势跟随者做多: momentum={momentum*100:+.2f}% "
                f"price={current_price:.2f}"
            )
            
            # 更新仓位
            self.position = signal['amount']
            self.entry_price = current_price
            self.entry_cycle = cycle
            
            return signal
        
        elif self.should_enter_short(momentum):
            signal = {
                'action': 'open',
                'side': 'sell',
                'amount': self.config.position_size_pct,
                'type': 'market',
                'reason': 'momentum_short'
            }
            
            logger.info(
                f"趋势跟随者做空: momentum={momentum*100:+.2f}% "
                f"price={current_price:.2f}"
            )
            
            # 更新仓位
            self.position = -signal['amount']
            self.entry_price = current_price
            self.entry_cycle = cycle
            
            return signal
        
        # 3. 持仓中，无操作
        return None
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        momentum = self.calculate_momentum()
        
        return {
            'type': 'trend_follower',
            'position': self.position,
            'entry_price': self.entry_price,
            'momentum': momentum,
            'price_history_len': len(self.price_history)
        }

