"""
Agent账户系统 - Prometheus v4.0
每个Agent的完整账户，记录虚拟和实际交易状态
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓信息"""
    side: str  # 'long' or 'short'
    amount: float
    entry_price: float
    entry_time: datetime
    confidence: float = 0.0


@dataclass
class TradeRecord:
    """交易记录"""
    trade_type: str  # 'buy' or 'sell'
    amount: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: float
    confidence: float


class AgentAccount:
    """
    Agent账户系统
    
    每个Agent拥有一个完整的账户，记录：
    - 虚拟资金和持仓
    - 实际持仓
    - 交易历史
    - 盈亏统计
    
    Agent通过账户查询自己的状态，Supervisor通过账户验证请求
    """
    
    def __init__(self, agent_id: str, initial_capital: float = 10000):
        """
        初始化Agent账户
        
        Args:
            agent_id: Agent ID
            initial_capital: 初始虚拟资金
        """
        self.agent_id = agent_id
        
        # ===== 虚拟账户 =====
        self.virtual_capital = initial_capital
        self.initial_capital = initial_capital
        self.virtual_positions: List[Position] = []
        self.virtual_trades: List[TradeRecord] = []
        
        # ===== 实际持仓 =====
        self.real_position: Optional[Position] = None
        self.real_trades: List[TradeRecord] = []
        
        # ===== 统计数据 =====
        self.total_pnl = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.trade_count = 0
        
        # ===== 时间戳 =====
        self.created_at = datetime.now()
        self.last_trade_time: Optional[datetime] = None
        
        logger.info(f"账户已创建: {agent_id}, 初始资金: {initial_capital} USDT")
    
    # ========== 状态查询接口 ==========
    
    def has_virtual_position(self) -> bool:
        """检查是否有虚拟持仓"""
        return len(self.virtual_positions) > 0
    
    def has_real_position(self) -> bool:
        """检查是否有实际持仓"""
        return self.real_position is not None
    
    def get_virtual_position_count(self) -> int:
        """获取虚拟持仓数量"""
        return len(self.virtual_positions)
    
    def get_real_position_info(self) -> Optional[Dict]:
        """获取实际持仓信息"""
        if self.real_position:
            return {
                'side': self.real_position.side,
                'amount': self.real_position.amount,
                'entry_price': self.real_position.entry_price,
                'entry_time': self.real_position.entry_time
            }
        return None
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """获取未实现盈亏"""
        if self.real_position:
            return (current_price - self.real_position.entry_price) * self.real_position.amount
        return 0.0
    
    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count
    
    # ========== 合法性检查 ==========
    
    def can_buy(self, amount: float, price: float) -> tuple[bool, str]:
        """
        检查是否能买入
        
        Returns:
            (bool, str): (是否可以, 原因)
        """
        # 检查1: 是否已有实际持仓
        if self.has_real_position():
            return False, "已有实际持仓"
        
        # 检查2: 虚拟资金是否足够
        required_capital = amount * price
        if self.virtual_capital < required_capital:
            return False, f"虚拟资金不足 (需要${required_capital:.2f}, 可用${self.virtual_capital:.2f})"
        
        # 检查3: 冷却期（可选）
        if self.last_trade_time:
            seconds_since_last = (datetime.now() - self.last_trade_time).total_seconds()
            if seconds_since_last < 60:  # 至少间隔1分钟
                return False, f"冷却期中 (还需{60-seconds_since_last:.0f}秒)"
        
        return True, "可以买入"
    
    def can_sell(self) -> tuple[bool, str]:
        """
        检查是否能卖出
        
        Returns:
            (bool, str): (是否可以, 原因)
        """
        # 检查1: 是否有虚拟持仓
        if not self.has_virtual_position():
            return False, "无虚拟持仓"
        
        # 检查2: 是否有实际持仓
        if not self.has_real_position():
            return False, "无实际持仓"
        
        return True, "可以卖出"
    
    # ========== 交易记录 ==========
    
    def record_virtual_buy(self, amount: float, price: float, confidence: float):
        """记录虚拟买入"""
        position = Position(
            side='long',
            amount=amount,
            entry_price=price,
            entry_time=datetime.now(),
            confidence=confidence
        )
        self.virtual_positions.append(position)
        self.trade_count += 1
        logger.debug(f"{self.agent_id}: 虚拟开多 {amount} @ ${price}")
    
    def record_virtual_sell(self, current_price: float, confidence: float) -> float:
        """
        记录虚拟卖出
        
        Returns:
            float: 本次交易盈亏
        """
        if not self.virtual_positions:
            return 0.0
        
        # 平掉第一个持仓（FIFO）
        position = self.virtual_positions.pop(0)
        pnl = (current_price - position.entry_price) * position.amount
        
        # 更新统计
        self.realized_pnl += pnl
        self.total_pnl += pnl
        self.virtual_capital += pnl
        
        if pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        # 记录交易
        trade = TradeRecord(
            trade_type='sell',
            amount=position.amount,
            entry_price=position.entry_price,
            exit_price=current_price,
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            pnl=pnl,
            confidence=confidence
        )
        self.virtual_trades.append(trade)
        
        logger.debug(f"{self.agent_id}: 虚拟平仓 PnL=${pnl:.2f}")
        return pnl
    
    def record_real_buy(self, amount: float, price: float, confidence: float):
        """记录实际买入"""
        self.real_position = Position(
            side='long',
            amount=amount,
            entry_price=price,
            entry_time=datetime.now(),
            confidence=confidence
        )
        self.last_trade_time = datetime.now()
        logger.info(f"{self.agent_id}: 实际开多 {amount} @ ${price}")
    
    def record_real_sell(self, current_price: float, confidence: float) -> float:
        """
        记录实际卖出
        
        Returns:
            float: 本次交易盈亏
        """
        if not self.real_position:
            return 0.0
        
        # 计算盈亏
        pnl = (current_price - self.real_position.entry_price) * self.real_position.amount
        
        # 记录交易
        trade = TradeRecord(
            trade_type='sell',
            amount=self.real_position.amount,
            entry_price=self.real_position.entry_price,
            exit_price=current_price,
            entry_time=self.real_position.entry_time,
            exit_time=datetime.now(),
            pnl=pnl,
            confidence=confidence
        )
        self.real_trades.append(trade)
        
        # 清除实际持仓
        self.real_position = None
        self.last_trade_time = datetime.now()
        
        logger.info(f"{self.agent_id}: 实际平仓 PnL=${pnl:.2f}")
        return pnl
    
    def calculate_unrealized_pnl(self, current_price: float):
        """计算未实现盈亏"""
        self.unrealized_pnl = 0.0
        
        # 虚拟持仓的未实现盈亏
        for pos in self.virtual_positions:
            self.unrealized_pnl += (current_price - pos.entry_price) * pos.amount
    
    def get_summary(self, current_price: float = 0) -> Dict:
        """
        获取账户摘要
        
        Agent在决策时调用此方法了解自己的状态
        """
        if current_price > 0:
            self.calculate_unrealized_pnl(current_price)
        
        return {
            'agent_id': self.agent_id,
            'virtual_capital': self.virtual_capital,
            'initial_capital': self.initial_capital,
            'capital_ratio': self.virtual_capital / self.initial_capital,
            'has_virtual_position': self.has_virtual_position(),
            'virtual_position_count': len(self.virtual_positions),
            'has_real_position': self.has_real_position(),
            'real_position': self.get_real_position_info(),
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'win_rate': self.get_win_rate(),
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'last_trade_time': self.last_trade_time
        }

