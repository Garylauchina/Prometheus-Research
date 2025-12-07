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
import uuid
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 自定义异常 - 账簿不一致错误（三大铁律第3关）
# ============================================================================
class LedgerInconsistencyError(Exception):
    """
    账簿不一致错误
    
    每笔交易后自动对账，发现不一致立即抛出此异常
    这是三大铁律第3关的守护机制！
    """
    def __init__(self, agent_id: str, issues: list, details: dict = None):
        self.agent_id = agent_id
        self.issues = issues
        self.details = details or {}
        
        message = f"\n{'='*80}\n"
        message += f"❌ 账簿不一致错误 - Agent: {agent_id}\n"
        message += f"{'='*80}\n"
        message += "检测到以下问题：\n"
        for i, issue in enumerate(issues, 1):
            message += f"  {i}. {issue}\n"
        
        if details:
            message += f"\n详细信息：\n"
            for key, value in details.items():
                message += f"  {key}: {value}\n"
        
        message += f"{'='*80}\n"
        message += "⚠️ 这是三大铁律第3关的守护！账簿一致性是系统生命线！\n"
        message += f"{'='*80}\n"
        
        super().__init__(message)


# ========== 数据类定义 ==========

@dataclass
class TradeRecord:
    """交易记录（公私账簿共用）"""
    agent_id: str
    trade_id: str
    trade_type: str  # 'buy', 'sell', 'short', 'cover', 'add', 'add_short'
    amount: float
    price: float
    timestamp: datetime
    confidence: float
    pnl: Optional[float] = None  # 平仓时才有
    is_real: bool = True  # True=实际交易, False=虚拟交易
    position_side: Optional[str] = None  # 'long' or 'short' (双向持仓模式)
    okx_order_id: Optional[str] = None  # OKX订单ID（用于精确对账）
    inst_id: Optional[str] = "BTC-USDT-SWAP"  # 标的
    reduce_only: bool = False
    closed: bool = False  # 是否为平仓交易
    closed_at: Optional[datetime] = None
    
    def to_dict(self):
        """转为字典（用于序列化）"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        if d.get('closed_at'):
            d['closed_at'] = d['closed_at'].isoformat()
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
    closed: bool = False
    closed_at: Optional[datetime] = None
    closed_pnl: Optional[float] = None
    
    # OKX 交易费率（Taker市价单）
    TAKER_FEE_RATE: float = 0.0005  # 0.05%
    
    def get_unrealized_pnl(self, current_price: float, include_fees: bool = True) -> float:
        """
        计算未实现盈亏（含交易费）
        
        Args:
            current_price: 当前价格
            include_fees: 是否扣除交易费（默认True）
            
        Returns:
            float: 未实现盈亏（已扣除开仓费和预估平仓费）
        """
        # 计算基础盈亏（方向性）
        if self.side == "long":
            base_pnl = (current_price - self.entry_price) * self.amount
        else:  # short
            base_pnl = (self.entry_price - current_price) * self.amount
        
        # 扣除交易费（开仓时已扣 + 平仓时将扣）
        if include_fees:
            entry_fee = self.entry_price * self.amount * self.TAKER_FEE_RATE  # 开仓费
            exit_fee = current_price * self.amount * self.TAKER_FEE_RATE      # 平仓费
            return base_pnl - entry_fee - exit_fee
        
        return base_pnl
    
    def get_pnl_ratio(self, current_price: float, include_fees: bool = True) -> float:
        """
        计算盈亏比例（相对于入场金额）
        
        Returns:
            float: 盈亏比例 (e.g., 0.05 = 5% profit)
        """
        position_value = self.entry_price * self.amount
        if position_value == 0:
            return 0.0
        
        pnl = self.get_unrealized_pnl(current_price, include_fees)
        return pnl / position_value
    
    def to_dict(self):
        """转为字典（用于序列化）"""
        return {
            'agent_id': self.agent_id,
            'side': self.side,
            'amount': self.amount,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'confidence': self.confidence
        }


# ========== 访问权限控制 ==========

class Role(Enum):
    """角色定义"""
    MASTERMIND = "mastermind"
    SUPERVISOR = "supervisor"
    MOIRAI = "moirai"  # ✅ V6新增：命运三女神
    AGENT = "agent"


class AccessDeniedException(Exception):
    """访问被拒绝异常"""
    pass


# ========== 账簿不一致处理 ==========

class DiscrepancyType(Enum):
    """不一致类型"""
    TRADE_COUNT_MISMATCH = "trade_count_mismatch"       # 交易笔数不一致
    POSITION_AMOUNT_MISMATCH = "position_amount_mismatch"  # 持仓数量不一致
    POSITION_PRICE_MISMATCH = "position_price_mismatch"    # 入场价格不一致
    BALANCE_MISMATCH = "balance_mismatch"               # 余额不一致
    OKX_POSITION_MISMATCH = "okx_position_mismatch"     # 与OKX实际持仓不一致
    UNCLAIMED_OKX_POSITION = "unclaimed_okx_position"   # 无人认领的OKX持仓


class ReconciliationAction(Enum):
    """
    修复动作 - Supervisor自动决策
    
    优先级规则：OKX实际 > 公共账簿 > 私有账簿
    - 涉及OKX的不一致：以OKX为准
    - 仅账簿间不一致：以公共账簿为准（Supervisor更权威）
    """
    NO_ACTION = "no_action"                 # 无需动作（差异在容忍范围内）
    SYNC_PRIVATE_TO_PUBLIC = "sync_private_to_public"   # 以公共账簿为准，覆盖私有账簿
    SYNC_PUBLIC_TO_PRIVATE = "sync_public_to_private"   # 以私有账簿为准，覆盖公共账簿（仅特殊情况）
    SYNC_BOTH_TO_OKX = "sync_both_to_okx"               # 以OKX实际为准，覆盖两个账簿
    RESET_POSITION = "reset_position"                   # 重置持仓记录
    RECALCULATE_BALANCE = "recalculate_balance"         # 重新计算余额


@dataclass
class DiscrepancyRecord:
    """不一致记录"""
    agent_id: str
    discrepancy_type: DiscrepancyType
    description: str
    private_value: any
    public_value: any
    okx_value: any = None
    detected_at: datetime = None
    action_taken: ReconciliationAction = None
    action_result: str = ""
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
    
    def to_dict(self):
        return {
            'agent_id': self.agent_id,
            'type': self.discrepancy_type.value,
            'description': self.description,
            'private_value': self.private_value,
            'public_value': self.public_value,
            'okx_value': self.okx_value,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'action_taken': self.action_taken.value if self.action_taken else None,
            'action_result': self.action_result
        }


class LedgerReconciler:
    """
    账簿调节器 - Supervisor使用
    
    职责：
    1. 检测公共账簿和私有账簿的不一致
    2. 检测与OKX实际持仓的不一致
    3. 自动决策并立即修复
    
    修复优先级：OKX实际 > 公共账簿 > 私有账簿
    """
    
    # 容忍阈值
    AMOUNT_TOLERANCE = 0.0001      # 数量容差（0.01%）
    PRICE_TOLERANCE = 0.01         # 价格容差（1%）
    BALANCE_TOLERANCE = 0.01       # 余额容差（$0.01）
    
    def __init__(self):
        self.discrepancy_history: List[DiscrepancyRecord] = []
        self.reconciliation_count = 0
        logger.info("账簿调节器已初始化")
    
    def detect_discrepancies(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        okx_position: dict = None
    ) -> List[DiscrepancyRecord]:
        """
        检测所有类型的不一致
        
        检测项目：
        1. 空记录（无效交易）
        2. 孤儿订单（一边有另一边没有）
        3. 交易笔数不一致
        4. 持仓数量不一致
        5. 与OKX实际持仓不一致
        
        Args:
            agent_id: Agent ID
            private_ledger: 私有账簿
            public_ledger: 公共账簿
            okx_position: OKX实际持仓（可选，用于三方校验）
        
        Returns:
            检测到的不一致列表
        """
        discrepancies = []
        
        private_trades = private_ledger.get_trade_history(caller_role=Role.SUPERVISOR)
        public_trades = public_ledger.get_agent_trades(agent_id)
        
        # ========== 1. 检测空记录（无效交易）==========
        invalid_private = self._find_invalid_trades(private_trades)
        invalid_public = self._find_invalid_trades(public_trades)
        
        if invalid_private:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.TRADE_COUNT_MISMATCH,
                description=f"私有账簿存在{len(invalid_private)}条空/无效记录",
                private_value=[t.trade_id for t in invalid_private],
                public_value=None
            ))
        
        if invalid_public:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.TRADE_COUNT_MISMATCH,
                description=f"公共账簿存在{len(invalid_public)}条空/无效记录",
                private_value=None,
                public_value=[t.trade_id for t in invalid_public]
            ))
        
        # ========== 2. 检测孤儿订单 ==========
        private_trade_ids = {t.trade_id for t in private_trades if t.trade_id}
        public_trade_ids = {t.trade_id for t in public_trades if t.trade_id}
        
        # 私有账簿有但公共账簿没有的（孤儿在私有）
        orphans_in_private = private_trade_ids - public_trade_ids
        if orphans_in_private:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.TRADE_COUNT_MISMATCH,
                description=f"孤儿订单(仅私有): {len(orphans_in_private)}笔",
                private_value=list(orphans_in_private),
                public_value=None
            ))
        
        # 公共账簿有但私有账簿没有的（孤儿在公共）
        orphans_in_public = public_trade_ids - private_trade_ids
        if orphans_in_public:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.TRADE_COUNT_MISMATCH,
                description=f"孤儿订单(仅公共): {len(orphans_in_public)}笔",
                private_value=None,
                public_value=list(orphans_in_public)
            ))
        
        # ========== 3. 检测交易笔数不一致 ==========
        # 过滤掉无效记录后再比较
        valid_private = [t for t in private_trades if self._is_valid_trade(t)]
        valid_public = [t for t in public_trades if self._is_valid_trade(t)]
        
        if len(valid_private) != len(valid_public):
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.TRADE_COUNT_MISMATCH,
                description=f"有效交易笔数不一致: 私有{len(valid_private)}笔, 公共{len(valid_public)}笔",
                private_value=len(valid_private),
                public_value=len(valid_public)
            ))
        
        # ========== 4. 检测持仓不一致（支持双向持仓）==========
        calculated_positions = self._calculate_position_from_trades(valid_public)
        
        # 检查多头持仓
        private_long = private_ledger.long_position
        if private_long and private_long.amount > 0:
            public_long = calculated_positions['long']
            if abs(private_long.amount - public_long) > self.AMOUNT_TOLERANCE:
                discrepancies.append(DiscrepancyRecord(
                    agent_id=agent_id,
                    discrepancy_type=DiscrepancyType.POSITION_AMOUNT_MISMATCH,
                    description=f"多头持仓数量不一致: 私有{private_long.amount:.4f}, 公共计算{public_long:.4f}",
                    private_value=private_long.amount,
                    public_value=public_long
                ))
        
        # 检查空头持仓
        private_short = private_ledger.short_position
        if private_short and private_short.amount > 0:
            public_short = calculated_positions['short']
            if abs(private_short.amount - public_short) > self.AMOUNT_TOLERANCE:
                discrepancies.append(DiscrepancyRecord(
                    agent_id=agent_id,
                    discrepancy_type=DiscrepancyType.POSITION_AMOUNT_MISMATCH,
                    description=f"空头持仓数量不一致: 私有{private_short.amount:.4f}, 公共计算{public_short:.4f}",
                    private_value=private_short.amount,
                    public_value=public_short
                ))
        
        # 检查是否私有账簿无持仓但公共账簿计算有持仓
        if (not private_long or private_long.amount == 0) and calculated_positions['long'] > self.AMOUNT_TOLERANCE:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.POSITION_AMOUNT_MISMATCH,
                description=f"私有无多头但公共计算有: {calculated_positions['long']:.4f}",
                private_value=0,
                public_value=calculated_positions['long']
            ))
        
        if (not private_short or private_short.amount == 0) and calculated_positions['short'] > self.AMOUNT_TOLERANCE:
            discrepancies.append(DiscrepancyRecord(
                agent_id=agent_id,
                discrepancy_type=DiscrepancyType.POSITION_AMOUNT_MISMATCH,
                description=f"私有无空头但公共计算有: {calculated_positions['short']:.4f}",
                private_value=0,
                public_value=calculated_positions['short']
            ))
        
        # ========== 5. 与OKX实际持仓比对（三方校验）==========
        if okx_position is not None:
            okx_amount = okx_position.get('amount', 0)
            okx_side = okx_position.get('side', 'long')
            
            if okx_side == 'long':
                private_amount = private_long.amount if private_long else 0
                public_amount = calculated_positions['long']
            else:  # short
                private_amount = private_short.amount if private_short else 0
                public_amount = calculated_positions['short']
            
            if abs(okx_amount - private_amount) > self.AMOUNT_TOLERANCE:
                discrepancies.append(DiscrepancyRecord(
                    agent_id=agent_id,
                    discrepancy_type=DiscrepancyType.OKX_POSITION_MISMATCH,
                    description=f"与OKX不一致({okx_side}): 私有{private_amount:.4f}, 公共{public_amount:.4f}, OKX{okx_amount:.4f}",
                    private_value=private_amount,
                    public_value=public_amount,
                    okx_value=okx_amount
                ))
        
        return discrepancies
    
    def _is_valid_trade(self, trade: TradeRecord) -> bool:
        """检查交易记录是否有效"""
        if not trade:
            return False
        if not trade.trade_id:
            return False
        if trade.amount <= 0:
            return False
        if trade.price <= 0:
            return False
        return True
    
    def _find_invalid_trades(self, trades: List[TradeRecord]) -> List[TradeRecord]:
        """找出无效的交易记录"""
        return [t for t in trades if not self._is_valid_trade(t)]
    
    def reconcile(
        self,
        discrepancy: DiscrepancyRecord,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        okx_position: dict = None
    ) -> ReconciliationAction:
        """
        立即修复不一致 - Supervisor自动决策
        
        决策规则：
        1. 涉及OKX的不一致 -> 以OKX为准
        2. 空记录/无效记录 -> 清理
        3. 孤儿订单 -> 补齐或删除
        4. 仅账簿间不一致 -> 以公共账簿为准
        
        Args:
            discrepancy: 不一致记录
            private_ledger: 私有账簿
            public_ledger: 公共账簿
            okx_position: OKX实际持仓
        
        Returns:
            采取的修复动作
        """
        action = ReconciliationAction.NO_ACTION
        result = ""
        
        try:
            if discrepancy.discrepancy_type == DiscrepancyType.OKX_POSITION_MISMATCH:
                # 与OKX不一致 -> 以OKX为准（最高优先级）
                action = ReconciliationAction.SYNC_BOTH_TO_OKX
                result = self._sync_to_okx(
                    discrepancy.agent_id,
                    private_ledger,
                    public_ledger,
                    okx_position
                )
            
            elif discrepancy.discrepancy_type == DiscrepancyType.TRADE_COUNT_MISMATCH:
                desc = discrepancy.description
                
                if "空/无效记录" in desc:
                    # 清理无效记录
                    action = ReconciliationAction.SYNC_PRIVATE_TO_PUBLIC
                    result = self._clean_invalid_trades(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger
                    )
                
                elif "孤儿订单(仅私有)" in desc:
                    # 私有账簿有孤儿 -> 同步到公共账簿
                    action = ReconciliationAction.SYNC_PUBLIC_TO_PRIVATE
                    result = self._sync_orphans_to_public(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger,
                        discrepancy.private_value  # 孤儿trade_id列表
                    )
                
                elif "孤儿订单(仅公共)" in desc:
                    # 公共账簿有孤儿 -> 同步到私有账簿
                    action = ReconciliationAction.SYNC_PRIVATE_TO_PUBLIC
                    result = self._sync_orphans_to_private(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger,
                        discrepancy.public_value  # 孤儿trade_id列表
                    )
                
                else:
                    # 一般交易笔数不一致 -> 以公共账簿为准
                    action = ReconciliationAction.SYNC_PRIVATE_TO_PUBLIC
                    result = self._sync_trade_count(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger
                    )
            
            elif discrepancy.discrepancy_type == DiscrepancyType.POSITION_AMOUNT_MISMATCH:
                desc = discrepancy.description
                
                if "空持仓记录" in desc:
                    # 清理空持仓
                    action = ReconciliationAction.RESET_POSITION
                    result = self._clean_empty_position(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger
                    )
                else:
                    # 持仓数量不一致 -> 以公共账簿为准
                    action = ReconciliationAction.SYNC_PRIVATE_TO_PUBLIC
                    result = self._sync_position(
                        discrepancy.agent_id,
                        private_ledger,
                        public_ledger
                    )
            
            elif discrepancy.discrepancy_type == DiscrepancyType.BALANCE_MISMATCH:
                # 余额不一致 -> 重新计算
                action = ReconciliationAction.RECALCULATE_BALANCE
                result = self._recalculate_balance(
                    discrepancy.agent_id,
                    private_ledger,
                    public_ledger
                )
            
            # 记录修复结果
            discrepancy.action_taken = action
            discrepancy.action_result = result
            self.discrepancy_history.append(discrepancy)
            self.reconciliation_count += 1
            
            logger.info(f"[调节] {discrepancy.agent_id}: {action.value} - {result}")
            
        except Exception as e:
            discrepancy.action_taken = action
            discrepancy.action_result = f"修复失败: {str(e)}"
            self.discrepancy_history.append(discrepancy)
            logger.error(f"[调节失败] {discrepancy.agent_id}: {e}")
        
        return action
    
    def reconcile_all(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        okx_position: dict = None
    ) -> List[ReconciliationAction]:
        """
        检测并修复所有不一致
        
        Returns:
            所有采取的修复动作列表
        """
        discrepancies = self.detect_discrepancies(
            agent_id, private_ledger, public_ledger, okx_position
        )
        
        actions = []
        for d in discrepancies:
            # 输出详细的不一致信息
            logger.warning(f"[账簿不一致] {agent_id}: {d.discrepancy_type.value}")
            logger.warning(f"  描述: {d.description}")
            logger.warning(f"  私有: {d.private_value} | 公共: {d.public_value}")
            
            action = self.reconcile(d, private_ledger, public_ledger, okx_position)
            actions.append(action)
        
        return actions
    
    def _calculate_position_from_trades(self, trades: List[TradeRecord]) -> Dict[str, float]:
        """
        从交易记录计算应有持仓（支持双向持仓）
        
        Returns:
            {'long': float, 'short': float} - 多头和空头持仓数量
        """
        long_position = 0.0
        short_position = 0.0
        
        for trade in trades:
            if trade.trade_type == 'buy':
                # 开多或加多
                long_position += trade.amount
            elif trade.trade_type == 'sell':
                # 平多
                long_position -= trade.amount
            elif trade.trade_type == 'short':
                # 开空或加空
                short_position += trade.amount
            elif trade.trade_type == 'cover':
                # 平空
                short_position -= trade.amount
        
        return {
            'long': max(0, long_position),
            'short': max(0, short_position)
        }
    
    def _sync_to_okx(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        okx_position: dict
    ) -> str:
        """以OKX实际为准同步账簿"""
        okx_amount = okx_position.get('amount', 0)
        okx_entry_price = okx_position.get('entry_price', 0)
        
        # 重置私有账簿持仓
        if okx_amount > 0:
            private_ledger.position = PositionRecord(
                agent_id=agent_id,
                side='long',
                amount=okx_amount,
                entry_price=okx_entry_price,
                opened_at=datetime.now(),
                confidence=1.0
            )
        else:
            private_ledger.position = None
        
        return f"已同步至OKX: {okx_amount} @ ${okx_entry_price}"
    
    def _sync_trade_count(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger'
    ) -> str:
        """以公共账簿交易记录为准同步"""
        public_trades = public_ledger.get_agent_trades(agent_id)
        
        # 清空私有账簿交易记录，用公共账簿重建
        private_ledger.trade_history = list(public_trades)
        
        return f"已从公共账簿同步{len(public_trades)}笔交易记录"
    
    def _sync_position(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger'
    ) -> str:
        """以公共账簿计算的持仓为准同步（支持双向持仓）"""
        public_trades = public_ledger.get_agent_trades(agent_id)
        # 只使用有效交易计算
        valid_trades = [t for t in public_trades if self._is_valid_trade(t)]
        calculated_positions = self._calculate_position_from_trades(valid_trades)
        
        results = []
        
        # 同步多头持仓
        long_amount = calculated_positions['long']
        if long_amount > 0:
            # 计算加权平均入场价
            long_cost = sum(t.amount * t.price for t in valid_trades if t.trade_type == 'buy')
            avg_long_price = long_cost / long_amount if long_amount > 0 else 0
            
            private_ledger.long_position = PositionRecord(
                agent_id=agent_id,
                side='long',
                amount=long_amount,
                entry_price=avg_long_price,
                entry_time=datetime.now(),
                confidence=1.0
            )
            results.append(f"多头{long_amount:.4f}@${avg_long_price:.2f}")
        else:
            private_ledger.long_position = None
        
        # 同步空头持仓
        short_amount = calculated_positions['short']
        if short_amount > 0:
            # 计算加权平均入场价
            short_cost = sum(t.amount * t.price for t in valid_trades if t.trade_type == 'short')
            avg_short_price = short_cost / short_amount if short_amount > 0 else 0
            
            private_ledger.short_position = PositionRecord(
                agent_id=agent_id,
                side='short',
                amount=short_amount,
                entry_price=avg_short_price,
                entry_time=datetime.now(),
                confidence=1.0
            )
            results.append(f"空头{short_amount:.4f}@${avg_short_price:.2f}")
        else:
            private_ledger.short_position = None
        
        if results:
            return f"已重建持仓: {', '.join(results)}"
        else:
            private_ledger.position = None
            return "已清空持仓记录"
    
    def _clean_invalid_trades(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger'
    ) -> str:
        """清理无效交易记录"""
        # 清理私有账簿
        original_count = len(private_ledger.trade_history)
        private_ledger.trade_history = [
            t for t in private_ledger.trade_history
            if self._is_valid_trade(t)
        ]
        private_cleaned = original_count - len(private_ledger.trade_history)
        
        # 清理公共账簿（通过重建）
        public_trades = public_ledger.get_agent_trades(agent_id)
        original_public = len(public_trades)
        valid_public = [t for t in public_trades if self._is_valid_trade(t)]
        public_cleaned = original_public - len(valid_public)
        
        # 更新公共账簿
        if public_cleaned > 0:
            public_ledger.trades_by_agent[agent_id] = valid_public
        
        return f"已清理无效记录: 私有{private_cleaned}条, 公共{public_cleaned}条"
    
    def _sync_orphans_to_public(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        orphan_trade_ids: List[str]
    ) -> str:
        """
        把私有账簿的孤儿订单同步到公共账簿
        
        私有账簿有记录但公共账簿没有 -> 补充到公共账簿
        """
        if not orphan_trade_ids:
            return "无孤儿订单需同步"
        
        synced = 0
        for trade in private_ledger.trade_history:
            if trade.trade_id in orphan_trade_ids and self._is_valid_trade(trade):
                # 添加到公共账簿
                public_ledger.record_trade(trade, caller_role=Role.SUPERVISOR)
                synced += 1
        
        return f"已将{synced}笔孤儿订单同步至公共账簿"
    
    def _sync_orphans_to_private(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger',
        orphan_trade_ids: List[str]
    ) -> str:
        """
        把公共账簿的孤儿订单同步到私有账簿
        
        公共账簿有记录但私有账簿没有 -> 补充到私有账簿
        """
        if not orphan_trade_ids:
            return "无孤儿订单需同步"
        
        synced = 0
        public_trades = public_ledger.get_agent_trades(agent_id)
        
        for trade in public_trades:
            if trade.trade_id in orphan_trade_ids and self._is_valid_trade(trade):
                # 添加到私有账簿
                private_ledger.trade_history.append(trade)
                synced += 1
        
        return f"已将{synced}笔孤儿订单同步至私有账簿"
    
    def _clean_empty_position(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger'
    ) -> str:
        """清理空持仓记录（支持双向持仓）"""
        # 清理空的多头持仓
        if private_ledger.long_position and private_ledger.long_position.amount <= 0:
            private_ledger.long_position = None
        
        # 清理空的空头持仓  
        if private_ledger.short_position and private_ledger.short_position.amount <= 0:
            private_ledger.short_position = None
        
        # 重新根据公共账簿计算持仓
        public_trades = public_ledger.get_agent_trades(agent_id)
        valid_trades = [t for t in public_trades if self._is_valid_trade(t)]
        calculated_positions = self._calculate_position_from_trades(valid_trades)
        
        # 如果公共账簿计算出有持仓但私有账簿没有，重建
        results = []
        
        long_amount = calculated_positions['long']
        if long_amount > 0 and (not private_ledger.long_position or private_ledger.long_position.amount == 0):
            long_cost = sum(t.amount * t.price for t in valid_trades if t.trade_type == 'buy')
            avg_price = long_cost / long_amount if long_amount > 0 else 0
            private_ledger.long_position = PositionRecord(
                agent_id=agent_id,
                side='long',
                amount=long_amount,
                entry_price=avg_price,
                entry_time=datetime.now(),
                confidence=1.0
            )
            results.append(f"重建多头{long_amount:.4f}")
        
        short_amount = calculated_positions['short']
        if short_amount > 0 and (not private_ledger.short_position or private_ledger.short_position.amount == 0):
            short_cost = sum(t.amount * t.price for t in valid_trades if t.trade_type == 'short')
            avg_price = short_cost / short_amount if short_amount > 0 else 0
            private_ledger.short_position = PositionRecord(
                agent_id=agent_id,
                side='short',
                amount=short_amount,
                entry_price=avg_price,
                entry_time=datetime.now(),
                confidence=1.0
            )
            results.append(f"重建空头{short_amount:.4f}")
        
        if results:
            return f"已清理并重建: {', '.join(results)}"
        else:
            return "已清理空持仓记录"
    
    def _recalculate_balance(
        self,
        agent_id: str,
        private_ledger: 'PrivateLedger',
        public_ledger: 'PublicLedger'
    ) -> str:
        """重新计算余额"""
        initial = private_ledger.initial_capital
        public_trades = public_ledger.get_agent_trades(agent_id)
        
        # 从交易记录重新计算
        balance = initial
        for trade in public_trades:
            if trade.trade_type == 'buy':
                balance -= trade.amount * trade.price
            elif trade.trade_type == 'sell':
                balance += trade.amount * trade.price
                if trade.pnl:
                    balance += trade.pnl
        
        old_balance = private_ledger.balance
        private_ledger.balance = balance
        
        return f"余额已重算: ${old_balance:.2f} -> ${balance:.2f}"
    
    def get_reconciliation_summary(self) -> dict:
        """获取调节统计摘要"""
        if not self.discrepancy_history:
            return {'total': 0, 'by_type': {}, 'by_action': {}}
        
        by_type = {}
        by_action = {}
        
        for d in self.discrepancy_history:
            t = d.discrepancy_type.value
            by_type[t] = by_type.get(t, 0) + 1
            
            if d.action_taken:
                a = d.action_taken.value
                by_action[a] = by_action.get(a, 0) + 1
        
        return {
            'total': len(self.discrepancy_history),
            'by_type': by_type,
            'by_action': by_action
        }


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
        
        # 持仓状态（双向持仓：可同时持有多空）
        self.virtual_position: Optional[PositionRecord] = None  # 保留兼容
        self.real_position: Optional[PositionRecord] = None     # 保留兼容（指向主要持仓）
        
        # 双向持仓：分离的多空持仓
        self.long_position: Optional[PositionRecord] = None   # 多头持仓
        self.short_position: Optional[PositionRecord] = None  # 空头持仓
        
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
    
    @property
    def position(self) -> Optional[PositionRecord]:
        """持仓（real_position的别名，用于兼容调节器）"""
        return self.real_position
    
    @position.setter
    def position(self, value: Optional[PositionRecord]):
        """设置持仓"""
        self.real_position = value
    
    @property
    def balance(self) -> float:
        """余额（virtual_capital的别名，用于兼容调节器）"""
        return self.virtual_capital
    
    @balance.setter
    def balance(self, value: float):
        """设置余额"""
        self.virtual_capital = value
    
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
        elif caller_role in [Role.SUPERVISOR, Role.MOIRAI]:
            # ✅ V6：Supervisor或Moirai通过AgentAccountSystem间接修改（系统操作）
            # caller_id=='system' 表示这是系统操作，允许
            if caller_id != 'system':
                raise AccessDeniedException(
                    f"{caller_role.value} 只能通过AgentAccountSystem修改私有账簿"
                )
        elif caller_role == Role.MASTERMIND:
            # Mastermind无权访问私有账簿
            raise AccessDeniedException(
                "Mastermind 无权访问私有账簿"
            )
    
    # ========== 状态查询（Agent决策时使用）==========
    
    def has_position(self, position_type='real', side: str = None) -> bool:
        """
        检查是否有持仓（支持双向持仓）
        
        Args:
            position_type: 'real' or 'virtual'
            side: 'long', 'short', or None(任意一边)
        """
        if side == 'long':
            return self.long_position is not None and self.long_position.amount > 0
        elif side == 'short':
            return self.short_position is not None and self.short_position.amount > 0
        else:
            # 检查是否有任意方向的持仓
            return (self.long_position is not None and self.long_position.amount > 0) or \
                   (self.short_position is not None and self.short_position.amount > 0)
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """获取未实现盈亏（汇总多空两个方向）"""
        total_unrealized = 0.0
        
        # 多头未实现盈亏
        if self.long_position and self.long_position.amount > 0:
            total_unrealized += self.long_position.get_unrealized_pnl(current_price)
        
        # 空头未实现盈亏
        if self.short_position and self.short_position.amount > 0:
            total_unrealized += self.short_position.get_unrealized_pnl(current_price)
        
        return total_unrealized
    
    def calculate_unrealized_pnl(self, current_price: float):
        """
        计算并更新未实现盈亏（Supervisor调用）
        
        这是一个便捷方法，计算结果存储在内部状态中
        """
        # 计算虚拟持仓的未实现盈亏
        unrealized = 0.0
        if self.virtual_position:
            unrealized += self.virtual_position.get_unrealized_pnl(current_price)
        
        # 实际持仓的未实现盈亏
        if self.real_position:
            unrealized += self.real_position.get_unrealized_pnl(current_price)
        
        # 可以存储到统计数据中
        # self.unrealized_pnl = unrealized  # 如果需要存储
    
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
        
        # 双向持仓信息
        has_long = self.long_position is not None and self.long_position.amount > 0
        has_short = self.short_position is not None and self.short_position.amount > 0
        
        # 为了向后兼容，设置 real_position 为主要持仓（多头优先）
        if has_long:
            self.real_position = self.long_position
        elif has_short:
            self.real_position = self.short_position
        else:
            self.real_position = None
        
        return {
            'agent_id': self.agent_id,
            'balance': self.virtual_capital,
            'initial_capital': self.initial_capital,
            'capital_ratio': self.virtual_capital / self.initial_capital,
            
            # 兼容旧代码：has_position 表示是否有任意方向持仓
            'has_position': has_long or has_short,
            'position_side': self.real_position.side if self.real_position else None,
            
            # 兼容旧代码：position_info 返回主要持仓
            'position_info': {
                'amount': self.real_position.amount if self.real_position else 0,
                'entry_price': self.real_position.entry_price if self.real_position else 0,
                'side': self.real_position.side if self.real_position else None,
                'unrealized_pnl': unrealized_pnl
            } if self.real_position else None,
            
            # 新增：双向持仓详细信息
            'long_position': {
                'amount': self.long_position.amount if has_long else 0,
                'entry_price': self.long_position.entry_price if has_long else 0,
                'unrealized_pnl': self.long_position.get_unrealized_pnl(current_price) if has_long else 0
            } if has_long else None,
            
            'short_position': {
                'amount': self.short_position.amount if has_short else 0,
                'entry_price': self.short_position.entry_price if has_short else 0,
                'unrealized_pnl': self.short_position.get_unrealized_pnl(current_price) if has_short else 0
            } if has_short else None,
            
            'total_pnl': self.total_pnl,
            'unrealized_pnl': unrealized_pnl,
            'win_rate': self.get_win_rate(),
            'trade_count': self.trade_count,
            'last_trade_time': self.last_trade_time
        }
    
    def get_trade_history(self, caller_role: Role = Role.SUPERVISOR, caller_id: str = None) -> List[TradeRecord]:
        """
        获取交易历史
        
        Args:
            caller_role: 调用者角色
            caller_id: 调用者ID
        
        Returns:
            交易记录列表
        """
        self._check_read_access(caller_role, caller_id)
        return self.trade_history
    
    # ========== 交易记录（Agent和Supervisor都可以调用）==========
    
    def record_buy(self, amount: float, price: float, confidence: float,
                   caller_role: Role = Role.AGENT, caller_id: str = None,
                   okx_order_id: str = None):
        """
        记录买入（支持加仓）
        
        如果已有持仓，则累加持仓量并计算加权平均入场价
        
        Args:
            amount: 买入数量
            price: 买入价格
            confidence: 信心度
            is_real: 是否实盘
            caller_role: 调用者角色（用于权限检查）
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        # 参数校验
        if amount is None or price is None or amount <= 0 or price <= 0:
            raise ValueError(f"record_buy 参数非法 amount={amount}, price={price}")
        
        # 双向持仓：买入只影响多头持仓
        # ✅ 统一使用long_position，不再区分is_real
        existing_long = self.long_position
        
        if existing_long and existing_long.amount > 0:
            # 加多仓：计算新的加权平均入场价
            old_amount = existing_long.amount
            old_price = existing_long.entry_price
            new_total_amount = old_amount + amount
            # 加权平均价 = (旧持仓*旧价 + 新买入*新价) / 总持仓
            new_avg_price = (old_amount * old_price + amount * price) / new_total_amount
            
            position = PositionRecord(
                agent_id=self.agent_id,
                side='long',
                amount=new_total_amount,  # 累加持仓量
                entry_price=new_avg_price,  # 加权平均入场价
                entry_time=existing_long.entry_time,  # 保留原始入场时间
                confidence=confidence
            )
            logger.debug(f"{self.agent_id}: 加多仓 {amount}→总多仓{new_total_amount:.3f}, 均价${new_avg_price:.2f}")
        else:
            # 新开多仓
            position = PositionRecord(
                agent_id=self.agent_id,
                side='long',
                amount=amount,
                entry_price=price,
                entry_time=datetime.now(),
                confidence=confidence
            )
            logger.debug(f"{self.agent_id}: 开多 {amount} @ ${price}")
        
        # ✅ 统一使用long_position，彻底废除双轨制！
        self.long_position = position
        # ❌ 删除所有对real_position和virtual_position的写入
        # 不再维护这些字段，避免不一致
        
        # 记录交易
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{uuid.uuid4().hex[:12]}",
            trade_type='buy',
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            is_real=True,  # ✅ V6：统一使用long_position/short_position，不再区分is_real
            position_side='long',  # 买入总是影响多头
            okx_order_id=okx_order_id,
            closed=False,
            inst_id="BTC-USDT-SWAP",
            reduce_only=False
        )
        self.trade_history.append(trade)
        self.trade_count += 1
        self.last_trade_time = datetime.now()
        
        logger.debug(f"{self.agent_id}: 私有账簿记录买入 {amount} @ ${price}")
    
    def record_sell(self, price: float, confidence: float,
                    caller_role: Role = Role.AGENT, caller_id: str = None,
                    okx_order_id: str = None) -> float:
        """
        记录卖出，返回盈亏
        
        Args:
            caller_role: 调用者角色（用于权限检查）
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        # 参数校验
        if price is None or price <= 0:
            raise ValueError(f"record_sell 参数非法 price={price}")
        
        # 双向持仓：卖出只处理多头持仓
        # ✅ 统一使用long_position,废除双轨制
        long_pos = self.long_position
        
        # 初始化盈亏和数量
        pnl = 0.0
        sell_amount = 0.0
        
        if not long_pos or long_pos.amount == 0:
            raise RuntimeError(f"{self.agent_id}: 无多头持仓，无法卖出")
        else:
            # 计算盈亏
            pnl = long_pos.get_unrealized_pnl(price)
            sell_amount = long_pos.amount
            
            # 更新统计
            self.total_pnl += pnl
            self.virtual_capital += pnl
            
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1
            
            # ✅ 统一清除多头持仓，彻底废除双轨制！
            # 标记持仓已平
            long_pos.closed = True
            long_pos.closed_at = datetime.now()
            long_pos.closed_pnl = pnl
            self.long_position = None  # 清除持仓
            # ❌ 删除所有对real_position和virtual_position的操作
            
            logger.debug(f"{self.agent_id}: 平多 {sell_amount} @ ${price}, PnL=${pnl:.2f}")
        
        # 记录交易（无论是否有持仓都要记录，保持账簿一致性）
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{uuid.uuid4().hex[:12]}",
            trade_type='sell',
            amount=sell_amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            pnl=pnl,
            is_real=True,  # ✅ V6：统一使用long_position/short_position
            position_side='long',  # 卖出总是平多头
            okx_order_id=okx_order_id,
            closed=True,
            closed_at=datetime.now(),
            inst_id="BTC-USDT-SWAP",
            reduce_only=True
        )
        self.trade_history.append(trade)
        self.trade_count += 1  # 每笔交易都要计数
        self.last_trade_time = datetime.now()
        # ❌ 删除重复的持仓清除逻辑（已在上面处理）
        
        logger.debug(f"{self.agent_id}: 私有账簿记录卖出 PnL=${pnl:.2f}")
        return pnl
    
    def record_short(self, amount: float, price: float, confidence: float,
                     caller_role: Role = Role.AGENT, caller_id: str = None,
                     okx_order_id: str = None):
        """
        记录开空（支持加空）
        
        如果已有空仓，则累加空仓量并计算加权平均入场价
        
        Args:
            amount: 做空数量
            price: 做空价格
            confidence: 信心度
            is_real: 是否实盘
            caller_role: 调用者角色
            caller_id: 调用者ID
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        
        # 双向持仓：开空只影响空头持仓
        # ✅ 统一使用short_position，不再区分is_real
        existing_short = self.short_position
        
        if existing_short and existing_short.amount > 0:
            # 加空：计算新的加权平均入场价
            old_amount = existing_short.amount
            old_price = existing_short.entry_price
            new_total_amount = old_amount + amount
            # 加权平均价 = (旧空仓*旧价 + 新开空*新价) / 总空仓
            new_avg_price = (old_amount * old_price + amount * price) / new_total_amount
            
            position = PositionRecord(
                agent_id=self.agent_id,
                side='short',
                amount=new_total_amount,
                entry_price=new_avg_price,
                entry_time=existing_short.entry_time,
                confidence=confidence
            )
            logger.debug(f"{self.agent_id}: 加空 {amount}→总空仓{new_total_amount:.3f}, 均价${new_avg_price:.2f}")
        else:
            # 新开空仓（双向持仓模式下，不检查是否有多仓）
            position = PositionRecord(
                agent_id=self.agent_id,
                side='short',
                amount=amount,
                entry_price=price,
                entry_time=datetime.now(),
                confidence=confidence
            )
            logger.debug(f"{self.agent_id}: 开空 {amount} @ ${price}")
        
        # ✅ 统一使用short_position，彻底废除双轨制！
        self.short_position = position
        # ❌ 删除所有对real_position和virtual_position的写入
        
        # 记录交易（无论成功失败都要记录，保持账簿一致性）
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{uuid.uuid4().hex[:12]}",
            trade_type='short',
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            pnl=0.0,
            is_real=True,  # ✅ V6：统一使用long_position/short_position
            position_side='short',  # 开空总是影响空头
            okx_order_id=okx_order_id,
            closed=False,
            inst_id="BTC-USDT-SWAP",
            reduce_only=False
        )
        self.trade_history.append(trade)
        self.trade_count += 1  # 每笔交易都要计数
        self.last_trade_time = datetime.now()
        
        logger.debug(f"{self.agent_id}: 私有账簿记录开空 {amount} @ ${price}")
    
    def record_cover(self, price: float, confidence: float,
                     caller_role: Role = Role.AGENT, caller_id: str = None,
                     okx_order_id: str = None) -> float:
        """
        记录平空（cover），返回盈亏
        
        Args:
            price: 平仓价格
            confidence: 信心度
            is_real: 是否实盘
            caller_role: 调用者角色
            caller_id: 调用者ID
            
        Returns:
            float: 盈亏金额（做空：入场价-平仓价）
        """
        # 权限检查
        self._check_write_access(caller_role, caller_id)
        
        # 双向持仓：平空只处理空头持仓
        # ✅ 统一使用short_position,废除双轨制
        short_pos = self.short_position
        
        # 初始化盈亏和数量
        pnl = 0.0
        cover_amount = 0.0
        
        if not short_pos or short_pos.amount == 0:
            raise RuntimeError(f"{self.agent_id}: 无空头持仓，无法平空")
        else:
            # 正常平空
            # 计算盈亏（做空盈亏 = (入场价 - 平仓价) * 数量）
            pnl = short_pos.get_unrealized_pnl(price)
            cover_amount = short_pos.amount
            
            # 更新统计
            self.total_pnl += pnl
            self.virtual_capital += pnl
            
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1
            
            # ✅ 统一清除空头持仓，彻底废除双轨制！
            # 标记持仓已平
            short_pos.closed = True
            short_pos.closed_at = datetime.now()
            short_pos.closed_pnl = pnl
            self.short_position = None  # 清除持仓
            # ❌ 删除所有对real_position和virtual_position的操作
            
            logger.debug(f"{self.agent_id}: 平空 {cover_amount} @ ${price}, PnL=${pnl:.2f}")
        
        # 记录交易（无论是否有持仓都要记录，保持账簿一致性）
        trade = TradeRecord(
            agent_id=self.agent_id,
            trade_id=f"{self.agent_id}_{uuid.uuid4().hex[:12]}",
            trade_type='cover',
            amount=cover_amount,
            price=price,
            timestamp=datetime.now(),
            confidence=confidence,
            pnl=pnl,
            is_real=True,  # ✅ V6：统一使用long_position/short_position
            position_side='short',  # 平空总是影响空头
            okx_order_id=okx_order_id,
            closed=True,
            closed_at=datetime.now(),
            inst_id="BTC-USDT-SWAP",
            reduce_only=True
        )
        self.trade_history.append(trade)
        self.trade_count += 1  # 每笔交易都要计数
        self.last_trade_time = datetime.now()
        # ❌ 删除重复的持仓清除逻辑（已在上面处理）
        
        logger.debug(f"{self.agent_id}: 私有账簿记录平空 PnL=${pnl:.2f}")
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

    def _calculate_position_from_trades(self, trades: List[TradeRecord]) -> Dict[str, float]:
        """
        从交易列表计算多/空持仓数量（与 LedgerReconciler 逻辑保持一致）
        """
        long_position = 0.0
        short_position = 0.0
        for trade in trades:
            if trade.trade_type == 'buy':
                long_position += trade.amount
            elif trade.trade_type == 'sell':
                long_position -= trade.amount
            elif trade.trade_type == 'short':
                short_position += trade.amount
            elif trade.trade_type == 'cover':
                short_position -= trade.amount
        return {'long': max(0, long_position), 'short': max(0, short_position)}
    
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
        if caller_role not in [Role.SUPERVISOR, Role.MOIRAI]:
            # ✅ V6：只有Supervisor或Moirai可以写入公共账簿
            raise AccessDeniedException(
                f"{caller_role.value} 无权修改公共账簿，只有Supervisor/Moirai可以修改"
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
    
    def record_trade(self, trade_type: str, amount: float, price: float, confidence: float,
                    caller_role: Role = Role.MOIRAI, okx_order_id: str = None):
        """
        记录交易（同时更新私有和公共账簿）
        
        只有Moirai才能调用此方法
        
        Args:
            trade_type: 'buy', 'sell', 'short', 'cover'
            amount: 交易数量
            price: 交易价格（应使用OKX实际成交价格）
            confidence: 信心度
            caller_role: 调用者角色
            okx_order_id: OKX订单ID（用于精确对账）
        """
        # ✅ 仅允许 Moirai 写账簿，且必须是有效数值
        if caller_role not in [Role.MOIRAI, Role.SUPERVISOR]:  # 兼容旧代码
            raise PermissionError("record_trade 必须由 Moirai 调用")
        if amount is None or price is None or amount <= 0 or price <= 0:
            raise ValueError(f"record_trade 参数非法 amount={amount}, price={price}")

        # Moirai调用，有权限更新私有账簿（但以系统身份）
        # 1. 更新私有账簿（Moirai以系统身份更新，不需要检查）
        pnl = None
        before_private_count = len(self.private_ledger.trade_history)
        
        if trade_type == 'buy':
            self.private_ledger.record_buy(
                amount, price, confidence,
                caller_role=Role.MOIRAI, caller_id='system',
                okx_order_id=okx_order_id
            )
        elif trade_type == 'sell':
            pnl = self.private_ledger.record_sell(
                price, confidence,
                caller_role=Role.MOIRAI, caller_id='system',
                okx_order_id=okx_order_id
            )
        elif trade_type == 'short':
            self.private_ledger.record_short(
                amount, price, confidence,
                caller_role=Role.MOIRAI, caller_id='system',
                okx_order_id=okx_order_id
            )
        elif trade_type == 'cover':
            pnl = self.private_ledger.record_cover(
                price, confidence,
                caller_role=Role.MOIRAI, caller_id='system',
                okx_order_id=okx_order_id
            )
        
        # 2. 提交到公共账簿（使用私有账簿的最后一笔交易记录，确保trade_id一致）
        after_private_count = len(self.private_ledger.trade_history)
        if after_private_count != before_private_count + 1:
            raise RuntimeError(f"{self.agent_id}: 私账写入计数异常 before={before_private_count}, after={after_private_count}")
        last_trade = self.private_ledger.trade_history[-1]
        self.public_ledger.record_trade(last_trade, caller_role=caller_role)

        # 3. 交易数一致性校验
        private_count = len(self.private_ledger.trade_history)
        public_count = len(self.public_ledger.get_agent_trades(self.agent_id))
        if private_count != public_count:
            raise RuntimeError(f"{self.agent_id}: 公私交易数不一致 private={private_count}, public={public_count}")

        # 4. 持仓一致性校验（基于公账交易序列重算）
        calc_pos = self.public_ledger._calculate_position_from_trades(self.public_ledger.get_agent_trades(self.agent_id))
        # ✅ 简化逻辑：统一使用long_position和short_position，不再检查virtual_position
        private_long = self.private_ledger.long_position.amount if self.private_ledger.long_position else 0.0
        private_short = self.private_ledger.short_position.amount if self.private_ledger.short_position else 0.0
        if abs(calc_pos.get('long', 0) - private_long) > 1e-8 or abs(calc_pos.get('short', 0) - private_short) > 1e-8:
            raise RuntimeError(
                f"{self.agent_id}: 公私持仓不一致 pub_long={calc_pos.get('long',0)}, pri_long={private_long}, "
                f"pub_short={calc_pos.get('short',0)}, pri_short={private_short}, "
                f"last_trade={last_trade.trade_type} {last_trade.amount} @ {last_trade.price}"
            )
        
        # 3. 更新公共账簿中的余额和统计
        self.public_ledger.update_agent_balance(self.agent_id, self.private_ledger.virtual_capital)
        self.public_ledger.update_agent_stats(self.agent_id, {
            'total_pnl': self.private_ledger.total_pnl,
            'trade_count': self.private_ledger.trade_count,
            'win_rate': self.private_ledger.get_win_rate()
        })
        
        # ✅ 4. 三大铁律第3关：每笔交易后自动对账验证
        self._verify_consistency_after_trade()
    
    def _verify_consistency_after_trade(self):
        """
        每笔交易后的自动对账验证（三大铁律第3关）
        
        检查项：
        1. 交易数量一致（已在record_trade中检查）
        2. 持仓一致（已在record_trade中检查）
        3. 空记录检查
        4. 金额合法性检查
        
        如果发现问题，立即抛出 LedgerInconsistencyError
        """
        issues = []
        details = {}
        
        # 检查1：私账中是否有空记录
        empty_private_trades = [
            t for t in self.private_ledger.trade_history 
            if t.amount == 0 or t.price == 0
        ]
        if empty_private_trades:
            issues.append(f"私账有{len(empty_private_trades)}条空记录（amount=0或price=0）")
            details['empty_private_count'] = len(empty_private_trades)
        
        # 检查2：公账中是否有空记录
        public_trades = self.public_ledger.get_agent_trades(self.agent_id)
        empty_public_trades = [
            t for t in public_trades 
            if t.amount == 0 or t.price == 0
        ]
        if empty_public_trades:
            issues.append(f"公账有{len(empty_public_trades)}条空记录（amount=0或price=0）")
            details['empty_public_count'] = len(empty_public_trades)
        
        # 检查3：最新一笔交易的合法性
        if self.private_ledger.trade_history:
            last_trade = self.private_ledger.trade_history[-1]
            if last_trade.amount <= 0:
                issues.append(f"最新交易amount非法: {last_trade.amount}")
            if last_trade.price <= 0:
                issues.append(f"最新交易price非法: {last_trade.price}")
            
            details['last_trade'] = {
                'trade_type': last_trade.trade_type,
                'amount': last_trade.amount,
                'price': last_trade.price,
                'timestamp': str(last_trade.timestamp)
            }
        
        # 检查4：交易数和持仓信息
        details['private_trade_count'] = len(self.private_ledger.trade_history)
        details['public_trade_count'] = len(public_trades)
        details['private_long_position'] = self.private_ledger.long_position.amount if self.private_ledger.long_position else 0
        details['private_short_position'] = self.private_ledger.short_position.amount if self.private_ledger.short_position else 0
        
        # 如果发现任何问题，立即抛出异常
        if issues:
            raise LedgerInconsistencyError(
                agent_id=self.agent_id,
                issues=issues,
                details=details
            )
    
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

