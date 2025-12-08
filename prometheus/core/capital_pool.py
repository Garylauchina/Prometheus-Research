"""
CapitalPool（资金池）- Prometheus v6.0
====================================

系统资金池，统一管理所有资金流动

核心职责：
1. 记录系统总注资
2. 管理可分配资金池
3. 回收淘汰Agent资金
4. 分配新Agent资金
5. 提供资金统计和对账

设计原则：
- 封装所有资金操作
- 不允许外部直接修改余额
- 所有操作都有日志
- 资金守恒验证
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """资金流动类型"""
    INVEST = "invest"          # 系统注资
    ALLOCATE = "allocate"      # 分配给Agent
    RECLAIM = "reclaim"        # 回收Agent资金
    ADJUSTMENT = "adjustment"  # 调整（异常情况）


@dataclass
class CapitalTransaction:
    """资金流动记录"""
    timestamp: datetime
    transaction_type: TransactionType
    amount: float
    agent_id: Optional[str]  # None表示系统级操作
    reason: str
    pool_balance_before: float
    pool_balance_after: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'type': self.transaction_type.value,
            'amount': self.amount,
            'agent_id': self.agent_id,
            'reason': self.reason,
            'pool_before': self.pool_balance_before,
            'pool_after': self.pool_balance_after
        }


class CapitalPool:
    """
    系统资金池
    
    资金守恒原则：
    系统总资金 = Σ(Agent当前资金) + 资金池余额
    系统总资金 ≈ 系统总注资 + 交易总盈亏 - 总手续费
    
    使用示例：
    >>> pool = CapitalPool()
    >>> pool.invest(amount=500000, source="genesis")
    >>> allocated = pool.allocate(amount=10000, agent_id="Agent_1", reason="genesis")
    >>> reclaimed = pool.reclaim(amount=5000, agent_id="Agent_1", reason="elimination")
    """
    
    def __init__(self):
        """初始化资金池"""
        self.total_invested = 0.0      # 系统总注资（只增不减）
        self.available_pool = 0.0      # 可分配资金池
        self.transaction_log: List[CapitalTransaction] = []  # 资金流动日志
        
        # 统计计数器
        self.invest_count = 0
        self.allocate_count = 0
        self.reclaim_count = 0
        
        logger.info("💰 CapitalPool已初始化")
    
    # ========== 注资接口 ==========
    
    def invest(self, amount: float, source: str = "system") -> bool:
        """
        系统注资
        
        Args:
            amount: 注资金额（必须>0）
            source: 资金来源（genesis/additional_funding/etc）
        
        Returns:
            bool: 是否成功
        """
        if amount <= 0:
            logger.error(f"❌ 注资失败：金额必须>0 (amount={amount})")
            return False
        
        before = self.available_pool
        
        # 增加总注资
        self.total_invested += amount
        
        # 增加可分配资金池
        self.available_pool += amount
        
        after = self.available_pool
        
        # 记录交易
        transaction = CapitalTransaction(
            timestamp=datetime.now(),
            transaction_type=TransactionType.INVEST,
            amount=amount,
            agent_id=None,  # 系统级操作
            reason=source,
            pool_balance_before=before,
            pool_balance_after=after
        )
        self.transaction_log.append(transaction)
        self.invest_count += 1
        
        logger.info(f"💰 系统注资: +${amount:,.2f} ({source})")
        logger.info(f"   总注资: ${self.total_invested:,.2f}")
        logger.info(f"   资金池: ${before:,.2f} → ${after:,.2f}")
        
        return True
    
    # ========== 分配接口 ==========
    
    def allocate(self, amount: float, agent_id: str, reason: str) -> float:
        """
        分配资金给Agent
        
        Args:
            amount: 期望分配金额
            agent_id: Agent ID
            reason: 分配原因（genesis/breeding/etc）
        
        Returns:
            float: 实际分配金额（可能小于期望，如果资金池不足）
        """
        if amount <= 0:
            logger.error(f"❌ 分配失败：金额必须>0 (amount={amount})")
            return 0.0
        
        before = self.available_pool
        
        # 检查资金池余额
        if self.available_pool <= 0:
            logger.error(f"❌ 分配失败：资金池已耗尽 (agent={agent_id}, requested=${amount:,.2f})")
            return 0.0
        
        # 实际分配金额（不超过资金池余额）
        actual_allocated = min(amount, self.available_pool)
        
        # 扣除资金池
        self.available_pool -= actual_allocated
        
        after = self.available_pool
        
        # 记录交易
        transaction = CapitalTransaction(
            timestamp=datetime.now(),
            transaction_type=TransactionType.ALLOCATE,
            amount=actual_allocated,
            agent_id=agent_id,
            reason=reason,
            pool_balance_before=before,
            pool_balance_after=after
        )
        self.transaction_log.append(transaction)
        self.allocate_count += 1
        
        # 日志输出
        if actual_allocated < amount:
            logger.warning(f"⚠️ 资金池不足：期望${amount:,.2f}，实际${actual_allocated:,.2f}")
        
        logger.info(f"💰 分配资金: ${actual_allocated:,.2f} → {agent_id} ({reason})")
        logger.info(f"   资金池: ${before:,.2f} → ${after:,.2f}")
        
        return actual_allocated
    
    # ========== 回收接口 ==========
    
    def reclaim(self, amount: float, agent_id: str, reason: str) -> bool:
        """
        回收Agent资金（淘汰时）
        
        Args:
            amount: 回收金额
            agent_id: Agent ID
            reason: 回收原因（elimination/suicide/etc）
        
        Returns:
            bool: 是否成功
        """
        if amount < 0:
            logger.error(f"❌ 回收失败：金额不能<0 (amount={amount})")
            return False
        
        if amount == 0:
            logger.debug(f"⚠️ 回收金额为0 (agent={agent_id})")
            return True
        
        before = self.available_pool
        
        # 回收到资金池
        self.available_pool += amount
        
        after = self.available_pool
        
        # 记录交易
        transaction = CapitalTransaction(
            timestamp=datetime.now(),
            transaction_type=TransactionType.RECLAIM,
            amount=amount,
            agent_id=agent_id,
            reason=reason,
            pool_balance_before=before,
            pool_balance_after=after
        )
        self.transaction_log.append(transaction)
        self.reclaim_count += 1
        
        logger.info(f"💰 回收资金: +${amount:,.2f} ← {agent_id} ({reason})")
        logger.info(f"   资金池: ${before:,.2f} → ${after:,.2f}")
        
        return True
    
    # ========== 统计接口 ==========
    
    def get_summary(self) -> Dict:
        """
        获取资金池统计摘要
        
        Returns:
            dict: {
                'total_invested': float,    # 系统总注资
                'available_pool': float,    # 可分配资金池
                'total_allocated': float,   # 累计分配
                'total_reclaimed': float,   # 累计回收
                'net_flow': float,          # 净流出（分配-回收）
                'transaction_count': int,   # 交易总数
                'invest_count': int,        # 注资次数
                'allocate_count': int,      # 分配次数
                'reclaim_count': int        # 回收次数
            }
        """
        # 统计累计分配和回收
        total_allocated = sum(
            t.amount for t in self.transaction_log 
            if t.transaction_type == TransactionType.ALLOCATE
        )
        total_reclaimed = sum(
            t.amount for t in self.transaction_log 
            if t.transaction_type == TransactionType.RECLAIM
        )
        
        net_flow = total_allocated - total_reclaimed
        
        return {
            'total_invested': self.total_invested,
            'available_pool': self.available_pool,
            'total_allocated': total_allocated,
            'total_reclaimed': total_reclaimed,
            'net_flow': net_flow,
            'transaction_count': len(self.transaction_log),
            'invest_count': self.invest_count,
            'allocate_count': self.allocate_count,
            'reclaim_count': self.reclaim_count
        }
    
    def get_transaction_log(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取资金流动日志
        
        Args:
            limit: 返回最近N条记录（None=全部）
        
        Returns:
            List[dict]: 交易记录列表
        """
        if limit:
            return [t.to_dict() for t in self.transaction_log[-limit:]]
        return [t.to_dict() for t in self.transaction_log]
    
    # ========== 对账接口 ==========
    
    def reconcile(self, agents: List, current_price: float = 0) -> Dict:
        """
        系统级对账：验证资金池一致性
        
        验证逻辑：
        1. 资金池余额 = 总注资 - 已分配 + 已回收
        2. 系统总资产 = Agent资金 + 资金池余额
        3. 系统盈亏 = 系统总资产 - 总注资 (含交易盈亏)
        
        注意：
        - 本方法验证资金流一致性，不验证系统是否盈利
        - 交易盈亏是正常现象，通过杠杆交易可能产生高额收益
        
        Args:
            agents: Agent列表
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            dict: {
                'passed': bool,                # 资金池一致性是否通过
                'total_invested': float,       # 系统总注资
                'total_agent_capital': float,  # Agent总资金（含未实现盈亏）
                'pool_balance': float,         # 资金池余额
                'system_total': float,         # 系统总资产
                'total_allocated': float,      # 已分配总额
                'total_reclaimed': float,      # 已回收总额
                'expected_pool': float,        # 理论池余额
                'pool_discrepancy': float,     # 池差异
                'pool_discrepancy_pct': float, # 池差异百分比
                'system_pnl': float,           # 系统净盈亏
                'system_roi_pct': float,       # 系统ROI百分比
                'tolerance_pct': float         # 容差百分比
            }
        """
        # 1. 统计Agent总资金（含未实现盈亏）
        total_agent_capital = 0.0
        agent_count = 0
        
        for agent in agents:
            if hasattr(agent, 'account') and agent.account:
                agent_count += 1
                # 已实现资金
                realized_capital = agent.account.private_ledger.virtual_capital
                # 未实现盈亏
                unrealized_pnl = 0.0
                if current_price > 0 and hasattr(agent, 'calculate_unrealized_pnl'):
                    unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
                
                total_agent_capital += (realized_capital + unrealized_pnl)
        
        # 2. 系统总资金 = Agent资金 + 资金池
        system_total = total_agent_capital + self.available_pool
        
        # 3. 验证资金池内部一致性（而非系统盈亏）
        # 资金池余额 = 总注资 - 已分配 + 已回收
        total_allocated = sum(
            t.amount for t in self.transaction_log 
            if t.transaction_type == TransactionType.ALLOCATE
        )
        total_reclaimed = sum(
            t.amount for t in self.transaction_log 
            if t.transaction_type == TransactionType.RECLAIM
        )
        
        expected_pool = self.total_invested - total_allocated + total_reclaimed
        pool_discrepancy = self.available_pool - expected_pool
        pool_discrepancy_pct = (pool_discrepancy / self.total_invested * 100) if self.total_invested > 0 else 0
        
        # 4. 计算系统盈亏（用于报告，不用于验证）
        system_pnl = system_total - self.total_invested
        system_roi_pct = (system_pnl / self.total_invested * 100) if self.total_invested > 0 else 0
        
        # 5. 判断是否通过（只验证资金池一致性，容差±1%）
        tolerance_pct = 1.0
        passed = abs(pool_discrepancy_pct) <= tolerance_pct
        
        # 6. 日志输出
        logger.info("=" * 70)
        logger.info("💰 系统级对账")
        logger.info("=" * 70)
        logger.info(f"系统总注资: ${self.total_invested:,.2f}")
        logger.info(f"Agent总资金: ${total_agent_capital:,.2f} ({agent_count}个Agent)")
        logger.info(f"资金池余额: ${self.available_pool:,.2f}")
        logger.info(f"系统总资产: ${system_total:,.2f}")
        logger.info("")
        logger.info(f"💸 资金流验证:")
        logger.info(f"   已分配: ${total_allocated:,.2f}")
        logger.info(f"   已回收: ${total_reclaimed:,.2f}")
        logger.info(f"   理论池余额: ${expected_pool:,.2f}")
        logger.info(f"   实际池余额: ${self.available_pool:,.2f}")
        logger.info(f"   池差异: ${pool_discrepancy:+,.2f} ({pool_discrepancy_pct:+.2f}%)")
        logger.info("")
        logger.info(f"📈 系统盈亏:")
        logger.info(f"   净盈亏: ${system_pnl:+,.2f}")
        logger.info(f"   系统ROI: {system_roi_pct:+.2f}%")
        
        if passed:
            logger.info("✅ 资金池一致性验证通过")
        else:
            logger.error(f"❌ 资金池一致性验证失败：差异超出容差({tolerance_pct}%)")
        
        logger.info("=" * 70)
        
        return {
            'passed': passed,
            'total_invested': self.total_invested,
            'total_agent_capital': total_agent_capital,
            'pool_balance': self.available_pool,
            'system_total': system_total,
            'total_allocated': total_allocated,
            'total_reclaimed': total_reclaimed,
            'expected_pool': expected_pool,
            'pool_discrepancy': pool_discrepancy,
            'pool_discrepancy_pct': pool_discrepancy_pct,
            'system_pnl': system_pnl,
            'system_roi_pct': system_roi_pct,
            'tolerance_pct': tolerance_pct,
            'agent_count': agent_count
        }
    
    # ========== 内部方法 ==========
    
    def _validate_balance(self) -> bool:
        """验证资金池余额不为负"""
        if self.available_pool < 0:
            logger.error(f"❌ 资金池余额异常：${self.available_pool:.2f} < 0")
            return False
        return True
    
    def __repr__(self) -> str:
        return (
            f"CapitalPool("
            f"invested=${self.total_invested:,.2f}, "
            f"available=${self.available_pool:,.2f}, "
            f"transactions={len(self.transaction_log)})"
        )

