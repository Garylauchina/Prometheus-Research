"""
逆向交易者对手盘

策略特点：
  - 高点做空，低点做多
  - 均值回归策略
  - "别人贪婪我恐惧，别人恐惧我贪婪"
  - 逆市场情绪交易

行为模式：
  - 价格偏离均值 > 阈值 → 开仓
  - 价格回归均值 → 平仓
  - 使用标准差识别极端价格
  - 赌"市场过度反应"
"""

from typing import Dict, Optional
from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContrarianConfig:
    """逆向交易者配置"""
    lookback_period: int = 20           # 回看周期
    entry_threshold: float = 2.0        # 入场阈值（2倍标准差）
    exit_threshold: float = 0.5         # 出场阈值（0.5倍标准差）
    position_size_pct: float = 0.50     # 仓位大小（50%）


class ContrarianAdversary:
    """
    逆向交易者对手盘
    
    核心功能：
      1. 计算价格偏离度（Z-score）
      2. 极端价格识别
      3. 均值回归交易
    """
    
    def __init__(self, config: Optional[ContrarianConfig] = None):
        self.config = config or ContrarianConfig()
        self.position = 0.0  # 当前仓位
        self.entry_price = 0.0
        self.price_history = []
        
        logger.info(
            f"逆向交易者初始化: entry_threshold={self.config.entry_threshold:.1f}σ"
        )
    
    def update_price_history(self, price: float):
        """更新价格历史"""
        self.price_history.append(price)
        
        # 保留回看周期的2倍数据
        max_len = self.config.lookback_period * 2
        if len(self.price_history) > max_len:
            self.price_history.pop(0)
    
    def calculate_zscore(self) -> float:
        """
        计算价格Z-score
        
        Z-score = (当前价格 - 均值) / 标准差
        
        返回：
          - zscore: 标准化偏离度
        """
        if len(self.price_history) < self.config.lookback_period:
            return 0.0
        
        recent_prices = self.price_history[-self.config.lookback_period:]
        
        mean = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        if std == 0:
            return 0.0
        
        current_price = self.price_history[-1]
        zscore = (current_price - mean) / std
        
        return zscore
    
    def should_enter_short(self, zscore: float) -> bool:
        """
        是否应该做空
        
        规则：
          - 价格过高（zscore > entry_threshold）
          - 当前无仓位或持多仓
        """
        return zscore > self.config.entry_threshold and self.position >= 0
    
    def should_enter_long(self, zscore: float) -> bool:
        """
        是否应该做多
        
        规则：
          - 价格过低（zscore < -entry_threshold）
          - 当前无仓位或持空仓
        """
        return zscore < -self.config.entry_threshold and self.position <= 0
    
    def should_exit(self, zscore: float) -> bool:
        """
        是否应该平仓
        
        规则：
          - 价格回归均值（abs(zscore) < exit_threshold）
          - 当前有仓位
        """
        return abs(zscore) < self.config.exit_threshold and self.position != 0
    
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
        
        # 计算Z-score
        zscore = self.calculate_zscore()
        
        # 1. 平仓检查
        if self.should_exit(zscore):
            signal = {
                'action': 'close',
                'side': 'sell' if self.position > 0 else 'buy',
                'amount': abs(self.position),
                'type': 'market',
                'reason': 'mean_reversion'
            }
            
            logger.info(
                f"逆向交易者平仓: {signal['side']} {signal['amount']:.2f} "
                f"(zscore={zscore:+.2f}, entry={self.entry_price:.2f})"
            )
            
            # 重置仓位
            self.position = 0.0
            self.entry_price = 0.0
            
            return signal
        
        # 2. 开仓信号
        if self.should_enter_short(zscore):
            signal = {
                'action': 'open',
                'side': 'sell',
                'amount': self.config.position_size_pct,
                'type': 'market',
                'reason': 'overbought'
            }
            
            logger.info(
                f"逆向交易者做空: zscore={zscore:+.2f} (超买) "
                f"price={current_price:.2f}"
            )
            
            # 更新仓位
            self.position = -signal['amount']
            self.entry_price = current_price
            
            return signal
        
        elif self.should_enter_long(zscore):
            signal = {
                'action': 'open',
                'side': 'buy',
                'amount': self.config.position_size_pct,
                'type': 'market',
                'reason': 'oversold'
            }
            
            logger.info(
                f"逆向交易者做多: zscore={zscore:+.2f} (超卖) "
                f"price={current_price:.2f}"
            )
            
            # 更新仓位
            self.position = signal['amount']
            self.entry_price = current_price
            
            return signal
        
        # 3. 持仓中，无操作
        return None
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        zscore = self.calculate_zscore()
        
        mean = np.mean(self.price_history[-self.config.lookback_period:]) if len(self.price_history) >= self.config.lookback_period else 0
        std = np.std(self.price_history[-self.config.lookback_period:]) if len(self.price_history) >= self.config.lookback_period else 0
        
        return {
            'type': 'contrarian',
            'position': self.position,
            'entry_price': self.entry_price,
            'zscore': zscore,
            'mean': mean,
            'std': std
        }

