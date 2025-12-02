"""
双账簿系统 - Prometheus v4.0
公共账簿 + 私有账簿 + 访问权限控制

设计理念：
- PublicLedger: 只有一本，Supervisor管理，用于监督和统计
- PrivateLedger: 每个Agent一本，Agent自己管理，用于决策
- Agent死亡时，私有账簿销毁，公共账簿归档

访问权限：
- Mastermind: 只读PublicLedger（整体统计）
- Supervisor: 读写PublicLedger，只读PrivateLedger
- Agent: 读写自己的PrivateLedger
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


# ========== 访问权限控制 ==========

class Role(Enum):
    """角色定义"""
    MASTERMIND = "mastermind"
    SUPERVISOR = "supervisor"
    AGENT = "agent"


class AccessDeniedException(Exception):
    """访问被拒绝异常"""
    pass


@dataclass
class TradeRecord:
    """交易记录（公私账簿共用）"""
    agent_id: str
    trade_id: str
    trade_type: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: datetime
    confidence: float
    pnl: Optional[float] = None  # 平仓时才有
    is_real: bool = True  # True=实际交易, False=虚拟交易
    
    def to_dict(self):
        """转为字典（用于序列化）"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class PositionRecord:
    """持仓记录"""
    agent_id: str
    side: str  # 'long' or 'short'
    amount: float
    entry_price: float
    entry_time: datetime
    confidence: float
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """计算未实现盈亏"""
        if self.side == 'long':
            return (current_price - self.entry_price) * self.amount
        else:
            return (self.entry_price - current_price) * self.amount


# ========== 私有账簿（Agent自己管理）==========

class PrivateLedger:
    """
    私有账簿 - Agent的私人账本
    
    每个Agent拥有一个私有账簿，记录自己的状态
    Agent决策时查询自己的私有账簿
    
    访问权限：
    - Agent（owner）: 读写
    - Supervisor: 只读（验证）
    - Mastermind: 无权访问
    """
    
    def __init__(self, agent_id: str, initial_capital: float = 10000):
        self.agent_id = agent_id
        self._owner_id = agent_id  # 所有者ID
        
        # 资金状态
        self.virtual_capital = initial_capital
        self.initial_capital = initial_capital
        
        # 持仓状态
        self.virtual_position: Optional[PositionRecord] = None
        self.real_position: Optional[PositionRecord] = None
        
        # 交易历史（只记录自己的）
        self.trade_history: List[TradeRecord] = []
        
        # 统计数据
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.trade_count = 0
        
        # 时间戳
        self.created_at = datetime.now()
        self.last_trade_time: Optional[datetime] = None
        
        logger.debug(f"私有账簿创建: {agent_id}")
    
    # ========== 访问权限控制 ==========
    
    def _check_read_access(self, caller_role: Role, caller_id: str = None):
        """检查读取权限"""
        if caller_role == Role.AGENT:
            # Agent只能访问自己的账簿
            if caller_id != self._owner_id:
                raise AccessDeniedException(
                    f"Agent {caller_id} 无权访问 {self._owner_id} 的私有账簿"
                )
        elif caller_role == Role.SUPERVISOR:
            # Supervisor可以只读任何Agent的私有账簿
            pass
        elif caller_role == Role.MASTERMIND:
            # Mastermind无权访问私有账簿
            raise AccessDeniedException(
                "Mastermind 无权访问私有账簿"
            )
    
    def _check_write_access(self, caller_role: Role, caller_id: str = None):
        """检查写入权限"""
        if caller_role == Role.AGENT:
            # Agent只能修改自己的账簿
            if caller_id != self._owner_id:
                raise AccessDeniedException(
                    f"Agent {caller_id} 无权修改 {self._owner_id} 的私有账簿"
                )
        elif caller_role == Role.SUPERVISOR:
            # Supervisor通过AgentAccountSystem间接修改（系统操作）
            # caller_id=='system' 表示这是系统操作，允许
            if caller_id != 'system':
                raise AccessDeniedException(
                    "Supervisor 只能通过AgentAccountSystem修改私有账簿"
                )
        elif caller_role == Role.MASTERMIND:
            # Mastermind无权访问私有账簿
            raise AccessDeniedException(
                "Mastermind 无权访问私有账簿"
            )
    
    # ========== 状态查询（Agent决策时使用）==========
    
    def has_position(self, position_type='real') -> bool:
        """检查是否有持仓"""
        if position_type == 'real':
            return self.real_position is not None
        else:
            return self.virtual_position is not None
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """获取未实现盈亏"""
        if self.real_position:
            return self.real_position.get_unrealized_pnl(current_price)
        return 0.0
    
    def get_balance(self) -> float:
        """获取可用资金"""
        return self.virtual_capital
    
    def can_afford(self, amount: float, price: float) -> bool:
        """检查是否能承担该交易"""
        required = amount * price
        return self.virtual_capital >= required
    
    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count
    
    def get_summary(self, current_price: float = 0, caller_role: Role = Role.AGENT, caller_id: str = None) -> Dict:
        """
        获取账户摘要（Agent决策时调用）
        
        这是Agent了解自己状态的主要方法
        
        Args:
            current_price: 当前价格
            caller_role: 调用者角色
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_read_access(caller_role, caller_id)
        
        unrealized_pnl = self.get_unrealized_pnl(current_price) if current_price > 0 else 0.0
        
        return {
            'agent_id': self.agent_id,
            'balance': self.virtual_capital,
            'initial_capital': self.initial_capital,
            'capital_ratio': self.virtual_capital / self.initial_capital,
            'has_position': self.has_position('real'),
            'position_info': {
                'amount': self.real_position.amount if self.real_position else 0,
                'entry_price': self.real_position.entry_price if self.real_position else 0,
                'unrealized_pnl': unrealized_pnl
            } if self.real_position else None,
            'total_pnl': self.total_pnl,
            'unrealized_pnl': unrealized_pnl,
            'win_rate': self.get_win_rate(),
            'trade_count': self.trade_count,
            'last_trade_time': self.last_trade_time
        }
    
    # ========== 交易记录（Agent和Supervisor都可以调用）==========
    
    def record_buy(self, amount: float, price: float, confidence: float, is_real=True, 
                   caller_role: Role = Role.AGENT, caller_id: str = None):
        """
        记录买入
        
        Args:
            caller_role: 调用者角色（用于权限检查）
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        
        position = PositionRecord(
            agent_id=self.agent_id,
            side='long',
            amount=amount,
            entry_price=price,
            entry_time=datetime.now(),
            confidence=confidence
        )
        
        if is_real:
            self.real_position = position
        else:
            self.virtual_position = position
        
        # 记录交易
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trade_type='buy',
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            is_real=is_real
        )
        self.trade_history.append(trade)
        self.trade_count += 1
        self.last_trade_time = datetime.now()
        
        logger.debug(f"{self.agent_id}: 私有账簿记录买入 {amount} @ ${price}")
    
    def record_sell(self, price: float, confidence: float, is_real=True,
                    caller_role: Role = Role.AGENT, caller_id: str = None) -> float:
        """
        记录卖出，返回盈亏
        
        Args:
            caller_role: 调用者角色（用于权限检查）
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        
        position = self.real_position if is_real else self.virtual_position
        
        if not position:
            logger.warning(f"{self.agent_id}: 无持仓，无法记录卖出")
            return 0.0
        
        # 计算盈亏
        pnl = position.get_unrealized_pnl(price)
        
        # 更新统计
        self.total_pnl += pnl
        self.virtual_capital += pnl
        
        if pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        # 记录交易
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trade_type='sell',
            amount=position.amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            pnl=pnl,
            is_real=is_real
        )
        self.trade_history.append(trade)
        self.last_trade_time = datetime.now()
        
        # 清除持仓
        if is_real:
            self.real_position = None
        else:
            self.virtual_position = None
        
        logger.debug(f"{self.agent_id}: 私有账簿记录卖出 PnL=${pnl:.2f}")
        return pnl


# ========== 公共账簿（Supervisor管理）==========

class PublicLedger:
    """
    公共账簿 - Supervisor的总账本
    
    只有一本公共账簿，记录所有Agent的交易
    用于监督、审计、统计、排名
    
    访问权限：
    - Mastermind: 只读（整体统计）
    - Supervisor: 读写（管理）
    - Agent: 无权访问
    """
    
    def __init__(self):
        # 所有Agent的交易记录
        self.all_trades: List[TradeRecord] = []
        
        # 按Agent索引的交易记录
        self.trades_by_agent: Dict[str, List[TradeRecord]] = {}
        
        # Agent余额快照
        self.agent_balances: Dict[str, float] = {}
        
        # Agent统计数据
        self.agent_stats: Dict[str, Dict] = {}
        
        # 死亡Agent归档
        self.archived_agents: Dict[str, Dict] = {}
        
        # 创建时间
        self.created_at = datetime.now()
        
        logger.info("公共账簿已创建")
    
    # ========== 访问权限控制 ==========
    
    def _check_read_access(self, caller_role: Role):
        """检查读取权限"""
        if caller_role == Role.AGENT:
            # Agent无权访问公共账簿
            raise AccessDeniedException(
                "Agent 无权访问公共账簿"
            )
        # Mastermind和Supervisor都可以读取
    
    def _check_write_access(self, caller_role: Role):
        """检查写入权限"""
        if caller_role != Role.SUPERVISOR:
            # 只有Supervisor可以写入公共账簿
            raise AccessDeniedException(
                f"{caller_role.value} 无权修改公共账簿，只有Supervisor可以修改"
            )
    
    # ========== 记录交易（Supervisor调用）==========
    
    def record_trade(self, trade: TradeRecord, caller_role: Role = Role.SUPERVISOR):
        """
        记录交易到公共账簿
        
        Supervisor在执行交易后调用此方法
        
        Args:
            caller_role: 调用者角色（用于权限检查）
        """
        # 权限检查
        self._check_write_access(caller_role)
        
        # 添加到总记录
        self.all_trades.append(trade)
        
        # 添加到Agent索引
        if trade.agent_id not in self.trades_by_agent:
            self.trades_by_agent[trade.agent_id] = []
        self.trades_by_agent[trade.agent_id].append(trade)
        
        logger.debug(f"公共账簿记录: {trade.agent_id} {trade.trade_type} @ ${trade.price}")
    
    def update_agent_balance(self, agent_id: str, balance: float):
        """更新Agent余额快照"""
        self.agent_balances[agent_id] = balance
    
    def update_agent_stats(self, agent_id: str, stats: Dict):
        """更新Agent统计数据"""
        self.agent_stats[agent_id] = {
            **stats,
            'last_update': datetime.now()
        }
    
    # ========== 查询和统计（Supervisor调用）==========
    
    def get_agent_trades(self, agent_id: str) -> List[TradeRecord]:
        """获取某个Agent的所有交易"""
        return self.trades_by_agent.get(agent_id, [])
    
    def get_all_trades(self, limit: int = None) -> List[TradeRecord]:
        """获取所有交易（可限制数量）"""
        if limit:
            return self.all_trades[-limit:]
        return self.all_trades
    
    def get_agent_balance(self, agent_id: str) -> float:
        """获取Agent余额"""
        return self.agent_balances.get(agent_id, 0.0)
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """获取Agent统计数据"""
        return self.agent_stats.get(agent_id)
    
    def get_all_agent_stats(self, caller_role: Role = Role.SUPERVISOR) -> Dict[str, Dict]:
        """
        获取所有活跃Agent的统计数据
        
        Args:
            caller_role: 调用者角色（用于权限检查）
        """
        # 权限检查
        self._check_read_access(caller_role)
        
        # 排除已归档的Agent
        return {
            agent_id: stats 
            for agent_id, stats in self.agent_stats.items()
            if agent_id not in self.archived_agents
        }
    
    def get_top_performers(self, limit: int = 10, caller_role: Role = Role.SUPERVISOR) -> List[tuple]:
        """
        获取表现最好的Agent
        
        Args:
            caller_role: 调用者角色（用于权限检查）
        """
        # 权限检查
        self._check_read_access(caller_role)
        
        active_stats = self.get_all_agent_stats(caller_role)
        
        # 按总盈亏排序
        ranked = sorted(
            active_stats.items(),
            key=lambda x: x[1].get('total_pnl', 0),
            reverse=True
        )
        
        return ranked[:limit]
    
    # ========== Agent死亡处理 ==========
    
    def archive_agent(self, agent_id: str, death_reason: str = "unknown"):
        """
        归档死亡Agent的数据
        
        当Agent死亡时：
        1. 将Agent数据移到归档区
        2. 从活跃列表中移除
        3. 保留必要的统计信息
        4. 清理详细交易记录（可选）
        """
        # 收集Agent数据
        agent_data = {
            'agent_id': agent_id,
            'death_time': datetime.now(),
            'death_reason': death_reason,
            'final_balance': self.agent_balances.get(agent_id, 0),
            'final_stats': self.agent_stats.get(agent_id, {}),
            'total_trades': len(self.trades_by_agent.get(agent_id, [])),
            # 只保留最后10笔交易记录
            'last_trades': [
                trade.to_dict() 
                for trade in self.trades_by_agent.get(agent_id, [])[-10:]
            ]
        }
        
        # 归档
        self.archived_agents[agent_id] = agent_data
        
        # 清理活跃数据
        if agent_id in self.trades_by_agent:
            del self.trades_by_agent[agent_id]
        if agent_id in self.agent_balances:
            del self.agent_balances[agent_id]
        if agent_id in self.agent_stats:
            del self.agent_stats[agent_id]
        
        logger.info(f"Agent已归档: {agent_id}, 原因: {death_reason}")
    
    def get_archived_agents(self) -> Dict[str, Dict]:
        """获取所有归档的Agent"""
        return self.archived_agents
    
    def get_archive_summary(self) -> Dict:
        """获取归档摘要"""
        return {
            'archived_count': len(self.archived_agents),
            'active_count': len(self.agent_stats),
            'total_trades': len(self.all_trades),
            'archive_list': list(self.archived_agents.keys())
        }
    
    # ========== 数据导出 ==========
    
    def export_to_json(self, filepath: str):
        """导出公共账簿到JSON文件"""
        data = {
            'created_at': self.created_at.isoformat(),
            'export_time': datetime.now().isoformat(),
            'total_trades': len(self.all_trades),
            'active_agents': len(self.agent_stats),
            'archived_agents': len(self.archived_agents),
            'agent_stats': self.agent_stats,
            'archived': self.archived_agents
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"公共账簿已导出: {filepath}")


# ========== 账户系统（组合私有+公共）==========

class AgentAccountSystem:
    """
    Agent账户系统（组合版）
    
    每个Agent拥有：
    - private_ledger: 自己管理，决策依据
    - 在public_ledger中有记录：Supervisor管理，监督审计
    """
    
    def __init__(self, agent_id: str, initial_capital: float, public_ledger: PublicLedger):
        self.agent_id = agent_id
        
        # 私有账簿（Agent自己访问）
        self.private_ledger = PrivateLedger(agent_id, initial_capital)
        
        # 公共账簿引用（只读，用于提交数据）
        self.public_ledger = public_ledger
        
        # 初始化公共账簿中的记录
        self.public_ledger.update_agent_balance(agent_id, initial_capital)
        self.public_ledger.update_agent_stats(agent_id, {
            'initial_capital': initial_capital,
            'created_at': datetime.now()
        })
        
        logger.info(f"账户系统创建: {agent_id}")
    
    def record_trade(self, trade_type: str, amount: float, price: float, confidence: float, is_real=True,
                    caller_role: Role = Role.SUPERVISOR):
        """
        记录交易（同时更新私有和公共账簿）
        
        只有Supervisor才能调用此方法
        
        Args:
            trade_type: 'buy' or 'sell'
            amount: 交易数量
            price: 交易价格
            confidence: 信心度
            is_real: 是否实际交易
            caller_role: 调用者角色
        """
        # Supervisor调用，有权限更新私有账簿（但以系统身份）
        # 1. 更新私有账簿（Supervisor以系统身份更新，不需要检查）
        if trade_type == 'buy':
            self.private_ledger.record_buy(
                amount, price, confidence, is_real,
                caller_role=Role.SUPERVISOR, caller_id='system'
            )
            pnl = None
        else:
            pnl = self.private_ledger.record_sell(
                price, confidence, is_real,
                caller_role=Role.SUPERVISOR, caller_id='system'
            )
        
        # 2. 提交到公共账簿
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trade_type=trade_type,
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            pnl=pnl,
            is_real=is_real
        )
        self.public_ledger.record_trade(trade, caller_role=caller_role)
        
        # 3. 更新公共账簿中的余额和统计
        self.public_ledger.update_agent_balance(self.agent_id, self.private_ledger.virtual_capital)
        self.public_ledger.update_agent_stats(self.agent_id, {
            'total_pnl': self.private_ledger.total_pnl,
            'trade_count': self.private_ledger.trade_count,
            'win_rate': self.private_ledger.get_win_rate()
        })
    
    def get_status_for_decision(self, current_price: float, 
                                caller_role: Role = Role.AGENT, 
                                caller_id: str = None) -> Dict:
        """
        获取决策所需的状态（从私有账簿）
        
        Agent决策时调用此方法
        
        Args:
            current_price: 当前价格
            caller_role: 调用者角色
            caller_id: 调用者ID
        """
        return self.private_ledger.get_summary(
            current_price, 
            caller_role=caller_role, 
            caller_id=caller_id
        )
    
    def archive(self, death_reason: str):
        """Agent死亡，归档数据"""
        self.public_ledger.archive_agent(self.agent_id, death_reason)

