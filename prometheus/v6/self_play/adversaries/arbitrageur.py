"""
套利者对手盘

策略特点：
  - 消除价差
  - 快速进出
  - 低风险低收益
  - 高频交易

行为模式：
  - 发现价差 → 立即套利
  - 买低卖高
  - 极短持仓时间（1-3周期）
  - 对价格敏感
"""

from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageurConfig:
    """套利者配置"""
    min_spread_pct: float = 0.001       # 最小价差（0.1%）
    position_size_pct: float = 0.30     # 仓位大小（30%）
    max_hold_time: int = 3              # 最大持仓时间（3周期）


class ArbitrageurAdversary:
    """
    套利者对手盘
    
    核心功能：
      1. 价差识别
      2. 快速套利
      3. 时间管理
    """
    
    def __init__(self, config: Optional[ArbitrageurConfig] = None):
        self.config = config or ArbitrageurConfig()
        self.position = 0.0
        self.entry_price = 0.0
        self.entry_cycle = 0
        self.last_price = 0.0
        
        logger.info(f"套利者初始化: min_spread={self.config.min_spread_pct*100:.2f}%")
    
    def detect_arbitrage_opportunity(
        self,
        current_price: float
    ) -> Optional[str]:
        """
        检测套利机会
        
        参数：
          - current_price: 当前价格
        
        返回：
          - opportunity: 'buy' or 'sell' or None
        """
        if self.last_price == 0:
            self.last_price = current_price
            return None
        
        # 计算价格变化
        price_change_pct = (current_price - self.last_price) / self.last_price
        
        # 价格下跌超过阈值 → 买入机会
        if price_change_pct < -self.config.min_spread_pct:
            return 'buy'
        
        # 价格上涨超过阈值 → 卖出机会
        elif price_change_pct > self.config.min_spread_pct:
            return 'sell'
        
        return None
    
    def should_force_exit(self, cycle: int) -> bool:
        """
        是否应该强制平仓
        
        规则：持仓时间超过最大持仓时间
        """
        if self.position == 0:
            return False
        
        hold_time = cycle - self.entry_cycle
        return hold_time >= self.config.max_hold_time
    
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
        # 1. 强制平仓检查
        if self.should_force_exit(cycle):
            signal = {
                'action': 'close',
                'side': 'sell' if self.position > 0 else 'buy',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'max_hold_time'
            }
            
            logger.info(
                f"套利者强制平仓: {signal['side']} {signal['amount']:.2f} "
                f"(hold_time={cycle - self.entry_cycle})"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 2. 检测套利机会
        opportunity = self.detect_arbitrage_opportunity(current_price)
        
        if opportunity and self.position == 0:
            # 开新仓
            signal = {
                'action': 'open',
                'side': opportunity,
                'amount': self.config.position_size_pct,
                'type': 'market',
                'reason': 'arbitrage'
            }
            
            logger.info(
                f"套利者{opportunity}: spread={abs(current_price - self.last_price)/self.last_price*100:.2f}% "
                f"price={current_price:.2f}"
            )
            
            # 更新仓位
            self.position = signal['amount'] if opportunity == 'buy' else -signal['amount']
            self.entry_price = current_price
            self.entry_cycle = cycle
            
            return signal
        
        # 3. 持仓中且有反向机会 → 平仓
        elif opportunity and (
            (self.position > 0 and opportunity == 'sell') or
            (self.position < 0 and opportunity == 'buy')
        ):
            signal = {
                'action': 'close',
                'side': 'sell' if self.position > 0 else 'buy',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'take_profit'
            }
            
            pnl_pct = ((current_price - self.entry_price) / self.entry_price) * (1 if self.position > 0 else -1)
            
            logger.info(
                f"套利者平仓: {signal['side']} {signal['amount']:.2f} "
                f"(PnL={pnl_pct*100:+.2f}%)"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 更新last_price
        self.last_price = current_price
        
        return None
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        return {
            'type': 'arbitrageur',
            'position': self.position,
            'entry_price': self.entry_price,
            'last_price': self.last_price,
            'hold_time': 0 if self.position == 0 else None
        }

